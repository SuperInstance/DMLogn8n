#!/usr/bin/env python3
"""
Biological Nanites - Self-Replicating Nanobots for Biological Tasks
Advanced nanorobotics system with biological components and autonomous functionality

This system provides:
- Self-replicating nanobot design and simulation
- DNA/RNA-based nanomachines
- Targeted drug delivery and medical applications
- Environmental remediation nanobots
- Quantum-entangled nanite swarms
- Molecular assembly and disassembly
- Nanoscale sensing and communication
- Swarm intelligence and coordination
"""

import numpy as np
import math
import random
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
import json
from collections import defaultdict
import hashlib

class NaniteType(Enum):
    """Types of biological nanites"""
    MEDICAL = "medical"
    ENVIRONMENTAL = "environmental"
    CONSTRUCTION = "construction"
    COMPUTING = "computing"
    SENSING = "sensing"
    REPAIR = "repair"
    QUANTUM = "quantum"
    UNIVERSAL = "universal"

class NaniteFunction(Enum):
    """Primary functions of nanites"""
    REPLICATION = "replication"
    REPAIR = "repair"
    ASSEMBLY = "assembly"
    DISASSEMBLY = "disassembly"
    DELIVERY = "delivery"
    SENSING = "sensing"
    COMPUTATION = "computation"
    COMMUNICATION = "communication"

class NaniteSize(Enum):
    """Size classifications"""
    MOLECULAR = "molecular"  # 1-10 nm
    NANO = "nano"  # 10-100 nm
    MICRON = "micron"  # 100-1000 nm
    COLLOIDAL = "colloidal"  # 1-10 μm

class SwarmBehavior(Enum):
    """Swarm intelligence behaviors"""
    FORAGING = "foraging"
    CONSTRUCTION = "construction"
    DEFENSE = "defense"
    COORDINATION = "coordination"
    SELF_ORGANIZATION = "self_organization"
    QUANTUM_COHERENCE = "quantum_coherence"

@dataclass
class NaniteStructure:
    """Physical structure of nanite"""
    chassis_material: str  # DNA, protein, carbon nanotube, etc.
    size: float  # nanometers
    mass: float  # attograms
    surface_area: float  # nm²
    power_source: str  # ATP, photosynthesis, quantum, etc.
    computation_capability: float  # FLOPS equivalent
    payload_capacity: float  # molecules

@dataclass
class NaniteProgramming:
    """Programming and control systems"""
    dna_sequence: str
    instruction_set: List[str]
    decision_tree: Dict
    neural_network_weights: Optional[np.ndarray]
    quantum_circuit: Optional[str]
    firmware_version: str

@dataclass
class NaniteCapabilities:
    """Functional capabilities"""
    mobility: float  # 0-1 speed
    manipulation: float  # 0-1 precision
    sensing: float  # 0-1 sensitivity
    communication: float  # 0-1 range/clarity
    replication_rate: float  # per hour
    energy_efficiency: float  # 0-1
    durability: float  # 0-1 lifespan
    autonomy: float  # 0-1 independence

@dataclass
class Nanite:
    """Individual nanite"""
    id: str
    type: NaniteType
    structure: NaniteStructure
    programming: NaniteProgramming
    capabilities: NaniteCapabilities
    position: np.ndarray  # 3D coordinates
    velocity: np.ndarray
    energy_level: float  # 0-1
    task_queue: List[Dict]
    memory: Dict[str, any]
    quantum_entanglement: Optional[Set[str]]
    swarm_id: Optional[str]

@dataclass
class Swarm:
    """Collection of coordinated nanites"""
    id: str
    nanites: List[Nanite]
    behavior: SwarmBehavior
    objective: str
    communication_network: Dict[str, List[str]]
    collective_intelligence: float
    quantum_coherence: float

class BiologicalNanites:
    """Advanced biological nanite system"""

    def __init__(self):
        # Nanite parameters
        self.max_nanites_per_swarm = 1000000
        self.default_nanite_size = 50.0  # nanometers
        self.replication_energy_cost = 0.3  # energy units
        self.communication_range = 1000.0  # nanometers
        self.quantum_entanglement_range = float('inf')  # unlimited

        # Material properties
        self.materials = {
            'DNA': {'strength': 0.3, 'flexibility': 0.9, 'biocompatibility': 1.0},
            'protein': {'strength': 0.5, 'flexibility': 0.7, 'biocompatibility': 1.0},
            'carbon_nanotube': {'strength': 1.0, 'flexibility': 0.3, 'biocompatibility': 0.6},
            'silicon': {'strength': 0.8, 'flexibility': 0.1, 'biocompatibility': 0.4},
            'graphene': {'strength': 0.9, 'flexibility': 0.5, 'biocompatibility': 0.7}
        }

        # Power sources
        self.power_sources = {
            'ATP': {'energy_density': 0.7, 'lifetime': 1.0, 'recharge_rate': 0.8},
            'glucose': {'energy_density': 0.5, 'lifetime': 2.0, 'recharge_rate': 0.6},
            'photosynthesis': {'energy_density': 0.3, 'lifetime': 10.0, 'recharge_rate': 0.9},
            'quantum': {'energy_density': 1.0, 'lifetime': 100.0, 'recharge_rate': 1.0},
            'magnetic': {'energy_density': 0.6, 'lifetime': 5.0, 'recharge_rate': 0.7}
        }

        # Swarm algorithms
        self.swarm_algorithms = {
            'particle_swarm': self._particle_swarm_coordination,
            'ant_colony': self._ant_colony_optimization,
            'flocking': self._flocking_behavior,
            'firefly': self._firefly_synchronization,
            'quantum_swarm': self._quantum_swarm_intelligence
        }

        # Active swarms
        self.active_swarms = {}
        self.nanite_registry = {}

    def design_nanite(self, nanite_type: NaniteType, primary_function: NaniteFunction,
                     size_class: NaniteSize, specialized_features: List[str] = None) -> Nanite:
        """Design a specialized nanite"""
        print(f"🔬 Designing {nanite_type.value} nanite")
        print(f"   Primary function: {primary_function.value}")
        print(f"   Size class: {size_class.value}")

        if specialized_features is None:
            specialized_features = []

        # Determine structure based on type and function
        structure = self._design_nanite_structure(nanite_type, primary_function, size_class)

        # Create programming based on function
        programming = self._create_nanite_programming(primary_function, specialized_features)

        # Define capabilities
        capabilities = self._define_nanite_capabilities(nanite_type, primary_function, structure)

        # Generate unique ID
        nanite_id = f"{nanite_type.value}_{primary_function.value}_{hashlib.md5(json.dumps({
            'type': nanite_type.value,
            'function': primary_function.value,
            'size': size_class.value,
            'features': specialized_features
        }).encode()).hexdigest()[:8]}"

        # Create nanite
        nanite = Nanite(
            id=nanite_id,
            type=nanite_type,
            structure=structure,
            programming=programming,
            capabilities=capabilities,
            position=np.random.randn(3) * 1000,  # Initial position
            velocity=np.zeros(3),
            energy_level=1.0,
            task_queue=[],
            memory={},
            quantum_entanglement=set() if 'quantum' in specialized_features else None,
            swarm_id=None
        )

        self.nanite_registry[nanite_id] = nanite

        print(f"   Nanite created: {nanite_id}")
        print(f"   Size: {structure.size:.1f} nm")
        print(f"   Mass: {structure.mass:.2f} ag")
        print(f"   Power source: {structure.power_source}")

        return nanite

    def _design_nanite_structure(self, nanite_type: NaniteType, primary_function: NaniteFunction,
                                size_class: NaniteSize) -> NaniteStructure:
        """Design physical structure of nanite"""
        # Determine size based on class
        size_ranges = {
            NaniteSize.MOLECULAR: (1, 10),
            NaniteSize.NANO: (10, 100),
            NaniteSize.MICRON: (100, 1000),
            NaniteSize.COLLOIDAL: (1000, 10000)
        }
        size = random.uniform(*size_ranges[size_class])

        # Calculate mass and surface area
        density = 1.0  # g/cm³ (approximation)
        volume = (4/3) * math.pi * (size/2)**3  # nm³
        mass = volume * density * 1e-21  # Convert to attograms
        surface_area = 4 * math.pi * (size/2)**2  # nm²

        # Select materials based on type
        if nanite_type == NaniteType.MEDICAL:
            material = random.choice(['DNA', 'protein'])
        elif nanite_type == NaniteType.CONSTRUCTION:
            material = random.choice(['carbon_nanotube', 'graphene'])
        elif nanite_type == NaniteType.QUANTUM:
            material = 'graphene'  # Good for quantum properties
        else:
            material = random.choice(['DNA', 'protein', 'carbon_nanotube'])

        # Select power source
        if primary_function == NaniteFunction.REPLICATION:
            power_source = random.choice(['ATP', 'glucose'])
        elif nanite_type == NaniteType.QUANTUM:
            power_source = 'quantum'
        elif 'solar' in [nanite_type.value, primary_function.value]:
            power_source = 'photosynthesis'
        else:
            power_source = random.choice(['ATP', 'glucose', 'magnetic'])

        # Calculate computation capability
        base_computation = size / 10  # Larger nanites can compute more
        if nanite_type == NaniteType.COMPUTING:
            computation_capability = base_computation * 10
        else:
            computation_capability = base_computation

        # Calculate payload capacity
        payload_capacity = size * 0.1  # 10% of size

        return NaniteStructure(
            chassis_material=material,
            size=size,
            mass=mass,
            surface_area=surface_area,
            power_source=power_source,
            computation_capability=computation_capability,
            payload_capacity=payload_capacity
        )

    def _create_nanite_programming(self, primary_function: NaniteFunction,
                                  specialized_features: List[str]) -> NaniteProgramming:
        """Create programming for nanite"""
        # Generate DNA sequence
        sequence_length = random.randint(1000, 10000)
        bases = ['A', 'T', 'G', 'C']
        dna_sequence = ''.join(random.choices(bases, k=sequence_length))

        # Create instruction set based on function
        instruction_sets = {
            NaniteFunction.REPLICATION: ['find_materials', 'assemble_copy', 'activate_copy'],
            NaniteFunction.REPAIR: ['locate_damage', 'assess_damage', 'apply_repair', 'verify_repair'],
            NaniteFunction.ASSEMBLY: ['locate_components', 'position_components', 'bond_components'],
            NaniteFunction.DISASSEMBLY: ['identify_target', 'break_bonds', 'collect_materials'],
            NaniteFunction.DELIVERY: ['locate_target', 'navigate_to_target', 'release_payload', 'verify_delivery'],
            NaniteFunction.SENSING: ['scan_environment', 'process_data', 'report_findings'],
            NaniteFunction.COMPUTATION: ['receive_input', 'process_data', 'output_result'],
            NaniteFunction.COMMUNICATION: ['encode_message', 'transmit_message', 'receive_message', 'decode_message']
        }

        base_instructions = instruction_sets.get(primary_function, ['idle'])
        instructions = base_instructions + specialized_features

        # Create simple decision tree
        decision_tree = {
            'root': {
                'condition': 'energy_level > 0.2',
                'true': 'execute_task',
                'false': 'seek_energy'
            },
            'execute_task': {
                'condition': 'task_queue not empty',
                'true': 'process_next_task',
                'false': 'idle'
            }
        }

        # Add quantum circuit if quantum features present
        quantum_circuit = None
        if 'quantum' in specialized_features:
            quantum_circuit = "Hadamard(0) -> CNOT(0,1) -> Measure(0,1)"

        return NaniteProgramming(
            dna_sequence=dna_sequence,
            instruction_set=instructions,
            decision_tree=decision_tree,
            neural_network_weights=None,  # Could add learning capabilities
            quantum_circuit=quantum_circuit,
            firmware_version="1.0.0"
        )

    def _define_nanite_capabilities(self, nanite_type: NaniteType, primary_function: NaniteFunction,
                                   structure: NaniteStructure) -> NaniteCapabilities:
        """Define nanite capabilities based on type and structure"""
        # Base capabilities
        capabilities = {
            NaniteType.MEDICAL: {'mobility': 0.7, 'manipulation': 0.6, 'sensing': 0.8, 'communication': 0.6},
            NaniteType.ENVIRONMENTAL: {'mobility': 0.8, 'manipulation': 0.7, 'sensing': 0.6, 'communication': 0.5},
            NaniteType.CONSTRUCTION: {'mobility': 0.5, 'manipulation': 0.9, 'sensing': 0.4, 'communication': 0.5},
            NaniteType.COMPUTING: {'mobility': 0.3, 'manipulation': 0.2, 'sensing': 0.5, 'communication': 0.8},
            NaniteType.SENSING: {'mobility': 0.6, 'manipulation': 0.3, 'sensing': 0.9, 'communication': 0.7},
            NaniteType.REPAIR: {'mobility': 0.6, 'manipulation': 0.8, 'sensing': 0.7, 'communication': 0.6},
            NaniteType.QUANTUM: {'mobility': 0.4, 'manipulation': 0.5, 'sensing': 0.8, 'communication': 1.0},
            NaniteType.UNIVERSAL: {'mobility': 0.6, 'manipulation': 0.6, 'sensing': 0.6, 'communication': 0.6}
        }

        base_caps = capabilities[nanite_type]

        # Adjust based on primary function
        function_modifiers = {
            NaniteFunction.REPLICATION: {'replication_rate': 0.8},
            NaniteFunction.REPAIR: {'manipulation': 1.2, 'durability': 1.2},
            NaniteFunction.ASSEMBLY: {'manipulation': 1.3, 'precision': 1.2},
            NaniteFunction.DELIVERY: {'mobility': 1.2, 'sensing': 1.1},
            NaniteFunction.SENSING: {'sensing': 1.3, 'communication': 1.1},
            NaniteFunction.COMPUTATION: {'computation_capability': 1.5},
            NaniteFunction.COMMUNICATION: {'communication': 1.4, 'autonomy': 1.2}
        }

        # Apply function modifiers
        for cap, modifier in function_modifiers.get(primary_function, {}).items():
            if cap in base_caps:
                base_caps[cap] *= modifier

        # Set default values for missing capabilities
        default_caps = {
            'replication_rate': 0.5,
            'energy_efficiency': 0.7,
            'durability': 0.6,
            'autonomy': 0.5
        }

        for cap, value in default_caps.items():
            if cap not in base_caps:
                base_caps[cap] = value

        # Adjust based on size
        size_modifier = math.log10(structure.size) / 2  # Normalize around 100nm
        if structure.size < 100:
            base_caps['mobility'] *= 1.5  # Smaller = more mobile
            base_caps['energy_efficiency'] *= 1.2
        else:
            base_caps['durability'] *= 1.3  # Larger = more durable

        return NaniteCapabilities(**base_caps)

    def create_swarm(self, swarm_size: int, nanite_template: Nanite,
                    behavior: SwarmBehavior, objective: str) -> Swarm:
        """Create a coordinated swarm of nanites"""
        print(f"🐝 Creating nanite swarm")
        print(f"   Swarm size: {swarm_size}")
        print(f"   Behavior: {behavior.value}")
        print(f"   Objective: {objective}")

        # Generate swarm ID
        swarm_id = f"swarm_{hashlib.md5(f'{swarm_size}_{behavior.value}_{objective}'.encode()).hexdigest()[:8]}"

        # Create nanites for swarm
        nanites = []
        for i in range(swarm_size):
            # Clone template with variations
            nanite = Nanite(
                id=f"{swarm_id}_nanite_{i:06d}",
                type=nanite_template.type,
                structure=nanite_template.structure,
                programming=nanite_template.programming,
                capabilities=nanite_template.capabilities,
                position=np.random.randn(3) * 100,  # Start close together
                velocity=np.random.randn(3) * 10,
                energy_level=random.uniform(0.8, 1.0),
                task_queue=[{'type': 'swarm_objective', 'objective': objective}],
                memory={'swarm_id': swarm_id, 'role': self._assign_swarm_role(i, swarm_size)},
                quantum_entanglement=set() if nanite_template.quantum_entanglement else None,
                swarm_id=swarm_id
            )
            nanites.append(nanite)
            self.nanite_registry[nanite.id] = nanite

        # Create communication network
        communication_network = self._establish_communication_network(nanites)

        # Calculate collective intelligence
        collective_intelligence = self._calculate_collective_intelligence(nanites)

        # Create swarm
        swarm = Swarm(
            id=swarm_id,
            nanites=nanites,
            behavior=behavior,
            objective=objective,
            communication_network=communication_network,
            collective_intelligence=collective_intelligence,
            quantum_coherence=0.0
        )

        self.active_swarms[swarm_id] = swarm

        print(f"   Swarm created: {swarm_id}")
        print(f"   Communication links: {len(communication_network)}")
        print(f"   Collective intelligence: {collective_intelligence:.3f}")

        return swarm

    def _assign_swarm_role(self, index: int, swarm_size: int) -> str:
        """Assign role to nanite in swarm"""
        if index == 0:
            return 'leader'
        elif index < swarm_size * 0.1:
            return 'coordinator'
        elif index < swarm_size * 0.3:
            return 'scout'
        elif index < swarm_size * 0.7:
            return 'worker'
        else:
            return 'support'

    def _establish_communication_network(self, nanites: List[Nanite]) -> Dict[str, List[str]]:
        """Establish communication network between nanites"""
        network = defaultdict(list)

        for i, nanite1 in enumerate(nanites):
            for j, nanite2 in enumerate(nanites):
                if i != j:
                    distance = np.linalg.norm(nanite1.position - nanite2.position)
                    if distance < self.communication_range:
                        # Calculate signal strength based on distance
                        signal_strength = 1.0 / (1.0 + distance / 100)
                        if signal_strength > 0.1:  # Minimum threshold
                            network[nanite1.id].append(nanite2.id)

        return dict(network)

    def _calculate_collective_intelligence(self, nanites: List[Nanite]) -> float:
        """Calculate collective intelligence of swarm"""
        if not nanites:
            return 0.0

        # Individual intelligence components
        avg_computation = np.mean([n.structure.computation_capability for n in nanites])
        avg_communication = np.mean([n.capabilities.communication for n in nanites])
        avg_autonomy = np.mean([n.capabilities.autonomy for n in nanites])

        # Network effects
        num_nanites = len(nanites)
        network_effect = math.log10(num_nanites + 1) / math.log10(1000000 + 1)  # Normalize to million nanites

        # Diversity bonus
        types = set(n.type for n in nanites)
        diversity_bonus = len(types) / len(NaniteType)

        # Collective intelligence
        collective = (avg_computation * 0.3 + avg_communication * 0.3 + avg_autonomy * 0.2 +
                     network_effect * 0.1 + diversity_bonus * 0.1)

        return min(1.0, collective)

    def simulate_swarm_behavior(self, swarm: Swarm, duration: float,
                              environment: Dict[str, any] = None) -> List[Dict]:
        """Simulate swarm behavior over time"""
        print(f"🔬 Simulating swarm behavior")
        print(f"   Swarm ID: {swarm.id}")
        print(f"   Duration: {duration} seconds")
        print(f"   Behavior: {swarm.behavior.value}")

        if environment is None:
            environment = {'temperature': 37.0, 'obstacles': [], 'targets': []}

        history = []
        time_step = 0.01  # 10ms time steps
        steps = int(duration / time_step)

        # Initialize quantum coherence for quantum swarms
        if swarm.behavior == SwarmBehavior.QUANTUM_COHERENCE:
            swarm.quantum_coherence = self._initialize_quantum_coherence(swarm.nanites)

        for step in range(steps):
            current_time = step * time_step

            # Update swarm behavior
            if swarm.behavior in self.swarm_algorithms:
                behavior_func = self.swarm_algorithms[swarm.behavior]
                behavior_func(swarm, environment, time_step)

            # Update individual nanites
            for nanite in swarm.nanites:
                self._update_nanite(nanite, environment, time_step)

            # Update communication network
            self._update_communication_network(swarm)

            # Update quantum coherence
            if swarm.quantum_coherence > 0:
                self._update_quantum_coherence(swarm, time_step)

            # Record state
            if step % 100 == 0:  # Record every second
                state = self._capture_swarm_state(swarm, current_time)
                history.append(state)

                # Progress update
                if step % 1000 == 0:
                    avg_energy = np.mean([n.energy_level for n in swarm.nanites])
                    print(f"   Time: {current_time:.1f}s, Avg energy: {avg_energy:.3f}, "
                          f"Coherence: {swarm.quantum_coherence:.3f}")

        print(f"✅ Swarm simulation complete!")
        return history

    def _update_nanite(self, nanite: Nanite, environment: Dict[str, any], dt: float):
        """Update individual nanite state"""
        # Energy consumption
        energy_consumption = dt * 0.01  # Base consumption
        nanite.energy_level = max(0, nanite.energy_level - energy_consumption)

        # Update position
        if nanite.energy_level > 0.1:
            nanite.position += nanite.velocity * dt

            # Add some randomness
            nanite.velocity += np.random.randn(3) * dt * 10

            # Limit velocity
            max_velocity = nanite.capabilities.mobility * 100
            speed = np.linalg.norm(nanite.velocity)
            if speed > max_velocity:
                nanite.velocity = nanite.velocity / speed * max_velocity

        # Process task queue
        if nanite.task_queue and nanite.energy_level > 0.2:
            task = nanite.task_queue[0]
            self._process_task(nanite, task, dt)
            if task.get('completed', False):
                nanite.task_queue.pop(0)

        # Energy recovery if possible
        if nanite.structure.power_source == 'photosynthesis':
            # Recover energy from light
            nanite.energy_level = min(1.0, nanite.energy_level + dt * 0.02)

    def _process_task(self, nanite: Nanite, task: Dict, dt: float):
        """Process individual nanite task"""
        task_type = task.get('type', 'unknown')

        if task_type == 'swarm_objective':
            # Work towards swarm objective
            progress = task.get('progress', 0.0)
            progress += dt * nanite.capabilities.manipulation * 0.1
            task['progress'] = progress
            if progress >= 1.0:
                task['completed'] = True

        elif task_type == 'replicate':
            # Self-replication
            if nanite.energy_level > self.replication_energy_cost:
                replication_progress = task.get('progress', 0.0)
                replication_progress += dt * nanite.capabilities.replication_rate
                task['progress'] = replication_progress
                if replication_progress >= 1.0:
                    # Create copy (simplified)
                    task['completed'] = True
                    task['copy_created'] = True

    def _particle_swarm_coordination(self, swarm: Swarm, environment: Dict[str, any], dt: float):
        """Particle swarm optimization coordination"""
        if not swarm.nanites:
            return

        # Find best performing nanite
        best_nanite = max(swarm.nanites, key=lambda n: n.energy_level)
        best_position = best_nanite.position

        # Update velocities based on swarm behavior
        for nanite in swarm.nanites:
            # Personal best
            personal_best = nanite.memory.get('best_position', nanite.position)
            # Global best
            global_best = best_position

            # PSO velocity update
            w = 0.7  # Inertia weight
            c1 = 1.5  # Personal coefficient
            c2 = 1.5  # Social coefficient

            r1, r2 = random.random(), random.random()
            nanite.velocity = (w * nanite.velocity +
                              c1 * r1 * (personal_best - nanite.position) +
                              c2 * r2 * (global_best - nanite.position))

            # Update personal best
            if nanite.energy_level > nanite.memory.get('best_energy', 0):
                nanite.memory['best_position'] = nanite.position.copy()
                nanite.memory['best_energy'] = nanite.energy_level

    def _ant_colony_optimization(self, swarm: Swarm, environment: Dict[str, any], dt: float):
        """Ant colony optimization behavior"""
        # Simple pheromone-based coordination
        for nanite in swarm.nanites:
            if random.random() < 0.1:  # 10% chance to lay pheromone
                nanite.memory['pheromone'] = nanite.position.copy()

            # Follow pheromone trails
            pheromones = [n.memory.get('pheromone') for n in swarm.nanites if 'pheromone' in n.memory]
            if pheromones:
                nearest_pheromone = min(pheromones, key=lambda p: np.linalg.norm(p - nanite.position))
                direction = nearest_pheromone - nanite.position
                if np.linalg.norm(direction) > 0:
                    direction = direction / np.linalg.norm(direction)
                    nanite.velocity = direction * nanite.capabilities.mobility * 50

    def _flocking_behavior(self, swarm: Swarm, environment: Dict[str, any], dt: float):
        """Flocking behavior (boids)"""
        for nanite in swarm.nanites:
            neighbors = [n for n in swarm.nanites if n.id != nanite.id and
                        np.linalg.norm(n.position - nanite.position) < 200]

            if neighbors:
                # Separation
                separation = np.zeros(3)
                for neighbor in neighbors:
                    diff = nanite.position - neighbor.position
                    distance = np.linalg.norm(diff)
                    if distance > 0 and distance < 50:
                        separation += diff / distance

                # Alignment
                alignment = np.mean([n.velocity for n in neighbors], axis=0)

                # Cohesion
                center = np.mean([n.position for n in neighbors], axis=0)
                cohesion = center - nanite.position

                # Combine behaviors
                nanite.velocity = (separation * 1.5 + alignment * 1.0 + cohesion * 1.0)

    def _firefly_synchronization(self, swarm: Swarm, environment: Dict[str, any], dt: float):
        """Firefly synchronization behavior"""
        for nanite in swarm.nanites:
            # Synchronize flash patterns (simplified as energy levels)
            neighbors = [n for n in swarm.nanites if n.id != nanite.id and
                        np.linalg.norm(n.position - nanite.position) < 300]

            if neighbors:
                avg_neighbor_energy = np.mean([n.energy_level for n in neighbors])
                # Move towards average
                nanite.energy_level += (avg_neighbor_energy - nanite.energy_level) * dt * 0.5

    def _quantum_swarm_intelligence(self, swarm: Swarm, environment: Dict[str, any], dt: float):
        """Quantum swarm intelligence with entanglement"""
        # Update quantum entanglement
        for i, nanite1 in enumerate(swarm.nanites):
            if nanite1.quantum_entanglement is not None:
                for j, nanite2 in enumerate(swarm.nanites[i+1:], i+1):
                    if nanite2.quantum_entanglement is not None:
                        # Quantum correlation
                        if random.random() < swarm.quantum_coherence:
                            nanite1.quantum_entanglement.add(nanite2.id)
                            nanite2.quantum_entanglement.add(nanite1.id)

                            # Quantum communication (instantaneous)
                            shared_state = (nanite1.energy_level + nanite2.energy_level) / 2
                            nanite1.energy_level = shared_state
                            nanite2.energy_level = shared_state

    def _initialize_quantum_coherence(self, nanites: List[Nanite]) -> float:
        """Initialize quantum coherence in swarm"""
        # Create quantum entanglement between some nanites
        num_entangled = min(len(nanites) // 10, 100)  # Entangle 10% or up to 100

        entangled_nanites = random.sample(nanites, num_entangled)
        for i, nanite1 in enumerate(entangled_nanites):
            for nanite2 in entangled_nanites[i+1:]:
                if nanite1.quantum_entanglement is not None:
                    nanite1.quantum_entanglement.add(nanite2.id)
                if nanite2.quantum_entanglement is not None:
                    nanite2.quantum_entanglement.add(nanite1.id)

        return num_entangled / len(nanites)

    def _update_quantum_coherence(self, swarm: Swarm, dt: float):
        """Update quantum coherence in swarm"""
        # Decoherence over time
        swarm.quantum_coherence *= (1 - dt * 0.01)

        # Maintain coherence through energy
        avg_energy = np.mean([n.energy_level for n in swarm.nanites])
        if avg_energy > 0.8:
            swarm.quantum_coherence = min(1.0, swarm.quantum_coherence + dt * 0.05)

    def _update_communication_network(self, swarm: Swarm):
        """Update communication network based on current positions"""
        new_network = defaultdict(list)

        for i, nanite1 in enumerate(swarm.nanites):
            for j, nanite2 in enumerate(swarm.nanites):
                if i != j:
                    distance = np.linalg.norm(nanite1.position - nanite2.position)
                    if distance < self.communication_range:
                        signal_strength = 1.0 / (1.0 + distance / 100)
                        if signal_strength > 0.1:
                            new_network[nanite1.id].append(nanite2.id)

        swarm.communication_network = dict(new_network)

    def _capture_swarm_state(self, swarm: Swarm, time: float) -> Dict:
        """Capture current swarm state"""
        positions = np.array([n.position for n in swarm.nanites])
        velocities = np.array([n.velocity for n in swarm.nanites])
        energies = [n.energy_level for n in swarm.nanites]

        return {
            'time': time,
            'swarm_id': swarm.id,
            'num_nanites': len(swarm.nanites),
            'avg_position': np.mean(positions, axis=0).tolist(),
            'position_spread': np.std(positions).tolist(),
            'avg_velocity': np.mean(velocities, axis=0).tolist(),
            'avg_energy': np.mean(energies),
            'energy_std': np.std(energies),
            'collective_intelligence': swarm.collective_intelligence,
            'quantum_coherence': swarm.quantum_coherence,
            'communication_links': sum(len(links) for links in swarm.communication_network.values())
        }

def main():
    """Demonstration of biological nanites system"""
    print("🔬 Biological Nanites - Self-Replicating Nanobots System")
    print("=" * 65)

    nanite_system = BiologicalNanites()

    # Design different types of nanites
    print(f"\n🏗️  Designing specialized nanites")

    medical_nanite = nanite_system.design_nanite(
        nanite_type=NaniteType.MEDICAL,
        primary_function=NaniteFunction.DELIVERY,
        size_class=NaniteSize.NANO,
        specialized_features=['targeting', 'biocompatible']
    )

    construction_nanite = nanite_system.design_nanite(
        nanite_type=NaniteType.CONSTRUCTION,
        primary_function=NaniteFunction.ASSEMBLY,
        size_class=NaniteSize.MICRON,
        specialized_features=['molecular_bonding', 'precision']
    )

    quantum_nanite = nanite_system.design_nanite(
        nanite_type=NaniteType.QUANTUM,
        primary_function=NaniteFunction.COMPUTATION,
        size_class=NaniteSize.NANO,
        specialized_features=['quantum', 'entanglement', 'superposition']
    )

    environmental_nanite = nanite_system.design_nanite(
        nanite_type=NaniteType.ENVIRONMENTAL,
        primary_function=NaniteFunction.DISASSEMBLY,
        size_class=NaniteSize.MICRON,
        specialized_features=['chemical_processing', 'waste_breakdown']
    )

    # Create swarms with different behaviors
    print(f"\n🐝 Creating nanite swarms")

    medical_swarm = nanite_system.create_swarm(
        swarm_size=1000,
        nanite_template=medical_nanite,
        behavior=SwarmBehavior.FORAGING,
        objective="target_disease_cells"
    )

    construction_swarm = nanite_system.create_swarm(
        swarm_size=500,
        nanite_template=construction_nanite,
        behavior=SwarmBehavior.CONSTRUCTION,
        objective="build_nanostructure"
    )

    quantum_swarm = nanite_system.create_swarm(
        swarm_size=200,
        nanite_template=quantum_nanite,
        behavior=SwarmBehavior.QUANTUM_COHERENCE,
        objective="quantum_computation"
    )

    # Simulate swarm behaviors
    print(f"\n🔬 Simulating swarm behaviors")

    environment = {
        'temperature': 37.0,
        'obstacles': [],
        'targets': [{'position': np.array([100, 100, 100]), 'type': 'disease_cell'}]
    }

    medical_history = nanite_system.simulate_swarm_behavior(
        swarm=medical_swarm,
        duration=10.0,
        environment=environment
    )

    construction_history = nanite_system.simulate_swarm_behavior(
        swarm=construction_swarm,
        duration=5.0,
        environment={'temperature': 25.0, 'obstacles': []}
    )

    quantum_history = nanite_system.simulate_swarm_behavior(
        swarm=quantum_swarm,
        duration=3.0,
        environment={'temperature': 20.0, 'quantum_field': True}
    )

    # Analyze results
    print(f"\n📊 Swarm behavior analysis")

    for swarm_name, history in [
        ("Medical Swarm", medical_history),
        ("Construction Swarm", construction_history),
        ("Quantum Swarm", quantum_history)
    ]:
        if history:
            final_state = history[-1]
            avg_energy = final_state['avg_energy']
            coherence = final_state['quantum_coherence']
            intelligence = final_state['collective_intelligence']

            print(f"   {swarm_name}:")
            print(f"     Final average energy: {avg_energy:.3f}")
            print(f"     Quantum coherence: {coherence:.3f}")
            print(f"     Collective intelligence: {intelligence:.3f}")
            print(f"     Communication links: {final_state['communication_links']}")

    # Test self-replication
    print(f"\n🔄 Testing self-replication")

    replication_nanite = nanite_system.design_nanite(
        nanite_type=NaniteType.UNIVERSAL,
        primary_function=NaniteFunction.REPLICATION,
        size_class=NaniteSize.NANO,
        specialized_features=['self_replication', 'resource_gathering']
    )

    replication_swarm = nanite_system.create_swarm(
        swarm_size=10,
        nanite_template=replication_nanite,
        behavior=SwarmBehavior.SELF_ORGANIZATION,
        objective="replicate_swarm"
    )

    # Add replication tasks
    for nanite in replication_swarm.nanites:
        nanite.task_queue.append({
            'type': 'replicate',
            'progress': 0.0,
            'completed': False
        })

    replication_history = nanite_system.simulate_swarm_behavior(
        swarm=replication_swarm,
        duration=5.0
    )

    # Count successful replications
    successful_replications = sum(
        1 for n in replication_swarm.nanites
        for task in n.task_queue
        if task.get('copy_created', False)
    )

    print(f"   Successful replications: {successful_replications}")
    print(f"   Swarm size growth: {len(replication_swarm.nanites)} → {len(replication_swarm.nanites) + successful_replications}")

    # Export results
    results = {
        'nanites_designed': 4,
        'swarms_created': 4,
        'total_nanites': len(medical_swarm.nanites) + len(construction_swarm.nanites) + len(quantum_swarm.nanites) + len(replication_swarm.nanites),
        'behaviors_tested': ['foraging', 'construction', 'quantum_coherence', 'self_organization'],
        'self_replication_success': successful_replications > 0,
        'quantum_coherence_achieved': max(s.quantum_coherence for s in [medical_swarm, construction_swarm, quantum_swarm, replication_swarm]),
        'max_collective_intelligence': max(s.collective_intelligence for s in [medical_swarm, construction_swarm, quantum_swarm, replication_swarm])
    }

    with open('/home/activeloguser/DMLogn8n/biology/synthetic/nanites_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n✨ Biological nanites system demonstration complete!")
    print(f"   Individual nanites designed: {len(nanite_system.nanite_registry)}")
    print(f"   Active swarms: {len(nanite_system.active_swarms)}")
    print(f"   Self-replication achieved: {successful_replications > 0}")
    print(f"   Max quantum coherence: {results['quantum_coherence_achieved']:.3f}")
    print(f"   Results exported to: nanites_results.json")

if __name__ == "__main__":
    main()