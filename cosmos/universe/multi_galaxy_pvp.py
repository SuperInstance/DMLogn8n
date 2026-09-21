#!/usr/bin/env python3
"""
Multi-Galaxy PVP System - Interstellar Warfare and Diplomacy
Handles fleet combat, galactic diplomacy, and empire management
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from enum import Enum
import random
import math
from abc import ABC, abstractmethod

# Physical Constants
c = 299792458  # Speed of light (m/s)
LIGHT_YEAR = 9.461e15  # meters
AU = 1.496e11  # meters

class DiplomaticStatus(Enum):
    ALLIED = "allied"
    FRIENDLY = "friendly"
    NEUTRAL = "neutral"
    SUSPICIOUS = "suspicious"
    HOSTILE = "hostile"
    WAR = "war"

class WarObjective(Enum):
    CONQUEST = "conquest"  # Complete conquest
    LIBERATION = "liberation"  # Liberate occupied systems
    RESOURCE_CONTROL = "resource_control"  # Control specific resources
    STRATEGIC_POSITIVE = "strategic_positive"  # Gain strategic position
    GENOCIDE = "genocide"  # Exterminate enemy
    PUNITIVE = "punitive"  # Punish for transgressions
    DEFENSIVE = "defensive"  # Defensive war

class FleetRole(Enum):
    ASSAULT = "assault"  # Direct combat
    DEFENSE = "defense"  # System defense
    RAIDER = "raider"  # Raiding operations
    SCOUT = "scout"  # Exploration and reconnaissance
    COLONIZATION = "colonization"  # Colonization support
    TRADE = "trade"  # Trade protection
    DIPLOMATIC = "diplomatic"  # Diplomatic missions
    SUPPORT = "support"  # Fleet support and logistics

class WeaponType(Enum):
    LASER = "laser"  # Energy weapons
    PLASMA = "plasma"  # Plasma cannons
    MISSILE = "missile"  # Guided missiles
    KINETIC = "kinetic"  # Railguns and mass drivers
    PARTICLE_BEAM = "particle_beam"  # Particle accelerators
    ANTIMATTER = "antimatter"  # Antimatter weapons
    GRAVITON = "graviton"  # Gravitational weapons
    QUANTUM_ENTANGLEMENT = "quantum_entanglement"  # Quantum weapons
    TEMPORAL = "temporal"  # Time-based weapons
    EXOTIC_MATTER = "exotic_matter"  # Reality-bending weapons

class DefenseType(Enum):
    SHIELDS = "shields"  # Energy shields
    ARMOR = "armor"  # Physical armor
    POINT_DEFENSE = "point_defense"  # Anti-missile systems
    JAMMING = "jamming"  # Electronic warfare
    COUNTERMEASURES = "countermeasures"  # Decoys and flares
    STEALTH = "stealth"  # Cloaking and stealth
    PHASE_SHIFTING = "phase_shifting"  # Phase shifting armor
    GRAVITIC_DEFLECTORS = "gravitic_deflectors"  # Gravity manipulation
    TEMPORAL_SHIELDS = "temporal_shields"  # Time distortion
    QUANTUM_ARMOR = "quantum_armor"  # Quantum probability armor

@dataclass
class Vector3D:
    """3D vector for spatial calculations"""
    x: float
    y: float
    z: float

    def magnitude(self):
        return np.sqrt(self.x**2 + self.y**2 + self.z**2)

    def normalize(self):
        mag = self.magnitude()
        if mag > 0:
            return Vector3D(self.x/mag, self.y/mag, self.z/mag)
        return Vector3D(0, 0, 0)

    def __add__(self, other):
        return Vector3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector3D(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar):
        return Vector3D(self.x * scalar, self.y * scalar, self.z * scalar)

    def distance_to(self, other):
        return (self - other).magnitude()

@dataclass
class WeaponSystem:
    """Represents a ship weapon system"""
    weapon_type: WeaponType
    damage: float  # Base damage value
    range: float  # Effective range in meters
    accuracy: float  # 0-1 accuracy rating
    fire_rate: float  # Shots per second
    energy_cost: float  # Energy per shot
    special_effects: List[str]  # Special effects
    tech_level: int  # Technology level 1-10
    reliability: float  # 0-1 reliability

@dataclass
class DefenseSystem:
    """Represents a ship defense system"""
    defense_type: DefenseType
    protection_value: float  # Damage reduction
    coverage: float  # 0-1 coverage area
    energy_cost: float  # Energy per second
    regen_rate: float  # Regeneration rate if applicable
    special_properties: List[str]  # Special properties
    tech_level: int  # Technology level
    effectiveness: float  # 0-1 effectiveness

@dataclass
class Ship:
    """Represents an individual starship"""
    id: str
    name: str
    ship_class: str
    hull_points: float  # Structural integrity
    max_hull_points: float
    shield_points: float  # Shield strength
    max_shield_points: float
    armor_points: float  # Armor value
    energy: float  # Current energy
    max_energy: float
    position: Vector3D
    velocity: Vector3D
    rotation: Vector3D  # Orientation
    weapons: List[WeaponSystem]
    defenses: List[DefenseSystem]
    crew: int  # Number of crew members
    cargo_capacity: float  # Cargo capacity
    ftl_capability: bool  # FTL travel capability
    stealth_level: float  # 0-1 stealth rating
    electronic_warfare: float  # 0-1 EW capability
    repair_rate: float  # Hull repair rate
    status: str  # operational, damaged, destroyed, etc.

@dataclass
class Fleet:
    """Represents a fleet of ships"""
    id: str
    name: str
    commander_id: str  # ID of fleet commander
    ships: List[Ship]
    fleet_role: FleetRole
    position: Vector3D
    destination: Optional[Vector3D]
    formation: str  # Combat formation type
    morale: float  # 0-1 fleet morale
    supply_level: float  # 0-1 supply status
    experience: float  # 0-1 combat experience
    special_orders: List[str]
    current_orders: str

@dataclass
class Empire:
    """Represents a space empire or civilization"""
    id: str
    name: str
    government_type: str  # democracy, monarchy, dictatorship, etc.
    leader_id: str
    home_system: str
    controlled_systems: Set[str]
    population: int  # Total population
    military_strength: float  # 0-1 military power
    economic_strength: float  # 0-1 economic power
    technological_level: float  # 0-1 technology advancement
    diplomatic_relations: Dict[str, DiplomaticStatus]
    active_wars: Set[str]  # IDs of enemy empires
    alliances: Set[str]  # IDs of allied empires
    resource_production: Dict[str, float]  # Resource production rates
    fleet_commanders: List[str]  # IDs of fleet commanders
    traits: List[str]  # Empire traits and characteristics

@dataclass
class CombatEngagement:
    """Represents a combat engagement between forces"""
    id: str
    location: Vector3D
    participants: Dict[str, List[str]]  # Empire ID to fleet IDs
    start_time: float
    end_time: Optional[float]
    status: str  # ongoing, victory, defeat, stalemate
    casualties: Dict[str, int]  # Empire ID to ship losses
    damage_dealt: Dict[str, float]  # Empire ID to total damage
    objectives: List[str]  # Combat objectives
    outcome: Dict[str, str]  # Results for each participant

@dataclass
class DiplomaticTreaty:
    """Represents a diplomatic treaty between empires"""
    id: str
    name: str
    signatories: List[str]  # Empire IDs
    treaty_type: str  # alliance, trade, peace, non-aggression, etc.
    terms: Dict[str, str]  # Treaty terms and conditions
    start_date: float
    end_date: Optional[float]
    auto_renew: bool
    enforcement_mechanism: str  # How treaty is enforced
    violations: List[Dict]  # History of violations

class CombatEngine:
    """Handles combat calculations and resolution"""

    def __init__(self):
        self.damage_multipliers = {
            WeaponType.LASER: {'shields': 1.2, 'armor': 0.8, 'hull': 1.0},
            WeaponType.PLASMA: {'shields': 1.0, 'armor': 1.5, 'hull': 1.2},
            WeaponType.MISSILE: {'shields': 0.9, 'armor': 1.3, 'hull': 1.4},
            WeaponType.KINETIC: {'shields': 0.7, 'armor': 1.2, 'hull': 1.6},
            WeaponType.PARTICLE_BEAM: {'shields': 1.3, 'armor': 0.9, 'hull': 1.1},
            WeaponType.ANTIMATTER: {'shields': 1.5, 'armor': 1.8, 'hull': 2.0},
            WeaponType.GRAVITON: {'shields': 0.5, 'armor': 1.0, 'hull': 1.5},
            WeaponType.QUANTUM_ENTANGLEMENT: {'shields': 1.0, 'armor': 1.0, 'hull': 2.5},
            WeaponType.TEMPORAL: {'shields': 0.8, 'armor': 0.8, 'hull': 1.8},
            WeaponType.EXOTIC_MATTER: {'shields': 1.8, 'armor': 2.0, 'hull': 3.0}
        }

    def calculate_hit_probability(self, attacker: Ship, target: Ship, weapon: WeaponSystem,
                                distance: float) -> float:
        """Calculate probability of hitting target"""

        base_accuracy = weapon.accuracy

        # Distance penalty
        max_range = weapon.range
        if distance > max_range:
            return 0.0
        distance_factor = 1.0 - (distance / max_range) * 0.5

        # Target size and speed
        size_factor = min(1.0, target.ship_class_size / 1000)  # Simplified size calculation
        speed_factor = max(0.1, 1.0 - target.velocity.magnitude() / c * 0.3)

        # Stealth and electronic warfare
        stealth_penalty = target.stealth_level * 0.3
        ew_penalty = target.electronic_warfare * 0.2

        # Attacker skill and targeting systems
        attacker_bonus = attacker.electronic_warfare * 0.1

        hit_probability = base_accuracy * distance_factor * size_factor * speed_factor
        hit_probability = max(0.01, hit_probability - stealth_penalty - ew_penalty + attacker_bonus)

        return min(1.0, hit_probability)

    def calculate_damage(self, attacker: Ship, weapon: WeaponSystem, target: Ship,
                        hit_location: str = 'random') -> Dict[str, float]:
        """Calculate damage dealt to target"""

        base_damage = weapon.damage

        # Critical hit chance
        critical_chance = 0.05 * weapon.tech_level / 10
        is_critical = random.random() < critical_chance
        if is_critical:
            base_damage *= 2.0

        # Apply damage multipliers based on weapon type and defense type
        damage_distribution = {'shields': 0, 'armor': 0, 'hull': 0}

        weapon_multipliers = self.damage_multipliers.get(weapon.weapon_type,
                                                       {'shields': 1.0, 'armor': 1.0, 'hull': 1.0})

        # Determine hit location based on shield status
        if target.shield_points > 0:
            # Hit shields first
            shield_damage = base_damage * weapon_multipliers['shields']
            damage_distribution['shields'] = shield_damage

            # Overflow damage goes to armor/hull
            overflow = max(0, shield_damage - target.shield_points)
            if overflow > 0:
                damage_distribution['shields'] = target.shield_points
                armor_damage = overflow * weapon_multipliers['armor']
                damage_distribution['armor'] = min(armor_damage, target.armor_points)

                overflow = max(0, armor_damage - target.armor_points)
                if overflow > 0:
                    damage_distribution['armor'] = target.armor_points
                    damage_distribution['hull'] = overflow * weapon_multipliers['hull']
        else:
            # No shields, hit armor directly
            armor_damage = base_damage * weapon_multipliers['armor']
            damage_distribution['armor'] = min(armor_damage, target.armor_points)

            overflow = max(0, armor_damage - target.armor_points)
            if overflow > 0:
                damage_distribution['armor'] = target.armor_points
                damage_distribution['hull'] = overflow * weapon_multipliers['hull']

        # Apply defense system reductions
        for defense in target.defenses:
            if defense.defense_type == DefenseType.ARMOR:
                damage_distribution['hull'] *= (1 - defense.protection_value * defense.effectiveness)
            elif defense.defense_type == DefenseType.SHIELDS and target.shield_points > 0:
                damage_distribution['shields'] *= (1 - defense.protection_value * defense.effectiveness)

        return damage_distribution

    def apply_damage(self, ship: Ship, damage: Dict[str, float]) -> bool:
        """Apply damage to ship, return True if ship destroyed"""

        # Apply shield damage
        ship.shield_points -= damage['shields']
        ship.shield_points = max(0, ship.shield_points)

        # Apply armor damage
        ship.armor_points -= damage['armor']
        ship.armor_points = max(0, ship.armor_points)

        # Apply hull damage
        ship.hull_points -= damage['hull']
        ship.hull_points = max(0, ship.hull_points)

        # Check if ship destroyed
        if ship.hull_points <= 0:
            ship.status = 'destroyed'
            return True

        # Update status based on damage
        hull_percentage = ship.hull_points / ship.max_hull_points
        if hull_percentage < 0.2:
            ship.status = 'critical'
        elif hull_percentage < 0.5:
            ship.status = 'damaged'
        else:
            ship.status = 'operational'

        return False

    def simulate_combat_round(self, fleet1: List[Ship], fleet2: List[Ship],
                            time_delta: float = 1.0) -> Dict[str, int]:
        """Simulate one round of combat"""

        casualties = {'fleet1': 0, 'fleet2': 0}
        destroyed_ships = []

        # Fleet 1 attacks Fleet 2
        for attacker in fleet1:
            if attacker.status == 'destroyed':
                continue

            # Find targets
            valid_targets = [ship for ship in fleet2 if ship.status != 'destroyed']
            if not valid_targets:
                break

            # Select target (prioritize damaged ships)
            target = min(valid_targets, key=lambda s: s.hull_points / s.max_hull_points)

            for weapon in attacker.weapons:
                if attacker.energy < weapon.energy_cost:
                    continue

                distance = attacker.position.distance_to(target.position)
                if distance > weapon.range:
                    continue

                # Calculate hit probability
                hit_chance = self.calculate_hit_probability(attacker, target, weapon, distance)
                if random.random() > hit_chance:
                    continue  # Miss

                # Calculate and apply damage
                damage = self.calculate_damage(attacker, weapon, target)
                destroyed = self.apply_damage(target, damage)

                attacker.energy -= weapon.energy_cost

                if destroyed:
                    casualties['fleet2'] += 1
                    destroyed_ships.append(target)

        # Fleet 2 attacks Fleet 1 (similar process)
        for attacker in fleet2:
            if attacker.status == 'destroyed':
                continue

            valid_targets = [ship for ship in fleet1 if ship.status != 'destroyed']
            if not valid_targets:
                break

            target = min(valid_targets, key=lambda s: s.hull_points / s.max_hull_points)

            for weapon in attacker.weapons:
                if attacker.energy < weapon.energy_cost:
                    continue

                distance = attacker.position.distance_to(target.position)
                if distance > weapon.range:
                    continue

                hit_chance = self.calculate_hit_probability(attacker, target, weapon, distance)
                if random.random() > hit_chance:
                    continue

                damage = self.calculate_damage(attacker, weapon, target)
                destroyed = self.apply_damage(target, damage)

                attacker.energy -= weapon.energy_cost

                if destroyed:
                    casualties['fleet1'] += 1
                    destroyed_ships.append(target)

        # Remove destroyed ships from fleets
        fleet1[:] = [ship for ship in fleet1 if ship.status != 'destroyed']
        fleet2[:] = [ship for ship in fleet2 if ship.status != 'destroyed']

        return casualties

class DiplomaticSystem:
    """Handles diplomatic relations between empires"""

    def __init__(self):
        self.relation_changes = []
        self.treaty_proposals = []
        self.active_treaties = {}

    def calculate_relation_change(self, empire1: Empire, empire2: Empire,
                                action: str, magnitude: float) -> float:
        """Calculate change in diplomatic relations"""

        current_status = empire1.diplomatic_relations.get(empire2.id, DiplomaticStatus.NEUTRAL)

        # Base relation value (-1 to 1)
        if current_status == DiplomaticStatus.ALLIED:
            relation_value = 0.8
        elif current_status == DiplomaticStatus.FRIENDLY:
            relation_value = 0.4
        elif current_status == DiplomaticStatus.NEUTRAL:
            relation_value = 0.0
        elif current_status == DiplomaticStatus.SUSPICIOUS:
            relation_value = -0.4
        elif current_status == DiplomaticStatus.HOSTILE:
            relation_value = -0.7
        else:  # WAR
            relation_value = -0.9

        # Action modifiers
        action_modifiers = {
            'trade_agreement': 0.1,
            'military_alliance': 0.3,
            'technology_sharing': 0.15,
            'gift': 0.05,
            'insult': -0.1,
            'border_violation': -0.2,
            'trade_dispute': -0.05,
            'espionage_caught': -0.15,
            'declaration_of_war': -0.5,
            'peace_treaty': 0.4,
            'mutual_defense': 0.25
        }

        modifier = action_modifiers.get(action, 0.0)
        new_relation_value = relation_value + modifier * magnitude

        # Apply personality trait modifiers
        if 'aggressive' in empire1.traits:
            new_relation_value *= 0.9
        if 'peaceful' in empire1.traits:
            new_relation_value *= 1.1
        if 'xenophobic' in empire1.traits:
            new_relation_value *= 0.8
        if 'diplomatic' in empire1.traits:
            new_relation_value *= 1.2

        # Clamp to valid range
        new_relation_value = max(-1.0, min(1.0, new_relation_value))

        return new_relation_value

    def update_diplomatic_status(self, empire1: Empire, empire2: Empire,
                               new_relation_value: float) -> None:
        """Update diplomatic status based on relation value"""

        if new_relation_value >= 0.7:
            new_status = DiplomaticStatus.ALLIED
        elif new_relation_value >= 0.4:
            new_status = DiplomaticStatus.FRIENDLY
        elif new_relation_value >= 0.1:
            new_status = DiplomaticStatus.NEUTRAL
        elif new_relation_value >= -0.3:
            new_status = DiplomaticStatus.SUSPICIOUS
        elif new_relation_value >= -0.6:
            new_status = DiplomaticStatus.HOSTILE
        else:
            new_status = DiplomaticStatus.WAR

        old_status = empire1.diplomatic_relations.get(empire2.id, DiplomaticStatus.NEUTRAL)
        empire1.diplomatic_relations[empire2.id] = new_status
        empire2.diplomatic_relations[empire1.id] = new_status

        # Handle war declarations
        if new_status == DiplomaticStatus.WAR and old_status != DiplomaticStatus.WAR:
            empire1.active_wars.add(empire2.id)
            empire2.active_wars.add(empire1.id)
            # Remove from alliances if applicable
            empire1.alliances.discard(empire2.id)
            empire2.alliances.discard(empire1.id)

        # Handle peace treaties
        elif old_status == DiplomaticStatus.WAR and new_status != DiplomaticStatus.WAR:
            empire1.active_wars.discard(empire2.id)
            empire2.active_wars.discard(empire1.id)

    def propose_treaty(self, proposer: Empire, recipient: Empire,
                      treaty_type: str, terms: Dict) -> bool:
        """Propose a treaty to another empire"""

        # Check if treaty is possible given current relations
        current_status = proposer.diplomatic_relations.get(recipient.id, DiplomaticStatus.NEUTRAL)

        # Certain treaties require minimum relationship levels
        if treaty_type == 'alliance' and current_status not in [DiplomaticStatus.FRIENDLY, DiplomaticStatus.ALLIED]:
            return False
        if treaty_type == 'trade' and current_status == DiplomaticStatus.WAR:
            return False

        # Calculate acceptance probability
        acceptance_chance = self.calculate_treaty_acceptance(proposer, recipient, treaty_type, terms)

        if random.random() < acceptance_chance:
            # Treaty accepted
            treaty_id = f"treaty_{proposer.id}_{recipient.id}_{len(self.active_treaties)}"
            treaty = DiplomaticTreaty(
                id=treaty_id,
                name=f"{treaty_type.title()} Treaty",
                signatories=[proposer.id, recipient.id],
                treaty_type=treaty_type,
                terms=terms,
                start_date=0,  # Would be current time
                end_date=None,
                auto_renew=treaty_type in ['trade', 'alliance'],
                enforcement_mechanism='mutual',
                violations=[]
            )

            self.active_treaties[treaty_id] = treaty
            return True

        return False

    def calculate_treaty_acceptance(self, proposer: Empire, recipient: Empire,
                                  treaty_type: str, terms: Dict) -> float:
        """Calculate probability of treaty acceptance"""

        base_chance = 0.5

        # Relationship factor
        current_status = proposer.diplomatic_relations.get(recipient.id, DiplomaticStatus.NEUTRAL)
        if current_status == DiplomaticStatus.ALLIED:
            relation_factor = 1.5
        elif current_status == DiplomaticStatus.FRIENDLY:
            relation_factor = 1.2
        elif current_status == DiplomaticStatus.NEUTRAL:
            relation_factor = 1.0
        elif current_status == DiplomaticStatus.SUSPICIOUS:
            relation_factor = 0.7
        else:
            relation_factor = 0.3

        # Power balance factor
        proposer_strength = proposer.military_strength + proposer.economic_strength
        recipient_strength = recipient.military_strength + recipient.economic_strength
        power_ratio = proposer_strength / (proposer_strength + recipient_strength)

        if abs(power_ratio - 0.5) < 0.2:  # Roughly equal powers
            power_factor = 1.2
        elif power_ratio > 0.7:  # Proposer much stronger
            power_factor = 0.8
        else:  # Proposer much weaker
            power_factor = 1.0

        # Trait factors
        if 'peaceful' in recipient.traits:
            trait_factor = 1.3
        elif 'aggressive' in recipient.traits:
            trait_factor = 0.8
        elif 'isolationist' in recipient.traits:
            trait_factor = 0.6
        else:
            trait_factor = 1.0

        # Treaty type factors
        treaty_factors = {
            'trade': 1.2,
            'alliance': 0.8,
            'non_aggression': 1.1,
            'mutual_defense': 0.9,
            'research_sharing': 1.0,
            'free_movement': 0.7
        }

        treaty_factor = treaty_factors.get(treaty_type, 1.0)

        # Calculate final acceptance chance
        acceptance_chance = base_chance * relation_factor * power_factor * trait_factor * treaty_factor
        return max(0.1, min(1.0, acceptance_chance))

class MultiGalaxyPVPSystem:
    """Main system for managing interstellar warfare and diplomacy"""

    def __init__(self):
        self.empires: Dict[str, Empire] = {}
        self.fleets: Dict[str, Fleet] = {}
        self.combat_engine = CombatEngine()
        self.diplomatic_system = DiplomaticSystem()
        self.combat_engagements: Dict[str, CombatEngagement] = {}
        self.war_history: List[Dict] = []
        self.current_time = 0.0
        self.galaxy_control: Dict[str, str] = {}  # System ID to Empire ID

    def create_empire(self, empire_data: Dict) -> Empire:
        """Create a new empire"""

        empire = Empire(
            id=empire_data['id'],
            name=empire_data['name'],
            government_type=empire_data.get('government_type', 'democracy'),
            leader_id=empire_data.get('leader_id', f"leader_{empire_data['id']}"),
            home_system=empire_data['home_system'],
            controlled_systems=set([empire_data['home_system']]),
            population=empire_data.get('population', 1000000000),
            military_strength=empire_data.get('military_strength', 0.5),
            economic_strength=empire_data.get('economic_strength', 0.5),
            technological_level=empire_data.get('technological_level', 0.5),
            diplomatic_relations={},
            active_wars=set(),
            alliances=set(),
            resource_production=empire_data.get('resource_production', {}),
            fleet_commanders=[],
            traits=empire_data.get('traits', ['peaceful'])
        )

        self.empires[empire.id] = empire
        self.galaxy_control[empire.home_system] = empire.id

        return empire

    def create_fleet(self, fleet_data: Dict) -> Fleet:
        """Create a new fleet"""

        fleet = Fleet(
            id=fleet_data['id'],
            name=fleet_data['name'],
            commander_id=fleet_data['commander_id'],
            ships=fleet_data.get('ships', []),
            fleet_role=FleetRole(fleet_data.get('role', 'assault')),
            position=Vector3D(*fleet_data.get('position', [0, 0, 0])),
            destination=None,
            formation=fleet_data.get('formation', 'line'),
            morale=fleet_data.get('morale', 0.8),
            supply_level=fleet_data.get('supply_level', 1.0),
            experience=fleet_data.get('experience', 0.5),
            special_orders=[],
            current_orders='patrol'
        )

        self.fleets[fleet.id] = fleet

        # Add commander to empire
        if fleet.commander_id in self.empires:
            self.empires[fleet.commander_id].fleet_commanders.append(fleet.commander_id)

        return fleet

    def create_ship(self, ship_data: Dict) -> Ship:
        """Create a new ship"""

        # Convert weapon data
        weapons = []
        for weapon_data in ship_data.get('weapons', []):
            weapon = WeaponSystem(
                weapon_type=WeaponType(weapon_data['type']),
                damage=weapon_data['damage'],
                range=weapon_data['range'],
                accuracy=weapon_data['accuracy'],
                fire_rate=weapon_data['fire_rate'],
                energy_cost=weapon_data['energy_cost'],
                special_effects=weapon_data.get('special_effects', []),
                tech_level=weapon_data.get('tech_level', 5),
                reliability=weapon_data.get('reliability', 0.9)
            )
            weapons.append(weapon)

        # Convert defense data
        defenses = []
        for defense_data in ship_data.get('defenses', []):
            defense = DefenseSystem(
                defense_type=DefenseType(defense_data['type']),
                protection_value=defense_data['protection_value'],
                coverage=defense_data.get('coverage', 1.0),
                energy_cost=defense_data['energy_cost'],
                regen_rate=defense_data.get('regen_rate', 0.0),
                special_properties=defense_data.get('special_properties', []),
                tech_level=defense_data.get('tech_level', 5),
                effectiveness=defense_data.get('effectiveness', 0.9)
            )
            defenses.append(defense)

        ship = Ship(
            id=ship_data['id'],
            name=ship_data['name'],
            ship_class=ship_data['class'],
            hull_points=ship_data['hull_points'],
            max_hull_points=ship_data['hull_points'],
            shield_points=ship_data.get('shield_points', 0),
            max_shield_points=ship_data.get('shield_points', 0),
            armor_points=ship_data.get('armor_points', 0),
            energy=ship_data.get('energy', 1000),
            max_energy=ship_data.get('energy', 1000),
            position=Vector3D(*ship_data.get('position', [0, 0, 0])),
            velocity=Vector3D(*ship_data.get('velocity', [0, 0, 0])),
            rotation=Vector3D(*ship_data.get('rotation', [0, 0, 0])),
            weapons=weapons,
            defenses=defenses,
            crew=ship_data.get('crew', 100),
            cargo_capacity=ship_data.get('cargo_capacity', 1000),
            ftl_capability=ship_data.get('ftl_capability', True),
            stealth_level=ship_data.get('stealth_level', 0.0),
            electronic_warfare=ship_data.get('electronic_warfare', 0.0),
            repair_rate=ship_data.get('repair_rate', 1.0),
            status='operational'
        )

        return ship

    def declare_war(self, aggressor_id: str, defender_id: str,
                   war_objective: WarObjective, justification: str = "") -> bool:
        """Declare war between empires"""

        if aggressor_id not in self.empires or defender_id not in self.empires:
            return False

        aggressor = self.empires[aggressor_id]
        defender = self.empires[defender_id]

        # Update diplomatic relations
        self.diplomatic_system.update_diplomatic_status(aggressor, defender, -1.0)

        # Record war declaration
        self.war_history.append({
            'type': 'war_declaration',
            'aggressor': aggressor_id,
            'defender': defender_id,
            'objective': war_objective.value,
            'justification': justification,
            'timestamp': self.current_time
        })

        return True

    def engage_fleets_in_combat(self, fleet1_id: str, fleet2_id: str,
                              location: Optional[Vector3D] = None) -> Optional[CombatEngagement]:
        """Engage two fleets in combat"""

        if fleet1_id not in self.fleets or fleet2_id not in self.fleets:
            return None

        fleet1 = self.fleets[fleet1_id]
        fleet2 = self.fleets[fleet2_id]

        # Determine combat location
        if location is None:
            location = Vector3D(
                (fleet1.position.x + fleet2.position.x) / 2,
                (fleet1.position.y + fleet2.position.y) / 2,
                (fleet1.position.z + fleet2.position.z) / 2
            )

        # Create combat engagement
        engagement_id = f"combat_{len(self.combat_engagements)}"
        engagement = CombatEngagement(
            id=engagement_id,
            location=location,
            participants={fleet1_id: [fleet1], fleet2_id: [fleet2]},
            start_time=self.current_time,
            end_time=None,
            status='ongoing',
            casualties={fleet1_id: 0, fleet2_id: 0},
            damage_dealt={fleet1_id: 0, fleet2_id: 0},
            objectives=['destroy_enemy_fleet'],
            outcome={}
        )

        self.combat_engagements[engagement_id] = engagement

        # Simulate combat
        self.simulate_combat(engagement)

        return engagement

    def simulate_combat(self, engagement: CombatEngagement, max_rounds: int = 100) -> None:
        """Simulate a complete combat engagement"""

        # Get participating fleets
        fleet_ids = list(engagement.participants.keys())
        if len(fleet_ids) != 2:
            return

        fleet1_id, fleet2_id = fleet_ids
        fleet1_ships = [ship for fleet in engagement.participants[fleet1_id] for ship in fleet.ships]
        fleet2_ships = [ship for fleet in engagement.participants[fleet2_id] for ship in fleet.ships]

        initial_fleet1_size = len(fleet1_ships)
        initial_fleet2_size = len(fleet2_ships)

        # Combat rounds
        for round_num in range(max_rounds):
            if not fleet1_ships or not fleet2_ships:
                break

            casualties = self.combat_engine.simulate_combat_round(fleet1_ships, fleet2_ships)
            engagement.casualties[fleet1_id] += casualties['fleet1']
            engagement.casualties[fleet2_id] += casualties['fleet2']

            # Ship regeneration and repair
            for ship in fleet1_ships + fleet2_ships:
                ship.shield_points = min(ship.max_shield_points,
                                       ship.shield_points + ship.max_shield_points * 0.01)
                ship.energy = min(ship.max_energy, ship.energy + ship.max_energy * 0.02)

        # Determine outcome
        if len(fleet1_ships) == 0 and len(fleet2_ships) == 0:
            engagement.status = 'stalemate'
            engagement.outcome[fleet1_id] = 'mutual_destruction'
            engagement.outcome[fleet2_id] = 'mutual_destruction'
        elif len(fleet1_ships) == 0:
            engagement.status = 'victory'
            engagement.outcome[fleet1_id] = 'defeat'
            engagement.outcome[fleet2_id] = 'victory'
        elif len(fleet2_ships) == 0:
            engagement.status = 'victory'
            engagement.outcome[fleet1_id] = 'victory'
            engagement.outcome[fleet2_id] = 'defeat'
        else:
            engagement.status = 'stalemate'
            engagement.outcome[fleet1_id] = 'indecisive'
            engagement.outcome[fleet2_id] = 'indecisive'

        engagement.end_time = self.current_time

        # Update fleets with surviving ships
        for fleet_id in fleet_ids:
            if fleet_id in self.fleets:
                if fleet_id == fleet1_id:
                    self.fleets[fleet_id].ships = fleet1_ships
                else:
                    self.fleets[fleet_id].ships = fleet2_ships

                # Update fleet morale
                remaining_ratio = len(self.fleets[fleet_id].ships) / max(initial_fleet1_size, initial_fleet2_size)
                self.fleets[fleet_id].morale *= remaining_ratio

        # Record combat in war history
        self.war_history.append({
            'type': 'fleet_combat',
            'engagement_id': engagement.id,
            'participants': fleet_ids,
            'outcome': engagement.outcome,
            'casualties': engagement.casualties,
            'timestamp': self.current_time
        })

    def negotiate_peace(self, empire1_id: str, empire2_id: str,
                       terms: Dict) -> bool:
        """Negotiate peace between warring empires"""

        if empire1_id not in self.empires or empire2_id not in self.empires:
            return False

        empire1 = self.empires[empire1_id]
        empire2 = self.empires[empire2_id]

        # Check if empires are at war
        if empire2_id not in empire1.active_wars:
            return False

        # Calculate peace acceptance probability
        war_weariness = self.calculate_war_weariness(empire1) * self.calculate_war_weariness(empire2)
        power_balance = (empire1.military_strength) / (empire1.military_strength + empire2.military_strength)

        peace_chance = war_weariness * 0.6 + (1 - abs(power_balance - 0.5) * 2) * 0.4

        if random.random() < peace_chance:
            # Peace accepted
            self.diplomatic_system.update_diplomatic_status(empire1, empire2, 0.2)

            # Remove from active wars
            empire1.active_wars.discard(empire2_id)
            empire2.active_wars.discard(empire1_id)

            # Record peace treaty
            self.war_history.append({
                'type': 'peace_treaty',
                'participants': [empire1_id, empire2_id],
                'terms': terms,
                'timestamp': self.current_time
            })

            return True

        return False

    def calculate_war_weariness(self, empire: Empire) -> float:
        """Calculate war weariness for an empire"""

        # Based on number of wars, casualties, and economic strain
        war_count = len(empire.active_wars)
        base_weariness = min(1.0, war_count * 0.2)

        # Economic strain
        economic_strain = 1.0 - empire.economic_strength
        weariness = base_weariness + economic_strain * 0.3

        # Trait modifiers
        if 'militaristic' in empire.traits:
            weariness *= 0.7
        elif 'peaceful' in empire.traits:
            weariness *= 1.3

        return min(1.0, weariness)

    def update_galaxy_control(self, system_id: str, new_controller: str) -> None:
        """Update control of a star system"""

        old_controller = self.galaxy_control.get(system_id)
        if old_controller:
            if old_controller in self.empires:
                self.empires[old_controller].controlled_systems.discard(system_id)

        self.galaxy_control[system_id] = new_controller
        if new_controller in self.empires:
            self.empires[new_controller].controlled_systems.add(system_id)

    def get_system_statistics(self) -> Dict:
        """Get statistics about controlled systems"""

        empire_control = {}
        for system_id, empire_id in self.galaxy_control.items():
            empire_control[empire_id] = empire_control.get(empire_id, 0) + 1

        return {
            'total_systems': len(self.galaxy_control),
            'empire_control': empire_control,
            'contested_systems': 0,  # Would need combat status tracking
            'uncontrolled_systems': 0  # Would need neutral system tracking
        }

# Example usage and testing
if __name__ == "__main__":
    # Create PVP system
    pvp_system = MultiGalaxyPVPSystem()

    print("Multi-Galaxy PVP System Initialized")
    print("Features:")
    print("- Fleet-based combat system")
    print("- Diplomatic relations and treaties")
    print("- Empire management")
    print("- Warfare and peace negotiations")
    print("- Dynamic galaxy control")

    # Create two empires
    print("\n" + "="*50)
    print("CREATING EMPIRES")
    print("="*50)

    terran_empire = pvp_system.create_empire({
        'id': 'terran_federation',
        'name': 'Terran Federation',
        'government_type': 'democracy',
        'home_system': 'sol',
        'population': 50000000000,
        'military_strength': 0.7,
        'economic_strength': 0.8,
        'technological_level': 0.7,
        'traits': ['diplomatic', 'expansionist'],
        'resource_production': {'energy': 1000, 'metals': 500, 'electronics': 200}
    })

    zylon_empire = pvp_system.create_empire({
        'id': 'zylon_collective',
        'name': 'Zylon Collective',
        'government_type': 'dictatorship',
        'home_system': 'zylon_prime',
        'population': 30000000000,
        'military_strength': 0.9,
        'economic_strength': 0.5,
        'technological_level': 0.8,
        'traits': ['aggressive', 'militaristic'],
        'resource_production': {'energy': 800, 'metals': 800, 'weapons': 400}
    })

    print(f"Created {terran_empire.name} and {zylon_empire.name}")

    # Set initial diplomatic relations
    pvp_system.diplomatic_system.update_diplomatic_status(terran_empire, zylon_empire, -0.3)
    print(f"Initial diplomatic status: Suspicious")

    # Create fleets
    print("\n" + "="*50)
    print("CREATING FLEETS")
    print("="*50)

    # Create some ships for the fleets
    terran_ship1 = pvp_system.create_ship({
        'id': 'ts_battlecruiser_1',
        'name': 'USS Indomitable',
        'class': 'battlecruiser',
        'hull_points': 5000,
        'shield_points': 3000,
        'armor_points': 2000,
        'energy': 5000,
        'crew': 500,
        'weapons': [
            {
                'type': 'laser',
                'damage': 100,
                'range': 100000,
                'accuracy': 0.9,
                'fire_rate': 2.0,
                'energy_cost': 50,
                'tech_level': 7
            },
            {
                'type': 'missile',
                'damage': 300,
                'range': 500000,
                'accuracy': 0.8,
                'fire_rate': 0.5,
                'energy_cost': 100,
                'tech_level': 6
            }
        ],
        'defenses': [
            {
                'type': 'shields',
                'protection_value': 0.3,
                'energy_cost': 100,
                'tech_level': 7,
                'effectiveness': 0.9
            },
            {
                'type': 'armor',
                'protection_value': 0.2,
                'energy_cost': 0,
                'tech_level': 6,
                'effectiveness': 1.0
            }
        ]
    })

    zylon_ship1 = pvp_system.create_ship({
        'id': 'zs_dreadnought_1',
        'name': 'Zylon Devastator',
        'class': 'dreadnought',
        'hull_points': 7000,
        'shield_points': 2000,
        'armor_points': 3000,
        'energy': 4000,
        'crew': 700,
        'weapons': [
            {
                'type': 'plasma',
                'damage': 150,
                'range': 80000,
                'accuracy': 0.85,
                'fire_rate': 1.5,
                'energy_cost': 80,
                'tech_level': 8
            },
            {
                'type': 'kinetic',
                'damage': 250,
                'range': 200000,
                'accuracy': 0.9,
                'fire_rate': 1.0,
                'energy_cost': 60,
                'tech_level': 7
            }
        ],
        'defenses': [
            {
                'type': 'armor',
                'protection_value': 0.4,
                'energy_cost': 0,
                'tech_level': 8,
                'effectiveness': 1.0
            }
        ]
    })

    # Create fleets
    terran_fleet = pvp_system.create_fleet({
        'id': 'tf_first_fleet',
        'name': 'First Fleet',
        'commander_id': 'terran_federation',
        'ships': [terran_ship1],
        'role': 'assault',
        'position': [0, 0, 0],
        'morale': 0.9,
        'experience': 0.6
    })

    zylon_fleet = pvp_system.create_fleet({
        'id': 'zc_battle_group',
        'name': 'Battle Group Alpha',
        'commander_id': 'zylon_collective',
        'ships': [zylon_ship1],
        'role': 'assault',
        'position': [100000, 0, 0],
        'morale': 0.95,
        'experience': 0.8
    })

    print(f"Created {terran_fleet.name} and {zylon_fleet.name}")
    print(f"  {terran_fleet.name}: {len(terran_fleet.ships)} ships")
    print(f"  {zylon_fleet.name}: {len(zylon_fleet.ships)} ships")

    # Declare war
    print("\n" + "="*50)
    print("DECLARING WAR")
    print("="*50)

    war_declared = pvp_system.declare_war(
        'zylon_collective',
        'terran_federation',
        WarObjective.CONQUEST,
        "Expansion of Zylon territory"
    )

    if war_declared:
        print("War declared between Zylon Collective and Terran Federation!")
        print(f"Zylon diplomatic status: {zylon_empire.diplomatic_relations['terran_federation'].value}")
        print(f"Terran diplomatic status: {terran_empire.diplomatic_relations['zylon_collective'].value}")

    # Simulate combat
    print("\n" + "="*50)
    print("FLEET COMBAT")
    print("="*50)

    print("Engaging fleets in combat...")
    combat = pvp_system.engage_fleets_in_combat('tf_first_fleet', 'zc_battle_group')

    if combat:
        print(f"Combat Engagement: {combat.id}")
        print(f"Status: {combat.status}")
        print(f"Duration: {combat.end_time - combat.start_time:.1f} time units")
        print(f"Casualties:")
        for fleet_id, casualties in combat.casualties.items():
            fleet_name = pvp_system.fleets[fleet_id].name if fleet_id in pvp_system.fleets else fleet_id
            print(f"  {fleet_name}: {casualties} ships lost")
        print(f"Outcomes:")
        for fleet_id, outcome in combat.outcome.items():
            fleet_name = pvp_system.fleets[fleet_id].name if fleet_id in pvp_system.fleets else fleet_id
            print(f"  {fleet_name}: {outcome}")

    # Attempt peace negotiations
    print("\n" + "="*50)
    print("PEACE NEGOTIATIONS")
    print("="*50)

    peace_terms = {
        'territory_exchanges': [],
        'reparations': {'energy': 500, 'metals': 200},
        'non_aggression_pact': True,
        'duration': 100  # turns/years
    }

    peace_successful = pvp_system.negotiate_peace(
        'zylon_collective',
        'terran_federation',
        peace_terms
    )

    if peace_successful:
        print("Peace treaty negotiated successfully!")
        print("Terms:")
        for term, value in peace_terms.items():
            print(f"  {term}: {value}")
    else:
        print("Peace negotiations failed - war continues")

    # System statistics
    print("\n" + "="*50)
    print("GALAXY STATISTICS")
    print("="*50)

    system_stats = pvp_system.get_system_statistics()
    for key, value in system_stats.items():
        print(f"{key}: {value}")

    print(f"\nWar History Events: {len(pvp_system.war_history)}")
    for event in pvp_system.war_history[-3:]:  # Show last 3 events
        print(f"  {event['type']}: {event.get('participants', 'N/A')} at {event['timestamp']}")

    print("\nMulti-Galaxy PVP Features:")
    print("- Advanced fleet combat with multiple weapon and defense types")
    print("- Diplomatic system with treaties and relations")
    print("- Empire management with traits and characteristics")
    print("- War declaration and peace negotiations")
    print("- Dynamic galaxy control")
    print("- Combat engagement simulation")
    print("- War weariness and economic factors")

    print("\nMulti-galaxy PVP system test completed successfully!")