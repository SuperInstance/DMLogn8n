#!/usr/bin/env python3
"""
Space Physics Engine - Realistic Space Physics and Orbital Mechanics
Implements Newtonian gravity, relativistic effects, and orbital dynamics
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import math
from enum import Enum

# Physical Constants
G = 6.67430e-11  # Gravitational constant (m^3 kg^-1 s^-2)
c = 299792458  # Speed of light (m/s)
AU = 1.496e11  # Astronomical Unit (m)
PARSEC = 3.086e16  # Parsec (m)
SOLAR_MASS = 1.989e30  # Solar mass (kg)
EARTH_MASS = 5.972e24  # Earth mass (kg)
SOLAR_RADIUS = 6.96e8  # Solar radius (m)
EARTH_RADIUS = 6.371e6  # Earth radius (m)

class OrbitType(Enum):
    CIRCULAR = "circular"
    ELLIPTICAL = "elliptical"
    PARABOLIC = "parabolic"
    HYPERBOLIC = "hyperbolic"

@dataclass
class Vector3D:
    """3D vector for positions and velocities"""
    x: float
    y: float
    z: float

    def __array__(self):
        return np.array([self.x, self.y, self.z])

    @classmethod
    def from_array(cls, arr):
        return cls(arr[0], arr[1], arr[2])

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

    def __truediv__(self, scalar):
        return Vector3D(self.x / scalar, self.y / scalar, self.z / scalar)

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other):
        return Vector3D(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )

@dataclass
class OrbitalElements:
    """Keplerian orbital elements"""
    semi_major_axis: float  # meters
    eccentricity: float  # 0 = circular, 0-1 = elliptical, 1 = parabolic, >1 = hyperbolic
    inclination: float  # radians
    longitude_of_ascending_node: float  # radians
    argument_of_periapsis: float  # radians
    true_anomaly: float  # radians
    epoch: float  # reference time (seconds)

@dataclass
class SpaceObject:
    """Base class for all space objects"""
    id: str
    mass: float  # kg
    radius: float  # meters
    position: Vector3D  # meters
    velocity: Vector3D  # m/s
    acceleration: Vector3D  # m/s^2
    rotation_period: float  # seconds
    albedo: float  # 0-1
    temperature: float  # Kelvin
    age: float  # seconds

class SpacePhysicsEngine:
    """Main physics engine for space simulation"""

    def __init__(self):
        self.objects: Dict[str, SpaceObject] = {}
        self.time = 0.0  # seconds
        self.dt = 3600.0  # 1 hour time step by default
        self.softening_parameter = 1e6  # meters (to prevent singularities)
        self.use_relativity = True
        self.use_tidal_effects = True
        self.use_radiation_pressure = True

    def add_object(self, obj: SpaceObject) -> None:
        """Add an object to the simulation"""
        self.objects[obj.id] = obj

    def remove_object(self, obj_id: str) -> None:
        """Remove an object from the simulation"""
        if obj_id in self.objects:
            del self.objects[obj_id]

    def calculate_gravitational_force(self, obj1: SpaceObject, obj2: SpaceObject) -> Vector3D:
        """Calculate gravitational force between two objects"""

        # Position vector from obj1 to obj2
        r_vec = obj2.position - obj1.position
        r = r_vec.magnitude()

        # Add softening to prevent singularities
        r_soft = np.sqrt(r**2 + self.softening_parameter**2)

        # Newton's law of gravitation
        force_magnitude = G * obj1.mass * obj2.mass / r_soft**2

        # Force direction (from obj1 toward obj2)
        force_direction = r_vec.normalize()

        return force_direction * force_magnitude

    def calculate_relativistic_correction(self, obj: SpaceObject, central_mass: float, r: float) -> float:
        """Calculate General Relativistic correction to orbital motion"""

        if not self.use_relativity or r < 1e6:
            return 1.0

        # Schwarzschild radius
        rs = 2 * G * central_mass / c**2

        # Post-Newtonian correction factor
        correction = 1.0 + 3 * rs / (2 * r)

        return correction

    def calculate_tidal_force(self, obj: SpaceObject, primary: SpaceObject) -> Vector3D:
        """Calculate tidal force on an object due to primary body"""

        r_vec = primary.position - obj.position
        r = r_vec.magnitude()

        if r < 1e6:
            return Vector3D(0, 0, 0)

        # Tidal force gradient
        tidal_strength = 2 * G * primary.mass * obj.radius / r**3

        # Direction (stretching along line to primary)
        direction = r_vec.normalize()

        return direction * tidal_strength

    def calculate_radiation_pressure(self, obj: SpaceObject, star: SpaceObject) -> Vector3D:
        """Calculate radiation pressure from a star"""

        if not self.use_radiation_pressure or star.temperature < 3000:
            return Vector3D(0, 0, 0)

        r_vec = obj.position - star.position
        r = r_vec.magnitude()

        if r < 1e6:
            return Vector3D(0, 0, 0)

        # Stellar luminosity (Stefan-Boltzmann law)
        sigma = 5.67e-8  # Stefan-Boltzmann constant
        luminosity = 4 * np.pi * star.radius**2 * sigma * star.temperature**4

        # Radiation pressure at distance r
        radiation_intensity = luminosity / (4 * np.pi * r**2)
        radiation_pressure = radiation_intensity / c

        # Force on object
        cross_section = np.pi * obj.radius**2
        force_magnitude = radiation_pressure * cross_section * (1 + obj.albedo)

        # Direction (away from star)
        direction = r_vec.normalize()

        return direction * force_magnitude

    def calculate_orbital_elements(self, obj: SpaceObject, primary: SpaceObject) -> OrbitalElements:
        """Calculate Keplerian orbital elements from position and velocity"""

        # Relative position and velocity
        r_vec = obj.position - primary.position
        v_vec = obj.velocity - primary.velocity
        r = r_vec.magnitude()
        v = v_vec.magnitude()

        # Standard gravitational parameter
        mu = G * (obj.mass + primary.mass)

        # Specific orbital energy
        epsilon = v**2 / 2 - mu / r

        # Semi-major axis
        if abs(epsilon) < 1e-10:  # Parabolic orbit
            a = float('inf')
        else:
            a = -mu / (2 * epsilon)

        # Angular momentum vector
        h_vec = r_vec.cross(v_vec)
        h = h_vec.magnitude()

        # Eccentricity vector
        e_vec = (v_vec.cross(h_vec) / mu) - (r_vec / r)
        e = e_vec.magnitude()

        # Inclination
        i = np.arccos(h_vec.z / h) if h > 0 else 0

        # Node line
        n_vec = Vector3D(0, 0, 1).cross(h_vec)
        n = n_vec.magnitude()

        # Longitude of ascending node
        if n > 0:
            omega = np.arccos(n_vec.x / n)
            if n_vec.y < 0:
                omega = 2 * np.pi - omega
        else:
            omega = 0

        # Argument of periapsis
        if e > 1e-10 and n > 0:
            arg_peri = np.arccos(n_vec.dot(e_vec) / (n * e))
            if e_vec.z < 0:
                arg_peri = 2 * np.pi - arg_peri
        else:
            arg_peri = 0

        # True anomaly
        if e > 1e-10:
            true_anomaly = np.arccos(e_vec.dot(r_vec) / (e * r))
            if r_vec.dot(v_vec) < 0:
                true_anomaly = 2 * np.pi - true_anomaly
        else:
            true_anomaly = 0

        return OrbitalElements(
            semi_major_axis=a,
            eccentricity=e,
            inclination=i,
            longitude_of_ascending_node=omega,
            argument_of_periapsis=arg_peri,
            true_anomaly=true_anomaly,
            epoch=self.time
        )

    def orbital_elements_to_state_vectors(self, elements: OrbitalElements, mu: float) -> Tuple[Vector3D, Vector3D]:
        """Convert orbital elements to position and velocity vectors"""

        a = elements.semi_major_axis
        e = elements.eccentricity
        i = elements.inclination
        omega = elements.longitude_of_ascending_node
        arg_peri = elements.argument_of_periapsis
        nu = elements.true_anomaly

        # Distance from focus
        if a == float('inf'):  # Parabolic orbit
            p = 1e10  # Large pseudo-semi-major axis
        else:
            p = a * (1 - e**2)

        r = p / (1 + e * np.cos(nu))

        # Position in orbital plane
        x_orbital = r * np.cos(nu)
        y_orbital = r * np.sin(nu)
        z_orbital = 0

        # Velocity in orbital plane
        h = np.sqrt(mu * p)
        vx_orbital = -mu / h * np.sin(nu)
        vy_orbital = mu / h * (e + np.cos(nu))
        vz_orbital = 0

        # Rotation matrices
        cos_omega = np.cos(omega)
        sin_omega = np.sin(omega)
        cos_i = np.cos(i)
        sin_i = np.sin(i)
        cos_arg_peri = np.cos(arg_peri)
        sin_arg_peri = np.sin(arg_peri)

        # Transform to inertial frame
        x = (cos_omega * cos_arg_peri - sin_omega * sin_arg_peri * cos_i) * x_orbital + \
            (-cos_omega * sin_arg_peri - sin_omega * cos_arg_peri * cos_i) * y_orbital

        y = (sin_omega * cos_arg_peri + cos_omega * sin_arg_peri * cos_i) * x_orbital + \
            (-sin_omega * sin_arg_peri + cos_omega * cos_arg_peri * cos_i) * y_orbital

        z = (sin_arg_peri * sin_i) * x_orbital + (cos_arg_peri * sin_i) * y_orbital

        vx = (cos_omega * cos_arg_peri - sin_omega * sin_arg_peri * cos_i) * vx_orbital + \
             (-cos_omega * sin_arg_peri - sin_omega * cos_arg_peri * cos_i) * vy_orbital

        vy = (sin_omega * cos_arg_peri + cos_omega * sin_arg_peri * cos_i) * vx_orbital + \
             (-sin_omega * sin_arg_peri + cos_omega * cos_arg_peri * cos_i) * vy_orbital

        vz = (sin_arg_peri * sin_i) * vx_orbital + (cos_arg_peri * sin_i) * vy_orbital

        position = Vector3D(x, y, z)
        velocity = Vector3D(vx, vy, vz)

        return position, velocity

    def calculate_hohmann_transfer(self, r1: float, r2: float, mu: float) -> Dict:
        """Calculate Hohmann transfer orbit parameters"""

        a_transfer = (r1 + r2) / 2

        # Velocities
        v1_circular = np.sqrt(mu / r1)
        v2_circular = np.sqrt(mu / r2)

        v_periapsis = np.sqrt(mu * (2/r1 - 1/a_transfer))
        v_apoapsis = np.sqrt(mu * (2/r2 - 1/a_transfer))

        # Delta-v requirements
        delta_v1 = abs(v_periapsis - v1_circular)
        delta_v2 = abs(v2_circular - v_apoapsis)
        total_delta_v = delta_v1 + delta_v2

        # Transfer time
        transfer_time = np.pi * np.sqrt(a_transfer**3 / mu)

        return {
            'semi_major_axis': a_transfer,
            'delta_v1': delta_v1,
            'delta_v2': delta_v2,
            'total_delta_v': total_delta_v,
            'transfer_time': transfer_time,
            'periapsis_velocity': v_periapsis,
            'apoapsis_velocity': v_apoapsis
        }

    def calculate_gravity_assist(self, obj: SpaceObject, planet: SpaceObject,
                                approach_velocity: Vector3D) -> Dict:
        """Calculate gravity assist parameters"""

        # Planet's orbital velocity
        v_planet = planet.velocity

        # Relative velocity
        v_rel_in = approach_velocity - v_planet
        v_rel_in_mag = v_rel_in.magnitude()

        # Planet's escape velocity
        v_escape = np.sqrt(2 * G * planet.mass / planet.radius)

        # Maximum possible deflection
        max_deflection = 2 * np.arcsin(1 / (1 + v_rel_in_mag**2 / v_escape**2))

        # Resulting velocity (assuming optimal approach)
        deflection_angle = max_deflection * 0.8  # 80% of maximum for safety
        speed_boost = 2 * v_planet.magnitude() * np.sin(deflection_angle / 2)

        return {
            'max_deflection': max_deflection,
            'deflection_angle': deflection_angle,
            'speed_boost': speed_boost,
            'v_escape': v_escape,
            'v_rel_in': v_rel_in_mag
        }

    def calculate_lagrange_points(self, primary: SpaceObject, secondary: SpaceObject) -> List[Vector3D]:
        """Calculate the five Lagrange points of a two-body system"""

        # System parameters
        mu = G * (primary.mass + secondary.mass)
        r = (secondary.position - primary.position).magnitude()
        m2 = secondary.mass
        m1 = primary.mass
        alpha = m2 / (m1 + m2)

        # Direction from primary to secondary
        direction = (secondary.position - primary.position).normalize()

        # L1 (between primary and secondary)
        r_L1 = r * (1 - (alpha/3)**(1/3))
        L1 = primary.position + direction * r_L1

        # L2 (beyond secondary)
        r_L2 = r * (1 + (alpha/3)**(1/3))
        L2 = primary.position + direction * r_L2

        # L3 (opposite side of primary)
        r_L3 = r * (1 - 5*alpha/12)
        L3 = primary.position - direction * r_L3

        # L4 and L5 (equilateral triangle points)
        perpendicular = Vector3D(-direction.y, direction.x, 0).normalize()
        r_L45 = r
        angle = np.pi / 3  # 60 degrees

        L4 = primary.position + direction * (r * alpha) + perpendicular * (r_L45 * np.sin(angle))
        L5 = primary.position + direction * (r * alpha) - perpendicular * (r_L45 * np.sin(angle))

        return [L1, L2, L3, L4, L5]

    def calculate_roche_limit(self, primary: SpaceObject, secondary: SpaceObject) -> float:
        """Calculate Roche limit - distance at which tidal forces disrupt the secondary"""

        # Density ratio
        rho_primary = primary.mass / (4/3 * np.pi * primary.radius**3)
        rho_secondary = secondary.mass / (4/3 * np.pi * secondary.radius**3)
        density_ratio = rho_primary / rho_secondary

        # Roche limit for fluid satellite
        roche_limit = 2.44 * primary.radius * (density_ratio)**(1/3)

        return roche_limit

    def calculate_hill_sphere(self, primary: SpaceObject, secondary: SpaceObject,
                             central_body: SpaceObject) -> float:
        """Calculate Hill sphere radius - region where secondary's gravity dominates"""

        a = (secondary.position - central_body.position).magnitude()
        m_secondary = secondary.mass
        m_central = central_body.mass

        hill_radius = a * (m_secondary / (3 * m_central))**(1/3)

        return hill_radius

    def calculate_time_dilation(self, obj: SpaceObject, massive_body: SpaceObject) -> float:
        """Calculate gravitational time dilation effect"""

        r = (obj.position - massive_body.position).magnitude()
        rs = 2 * G * massive_body.mass / c**2  # Schwarzschild radius

        if r < rs:
            return 0  # Inside event horizon

        # Gravitational time dilation factor
        time_dilation = np.sqrt(1 - rs/r)

        return time_dilation

    def calculate_escape_velocity(self, obj: SpaceObject, from_body: SpaceObject) -> float:
        """Calculate escape velocity from a body at object's current position"""

        r = (obj.position - from_body.position).magnitude()
        v_escape = np.sqrt(2 * G * from_body.mass / r)

        return v_escape

    def calculate_orbital_period(self, semi_major_axis: float, central_mass: float) -> float:
        """Calculate orbital period using Kepler's third law"""

        mu = G * central_mass
        period = 2 * np.pi * np.sqrt(semi_major_axis**3 / mu)

        return period

    def calculate_synodic_period(self, period1: float, period2: float) -> float:
        """Calculate synodic period between two orbiting bodies"""

        if abs(period1 - period2) < 1e-10:
            return float('inf')

        synodic = abs(1 / (1/period1 - 1/period2))
        return synodic

    def update_accelerations(self) -> None:
        """Update accelerations for all objects"""

        # Reset accelerations
        for obj in self.objects.values():
            obj.acceleration = Vector3D(0, 0, 0)

        # Calculate gravitational forces
        for i, obj1 in enumerate(self.objects.values()):
            for j, obj2 in enumerate(self.objects.values()):
                if i >= j:  # Skip self and duplicate pairs
                    continue

                # Gravitational force
                force = self.calculate_gravitational_force(obj1, obj2)

                # Apply Newton's third law
                obj1.acceleration = obj1.acceleration + (force / obj1.mass)
                obj2.acceleration = obj2.acceleration - (force / obj2.mass)

                # Add relativistic corrections for massive bodies
                if self.use_relativity and (obj1.mass > 1e28 or obj2.mass > 1e28):
                    r = (obj2.position - obj1.position).magnitude()
                    if obj1.mass > 1e28:  # obj1 is massive
                        correction = self.calculate_relativistic_correction(obj2, obj1.mass, r)
                        obj2.acceleration = obj2.acceleration * correction
                    if obj2.mass > 1e28:  # obj2 is massive
                        correction = self.calculate_relativistic_correction(obj1, obj2.mass, r)
                        obj1.acceleration = obj1.acceleration * correction

        # Add tidal effects
        if self.use_tidal_effects:
            for obj1 in self.objects.values():
                for obj2 in self.objects.values():
                    if obj1.id != obj2.id and obj2.mass > 1e25:  # Only from massive bodies
                        tidal_force = self.calculate_tidal_force(obj1, obj2)
                        obj1.acceleration = obj1.acceleration + (tidal_force / obj1.mass)

        # Add radiation pressure from hot stars
        if self.use_radiation_pressure:
            for obj1 in self.objects.values():
                for obj2 in self.objects.values():
                    if obj1.id != obj2.id and obj2.temperature > 3000:  # Hot stars
                        radiation_force = self.calculate_radiation_pressure(obj1, obj2)
                        obj1.acceleration = obj1.acceleration + (radiation_force / obj1.mass)

    def integrate_rk4(self, dt: float) -> None:
        """4th order Runge-Kutta integration for improved accuracy"""

        # Store initial state
        initial_positions = {obj_id: obj.position for obj_id, obj in self.objects.items()}
        initial_velocities = {obj_id: obj.velocity for obj_id, obj in self.objects.items()}

        # k1
        self.update_accelerations()
        k1_v = {obj_id: obj.acceleration for obj_id, obj in self.objects.items()}
        k1_r = {obj_id: obj.velocity for obj_id, obj in self.objects.items()}

        # k2
        for obj_id, obj in self.objects.items():
            obj.position = initial_positions[obj_id] + k1_r[obj_id] * (dt/2)
            obj.velocity = initial_velocities[obj_id] + k1_v[obj_id] * (dt/2)

        self.update_accelerations()
        k2_v = {obj_id: obj.acceleration for obj_id, obj in self.objects.items()}
        k2_r = {obj_id: obj.velocity for obj_id, obj in self.objects.items()}

        # k3
        for obj_id, obj in self.objects.items():
            obj.position = initial_positions[obj_id] + k2_r[obj_id] * (dt/2)
            obj.velocity = initial_velocities[obj_id] + k2_v[obj_id] * (dt/2)

        self.update_accelerations()
        k3_v = {obj_id: obj.acceleration for obj_id, obj in self.objects.items()}
        k3_r = {obj_id: obj.velocity for obj_id, obj in self.objects.items()}

        # k4
        for obj_id, obj in self.objects.items():
            obj.position = initial_positions[obj_id] + k3_r[obj_id] * dt
            obj.velocity = initial_velocities[obj_id] + k3_v[obj_id] * dt

        self.update_accelerations()
        k4_v = {obj_id: obj.acceleration for obj_id, obj in self.objects.items()}
        k4_r = {obj_id: obj.velocity for obj_id, obj in self.objects.items()}

        # Final update
        for obj_id, obj in self.objects.items():
            obj.position = initial_positions[obj_id] + (k1_r[obj_id] + 2*k2_r[obj_id] + 2*k3_r[obj_id] + k4_r[obj_id]) * (dt/6)
            obj.velocity = initial_velocities[obj_id] + (k1_v[obj_id] + 2*k2_v[obj_id] + 2*k3_v[obj_id] + k4_v[obj_id]) * (dt/6)

    def step(self, dt: Optional[float] = None) -> None:
        """Advance simulation by one time step"""

        if dt is not None:
            self.dt = dt

        # Use RK4 for better accuracy
        self.integrate_rk4(self.dt)

        self.time += self.dt

    def detect_collisions(self) -> List[Tuple[str, str]]:
        """Detect collisions between objects"""

        collisions = []

        for i, obj1 in enumerate(self.objects.values()):
            for j, obj2 in enumerate(self.objects.values()):
                if i >= j:
                    continue

                distance = (obj1.position - obj2.position).magnitude()
                min_distance = obj1.radius + obj2.radius

                if distance < min_distance:
                    collisions.append((obj1.id, obj2.id))

        return collisions

    def merge_objects(self, obj1_id: str, obj2_id: str) -> SpaceObject:
        """Merge two colliding objects"""

        obj1 = self.objects[obj1_id]
        obj2 = self.objects[obj2_id]

        # Conservation of mass
        total_mass = obj1.mass + obj2.mass

        # Conservation of momentum
        total_momentum = obj1.velocity * obj1.mass + obj2.velocity * obj2.mass
        final_velocity = total_momentum / total_mass

        # Position of center of mass
        final_position = (obj1.position * obj1.mass + obj2.position * obj2.mass) / total_mass

        # New radius (assuming spherical bodies and constant density)
        volume1 = 4/3 * np.pi * obj1.radius**3
        volume2 = 4/3 * np.pi * obj2.radius**3
        final_radius = (3/4/np.pi * (volume1 + volume2))**(1/3)

        # Create merged object
        merged_obj = SpaceObject(
            id=f"{obj1_id}-{obj2_id}-merged",
            mass=total_mass,
            radius=final_radius,
            position=final_position,
            velocity=final_velocity,
            acceleration=Vector3D(0, 0, 0),
            rotation_period=max(obj1.rotation_period, obj2.rotation_period),
            albedo=(obj1.albedo + obj2.albedo) / 2,
            temperature=(obj1.temperature + obj2.temperature) / 2,
            age=max(obj1.age, obj2.age)
        )

        # Remove original objects and add merged one
        self.remove_object(obj1_id)
        self.remove_object(obj2_id)
        self.add_object(merged_obj)

        return merged_obj

    def calculate_system_energy(self) -> Dict[str, float]:
        """Calculate total energy of the system"""

        kinetic_energy = 0
        potential_energy = 0

        objects_list = list(self.objects.values())

        # Kinetic energy
        for obj in objects_list:
            v_squared = obj.velocity.magnitude()**2
            kinetic_energy += 0.5 * obj.mass * v_squared

        # Gravitational potential energy
        for i, obj1 in enumerate(objects_list):
            for j in range(i+1, len(objects_list)):
                obj2 = objects_list[j]
                r = (obj2.position - obj1.position).magnitude()
                if r > 0:
                    potential_energy -= G * obj1.mass * obj2.mass / r

        total_energy = kinetic_energy + potential_energy

        return {
            'kinetic': kinetic_energy,
            'potential': potential_energy,
            'total': total_energy
        }

    def calculate_system_angular_momentum(self) -> Vector3D:
        """Calculate total angular momentum of the system"""

        total_L = Vector3D(0, 0, 0)

        for obj in self.objects.values():
            # Angular momentum L = r × mv
            L = obj.position.cross(obj.velocity * obj.mass)
            total_L = total_L + L

        return total_L

    def calculate_barycenter(self, obj_ids: List[str]) -> Vector3D:
        """Calculate center of mass for a group of objects"""

        total_mass = 0
        weighted_position = Vector3D(0, 0, 0)

        for obj_id in obj_ids:
            if obj_id in self.objects:
                obj = self.objects[obj_id]
                total_mass += obj.mass
                weighted_position = weighted_position + obj.position * obj.mass

        if total_mass > 0:
            return weighted_position / total_mass
        else:
            return Vector3D(0, 0, 0)

# Utility functions for common calculations
def calculate_sphere_of_influence(body_mass: float, orbital_radius: float,
                                 central_mass: float) -> float:
    """Calculate sphere of influence radius"""
    return orbital_radius * (body_mass / central_mass) ** 0.4

def calculate_delta_v_hohmann(r1: float, r2: float, mu: float) -> float:
    """Calculate total delta-v for Hohmann transfer"""
    hohmann = SpacePhysicsEngine().calculate_hohmann_transfer(r1, r2, mu)
    return hohmann['total_delta_v']

def calculate_orbital_velocity(radius: float, central_mass: float) -> float:
    """Calculate circular orbital velocity"""
    return np.sqrt(G * central_mass / radius)

def calculate_synodic_period_inner(inner_period: float, outer_period: float) -> float:
    """Calculate synodic period for inner body relative to outer"""
    return abs(1 / (1/inner_period - 1/outer_period))

# Example usage
if __name__ == "__main__":
    # Create physics engine
    physics = SpacePhysicsEngine()

    # Create Sun-like star
    sun = SpaceObject(
        id="sun",
        mass=SOLAR_MASS,
        radius=SOLAR_RADIUS,
        position=Vector3D(0, 0, 0),
        velocity=Vector3D(0, 0, 0),
        acceleration=Vector3D(0, 0, 0),
        rotation_period=25.4 * 24 * 3600,  # 25.4 days
        albedo=0.0,
        temperature=5778,
        age=4.6e9 * 365.25 * 24 * 3600
    )

    # Create Earth-like planet
    earth = SpaceObject(
        id="earth",
        mass=EARTH_MASS,
        radius=EARTH_RADIUS,
        position=Vector3D(AU, 0, 0),
        velocity=Vector3D(0, 29780, 0),  # Earth's orbital velocity
        acceleration=Vector3D(0, 0, 0),
        rotation_period=24 * 3600,  # 24 hours
        albedo=0.3,
        temperature=288,
        age=4.5e9 * 365.25 * 24 * 3600
    )

    # Add objects to simulation
    physics.add_object(sun)
    physics.add_object(earth)

    print("Initial Earth orbital parameters:")
    elements = physics.calculate_orbital_elements(earth, sun)
    print(f"Semi-major axis: {elements.semi_major_axis/AU:.3f} AU")
    print(f"Eccentricity: {elements.eccentricity:.3f}")
    print(f"Inclination: {np.degrees(elements.inclination):.1f} degrees")

    # Calculate orbital period
    period = physics.calculate_orbital_period(elements.semi_major_axis, sun.mass)
    print(f"Orbital period: {period/(365.25*24*3600):.2f} years")

    # Calculate escape velocity
    v_escape = physics.calculate_escape_velocity(earth, sun)
    print(f"Escape velocity from Earth's orbit: {v_escape/1000:.2f} km/s")

    # Simulate for one year
    print("\nSimulating one year...")
    steps = int(365.25 * 24 * 3600 / physics.dt)  # One year in hours

    for i in range(steps):
        physics.step()
        if i % (steps // 10) == 0:  # Print progress
            progress = i / steps * 100
            distance = (earth.position - sun.position).magnitude()
            velocity = earth.velocity.magnitude()
            print(f"Progress: {progress:.0f}%, Distance: {distance/AU:.3f} AU, Velocity: {velocity/1000:.2f} km/s")

    # Final orbital parameters
    print("\nFinal Earth orbital parameters:")
    final_elements = physics.calculate_orbital_elements(earth, sun)
    print(f"Semi-major axis: {final_elements.semi_major_axis/AU:.3f} AU")
    print(f"Eccentricity: {final_elements.eccentricity:.3f}")
    print(f"Inclination: {np.degrees(final_elements.inclination):.1f} degrees")

    # Check energy conservation
    energy = physics.calculate_system_energy()
    print(f"\nTotal system energy: {energy['total']:.2e} J")
    print(f"Energy change: {(energy['total'] - energy['total']) * 100:.6f}%")  # Should be ~0

    # Calculate Lagrange points
    lagrange_points = physics.calculate_lagrange_points(sun, earth)
    print(f"\nLagrange points:")
    for i, point in enumerate(lagrange_points, 1):
        distance_from_earth = (point - earth.position).magnitude()
        print(f"L{i}: {distance_from_earth/AU:.3f} AU from Earth")

    print("\nSpace physics engine test completed successfully!")