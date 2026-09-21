#!/usr/bin/env python3
"""
Space Travel Mechanics - Faster-Than-Light Travel and Wormhole Networks
Implements various FTL methods, wormholes, and interstellar navigation
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
G = 6.67430e-11  # Gravitational constant
LIGHT_YEAR = 9.461e15  # meters
PARSEC = 3.086e16  # meters
AU = 1.496e11  # meters
SOLAR_MASS = 1.989e30  # kg

class TravelMethod(Enum):
    SUBLIGHT = "sublight"
    WARP_DRIVE = "warp_drive"
    HYPERSPACE = "hyperspace"
    WORMHOLE = "wormhole"
    QUANTUM_TUNNEL = "quantum_tunnel"
    ALGUBUBE_DRIVE = "algubube_drive"
    DRAKE_DRIVE = "drake_drive"
    SPACETIME_FOLD = "spacetime_fold"

class WormholeType(Enum):
    NATURAL = "natural"
    ARTIFICIAL = "artificial"
    STABLE = "stable"
    TRANSIENT = "transient"
    MICROSCOPIC = "microscopic"
    MACROSCOPIC = "macroscopic"

class NavigationStatus(Enum):
    IDLE = "idle"
    CHARGING = "charging"
    ACCELERATING = "accelerating"
    CRUISING = "cruising"
    DECELERATING = "decelerating"
    EMERGENCY_STOP = "emergency_stop"
    LOST_IN_SPACE = "lost_in_space"

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
class TravelPath:
    """Represents a travel route between two points"""
    start: Vector3D
    end: Vector3D
    waypoints: List[Vector3D] = field(default_factory=list)
    method: TravelMethod = TravelMethod.SUBLIGHT
    estimated_time: float = 0.0  # seconds
    energy_cost: float = 0.0  # Joules
    risk_factor: float = 0.0  # 0-1 scale

@dataclass
class Wormhole:
    """Represents a wormhole connection"""
    id: str
    mouth1_pos: Vector3D
    mouth2_pos: Vector3D
    wormhole_type: WormholeType
    stability: float  # 0-1, how stable it is
    max_radius: float  # meters, maximum ship size that can pass
    energy_cost: float  # Joules to maintain
    age: float  # seconds since creation
    lifespan: float  # total expected lifespan
    creator: Optional[str] = None  # Civilization that created it
    traffic_count: int = 0  # Number of ships that have used it

@dataclass
class FTLDrive:
    """Base class for FTL drive systems"""
    name: str
    max_speed_factor: float  # Multiple of c
    energy_efficiency: float  # Energy per unit distance
    acceleration_time: float  # Time to reach max speed
    deceleration_time: float  # Time to decelerate
    reliability: float  # 0-1, chance of successful jump
    technology_level: int  # 1-10, how advanced it is
    maintenance_cost: float  # Resources per use
    special_requirements: List[str] = field(default_factory=list)

class FTLEngine(ABC):
    """Abstract base class for FTL propulsion systems"""

    @abstractmethod
    def calculate_travel_time(self, distance: float, ship_mass: float) -> float:
        """Calculate travel time for given distance and ship mass"""
        pass

    @abstractmethod
    def calculate_energy_cost(self, distance: float, ship_mass: float) -> float:
        """Calculate energy cost for given distance and ship mass"""
        pass

    @abstractmethod
    def can_travel(self, distance: float, ship_mass: float, available_energy: float) -> bool:
        """Check if ship can make the jump"""
        pass

class WarpDrive(FTLEngine):
    """Warp drive - contracts space in front, expands behind"""

    def __init__(self, warp_factor: float = 5.0):
        self.warp_factor = warp_factor
        self.energy_per_warp = 1e32  # Joules per warp factor unit
        self.min_ship_mass = 1e6  # kg
        self.max_ship_mass = 1e12  # kg

    def calculate_travel_time(self, distance: float, ship_mass: float) -> float:
        """Warp travel time calculation"""
        # Warp factor affects effective speed
        effective_speed = self.warp_factor * c
        # Include acceleration/deceleration phases
        accel_time = min(distance / (2 * effective_speed), 3600)  # Max 1 hour
        cruise_time = distance / effective_speed
        return 2 * accel_time + cruise_time

    def calculate_energy_cost(self, distance: float, ship_mass: float) -> float:
        """Warp drive energy cost"""
        base_energy = self.energy_per_warp * self.warp_factor * distance / LIGHT_YEAR
        mass_factor = (ship_mass / self.min_ship_mass) ** 0.5
        return base_energy * mass_factor

    def can_travel(self, distance: float, ship_mass: float, available_energy: float) -> bool:
        """Check if warp jump is possible"""
        if ship_mass < self.min_ship_mass or ship_mass > self.max_ship_mass:
            return False
        required_energy = self.calculate_energy_cost(distance, ship_mass)
        return available_energy >= required_energy

class HyperspaceDrive(FTLEngine):
    """Hyperspace drive - travels through alternate dimension"""

    def __init__(self, hyperspace_level: int = 1):
        self.hyperspace_level = hyperspace_level
        self.speed_multiplier = 10 ** hyperspace_level
        self.jump_cooldown = 300  # seconds between jumps
        self.jump_stability = 0.95 - hyperspace_level * 0.05

    def calculate_travel_time(self, distance: float, ship_mass: float) -> float:
        """Hyperspace travel is much faster"""
        effective_speed = self.speed_multiplier * c
        # Include jump initialization time
        init_time = 60  # 1 minute to enter hyperspace
        travel_time = distance / effective_speed
        exit_time = 30  # 30 seconds to exit hyperspace
        return init_time + travel_time + exit_time

    def calculate_energy_cost(self, distance: float, ship_mass: float) -> float:
        """Hyperspace energy cost"""
        base_energy = 1e30 * distance / LIGHT_YEAR
        mass_factor = ship_mass / 1e9  # Normalized to 1 billion kg
        level_factor = self.hyperspace_level ** 2
        return base_energy * mass_factor * level_factor

    def can_travel(self, distance: float, ship_mass: float, available_energy: float) -> bool:
        """Check hyperspace jump feasibility"""
        if distance < 0.1 * LIGHT_YEAR:  # Too short for hyperspace
            return False
        required_energy = self.calculate_energy_cost(distance, ship_mass)
        return available_energy >= required_energy

class QuantumTunnelDrive(FTLEngine):
    """Quantum tunneling drive - instant but short range"""

    def __init__(self, max_range: float = 10 * LIGHT_YEAR):
        self.max_range = max_range
        self.tunnel_probability = 0.99
        self.energy_per_meter = 1e25  # Joules per meter

    def calculate_travel_time(self, distance: float, ship_mass: float) -> float:
        """Quantum tunneling is nearly instantaneous"""
        if distance > self.max_range:
            return float('inf')
        # Only tunnel initiation and stabilization time
        return 1.0  # 1 second total

    def calculate_energy_cost(self, distance: float, ship_mass: float) -> float:
        """Quantum tunneling energy cost"""
        if distance > self.max_range:
            return float('inf')
        return self.energy_per_meter * distance

    def can_travel(self, distance: float, ship_mass: float, available_energy: float) -> bool:
        """Check quantum tunnel feasibility"""
        if distance > self.max_range:
            return False
        required_energy = self.calculate_energy_cost(distance, ship_mass)
        return available_energy >= required_energy

class SpaceTravelSystem:
    """Main space travel management system"""

    def __init__(self):
        self.ftl_engines: Dict[str, FTLEngine] = {}
        self.wormholes: Dict[str, Wormhole] = {}
        self.active_ships: Dict[str, 'Spaceship'] = {}
        self.navigation_network: Dict[str, List[str]] = {}  # System connections
        self.travel_log: List[Dict] = []
        self.gravity_wells: List[Dict] = []  # Massive objects affecting travel

        # Initialize default FTL engines
        self.initialize_ftl_engines()

    def initialize_ftl_engines(self):
        """Initialize available FTL propulsion systems"""
        self.ftl_engines['warp_1'] = WarpDrive(warp_factor=1.0)
        self.ftl_engines['warp_5'] = WarpDrive(warp_factor=5.0)
        self.ftl_engines['warp_9'] = WarpDrive(warp_factor=9.0)
        self.ftl_engines['hyper_1'] = HyperspaceDrive(hyperspace_level=1)
        self.ftl_engines['hyper_3'] = HyperspaceDrive(hyperspace_level=3)
        self.ftl_engines['quantum'] = QuantumTunnelDrive(max_range=10 * LIGHT_YEAR)

    def add_wormhole(self, wormhole: Wormhole) -> None:
        """Add a wormhole to the network"""
        self.wormholes[wormhole.id] = wormhole
        self.update_navigation_network()

    def create_natural_wormhole(self, pos1: Vector3D, pos2: Vector3D) -> Wormhole:
        """Create a natural wormhole between two points"""
        wormhole_id = f"natural_{len(self.wormholes)}"
        distance = pos1.distance_to(pos2)

        wormhole = Wormhole(
            id=wormhole_id,
            mouth1_pos=pos1,
            mouth2_pos=pos2,
            wormhole_type=WormholeType.NATURAL,
            stability=np.random.uniform(0.5, 0.9),
            max_radius=np.random.uniform(10, 1000),  # 10-1000 meters
            energy_cost=0,  # Natural wormholes don't require energy to maintain
            age=0,
            lifespan=np.random.uniform(1e6, 1e9) * 365.25 * 24 * 3600,  # 1M to 1B years
            creator=None
        )

        self.add_wormhole(wormhole)
        return wormhole

    def create_artificial_wormhole(self, pos1: Vector3D, pos2: Vector3D,
                                 creator: str, stability: float = 0.95) -> Wormhole:
        """Create an artificial wormhole"""
        wormhole_id = f"artificial_{len(self.wormholes)}"
        distance = pos1.distance_to(pos2)

        # Energy cost proportional to distance and desired stability
        energy_cost = 1e35 * (distance / LIGHT_YEAR) * stability

        wormhole = Wormhole(
            id=wormhole_id,
            mouth1_pos=pos1,
            mouth2_pos=pos2,
            wormhole_type=WormholeType.ARTIFICIAL,
            stability=stability,
            max_radius=100,  # Standard 100m radius
            energy_cost=energy_cost,
            age=0,
            lifespan=1e8 * 365.25 * 24 * 3600,  # 100 million years
            creator=creator
        )

        self.add_wormhole(wormhole)
        return wormhole

    def calculate_optimal_path(self, start: Vector3D, end: Vector3D,
                             ship_mass: float, available_energy: float,
                             preferred_method: TravelMethod = TravelMethod.WARP_DRIVE) -> TravelPath:
        """Calculate optimal travel path between two points"""

        direct_distance = start.distance_to(end)

        # Check all possible travel methods
        best_path = None
        best_time = float('inf')

        # Direct FTL travel
        for engine_name, engine in self.ftl_engines.items():
            if engine.can_travel(direct_distance, ship_mass, available_energy):
                travel_time = engine.calculate_travel_time(direct_distance, ship_mass)
                energy_cost = engine.calculate_energy_cost(direct_distance, ship_mass)
                risk_factor = self.calculate_risk_factor(direct_distance, engine_name)

                if travel_time < best_time:
                    best_time = travel_time
                    best_path = TravelPath(
                        start=start,
                        end=end,
                        method=TravelMethod.WARP_DRIVE if 'warp' in engine_name else TravelMethod.HYPERSPACE,
                        estimated_time=travel_time,
                        energy_cost=energy_cost,
                        risk_factor=risk_factor
                    )

        # Check wormhole routes
        wormhole_path = self.calculate_wormhole_path(start, end, ship_mass)
        if wormhole_path and wormhole_path.estimated_time < best_time:
            best_path = wormhole_path

        # Check multi-hop routes through wormholes
        multi_hop_path = self.calculate_multi_hop_path(start, end, ship_mass, available_energy)
        if multi_hop_path and multi_hop_path.estimated_time < best_time:
            best_path = multi_hop_path

        # If no FTL path found, use sublight
        if best_path is None:
            sublight_time = direct_distance / (0.1 * c)  # 10% light speed
            best_path = TravelPath(
                start=start,
                end=end,
                method=TravelMethod.SUBLIGHT,
                estimated_time=sublight_time,
                energy_cost=0,
                risk_factor=0.1
            )

        return best_path

    def calculate_wormhole_path(self, start: Vector3D, end: Vector3D,
                              ship_mass: float) -> Optional[TravelPath]:
        """Calculate path using wormhole network"""

        # Find wormhole mouths near start and end
        nearby_wormholes_start = []
        nearby_wormholes_end = []

        for wormhole in self.wormholes.values():
            dist_to_start1 = wormhole.mouth1_pos.distance_to(start)
            dist_to_start2 = wormhole.mouth2_pos.distance_to(start)
            dist_to_end1 = wormhole.mouth1_pos.distance_to(end)
            dist_to_end2 = wormhole.mouth2_pos.distance_to(end)

            if dist_to_start1 < 0.1 * LIGHT_YEAR:
                nearby_wormholes_start.append((wormhole, wormhole.mouth1_pos, wormhole.mouth2_pos, dist_to_start1))
            if dist_to_start2 < 0.1 * LIGHT_YEAR:
                nearby_wormholes_start.append((wormhole, wormhole.mouth2_pos, wormhole.mouth1_pos, dist_to_start2))
            if dist_to_end1 < 0.1 * LIGHT_YEAR:
                nearby_wormholes_end.append((wormhole, wormhole.mouth1_pos, wormhole.mouth2_pos, dist_to_end1))
            if dist_to_end2 < 0.1 * LIGHT_YEAR:
                nearby_wormholes_end.append((wormhole, wormhole.mouth2_pos, wormhole.mouth1_pos, dist_to_end2))

        # Find best wormhole combination
        best_path = None
        best_time = float('inf')

        for start_wh, start_pos, exit_pos, start_dist in nearby_wormholes_start:
            for end_wh, end_pos, end_exit_pos, end_dist in nearby_wormholes_end:
                if start_wh.id == end_wh.id:
                    # Same wormhole - check if it connects our destinations
                    if (exit_pos.distance_to(end) < 0.1 * LIGHT_YEAR or
                        end_exit_pos.distance_to(end) < 0.1 * LIGHT_YEAR):
                        total_time = start_dist / (0.1 * c) + 1.0  # 1 second through wormhole
                        if total_time < best_time:
                            best_time = total_time
                            best_path = TravelPath(
                                start=start,
                                end=end,
                                waypoints=[start_pos, exit_pos],
                                method=TravelMethod.WORMHOLE,
                                estimated_time=total_time,
                                energy_cost=0,
                                risk_factor=0.1
                            )

        return best_path

    def calculate_multi_hop_path(self, start: Vector3D, end: Vector3D,
                                ship_mass: float, available_energy: float,
                                max_hops: int = 3) -> Optional[TravelPath]:
        """Calculate multi-hop path through wormhole network"""

        # This is a simplified version - a real implementation would use graph algorithms
        # like Dijkstra's algorithm to find optimal routes

        visited = set()
        queue = [(start, [], 0)]  # (current_pos, path, total_time)
        best_path = None
        best_time = float('inf')

        while queue and len(visited) < 50:  # Limit search
            current_pos, path, total_time = queue.pop(0)

            if current_pos.distance_to(end) < 0.1 * LIGHT_YEAR:
                if total_time < best_time:
                    best_time = total_time
                    best_path = TravelPath(
                        start=start,
                        end=end,
                        waypoints=path,
                        method=TravelMethod.WORMHOLE,
                        estimated_time=total_time,
                        energy_cost=0,
                        risk_factor=0.2 * len(path)
                    )
                continue

            if len(path) >= max_hops:
                continue

            visited.add(current_pos)

            # Find nearby wormhole mouths
            for wormhole in self.wormholes.values():
                for mouth_pos in [wormhole.mouth1_pos, wormhole.mouth2_pos]:
                    if mouth_pos.distance_to(current_pos) < 0.5 * LIGHT_YEAR:
                        # Calculate travel time to wormhole mouth
                        travel_time = mouth_pos.distance_to(current_pos) / (0.1 * c)
                        new_total_time = total_time + travel_time + 1.0  # +1s through wormhole

                        # Determine exit position
                        if mouth_pos == wormhole.mouth1_pos:
                            exit_pos = wormhole.mouth2_pos
                        else:
                            exit_pos = wormhole.mouth1_pos

                        new_path = path + [mouth_pos, exit_pos]

                        # Add to queue if promising
                        if new_total_time < best_time * 2:  # Only consider if potentially better
                            queue.append((exit_pos, new_path, new_total_time))

        return best_path

    def calculate_risk_factor(self, distance: float, engine_type: str) -> float:
        """Calculate risk factor for FTL travel"""

        base_risk = 0.1

        # Distance-based risk
        distance_risk = min(0.5, distance / (100 * LIGHT_YEAR))

        # Engine-specific risk
        if 'warp' in engine_type:
            engine_risk = 0.05 * float(engine_type.split('_')[1]) / 10
        elif 'hyper' in engine_type:
            level = int(engine_type.split('_')[1])
            engine_risk = 0.02 * level
        else:
            engine_risk = 0.01

        # Gravity well interference
        gravity_risk = self.calculate_gravity_interference_risk(distance)

        total_risk = base_risk + distance_risk + engine_risk + gravity_risk
        return min(1.0, total_risk)

    def calculate_gravity_interference_risk(self, distance: float) -> float:
        """Calculate risk from gravity wells along travel path"""
        # Simplified - would need actual path integration
        return np.random.uniform(0, 0.1)

    def update_navigation_network(self) -> None:
        """Update the navigation network based on wormholes"""
        self.navigation_network.clear()

        for wormhole in self.wormholes.values():
            # Add connection between wormhole endpoints
            pos1_str = f"{wormhole.mouth1_pos.x:.1f},{wormhole.mouth1_pos.y:.1f},{wormhole.mouth1_pos.z:.1f}"
            pos2_str = f"{wormhole.mouth2_pos.x:.1f},{wormhole.mouth2_pos.y:.1f},{wormhole.mouth2_pos.z:.1f}"

            if pos1_str not in self.navigation_network:
                self.navigation_network[pos1_str] = []
            if pos2_str not in self.navigation_network:
                self.navigation_network[pos2_str] = []

            self.navigation_network[pos1_str].append(pos2_str)
            self.navigation_network[pos2_str].append(pos1_str)

    def simulate_travel(self, path: TravelPath, ship_mass: float) -> Dict:
        """Simulate travel along a path"""

        simulation_result = {
            'success': True,
            'actual_time': path.estimated_time,
            'energy_used': path.energy_cost,
            'events': [],
            'deviations': []
        }

        # Random events during travel
        if random.random() < path.risk_factor:
            event_type = random.choice([
                'engine_malfunction',
                'gravity_anomaly',
                'space_debris',
                'energy_surge',
                'navigation_error'
            ])
            simulation_result['events'].append(event_type)

            if event_type == 'engine_malfunction':
                simulation_result['actual_time'] *= 1.5
                simulation_result['energy_used'] *= 1.3
            elif event_type == 'navigation_error':
                simulation_result['deviations'].append(Vector3D(
                    random.uniform(-0.01, 0.01) * LIGHT_YEAR,
                    random.uniform(-0.01, 0.01) * LIGHT_YEAR,
                    random.uniform(-0.01, 0.01) * LIGHT_YEAR
                ))

        # Update wormhole usage
        if path.method == TravelMethod.WORMHOLE:
            for wormhole in self.wormholes.values():
                for waypoint in path.waypoints:
                    if (waypoint.distance_to(wormhole.mouth1_pos) < 0.01 * LIGHT_YEAR or
                        waypoint.distance_to(wormhole.mouth2_pos) < 0.01 * LIGHT_YEAR):
                        wormhole.traffic_count += 1
                        break

        return simulation_result

    def add_gravity_well(self, position: Vector3D, mass: float, radius: float) -> None:
        """Add a gravity well that affects travel"""
        self.gravity_wells.append({
            'position': position,
            'mass': mass,
            'radius': radius,
            'influence_radius': 10 * radius  # Gravity well affects travel within this range
        })

    def is_path_blocked_by_gravity(self, start: Vector3D, end: Vector3D) -> bool:
        """Check if a path is blocked by gravity wells"""
        for well in self.gravity_wells:
            # Simplified line-sphere intersection check
            if self.line_intersects_sphere(start, end, well['position'], well['influence_radius']):
                return True
        return False

    def line_intersects_sphere(self, start: Vector3D, end: Vector3D,
                             sphere_center: Vector3D, sphere_radius: float) -> bool:
        """Check if line segment intersects with sphere"""
        # Vector from start to end
        d = end - start
        # Vector from start to sphere center
        f = start - sphere_center

        a = d.x * d.x + d.y * d.y + d.z * d.z
        b = 2 * (f.x * d.x + f.y * d.y + f.z * d.z)
        c = f.x * f.x + f.y * f.y + f.z * f.z - sphere_radius * sphere_radius

        discriminant = b * b - 4 * a * c

        if discriminant < 0:
            return False

        discriminant = np.sqrt(discriminant)
        t1 = (-b - discriminant) / (2 * a)
        t2 = (-b + discriminant) / (2 * a)

        return (0 <= t1 <= 1) or (0 <= t2 <= 1)

    def get_travel_statistics(self) -> Dict:
        """Get statistics about the travel network"""
        total_wormholes = len(self.wormholes)
        natural_wormholes = sum(1 for w in self.wormholes.values() if w.wormhole_type == WormholeType.NATURAL)
        artificial_wormholes = total_wormholes - natural_wormholes

        total_distance = 0
        for w in self.wormholes.values():
            total_distance += w.mouth1_pos.distance_to(w.mouth2_pos)

        return {
            'total_wormholes': total_wormholes,
            'natural_wormholes': natural_wormholes,
            'artificial_wormholes': artificial_wormholes,
            'total_wormhole_length': total_distance,
            'average_wormhole_length': total_distance / total_wormholes if total_wormholes > 0 else 0,
            'available_ftl_engines': len(self.ftl_engines),
            'gravity_wells': len(self.gravity_wells),
            'total_travels': len(self.travel_log)
        }

class Spaceship:
    """Represents a spaceship capable of FTL travel"""

    def __init__(self, ship_id: str, name: str, mass: float, max_energy: float):
        self.id = ship_id
        self.name = name
        self.mass = mass
        self.max_energy = max_energy
        self.current_energy = max_energy
        self.position = Vector3D(0, 0, 0)
        self.destination = None
        self.status = NavigationStatus.IDLE
        self.current_path = None
        self.ftl_engine = None
        self.traveled_distance = 0

    def set_ftl_engine(self, engine_type: str) -> bool:
        """Set the FTL engine type"""
        # In a real implementation, this would interface with the travel system
        return True

    def calculate_travel_cost(self, destination: Vector3D) -> Dict:
        """Calculate travel cost to destination"""
        if not self.ftl_engine:
            return {'time': float('inf'), 'energy': float('inf'), 'possible': False}

        distance = self.position.distance_to(destination)
        travel_time = self.ftl_engine.calculate_travel_time(distance, self.mass)
        energy_cost = self.ftl_engine.calculate_energy_cost(distance, self.mass)

        return {
            'time': travel_time,
            'energy': energy_cost,
            'possible': self.current_energy >= energy_cost
        }

# Example usage and testing
if __name__ == "__main__":
    # Create space travel system
    travel_system = SpaceTravelSystem()

    print("Initializing Space Travel System...")
    print(f"Available FTL engines: {list(travel_system.ftl_engines.keys())}")

    # Add some gravity wells (stars, black holes, etc.)
    travel_system.add_gravity_well(
        Vector3D(0, 0, 0),  # Center
        SOLAR_MASS,
        SOLAR_RADIUS
    )

    travel_system.add_gravity_well(
        Vector3D(10 * LIGHT_YEAR, 0, 0),  # Another star
        2 * SOLAR_MASS,
        2 * SOLAR_RADIUS
    )

    # Create some natural wormholes
    print("\nCreating natural wormholes...")
    wormhole1 = travel_system.create_natural_wormhole(
        Vector3D(0, 0, 0),
        Vector3D(5 * LIGHT_YEAR, 3 * LIGHT_YEAR, 1 * LIGHT_YEAR)
    )

    wormhole2 = travel_system.create_natural_wormhole(
        Vector3D(10 * LIGHT_YEAR, 0, 0),
        Vector3D(20 * LIGHT_YEAR, -5 * LIGHT_YEAR, 2 * LIGHT_YEAR)
    )

    # Create an artificial wormhole
    print("Creating artificial wormhole...")
    artificial_wormhole = travel_system.create_artificial_wormhole(
        Vector3D(5 * LIGHT_YEAR, 3 * LIGHT_YEAR, 1 * LIGHT_YEAR),
        Vector3D(25 * LIGHT_YEAR, 10 * LIGHT_YEAR, -3 * LIGHT_YEAR),
        creator="Human Federation",
        stability=0.98
    )

    print(f"Created {len(travel_system.wormholes)} wormholes")

    # Test travel calculations
    print("\nTesting travel calculations...")

    start_pos = Vector3D(0, 0, 0)
    end_pos = Vector3D(25 * LIGHT_YEAR, 10 * LIGHT_YEAR, -3 * LIGHT_YEAR)
    ship_mass = 1e9  # 1 billion kg
    available_energy = 1e40  # Very high energy for testing

    print(f"Direct distance: {start_pos.distance_to(end_pos) / LIGHT_YEAR:.2f} light-years")

    # Calculate optimal path
    optimal_path = travel_system.calculate_optimal_path(
        start_pos, end_pos, ship_mass, available_energy
    )

    print(f"\nOptimal Travel Path:")
    print(f"  Method: {optimal_path.method.value}")
    print(f"  Estimated time: {optimal_path.estimated_time / (365.25 * 24 * 3600):.2f} years")
    print(f"  Energy cost: {optimal_path.energy_cost:.2e} Joules")
    print(f"  Risk factor: {optimal_path.risk_factor:.3f}")
    print(f"  Waypoints: {len(optimal_path.waypoints)}")

    # Simulate the travel
    print("\nSimulating travel...")
    travel_result = travel_system.simulate_travel(optimal_path, ship_mass)

    print(f"Travel simulation results:")
    print(f"  Success: {travel_result['success']}")
    print(f"  Actual time: {travel_result['actual_time'] / (365.25 * 24 * 3600):.2f} years")
    print(f"  Energy used: {travel_result['energy_used']:.2e} Joules")
    print(f"  Events: {travel_result['events']}")

    # Test different FTL methods
    print("\nTesting different FTL methods...")
    distance = 50 * LIGHT_YEAR

    for engine_name, engine in travel_system.ftl_engines.items():
        if engine.can_travel(distance, ship_mass, available_energy):
            travel_time = engine.calculate_travel_time(distance, ship_mass)
            energy_cost = engine.calculate_energy_cost(distance, ship_mass)
            print(f"  {engine_name}: {travel_time / (365.25 * 24 * 3600):.2f} years, {energy_cost:.2e} J")

    # Get system statistics
    print("\nTravel System Statistics:")
    stats = travel_system.get_travel_statistics()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2e}")
        else:
            print(f"  {key}: {value}")

    # Test path blocking by gravity wells
    print("\nTesting gravity well interference...")
    blocked_start = Vector3D(-5 * LIGHT_YEAR, 0, 0)
    blocked_end = Vector3D(5 * LIGHT_YEAR, 0, 0)
    is_blocked = travel_system.is_path_blocked_by_gravity(blocked_start, blocked_end)
    print(f"Path from {blocked_start.distance_to(blocked_end)/LIGHT_YEAR:.1f} ly blocked: {is_blocked}")

    # Create a spaceship and test its capabilities
    print("\nCreating test spaceship...")
    test_ship = Spaceship("test_ship_001", "Explorer", ship_mass, available_energy)
    test_ship.position = start_pos
    test_ship.set_ftl_engine('warp_5')

    ship_travel_cost = test_ship.calculate_travel_cost(end_pos)
    print(f"Ship travel cost:")
    print(f"  Time: {ship_travel_cost['time'] / (365.25 * 24 * 3600):.2f} years")
    print(f"  Energy: {ship_travel_cost['energy']:.2e} J")
    print(f"  Possible: {ship_travel_cost['possible']}")

    print("\nSpace travel system test completed successfully!")
    print("\nFTL Travel Features:")
    print("- Multiple FTL propulsion methods (Warp, Hyperspace, Quantum Tunneling)")
    print("- Natural and artificial wormhole networks")
    print("- Multi-hop route optimization")
    print("- Gravity well interference")
    print("- Risk assessment and event simulation")
    print("- Energy management and constraints")
    print("- Dynamic path calculation")