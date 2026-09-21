"""
Historical Simulation and Timeline Generation System
Simulates the complete history of a world from creation to the present day,
including the rise and fall of civilizations, major events, technological
advancement, and the formation of the current geopolitical landscape.
"""

import numpy as np
import random
from collections import defaultdict, deque
import math
from typing import List, Tuple, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

class EraType(Enum):
    MYTHICAL = "mythical"
    ANCIENT = "ancient"
    CLASSICAL = "classical"
    MEDIEVAL = "medieval"
    RENAISSANCE = "renaissance"
    INDUSTRIAL = "industrial"
    MODERN = "modern"
    FUTURE = "future"

class EventType(Enum):
    FOUNDING = "founding"
    CONQUEST = "conquest"
    DISCOVERY = "discovery"
    INVENTION = "invention"
    DISASTER = "disaster"
    ALLIANCE = "alliance"
    REVOLUTION = "revolution"
    TRADE = "trade"
    EXPLORATION = "exploration"
    RELIGIOUS_EVENT = "religious_event"
    CULTURAL_EVENT = "cultural_event"
    NATURAL_DISASTER = "natural_disaster"
    PLAGUE = "plague"
    WAR = "war"
    PEACE_TREATY = "peace_treaty"
    GOLDEN_AGE = "golden_age"
    DARK_AGE = "dark_age"

class CivilizationStatus(Enum):
    TRIBAL = "tribal"
    EMERGING = "emerging"
    ESTABLISHED = "established"
    EXPANDING = "expanding"
    DECLINING = "decling"
    COLLAPSED = "collapsed"
    DESTROYED = "destroyed"
    REBORN = "reborn"

class TechnologyTier(Enum):
    STONE = "stone"
    BRONZE = "bronze"
    IRON = "iron"
    MEDIEVAL = "medieval"
    RENAISSANCE = "renaissance"
    INDUSTRIAL = "industrial"
    MODERN = "modern"
    SPACE = "space"
    MAGICAL = "magical"

class GovernmentEvolution(Enum):
    TRIBAL_COUNCIL = "tribal_council"
    CHIEFDOM = "chiefdom"
    MONARCHY = "monarchy"
    REPUBLIC = "republic"
    EMPIRE = "empire"
    THEOCRACY = "theocracy"
    FEUDAL = "feudal"
    DEMOCRACY = "democracy"
    ANARCHY = "anarchy"
    MILITARY_DICTATORSHIP = "military_dictatorship"

@dataclass
class HistoricalEvent:
    """Represents a single historical event"""
    id: str
    name: str
    description: str
    event_type: EventType
    year: int
    location: Tuple[int, int]
    participants: List[str] = field(default_factory=list)  # Civilization names
    consequences: List[str] = field(default_factory=list)
    significance: float = 0.5  # 0.0 - 1.0
    era: EraType = EraType.ANCIENT
    related_events: List[str] = field(default_factory=list)
    impact_scope: str = "local"  # local, regional, continental, global

@dataclass
class Civilization:
    """Represents a civilization throughout history"""
    name: str
    founding_year: int
    collapse_year: Optional[int] = None
    status: CivilizationStatus = CivilizationStatus.TRIBAL
    government: GovernmentEvolution = GovernmentEvolution.TRIBAL_COUNCIL
    technology_tier: TechnologyTier = TechnologyTier.STONE
    territory: List[Tuple[int, int]] = field(default_factory=list)
    population_history: Dict[int, int] = field(default_factory=dict)
    capital: Optional[Tuple[int, int]] = None
    culture_name: str = ""
    language_family: str = ""
    religion: str = ""
    major_achievements: List[str] = field(default_factory=list)
    military_history: List[str] = field(default_factory=list)
    diplomatic_relations: Dict[str, str] = field(default_factory=dict)
    resource_control: Dict[str, float] = field(default_factory=dict)
    golden_ages: List[Tuple[int, int]] = field(default_factory=list)  # (start, end)
    dark_ages: List[Tuple[int, int]] = field(default_factory=list)
    notable_leaders: List[Tuple[int, str]] = field(default_factory=list)  # (year, name)

@dataclass
class Era:
    """Represents a historical era"""
    name: str
    era_type: EraType
    start_year: int
    end_year: int
    description: str
    major_events: List[str] = field(default_factory=list)
    dominant_civilizations: List[str] = field(default_factory=list)
    technological_advances: List[str] = field(default_factory=list)
    cultural_movements: List[str] = field(default_factory=list)

@dataclass
class Timeline:
    """Complete world timeline"""
    current_year: int
    start_year: int
    events: List[HistoricalEvent] = field(default_factory=list)
    civilizations: Dict[str, Civilization] = field(default_factory=dict)
    eras: List[Era] = field(default_factory=list)
    world_statistics: Dict[int, Dict] = field(default_factory=dict)

class HistoricalSimulator:
    """Simulates historical processes and patterns"""

    def __init__(self, width: int, height: int, seed: Optional[int] = None):
        self.width = width
        self.height = height
        self.seed = seed or random.randint(0, 2**31 - 1)
        random.seed(self.seed)
        np.random.seed(self.seed)

        # Historical parameters
        self.world_start_year = -5000  # 5000 years before current
        self.current_year = 0
        self.time_step = 25  # Years per simulation step

        # Simulation state
        self.civilizations = {}
        self.events = []
        self.eras = []

    def simulate_history(self, num_steps: int = 200) -> Timeline:
        """Run complete historical simulation"""
        timeline = Timeline(
            current_year=self.current_year,
            start_year=self.world_start_year
        )

        # Initialize eras
        self._initialize_eras()

        # Simulation steps
        for step in range(num_steps):
            year = self.world_start_year + (step + 1) * self.time_step
            self.current_year = year

            # Determine current era
            current_era = self._get_current_era(year)

            # Simulate this time period
            self._simulate_time_step(year, current_era)

            # Collect statistics
            self._collect_statistics(year)

        # Compile final timeline
        timeline.events = self.events
        timeline.civilizations = self.civilizations
        timeline.eras = self.eras
        timeline.world_statistics = self._compile_statistics()

        return timeline

    def _initialize_eras(self) -> None:
        """Initialize historical eras"""
        era_definitions = [
            (EraType.MYTHICAL, -5000, -3000, "Time of creation myths and legendary beings"),
            (EraType.ANCIENT, -3000, -1000, "Rise of the first civilizations"),
            (EraType.CLASSICAL, -1000, 500, "Golden age of ancient empires"),
            (EraType.MEDIEVAL, 500, 1500, "Age of feudalism and religious dominance"),
            (EraType.RENAISSANCE, 1500, 1800, "Cultural rebirth and exploration"),
            (EraType.INDUSTRIAL, 1800, 1950, "Industrial revolution and global expansion"),
            (EraType.MODERN, 1950, 2020, "Technological advancement and global conflicts"),
            (EraType.FUTURE, 2020, 2100, "Emerging technologies and new challenges")
        ]

        for era_type, start_year, end_year, description in era_definitions:
            era = Era(
                name=f"The {era_type.value.title()} Age",
                era_type=era_type,
                start_year=start_year,
                end_year=end_year,
                description=description
            )
            self.eras.append(era)

    def _get_current_era(self, year: int) -> Era:
        """Get current era based on year"""
        for era in self.eras:
            if era.start_year <= year <= era.end_year:
                return era
        return self.eras[-1]  # Default to last era

    def _simulate_time_step(self, year: int, era: Era) -> None:
        """Simulate one time step in history"""
        # Civilization emergence and evolution
        self._simulate_civilization_lifecycle(year, era)

        # Inter-civilization interactions
        self._simulate_civilization_interactions(year, era)

        # Natural disasters and environmental events
        self._simulate_natural_events(year, era)

        # Technological advancement
        self._simulate_technological_advancement(year, era)

        # Cultural developments
        self._simulate_cultural_development(year, era)

        # Economic changes
        self._simulate_economic_changes(year, era)

    def _simulate_civilization_lifecycle(self, year: int, era: Era) -> None:
        """Simulate civilization emergence, growth, and decline"""
        # Chance of new civilization emerging
        if random.random() < self._get_civilization_emergence_probability(year, era):
            self._create_new_civilization(year, era)

        # Update existing civilizations
        for civ_name, civ in list(self.civilizations.items()):
            self._update_civilization(civ, year, era)

            # Check for civilization collapse
            if civ.status not in [CivilizationStatus.COLLAPSED, CivilizationStatus.DESTROYED]:
                if self._should_civilization_collapse(civ, year):
                    self._collapse_civilization(civ, year)

    def _get_civilization_emergence_probability(self, year: int, era: Era) -> float:
        """Get probability of civilization emergence"""
        base_probability = 0.1

        # Adjust based on era
        era_multipliers = {
            EraType.MYTHICAL: 0.5,
            EraType.ANCIENT: 0.3,
            EraType.CLASSICAL: 0.1,
            EraType.MEDIEVAL: 0.05,
            EraType.RENAISSANCE: 0.03,
            EraType.INDUSTRIAL: 0.02,
            EraType.MODERN: 0.01,
            EraType.FUTURE: 0.01
        }

        multiplier = era_multipliers.get(era.era_type, 0.1)

        # Adjust based on existing civilizations
        existing_count = len([c for c in self.civilizations.values()
                            if c.status not in [CivilizationStatus.COLLAPSED, CivilizationStatus.DESTROYED]])
        if existing_count > 10:
            multiplier *= 0.5

        return base_probability * multiplier

    def _create_new_civilization(self, year: int, era: Era) -> None:
        """Create a new civilization"""
        # Generate civilization name
        name = self._generate_civilization_name()

        # Choose location
        location = self._choose_civilization_location()

        # Determine initial characteristics
        initial_status = CivilizationStatus.TRIBAL
        initial_government = self._determine_initial_government(era)
        initial_tech = self._determine_initial_technology(era)

        # Create civilization
        civilization = Civilization(
            name=name,
            founding_year=year,
            status=initial_status,
            government=initial_government,
            technology_tier=initial_tech,
            capital=location,
            territory=[location],
            culture_name=name + " Culture",
            language_family=self._generate_language_family(),
            religion=self._generate_initial_religion(era)
        )

        # Set initial population
        initial_population = random.randint(500, 5000)
        civilization.population_history[year] = initial_population

        # Add to civilizations
        self.civilizations[name] = civilization

        # Create founding event
        event = HistoricalEvent(
            id=f"founding_{name}_{year}",
            name=f"Founding of {name}",
            description=f"The {name} civilization is established in the region.",
            event_type=EventType.FOUNDING,
            year=year,
            location=location,
            participants=[name],
            significance=0.6,
            era=era.era_type,
            impact_scope="regional"
        )
        self.events.append(event)

    def _generate_civilization_name(self) -> str:
        """Generate civilization name"""
        prefixes = ["Ancient", "Great", "Northern", "Southern", "Eastern", "Western",
                   "High", "Low", "River", "Mountain", "Stone", "Golden", "Silver",
                   "Crystal", "Shadow", "Light", "Fire", "Ice", "Storm", "Sun", "Moon"]
        suffixes = ["Empire", "Kingdom", "Republic", "Dynasty", "Confederacy",
                   "League", "Alliance", "Principality", "Dominion", "Territory",
                   "Realm", "Nation", "State", "Culture", "People", "Tribe", "Clan"]

        if random.random() < 0.3:
            # Use prefix + suffix
            return f"{random.choice(prefixes)} {random.choice(suffixes)}"
        else:
            # Generate unique name
            syllables = ["tor", "gan", "dor", "vil", "nas", "car", "mar", "val",
                        "ria", "lia", "tia", "nia", "sia", "mia", "bia", "gia"]
            num_syllables = random.randint(2, 4)
            name = "".join(random.choice(syllables) for _ in range(num_syllables))
            return name.capitalize()

    def _choose_civilization_location(self) -> Tuple[int, int]:
        """Choose location for new civilization"""
        # Prefer certain areas for early civilizations
        if self.current_year < -2000:  # Ancient era
            # Prefer river valleys and coastal areas
            x = random.randint(10, self.width - 10)
            y = random.randint(10, self.height - 10)
        else:
            # More spread out
            x = random.randint(5, self.width - 5)
            y = random.randint(5, self.height - 5)

        return (y, x)

    def _determine_initial_government(self, era: Era) -> GovernmentEvolution:
        """Determine initial government type based on era"""
        if era.era_type in [EraType.MYTHICAL, EraType.ANCIENT]:
            return random.choice([GovernmentEvolution.TRIBAL_COUNCIL, GovernmentEvolution.CHIEFDOM])
        elif era.era_type == EraType.CLASSICAL:
            return random.choice([GovernmentEvolution.MONARCHY, GovernmentEvolution.REPUBLIC])
        elif era.era_type == EraType.MEDIEVAL:
            return random.choice([GovernmentEvolution.FEUDAL, GovernmentEvolution.MONARCHY])
        else:
            return GovernmentEvolution.REPUBLIC

    def _determine_initial_technology(self, era: Era) -> TechnologyTier:
        """Determine initial technology level based on era"""
        era_tech_map = {
            EraType.MYTHICAL: TechnologyTier.STONE,
            EraType.ANCIENT: TechnologyTier.BRONZE,
            EraType.CLASSICAL: TechnologyTier.IRON,
            EraType.MEDIEVAL: TechnologyTier.MEDIEVAL,
            EraType.RENAISSANCE: TechnologyTier.RENAISSANCE,
            EraType.INDUSTRIAL: TechnologyTier.INDUSTRIAL,
            EraType.MODERN: TechnologyTier.MODERN,
            EraType.FUTURE: TechnologyTier.SPACE
        }

        base_tech = era_tech_map.get(era.era_type, TechnologyTier.STONE)

        # Some variation
        tech_tiers = list(TechnologyTier)
        current_index = tech_tiers.index(base_tech)
        if current_index > 0 and random.random() < 0.3:
            base_tech = tech_tiers[current_index - 1]  # Slightly less advanced

        return base_tech

    def _generate_language_family(self) -> str:
        """Generate language family name"""
        families = ["Indo-European", "Sino-Tibetan", "Afro-Asiatic", "Austronesian",
                   "Niger-Congo", "Trans-New Guinea", "Isolated", "Ancient",
                   "Proto-World", "Mysterious", "Lost"]
        return random.choice(families)

    def _generate_initial_religion(self, era: Era) -> str:
        """Generate initial religion based on era"""
        if era.era_type == EraType.MYTHICAL:
            return random.choice(["Animism", "Nature Worship", "Ancestor Worship", "Pantheonism"])
        elif era.era_type in [EraType.ANCIENT, EraType.CLASSICAL]:
            return random.choice(["Polytheism", "State Religion", "Mystery Cults", "Philosophical Schools"])
        elif era.era_type == EraType.MEDIEVAL:
            return random.choice(["Organized Religion", "Monotheism", "Schismatic Movements"])
        else:
            return random.choice(["Secularism", "New Religious Movements", "Syncretism"])

    def _update_civilization(self, civ: Civilization, year: int, era: Era) -> None:
        """Update civilization state"""
        # Update population
        self._update_population(civ, year)

        # Update status
        self._update_civilization_status(civ, year)

        # Update government
        if random.random() < 0.1:  # 10% chance of government change
            self._evolve_government(civ, era)

        # Update technology
        if random.random() < 0.2:  # 20% chance of advancement
            self._advance_technology(civ, era)

        # Update territory
        if random.random() < 0.3:  # 30% chance of territory change
            self._update_territory(civ, year)

        # Check for golden or dark age
        self._check_age_transitions(civ, year)

    def _update_population(self, civ: Civilization, year: int) -> None:
        """Update civilization population"""
        last_pop = civ.population_history.get(max(civ.population_history.keys()), 1000)

        # Growth rate based on status and era
        base_growth_rate = 0.02  # 2% per year

        if civ.status == CivilizationStatus.EXPANDING:
            base_growth_rate *= 2.0
        elif civ.status == CivilizationStatus.DECLINING:
            base_growth_rate *= -0.5
        elif civ.status == CivilizationStatus.GOLDEN_AGE:
            base_growth_rate *= 1.5

        # Add some randomness
        growth_rate = base_growth_rate * random.uniform(0.5, 1.5)

        # Apply growth
        new_population = int(last_pop * math.exp(growth_rate * self.time_step))
        civ.population_history[year] = new_population

    def _update_civilization_status(self, civ: Civilization, year: int) -> None:
        """Update civilization status based on conditions"""
        current_pop = civ.population_history.get(year, 1000)
        max_pop = max(civ.population_history.values()) if civ.population_history else 1000

        # Determine status based on population trends
        if current_pop < max_pop * 0.3:
            if civ.status not in [CivilizationStatus.COLLAPSED, CivilizationStatus.DESTROYED]:
                civ.status = CivilizationStatus.DECLINING
        elif current_pop > max_pop * 1.2:
            civ.status = CivilizationStatus.EXPANDING
        elif civ.status == CivilizationStatus.DECLINING and current_pop > max_pop * 0.6:
            civ.status = CivilizationStatus.REBORN

    def _evolve_government(self, civ: Civilization, era: Era) -> None:
        """Evolve civilization government"""
        current_gov = civ.government

        # Define evolution paths
        evolution_paths = {
            GovernmentEvolution.TRIBAL_COUNCIL: [GovernmentEvolution.CHIEFDOM],
            GovernmentEvolution.CHIEFDOM: [GovernmentEvolution.MONARCHY, GovernmentEvolution.REPUBLIC],
            GovernmentEvolution.MONARCHY: [GovernmentEvolution.EMPIRE, GovernmentEvolution.FEUDAL, GovernmentEvolution.REPUBLIC],
            GovernmentEvolution.REPUBLIC: [GovernmentEvolution.EMPIRE, GovernmentEvolution.DEMOCRACY],
            GovernmentEvolution.FEUDAL: [GovernmentEvolution.MONARCHY, GovernmentEvolution.REPUBLIC],
            GovernmentEvolution.EMPIRE: [GovernmentEvolution.REPUBLIC, GovernmentEvolution.MILITARY_DICTATORSHIP],
            GovernmentEvolution.DEMOCRACY: [GovernmentEvolution.REPUBLIC, GovernmentEvolution.ANARCHY],
            GovernmentEvolution.THEOCRACY: [GovernmentEvolution.MONARCHY, GovernmentEvolution.REPUBLIC]
        }

        possible_evolutions = evolution_paths.get(current_gov, [])
        if possible_evolutions:
            new_gov = random.choice(possible_evolutions)

            # Create government change event
            event = HistoricalEvent(
                id=f"gov_change_{civ.name}_{year}",
                name=f"Government Reform in {civ.name}",
                description=f"{civ.name} transitions from {current_gov.value} to {new_gov.value}.",
                event_type=EventType.REVOLUTION,
                year=year,
                location=civ.capital or (0, 0),
                participants=[civ.name],
                significance=0.7,
                era=era.era_type,
                impact_scope="national"
            )
            self.events.append(event)

            civ.government = new_gov

    def _advance_technology(self, civ: Civilization, era: Era) -> None:
        """Advance civilization technology"""
        current_tech = civ.technology_tier
        tech_tiers = list(TechnologyTier)
        current_index = tech_tiers.index(current_tech)

        # Check if advancement is possible
        if current_index < len(tech_tiers) - 1:
            advancement_chance = 0.3  # Base 30% chance

            # Modify based on era and current status
            if civ.status == CivilizationStatus.EXPANDING:
                advancement_chance *= 1.5
            elif civ.status == CivilizationStatus.GOLDEN_AGE:
                advancement_chance *= 2.0

            if random.random() < advancement_chance:
                new_tech = tech_tiers[current_index + 1]
                civ.technology_tier = new_tech

                # Create invention event
                event = HistoricalEvent(
                    id=f"tech_advance_{civ.name}_{year}",
                    name=f"Technological Advancement in {civ.name}",
                    description=f"{civ.name} discovers {new_tech.value} technology.",
                    event_type=EventType.INVENTION,
                    year=year,
                    location=civ.capital or (0, 0),
                    participants=[civ.name],
                    significance=0.8,
                    era=era.era_type,
                    impact_scope="continental"
                )
                self.events.append(event)

                # Add to achievements
                civ.major_achievements.append(f"Developed {new_tech.value} technology")

    def _update_territory(self, civ: Civilization, year: int) -> None:
        """Update civilization territory"""
        if not civ.capital:
            return

        # Expansion or contraction based on status
        if civ.status == CivilizationStatus.EXPANDING:
            # Expand territory
            expansion_range = 3
        elif civ.status == CivilizationStatus.DECLINING:
            # Contract territory
            expansion_range = -1
        else:
            # Small changes
            expansion_range = random.choice([-1, 0, 1])

        if expansion_range != 0:
            # Add or remove territory
            for _ in range(abs(expansion_range)):
                if expansion_range > 0:
                    # Add new territory
                    new_pos = self._expand_territory(civ)
                    if new_pos and new_pos not in civ.territory:
                        civ.territory.append(new_pos)
                else:
                    # Remove territory
                    if len(civ.territory) > 1:
                        civ.territory.pop(random.randint(0, len(civ.territory) - 1))

    def _expand_territory(self, civ: Civilization) -> Optional[Tuple[int, int]]:
        """Expand civilization territory by one cell"""
        if not civ.territory:
            return None

        # Find border positions
        border_positions = []
        for pos in civ.territory:
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                new_pos = (pos[0] + dy, pos[1] + dx)
                if (0 <= new_pos[0] < self.height and
                    0 <= new_pos[1] < self.width and
                    new_pos not in civ.territory):
                    border_positions.append(new_pos)

        if border_positions:
            return random.choice(border_positions)
        return None

    def _check_age_transitions(self, civ: Civilization, year: int) -> None:
        """Check for golden age or dark age transitions"""
        current_pop = civ.population_history.get(year, 1000)
        recent_pops = [civ.population_history.get(y, 1000)
                      for y in range(year - 100, year + 1, 25)
                      if y in civ.population_history]

        if len(recent_pops) >= 3:
            # Check trends
            avg_recent = np.mean(recent_pops)
            trend = "increasing" if recent_pops[-1] > recent_pops[0] else "decreasing"

            # Golden age conditions
            if (trend == "increasing" and
                avg_recent > np.mean(list(civ.population_history.values())) * 1.5 and
                civ.status == CivilizationStatus.EXPANDING and
                not civ.golden_ages):

                # Start golden age
                civ.golden_ages.append((year, year + 200))  # 200 year golden age
                civ.status = CivilizationStatus.ESTABLISHED

                event = HistoricalEvent(
                    id=f"golden_age_{civ.name}_{year}",
                    name=f"Golden Age of {civ.name}",
                    description=f"{civ.name} enters a golden age of prosperity and cultural achievement.",
                    event_type=EventType.GOLDEN_AGE,
                    year=year,
                    location=civ.capital or (0, 0),
                    participants=[civ.name],
                    significance=0.9,
                    era=self._get_current_era(year).era_type,
                    impact_scope="continental"
                )
                self.events.append(event)

            # Dark age conditions
            elif (trend == "decreasing" and
                  avg_recent < np.mean(list(civ.population_history.values())) * 0.5 and
                  not civ.dark_ages):

                # Start dark age
                civ.dark_ages.append((year, year + 150))  # 150 year dark age
                civ.status = CivilizationStatus.DECLINING

                event = HistoricalEvent(
                    id=f"dark_age_{civ.name}_{year}",
                    name=f"Dark Age of {civ.name}",
                    description=f"{civ.name} enters a period of decline and stagnation.",
                    event_type=EventType.DARK_AGE,
                    year=year,
                    location=civ.capital or (0, 0),
                    participants=[civ.name],
                    significance=0.8,
                    era=self._get_current_era().era_type,
                    impact_scope="regional"
                )
                self.events.append(event)

    def _should_civilization_collapse(self, civ: Civilization, year: int) -> bool:
        """Determine if civilization should collapse"""
        current_pop = civ.population_history.get(year, 1000)
        max_pop = max(civ.population_history.values()) if civ.population_history else 1000

        # Collapse conditions
        collapse_factors = []

        # Population collapse
        if current_pop < max_pop * 0.1:
            collapse_factors.append("population_collapse")

        # Military defeat (simplified)
        if random.random() < 0.05:  # 5% chance per step
            collapse_factors.append("military_defeat")

        # Natural disaster
        if random.random() < 0.03:  # 3% chance per step
            collapse_factors.append("natural_disaster")

        # Internal strife
        if random.random() < 0.04:  # 4% chance per step
            collapse_factors.append("internal_strife")

        return len(collapse_factors) >= 2

    def _collapse_civilization(self, civ: Civilization, year: int) -> None:
        """Collapse a civilization"""
        civ.collapse_year = year
        civ.status = CivilizationStatus.COLLAPSED

        # Create collapse event
        event = HistoricalEvent(
            id=f"collapse_{civ.name}_{year}",
            name=f"Fall of {civ.name}",
            description=f"The {civ.name} civilization collapses after years of decline.",
            event_type=EventType.DISASTER,
            year=year,
            location=civ.capital or (0, 0),
            participants=[civ.name],
            significance=0.9,
            era=self._get_current_era(year).era_type,
            impact_scope="continental"
        )
        self.events.append(event)

    def _simulate_civilization_interactions(self, year: int, era: Era) -> None:
        """Simulate interactions between civilizations"""
        active_civs = [c for c in self.civilizations.values()
                      if c.status not in [CivilizationStatus.COLLAPSED, CivilizationStatus.DESTROYED]]

        if len(active_civs) < 2:
            return

        # Check for conflicts
        for i, civ1 in enumerate(active_civs):
            for civ2 in active_civs[i+1:]:
                if self._should_civilizations_interact(civ1, civ2, year):
                    interaction_type = self._determine_interaction_type(civ1, civ2, era)
                    self._create_interaction_event(civ1, civ2, interaction_type, year, era)

    def _should_civilizations_interact(self, civ1: Civilization, civ2: Civilization, year: int) -> bool:
        """Determine if two civilizations should interact"""
        # Check territorial proximity
        if not civ1.territory or not civ2.territory:
            return False

        # Calculate minimum distance between territories
        min_distance = float('inf')
        for pos1 in civ1.territory:
            for pos2 in civ2.territory:
                distance = abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
                min_distance = min(min_distance, distance)

        # More likely to interact if close
        proximity_factor = max(0, 1 - min_distance / 20)

        # Era affects interaction likelihood
        era_multipliers = {
            EraType.ANCIENT: 0.3,
            EraType.CLASSICAL: 0.5,
            EraType.MEDIEVAL: 0.4,
            EraType.RENAISSANCE: 0.6,
            EraType.INDUSTRIAL: 0.8,
            EraType.MODERN: 0.9,
            EraType.FUTURE: 1.0
        }

        era_multiplier = era_multipliers.get(self._get_current_era(year).era_type, 0.5)

        return random.random() < proximity_factor * era_multiplier * 0.3

    def _determine_interaction_type(self, civ1: Civilization, civ2: Civilization, era: Era) -> EventType:
        """Determine type of interaction between civilizations"""
        # Power imbalance affects interaction type
        pop1 = civ1.population_history.get(self.current_year, 1000)
        pop2 = civ2.population_history.get(self.current_year, 1000)
        power_ratio = max(pop1, pop2) / min(pop1, pop2)

        interaction_weights = {
            EventType.TRADE: 0.3,
            EventType.WAR: 0.2,
            EventType.ALLIANCE: 0.15,
            EventType.EXPLORATION: 0.1,
            EventType.CULTURAL_EVENT: 0.1,
            EventType.RELIGIOUS_EVENT: 0.1,
            EventType.DISCOVERY: 0.05
        }

        # Adjust weights based on era
        if era.era_type in [EraType.MEDIEVAL, EraType.ANCIENT]:
            interaction_weights[EventType.WAR] *= 1.5
        elif era.era_type in [EraType.RENAISSANCE, EraType.INDUSTRIAL]:
            interaction_weights[EventType.TRADE] *= 1.5

        # Adjust based on power imbalance
        if power_ratio > 3:
            interaction_weights[EventType.WAR] *= 1.5
            interaction_weights[EventType.ALLIANCE] *= 0.5

        # Normalize weights
        total_weight = sum(interaction_weights.values())
        normalized_weights = {k: v/total_weight for k, v in interaction_weights.items()}

        # Choose interaction type
        interaction_types = list(normalized_weights.keys())
        probabilities = list(normalized_weights.values())
        return np.random.choice(interaction_types, p=probabilities)

    def _create_interaction_event(self, civ1: Civilization, civ2: Civilization,
                                interaction_type: EventType, year: int, era: Era) -> None:
        """Create event for civilization interaction"""
        event_templates = {
            EventType.TRADE: [
                f"{civ1.name} establishes trade routes with {civ2.name}",
                f"Merchants from {civ1.name} and {civ2.name} begin regular exchange"
            ],
            EventType.WAR: [
                f"War breaks out between {civ1.name} and {civ2.name}",
                f"{civ1.name} attacks {civ2.name}"
            ],
            EventType.ALLIANCE: [
                f"{civ1.name} and {civ2.name} form a military alliance",
                f"{civ1.name} and {civ2.name} sign a mutual defense pact"
            ],
            EventType.EXPLORATION: [
                f"Explorers from {civ1.name} make contact with {civ2.name}",
                f"{civ1.name} discovers the lands of {civ2.name}"
            ]
        }

        templates = event_templates.get(interaction_type, [f"Interaction between {civ1.name} and {civ2.name}"])
        description = random.choice(templates)

        event = HistoricalEvent(
            id=f"interaction_{civ1.name}_{civ2.name}_{year}",
            name=f"{interaction_type.value.title()} between {civ1.name} and {civ2.name}",
            description=description,
            event_type=interaction_type,
            year=year,
            location=self._calculate_interaction_location(civ1, civ2),
            participants=[civ1.name, civ2.name],
            significance=0.6,
            era=era.era_type,
            impact_scope="regional"
        )
        self.events.append(event)

        # Update diplomatic relations
        civ1.diplomatic_relations[civ2.name] = interaction_type.value
        civ2.diplomatic_relations[civ1.name] = interaction_type.value

    def _calculate_interaction_location(self, civ1: Civilization, civ2: Civilization) -> Tuple[int, int]:
        """Calculate location of interaction between civilizations"""
        if civ1.capital and civ2.capital:
            # Midpoint between capitals
            y = (civ1.capital[0] + civ2.capital[0]) // 2
            x = (civ1.capital[1] + civ2.capital[1]) // 2
            return (y, x)
        elif civ1.capital:
            return civ1.capital
        elif civ2.capital:
            return civ2.capital
        else:
            return (self.height // 2, self.width // 2)

    def _simulate_natural_events(self, year: int, era: Era) -> None:
        """Simulate natural disasters and environmental events"""
        # Chance of natural disaster
        if random.random() < 0.1:  # 10% chance per step
            disaster_type = random.choice([
                EventType.NATURAL_DISASTER,
                EventType.PLAGUE
            ])

            # Choose affected area
            affected_civs = random.sample(
                list(self.civilizations.keys()),
                min(random.randint(1, 3), len(self.civilizations))
            )

            # Create disaster event
            disaster_templates = {
                EventType.NATURAL_DISASTER: [
                    "A massive earthquake strikes the region",
                    "Volcanic eruption devastates the landscape",
                    "Great flood destroys settlements",
                    "Drought causes widespread famine"
                ],
                EventType.PLAGUE: [
                    "A deadly plague sweeps through the population",
                    "Mysterious illness causes widespread suffering",
                    "Contagious disease spreads rapidly"
                ]
            }

            templates = disaster_templates.get(disaster_type, ["A natural disaster occurs"])
            description = random.choice(templates)

            # Choose location
            location = (random.randint(10, self.height - 10), random.randint(10, self.width - 10))

            event = HistoricalEvent(
                id=f"disaster_{year}_{random.randint(1000, 9999)}",
                name=f"Natural Disaster",
                description=description,
                event_type=disaster_type,
                year=year,
                location=location,
                participants=affected_civs,
                significance=0.7,
                era=era.era_type,
                impact_scope="regional"
            )
            self.events.append(event)

            # Affect civilizations
            for civ_name in affected_civs:
                if civ_name in self.civilizations:
                    civ = self.civilizations[civ_name]
                    current_pop = civ.population_history.get(year, 1000)
                    civ.population_history[year] = int(current_pop * 0.7)  # 30% population loss

    def _simulate_technological_advancement(self, year: int, era: Era) -> None:
        """Simulate technological breakthroughs and innovations"""
        if random.random() < 0.15:  # 15% chance per step
            # Choose civilization for advancement
            active_civs = [c for c in self.civilizations.values()
                          if c.status not in [CivilizationStatus.COLLAPSED, CivilizationStatus.DESTROYED]]

            if active_civs:
                civ = random.choice(active_civs)

                # Generate technological breakthrough
                breakthroughs = {
                    TechnologyTier.STONE: ["tool making", "fire control", "shelter building"],
                    TechnologyTier.BRONZE: ["metalworking", "writing", "agriculture"],
                    TechnologyTier.IRON: ["iron smelting", "advanced agriculture", "early mathematics"],
                    TechnologyTier.MEDIEVAL: ["feudalism", "heavy cavalry", "gothic architecture"],
                    TechnologyTier.RENAISSANCE: ["printing press", "gunpowder weapons", "perspective art"],
                    TechnologyTier.INDUSTRIAL: ["steam power", "mass production", "railways"],
                    TechnologyTier.MODERN: ["electricity", "automobiles", "telecommunications"],
                    TechnologyTier.SPACE: ["space travel", "computers", "nuclear power"]
                }

                current_tech = civ.technology_tier
                possible_breakthroughs = breakthroughs.get(current_tech, ["general advancement"])
                breakthrough = random.choice(possible_breakthroughs)

                # Create invention event
                event = HistoricalEvent(
                    id=f"breakthrough_{civ.name}_{year}",
                    name=f"Technological Breakthrough in {civ.name}",
                    description=f"{civ.name} develops {breakthrough}.",
                    event_type=EventType.INVENTION,
                    year=year,
                    location=civ.capital or (0, 0),
                    participants=[civ.name],
                    significance=0.8,
                    era=era.era_type,
                    impact_scope="continental"
                )
                self.events.append(event)

                # Add to achievements
                civ.major_achievements.append(f"Invented {breakthrough}")

    def _simulate_cultural_development(self, year: int, era: Era) -> None:
        """Simulate cultural developments and movements"""
        if random.random() < 0.2:  # 20% chance per step
            # Choose civilization
            active_civs = [c for c in self.civilizations.values()
                          if c.status not in [CivilizationStatus.COLLAPSED, CivilizationStatus.DESTROYED]]

            if active_civs:
                civ = random.choice(active_civs)

                # Generate cultural development
                cultural_developments = [
                    "new artistic movement emerges",
                    "philosophical school founded",
                    "literary classic composed",
                    "architectural style developed",
                    "musical tradition established",
                    "religious reformation occurs",
                    "cultural renaissance begins"
                ]

                development = random.choice(cultural_developments)

                # Create cultural event
                event = HistoricalEvent(
                    id=f"cultural_{civ.name}_{year}",
                    name=f"Cultural Development in {civ.name}",
                    description=f"A {development} in {civ.name}.",
                    event_type=EventType.CULTURAL_EVENT,
                    year=year,
                    location=civ.capital or (0, 0),
                    participants=[civ.name],
                    significance=0.5,
                    era=era.era_type,
                    impact_scope="national"
                )
                self.events.append(event)

    def _simulate_economic_changes(self, year: int, era: Era) -> None:
        """Simulate economic developments and changes"""
        if random.random() < 0.15:  # 15% chance per step
            # Economic developments
            economic_developments = [
                "trade network established",
                "currency system introduced",
                "market economy develops",
                "guild system formed",
                "banking system created",
                "merchant class rises",
                "economic reform implemented"
            ]

            development = random.choice(economic_developments)

            # Create trade event
            event = HistoricalEvent(
                id=f"economic_{year}_{random.randint(1000, 9999)}",
                name="Economic Development",
                description=f"{development} in the world.",
                event_type=EventType.TRADE,
                year=year,
                location=(random.randint(10, self.height - 10), random.randint(10, self.width - 10)),
                significance=0.6,
                era=era.era_type,
                impact_scope="regional"
            )
            self.events.append(event)

    def _collect_statistics(self, year: int) -> None:
        """Collect world statistics for this year"""
        stats = {
            'total_civilizations': len(self.civilizations),
            'active_civilizations': len([c for c in self.civilizations.values()
                                      if c.status not in [CivilizationStatus.COLLAPSED, CivilizationStatus.DESTROYED]]),
            'total_population': sum(civ.population_history.get(year, 0) for civ in self.civilizations.values()),
            'technology_levels': defaultdict(int),
            'government_types': defaultdict(int),
            'civilization_statuses': defaultdict(int)
        }

        # Count technology levels and governments
        for civ in self.civilizations.values():
            stats['technology_levels'][civ.technology_tier.value] += 1
            stats['government_types'][civ.government.value] += 1
            stats['civilization_statuses'][civ.status.value] += 1

        # Store statistics
        if year not in self.world_statistics:
            self.world_statistics = {}

    def _compile_statistics(self) -> Dict[int, Dict]:
        """Compile collected statistics"""
        return self.world_statistics

class WorldHistory:
    """Main world history generation system"""

    def __init__(self, width: int, height: int, seed: Optional[int] = None):
        self.width = width
        self.height = height
        self.seed = seed or random.randint(0, 2**31 - 1)

        self.historical_simulator = HistoricalSimulator(width, height, self.seed)
        self.timeline = None

    def generate_world_history(self, num_steps: int = 200) -> Timeline:
        """Generate complete world history"""
        print(f"Generating world history with {num_steps} time steps...")

        self.timeline = self.historical_simulator.simulate_history(num_steps)

        return self.timeline

    def get_major_events(self, min_significance: float = 0.7) -> List[HistoricalEvent]:
        """Get major historical events"""
        if not self.timeline:
            return []

        return [event for event in self.timeline.events if event.significance >= min_significance]

    def get_civilization_history(self, civilization_name: str) -> Optional[Dict]:
        """Get detailed history of a specific civilization"""
        if not self.timeline or civilization_name not in self.timeline.civilizations:
            return None

        civ = self.timeline.civilizations[civilization_name]

        # Get events involving this civilization
        civ_events = [event for event in self.timeline.events
                     if civilization_name in event.participants]

        return {
            'civilization': civ,
            'events': civ_events,
            'golden_ages': civ.golden_ages,
            'dark_ages': civ.dark_ages,
            'major_achievements': civ.major_achievements,
            'notable_leaders': civ.notable_leaders
        }

    def get_era_summary(self, era_type: EraType) -> Optional[Dict]:
        """Get summary of a specific era"""
        if not self.timeline:
            return None

        era = None
        for e in self.timeline.eras:
            if e.era_type == era_type:
                era = e
                break

        if not era:
            return None

        # Get events in this era
        era_events = [event for event in self.timeline.events
                     if event.era == era_type]

        # Get civilizations that existed during this era
        era_civs = []
        for civ in self.timeline.civilizations.values():
            if (era.start_year <= civ.founding_year <= era.end_year or
                (civ.collapse_year and era.start_year <= civ.collapse_year <= era.end_year)):
                era_civs.append(civ.name)

        return {
            'era': era,
            'events': era_events,
            'civilizations': era_civs,
            'event_count': len(era_events),
            'dominant_civilizations': era.dominant_civilizations
        }

    def analyze_historical_patterns(self) -> Dict:
        """Analyze patterns in world history"""
        if not self.timeline:
            return {}

        analysis = {
            'total_events': len(self.timeline.events),
            'total_civilizations': len(self.timeline.civilizations),
            'event_types': defaultdict(int),
            'era_distribution': defaultdict(int),
            'civilization_lifespans': [],
            'most_significant_events': [],
            'common_causes_of_collapse': [],
            'technological_progression': []
        }

        # Analyze events
        for event in self.timeline.events:
            analysis['event_types'][event.event_type.value] += 1
            analysis['era_distribution'][event.era.value] += 1

        # Civilization lifespans
        for civ in self.timeline.civilizations.values():
            if civ.collapse_year:
                lifespan = civ.collapse_year - civ.founding_year
                analysis['civilization_lifespans'].append(lifespan)
            else:
                lifespan = self.timeline.current_year - civ.founding_year
                analysis['civilization_lifespans'].append(lifespan)

        # Most significant events
        sorted_events = sorted(self.timeline.events, key=lambda e: e.significance, reverse=True)
        analysis['most_significant_events'] = sorted_events[:10]

        return analysis

# Utility functions
def format_timeline_summary(timeline: Timeline) -> str:
    """Format timeline as readable summary"""
    if not timeline:
        return "No timeline data available."

    summary = []
    summary.append(f"World History: {timeline.start_year} to {timeline.current_year}")
    summary.append(f"Total Events: {len(timeline.events)}")
    summary.append(f"Total Civilizations: {len(timeline.civilizations)}")
    summary.append("")

    # Era summary
    summary.append("Historical Eras:")
    for era in timeline.eras:
        era_events = [e for e in timeline.events if e.era == era.era_type]
        summary.append(f"  {era.name} ({era.start_year} to {era.end_year}): {len(era_events)} events")
    summary.append("")

    # Major civilizations
    summary.append("Major Civilizations:")
    for civ_name, civ in timeline.civilizations.items():
        if civ.status not in [CivilizationStatus.COLLAPSED, CivilizationStatus.DESTROYED]:
            current_pop = civ.population_history.get(timeline.current_year, 0)
            summary.append(f"  {civ_name}: Population {current_pop:,}, Status: {civ.status.value}")
    summary.append("")

    # Recent major events
    recent_events = [e for e in timeline.events if e.year > timeline.current_year - 200]
    recent_events.sort(key=lambda e: e.year)
    summary.append("Recent Major Events (Last 200 years):")
    for event in recent_events[-5:]:
        summary.append(f"  {event.year}: {event.name}")

    return "\n".join(summary)

if __name__ == "__main__":
    # Example usage
    print("Generating world history...")
    world_history = WorldHistory(width=100, height=100, seed=42)

    # Generate complete history
    timeline = world_history.generate_world_history(num_steps=200)

    # Display summary
    summary = format_timeline_summary(timeline)
    print(summary)

    # Analyze patterns
    analysis = world_history.analyze_historical_patterns()
    print(f"\nHistorical Analysis:")
    print(f"Total events: {analysis['total_events']}")
    print(f"Total civilizations: {analysis['total_civilizations']}")
    if analysis['civilization_lifespans']:
        avg_lifespan = np.mean(analysis['civilization_lifespans'])
        print(f"Average civilization lifespan: {avg_lifespan:.0f} years")

    print(f"\nEvent type distribution:")
    for event_type, count in analysis['event_types'].items():
        print(f"  {event_type}: {count}")

    print(f"\nMost significant events:")
    for event in analysis['most_significant_events'][:5]:
        print(f"  {event.year}: {event.name} (significance: {event.significance:.2f})")

    # Get civilization details for a sample
    if timeline.civilizations:
        sample_civ = list(timeline.civilizations.keys())[0]
        civ_history = world_history.get_civilization_history(sample_civ)
        if civ_history:
            print(f"\nSample Civilization: {sample_civ}")
            print(f"  Founded: {civ_history['civilization'].founding_year}")
            print(f"  Status: {civ_history['civilization'].status.value}")
            print(f"  Technology: {civ_history['civilization'].technology_tier.value}")
            print(f"  Government: {civ_history['civilization'].government.value}")
            print(f"  Major achievements: {len(civ_history['major_achievements'])}")
            print(f"  Golden ages: {len(civ_history['golden_ages'])}")
            print(f"  Dark ages: {len(civ_history['dark_ages'])}")

    print("\nWorld history generation complete!")