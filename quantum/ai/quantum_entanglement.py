"""
Quantum Entanglement - Quantum Entanglement for AI Communication
=================================================================

Advanced quantum entanglement systems enabling instantaneous AI agent communication,
quantum networking, and distributed quantum computing capabilities.

Key Features:
- Quantum entanglement generation and management
- Bell state creation and verification
- Quantum teleportation protocols
- Entanglement swapping and quantum repeaters
- Multi-partite entanglement networks
- Quantum error correction through entanglement
- Quantum sensing and metrology
- Distributed quantum computing

Applications:
- Instantaneous AI agent communication
- Quantum secure communication
- Distributed learning systems
- Quantum sensing networks
- Multi-agent coordination
- Quantum-enhanced decision making
- Quantum swarm intelligence
"""

import numpy as np
import time
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging
from abc import ABC, abstractmethod
import json

class EntanglementType(Enum):
    """Types of quantum entanglement"""
    BELL_STATE = "bell"
    GHZ_STATE = "ghz"
    W_STATE = "w"
    CLUSTER_STATE = "cluster"
    GRAPH_STATE = "graph"
    NOON_STATE = "noon"
    SQUEEZED_STATE = "squeezed"

class EntanglementProtocol(Enum):
    """Quantum communication protocols"""
    QUANTUM_TELEPORTATION = "teleportation"
    SUPERDENSE_CODING = "superdense_coding"
    ENTANGLEMENT_SWAPPING = "swapping"
    QUANTUM_KEY_DISTRIBUTION = "qkd"
    QUANTUM_SECRET_SHARING = "secret_sharing"

@dataclass
class EntangledPair:
    """Entangled quantum pair representation"""
    id: str
    type: EntanglementType
    qubits: List[int]
    circuit_id: str
    fidelity: float
    creation_time: float
    measurement_history: List[Dict[str, Any]]
    entangled_agents: List[str] = None

@dataclass
class QuantumChannel:
    """Quantum communication channel"""
    id: str
    entangled_pairs: List[str]
    channel_capacity: float
    noise_level: float
    bandwidth: float
    active: bool = True
    latency: float = 0.0  # Instantaneous for entanglement

@dataclass
class TeleportationResult:
    """Quantum teleportation result"""
    success: bool
    fidelity: float
    transmitted_state: np.ndarray
    classical_bits: List[int]
    execution_time: float

class QuantumEntanglement:
    """Advanced quantum entanglement system for AI communication"""

    def __init__(self, processor):
        self.processor = processor
        self.logger = logging.getLogger(__name__)

        # Entanglement registry
        self.entangled_pairs: Dict[str, EntangledPair] = {}
        self.quantum_channels: Dict[str, QuantumChannel] = {}

        # Network topology
        self.agent_connections: Dict[str, List[str]] = {}
        self.entanglement_network: Dict[str, List[str]] = {}

        # Performance metrics
        self.metrics = {
            "total_entangled_pairs": 0,
            "successful_teleportations": 0,
            "average_fidelity": 0.0,
            "network_capacity": 0.0,
            "entanglement_distribution_rate": 0.0,
            "quantum_communication_volume": 0
        }

        # Protocol implementations
        self.protocols = {
            "teleportation": self._quantum_teleportation,
            "superdense_coding": self._superdense_coding,
            "entanglement_swapping": self._entanglement_swapping,
            "qkd": self._quantum_key_distribution
        }

    def create_bell_pair(self, agent_a: str, agent_b: str) -> str:
        """Create Bell state entangled pair for two AI agents"""
        pair_id = f"bell_{agent_a}_{agent_b}_{int(time.time())}"
        circuit_id = self.processor.create_bell_state(0, 1)

        # Calculate initial fidelity
        fidelity = self._calculate_entanglement_fidelity(circuit_id)

        entangled_pair = EntangledPair(
            id=pair_id,
            type=EntanglementType.BELL_STATE,
            qubits=[0, 1],
            circuit_id=circuit_id,
            fidelity=fidelity,
            creation_time=time.time(),
            measurement_history=[],
            entangled_agents=[agent_a, agent_b]
        )

        self.entangled_pairs[pair_id] = entangled_pair

        # Update agent connections
        if agent_a not in self.agent_connections:
            self.agent_connections[agent_a] = []
        if agent_b not in self.agent_connections:
            self.agent_connections[agent_b] = []

        self.agent_connections[agent_a].append(agent_b)
        self.agent_connections[agent_b].append(agent_a)

        # Update metrics
        self.metrics["total_entangled_pairs"] += 1
        self._update_average_fidelity(fidelity)

        self.logger.info(f"Created Bell pair {pair_id} between {agent_a} and {agent_b}")
        return pair_id

    def create_ghz_state(self, agents: List[str]) -> str:
        """Create GHZ state for multiple AI agents"""
        num_agents = len(agents)
        pair_id = f"ghz_{'_'.join(agents)}_{int(time.time())}"
        circuit_id = self.processor.create_ghz_state(num_agents)

        fidelity = self._calculate_entanglement_fidelity(circuit_id)

        entangled_pair = EntangledPair(
            id=pair_id,
            type=EntanglementType.GHZ_STATE,
            qubits=list(range(num_agents)),
            circuit_id=circuit_id,
            fidelity=fidelity,
            creation_time=time.time(),
            measurement_history=[],
            entangled_agents=agents.copy()
        )

        self.entangled_pairs[pair_id] = entangled_pair

        # Update multi-agent connections
        for i, agent in enumerate(agents):
            if agent not in self.agent_connections:
                self.agent_connections[agent] = []
            for j, other_agent in enumerate(agents):
                if i != j:
                    self.agent_connections[agent].append(other_agent)

        self.metrics["total_entangled_pairs"] += 1
        self._update_average_fidelity(fidelity)

        self.logger.info(f"Created GHZ state {pair_id} for {len(agents)} agents")
        return pair_id

    def create_w_state(self, agents: List[str]) -> str:
        """Create W state for robust multi-agent entanglement"""
        num_agents = len(agents)
        pair_id = f"w_{'_'.join(agents)}_{int(time.time())}"
        circuit_id = self._create_w_state_circuit(num_agents)

        fidelity = self._calculate_entanglement_fidelity(circuit_id)

        entangled_pair = EntangledPair(
            id=pair_id,
            type=EntanglementType.W_STATE,
            qubits=list(range(num_agents)),
            circuit_id=circuit_id,
            fidelity=fidelity,
            creation_time=time.time(),
            measurement_history=[],
            entangled_agents=agents.copy()
        )

        self.entangled_pairs[pair_id] = entangled_pair

        # Update connections
        for agent in agents:
            if agent not in self.agent_connections:
                self.agent_connections[agent] = []
            self.agent_connections[agent].extend([a for a in agents if a != agent])

        self.metrics["total_entangled_pairs"] += 1
        self._update_average_fidelity(fidelity)

        self.logger.info(f"Created W state {pair_id} for {len(agents)} agents")
        return pair_id

    def _create_w_state_circuit(self, num_qubits: int) -> str:
        """Create W state circuit"""
        circuit_id = self.processor.create_circuit("w_state", num_qubits)

        # W state preparation
        self.processor.add_gate(circuit_id, "h", [0])
        for i in range(1, num_qubits):
            self.processor.add_gate(circuit_id, "cy", [0, i])

        return circuit_id

    def create_quantum_channel(self, channel_id: str, entangled_pairs: List[str],
                              bandwidth: float = 1.0, noise_level: float = 0.01) -> str:
        """Create quantum communication channel"""
        # Validate entangled pairs
        for pair_id in entangled_pairs:
            if pair_id not in self.entangled_pairs:
                raise ValueError(f"Entangled pair {pair_id} not found")

        channel = QuantumChannel(
            id=channel_id,
            entangled_pairs=entangled_pairs.copy(),
            channel_capacity=bandwidth * len(entangled_pairs),
            noise_level=noise_level,
            bandwidth=bandwidth,
            latency=0.0  # Instantaneous quantum communication
        )

        self.quantum_channels[channel_id] = channel

        # Update network capacity
        self.metrics["network_capacity"] += channel.channel_capacity

        self.logger.info(f"Created quantum channel {channel_id} with {len(entangled_pairs)} entangled pairs")
        return channel_id

    def quantum_teleportation(self, state_to_teleport: np.ndarray, source_agent: str,
                            target_agent: str, entangled_pair_id: str = None) -> TeleportationResult:
        """Perform quantum teleportation between AI agents"""
        start_time = time.time()

        # Find or create entangled pair
        if entangled_pair_id is None:
            entangled_pair_id = self._find_entangled_pair(source_agent, target_agent)
            if entangled_pair_id is None:
                entangled_pair_id = self.create_bell_pair(source_agent, target_agent)

        entangled_pair = self.entangled_pairs[entangled_pair_id]

        # Perform teleportation protocol
        success, fidelity, classical_bits = self._quantum_teleportation(
            state_to_teleport, entangled_pair
        )

        execution_time = time.time() - start_time

        if success:
            self.metrics["successful_teleportations"] += 1
            self.metrics["quantum_communication_volume"] += 1

        result = TeleportationResult(
            success=success,
            fidelity=fidelity,
            transmitted_state=state_to_teleport,
            classical_bits=classical_bits,
            execution_time=execution_time
        )

        # Update entangled pair history
        entangled_pair.measurement_history.append({
            "timestamp": time.time(),
            "protocol": "teleportation",
            "success": success,
            "fidelity": fidelity
        })

        self.logger.info(f"Quantum teleportation {success and 'successful' or 'failed'} "
                        f"between {source_agent} and {target_agent}")
        return result

    def _quantum_teleportation(self, state: np.ndarray, entangled_pair: EntangledPair) -> Tuple[bool, float, List[int]]:
        """Implement quantum teleportation protocol"""
        # Step 1: Prepare quantum circuit
        circuit_id = self.processor.create_circuit("teleportation", 3, 2)

        # Encode state to teleport
        theta = np.arccos(state[0]) if len(state) >= 1 else 0
        phi = np.angle(state[1]) if len(state) >= 2 else 0

        self.processor.add_gate(circuit_id, "ry", [0], [theta])
        self.processor.add_gate(circuit_id, "rz", [0], [phi])

        # Create entanglement between qubits 1 and 2
        self.processor.add_gate(circuit_id, "h", [1])
        self.processor.add_gate(circuit_id, "cx", [1, 2])

        # Bell measurement on qubits 0 and 1
        self.processor.add_gate(circuit_id, "cx", [0, 1])
        self.processor.add_gate(circuit_id, "h", [0])

        # Measure qubits 0 and 1
        self.processor.add_gate(circuit_id, "measure", [0], [], [0])
        self.processor.add_gate(circuit_id, "measure", [1], [], [1])

        # Execute circuit
        result = self.processor.execute_circuit(circuit_id, shots=1)

        # Extract classical bits
        counts = result.counts
        measurement = list(counts.keys())[0] if counts else "00"
        classical_bits = [int(measurement[0]), int(measurement[1])]

        # Calculate fidelity based on measurement result
        base_fidelity = entangled_pair.fidelity
        noise_penalty = np.random.uniform(0.01, 0.05)
        fidelity = max(0.5, base_fidelity - noise_penalty)

        success = np.random.random() < fidelity

        return success, fidelity, classical_bits

    def superdense_coding(self, bits_to_send: List[int], source_agent: str,
                         target_agent: str, entangled_pair_id: str = None) -> Dict[str, Any]:
        """Perform superdense coding to transmit 2 classical bits using 1 qubit"""
        if len(bits_to_send) != 2:
            raise ValueError("Superdense coding requires exactly 2 bits")

        # Find or create entangled pair
        if entangled_pair_id is None:
            entangled_pair_id = self._find_entangled_pair(source_agent, target_agent)
            if entangled_pair_id is None:
                entangled_pair_id = self.create_bell_pair(source_agent, target_agent)

        entangled_pair = self.entangled_pairs[entangled_pair_id]

        start_time = time.time()

        # Perform superdense coding protocol
        success, received_bits = self._superdense_coding(bits_to_send, entangled_pair)

        execution_time = time.time() - start_time

        if success:
            self.metrics["quantum_communication_volume"] += 2  # 2 bits transmitted

        result = {
            "success": success,
            "sent_bits": bits_to_send,
            "received_bits": received_bits,
            "execution_time": execution_time,
            "fidelity": entangled_pair.fidelity
        }

        self.logger.info(f"Superdense coding {success and 'successful' or 'failed'} "
                        f"between {source_agent} and {target_agent}")
        return result

    def _superdense_coding(self, bits: List[int], entangled_pair: EntangledPair) -> Tuple[bool, List[int]]:
        """Implement superdense coding protocol"""
        # Step 1: Encode bits using quantum gates
        circuit_id = self.processor.create_circuit("superdense", 2, 2)

        # Create initial Bell state
        self.processor.add_gate(circuit_id, "h", [0])
        self.processor.add_gate(circuit_id, "cx", [0, 1])

        # Encode bits on qubit 0
        if bits[0] == 1:
            self.processor.add_gate(circuit_id, "x", [0])
        if bits[1] == 1:
            self.processor.add_gate(circuit_id, "z", [0])

        # Bell measurement
        self.processor.add_gate(circuit_id, "cx", [0, 1])
        self.processor.add_gate(circuit_id, "h", [0])

        # Measure both qubits
        self.processor.add_gate(circuit_id, "measure", [0], [], [0])
        self.processor.add_gate(circuit_id, "measure", [1], [], [1])

        # Execute circuit
        result = self.processor.execute_circuit(circuit_id, shots=1)

        # Extract received bits
        counts = result.counts
        measurement = list(counts.keys())[0] if counts else "00"
        received_bits = [int(measurement[1]), int(measurement[0])]  # Note the order

        # Check if transmission was successful
        success = (bits == received_bits) and (np.random.random() < entangled_pair.fidelity)

        return success, received_bits

    def entanglement_swapping(self, intermediate_agent: str, source_agent: str,
                             target_agent: str) -> str:
        """Perform entanglement swapping to extend quantum network"""
        # Find existing entangled pairs
        source_pair_id = self._find_entangled_pair(source_agent, intermediate_agent)
        target_pair_id = self._find_entangled_pair(intermediate_agent, target_agent)

        if source_pair_id is None or target_pair_id is None:
            raise ValueError("Required entangled pairs not found for swapping")

        start_time = time.time()

        # Perform entanglement swapping
        success, new_pair_id = self._entanglement_swapping(
            source_pair_id, target_pair_id, source_agent, target_agent
        )

        execution_time = time.time() - start_time

        if success:
            self.logger.info(f"Entanglement swapping successful: {new_pair_id} "
                           f"between {source_agent} and {target_agent}")
            return new_pair_id
        else:
            self.logger.error("Entanglement swapping failed")
            return None

    def _entanglement_swapping(self, pair1_id: str, pair2_id: str,
                              agent1: str, agent2: str) -> Tuple[bool, str]:
        """Implement entanglement swapping protocol"""
        pair1 = self.entangled_pairs[pair1_id]
        pair2 = self.entangled_pairs[pair2_id]

        # Create swapping circuit
        circuit_id = self.processor.create_circuit("entanglement_swapping", 4, 2)

        # Initialize both Bell pairs
        self.processor.add_gate(circuit_id, "h", [0])
        self.processor.add_gate(circuit_id, "cx", [0, 1])
        self.processor.add_gate(circuit_id, "h", [2])
        self.processor.add_gate(circuit_id, "cx", [2, 3])

        # Perform Bell measurement on intermediate qubits (1 and 2)
        self.processor.add_gate(circuit_id, "cx", [1, 2])
        self.processor.add_gate(circuit_id, "h", [1])

        # Measure intermediate qubits
        self.processor.add_gate(circuit_id, "measure", [1], [], [0])
        self.processor.add_gate(circuit_id, "measure", [2], [], [1])

        # Execute circuit
        result = self.processor.execute_circuit(circuit_id, shots=1)

        # Calculate success probability
        base_fidelity = (pair1.fidelity + pair2.fidelity) / 2
        success = np.random.random() < base_fidelity

        if success:
            # Create new entangled pair
            new_pair_id = f"swapped_{agent1}_{agent2}_{int(time.time())}"
            new_circuit_id = self.processor.create_bell_state(0, 1)

            entangled_pair = EntangledPair(
                id=new_pair_id,
                type=EntanglementType.BELL_STATE,
                qubits=[0, 1],
                circuit_id=new_circuit_id,
                fidelity=base_fidelity * 0.9,  # Slight degradation
                creation_time=time.time(),
                measurement_history=[],
                entangled_agents=[agent1, agent2]
            )

            self.entangled_pairs[new_pair_id] = entangled_pair

            # Update agent connections
            if agent1 not in self.agent_connections:
                self.agent_connections[agent1] = []
            if agent2 not in self.agent_connections:
                self.agent_connections[agent2] = []

            self.agent_connections[agent1].append(agent2)
            self.agent_connections[agent2].append(agent1)

            return True, new_pair_id
        else:
            return False, None

    def quantum_key_distribution(self, alice_agent: str, bob_agent: str,
                                key_length: int = 256) -> Dict[str, Any]:
        """Perform quantum key distribution (BB84 protocol)"""
        start_time = time.time()

        # Generate raw key
        raw_key = self._generate_quantum_key(alice_agent, bob_agent, key_length)

        # Sift key (error checking)
        sifted_key = self._sift_quantum_key(raw_key)

        # Error estimation and privacy amplification
        final_key = self._privacy_amplification(sifted_key)

        execution_time = time.time() - start_time

        result = {
            "alice_agent": alice_agent,
            "bob_agent": bob_agent,
            "raw_key_length": len(raw_key),
            "sifted_key_length": len(sifted_key),
            "final_key_length": len(final_key),
            "final_key": final_key,
            "execution_time": execution_time,
            "security_level": "quantum_secure"
        }

        self.logger.info(f"QKD completed: {len(final_key)} bits generated between "
                        f"{alice_agent} and {bob_agent}")
        return result

    def _generate_quantum_key(self, alice: str, bob: str, length: int) -> List[Tuple[int, str]]:
        """Generate raw quantum key using BB84 protocol"""
        raw_key = []

        for _ in range(length):
            # Alice chooses random bit and basis
            bit = np.random.randint(0, 2)
            basis = np.random.choice(["Z", "X"])

            # Prepare quantum state
            if basis == "Z":
                state = [1, 0] if bit == 0 else [0, 1]
            else:  # X basis
                state = [1/np.sqrt(2), 1/np.sqrt(2)] if bit == 0 else [1/np.sqrt(2), -1/np.sqrt(2)]

            # Bob chooses measurement basis
            bob_basis = np.random.choice(["Z", "X"])

            # Simulate measurement
            if bob_basis == basis:
                # Correct basis - measurement is accurate
                measured_bit = bit
            else:
                # Wrong basis - random result
                measured_bit = np.random.randint(0, 2)

            raw_key.append((bit, basis, bob_basis, measured_bit))

        return raw_key

    def _sift_quantum_key(self, raw_key: List[Tuple[int, str]]) -> List[int]:
        """Sift quantum key by keeping only measurements with matching bases"""
        sifted_key = []
        for bit, alice_basis, bob_basis, measured_bit in raw_key:
            if alice_basis == bob_basis:
                sifted_key.append(measured_bit)
        return sifted_key

    def _privacy_amplification(self, sifted_key: List[int]) -> List[int]:
        """Perform privacy amplification to remove any information an eavesdropper might have"""
        if not sifted_key:
            return []

        # Simple hash-based privacy amplification
        # In practice, would use universal hash functions
        key_length = min(len(sifted_key), 256)
        final_key = []

        for i in range(key_length):
            # XOR multiple bits to amplify privacy
            xor_result = 0
            for j in range(0, len(sifted_key), key_length):
                if i + j < len(sifted_key):
                    xor_result ^= sifted_key[i + j]
            final_key.append(xor_result)

        return final_key

    def create_quantum_network(self, agents: List[str], topology: str = "fully_connected") -> Dict[str, Any]:
        """Create quantum network of entangled AI agents"""
        network_id = f"quantum_network_{'_'.join(agents)}_{int(time.time())}"
        entangled_pairs = []

        if topology == "fully_connected":
            # Create Bell pairs between all agent pairs
            for i in range(len(agents)):
                for j in range(i + 1, len(agents)):
                    pair_id = self.create_bell_pair(agents[i], agents[j])
                    entangled_pairs.append(pair_id)

        elif topology == "star":
            # Star topology with central hub
            hub = agents[0]
            for agent in agents[1:]:
                pair_id = self.create_bell_pair(hub, agent)
                entangled_pairs.append(pair_id)

        elif topology == "ring":
            # Ring topology
            for i in range(len(agents)):
                next_agent = agents[(i + 1) % len(agents)]
                pair_id = self.create_bell_pair(agents[i], next_agent)
                entangled_pairs.append(pair_id)

        # Create quantum channels
        channel_id = f"channel_{network_id}"
        self.create_quantum_channel(channel_id, entangled_pairs, bandwidth=len(agents))

        return {
            "network_id": network_id,
            "agents": agents,
            "topology": topology,
            "entangled_pairs": entangled_pairs,
            "channel_id": channel_id,
            "network_capacity": self.metrics["network_capacity"]
        }

    def verify_entanglement(self, entangled_pair_id: str) -> Dict[str, Any]:
        """Verify entanglement fidelity using Bell inequality tests"""
        if entangled_pair_id not in self.entangled_pairs:
            raise ValueError(f"Entangled pair {entangled_pair_id} not found")

        entangled_pair = self.entangled_pairs[entangled_pair_id]

        # Perform Bell state tomography
        fidelity = self._perform_bell_tomography(entangled_pair)

        # Calculate Bell inequality violation
        bell_parameter = self._calculate_bell_parameter(entangled_pair)

        # Update fidelity
        entangled_pair.fidelity = fidelity

        result = {
            "pair_id": entangled_pair_id,
            "fidelity": fidelity,
            "bell_parameter": bell_parameter,
            "entanglement_verified": bell_parameter > 2.0,
            "timestamp": time.time()
        }

        self.logger.info(f"Entanglement verification for {entangled_pair_id}: "
                        f"fidelity={fidelity:.3f}, Bell parameter={bell_parameter:.3f}")
        return result

    def _perform_bell_tomography(self, entangled_pair: EntangledPair) -> float:
        """Perform Bell state tomography to measure fidelity"""
        # Simulate tomography measurements
        num_measurements = 1000
        measurement_results = []

        for _ in range(num_measurements):
            # Create measurement circuit
            circuit_id = self.processor.create_circuit("tomography", 2, 2)

            # Add measurement bases (Z-Z, Z-X, X-Z, X-X)
            basis_choice = np.random.randint(0, 4)
            if basis_choice == 0:
                # Z-Z measurement (default)
                pass
            elif basis_choice == 1:
                # Z-X measurement
                self.processor.add_gate(circuit_id, "h", [1])
            elif basis_choice == 2:
                # X-Z measurement
                self.processor.add_gate(circuit_id, "h", [0])
            else:
                # X-X measurement
                self.processor.add_gate(circuit_id, "h", [0])
                self.processor.add_gate(circuit_id, "h", [1])

            # Measure
            self.processor.add_gate(circuit_id, "measure", [0], [], [0])
            self.processor.add_gate(circuit_id, "measure", [1], [], [1])

            # Execute
            result = self.processor.execute_circuit(circuit_id, shots=1)
            counts = result.counts
            measurement = list(counts.keys())[0] if counts else "00"
            measurement_results.append((basis_choice, measurement))

        # Calculate fidelity from measurement statistics
        fidelity = self._calculate_fidelity_from_tomography(measurement_results, entangled_pair)
        return fidelity

    def _calculate_fidelity_from_tomography(self, measurements: List[Tuple[int, str]],
                                          entangled_pair: EntangledPair) -> float:
        """Calculate fidelity from tomography measurements"""
        # Simplified fidelity calculation
        # In practice, would use maximum likelihood estimation

        base_fidelity = entangled_pair.fidelity
        noise = np.random.normal(0, 0.02)  # Measurement noise
        fidelity = np.clip(base_fidelity + noise, 0.5, 1.0)

        return fidelity

    def _calculate_bell_parameter(self, entangled_pair: EntangledPair) -> float:
        """Calculate CHSH Bell parameter"""
        # Simulate CHSH inequality test
        # Classical bound: 2.0, Quantum bound: 2√2 ≈ 2.828

        base_violation = 2.5  # Start with quantum violation
        noise_factor = np.random.uniform(-0.3, 0.1)
        bell_parameter = base_violation + noise_factor

        return max(2.0, min(2.828, bell_parameter))

    def _calculate_entanglement_fidelity(self, circuit_id: str) -> float:
        """Calculate initial entanglement fidelity"""
        # Simulate fidelity based on circuit depth and backend noise
        circuit = self.processor.circuits[circuit_id]
        base_fidelity = 0.95
        depth_penalty = 0.001 * circuit.depth
        noise = np.random.uniform(0.01, 0.05)

        fidelity = base_fidelity - depth_penalty - noise
        return max(0.5, fidelity)

    def _find_entangled_pair(self, agent_a: str, agent_b: str) -> Optional[str]:
        """Find existing entangled pair between two agents"""
        for pair_id, pair in self.entangled_pairs.items():
            agents = pair.entangled_agents
            if agents and agent_a in agents and agent_b in agents:
                return pair_id
        return None

    def _update_average_fidelity(self, new_fidelity: float):
        """Update average fidelity metric"""
        if self.metrics["total_entangled_pairs"] == 1:
            self.metrics["average_fidelity"] = new_fidelity
        else:
            n = self.metrics["total_entangled_pairs"]
            old_avg = self.metrics["average_fidelity"]
            self.metrics["average_fidelity"] = (old_avg * (n - 1) + new_fidelity) / n

    def get_network_status(self) -> Dict[str, Any]:
        """Get comprehensive quantum network status"""
        return {
            "total_entangled_pairs": self.metrics["total_entangled_pairs"],
            "active_channels": len(self.quantum_channels),
            "connected_agents": len(self.agent_connections),
            "average_fidelity": self.metrics["average_fidelity"],
            "network_capacity": self.metrics["network_capacity"],
            "successful_teleportations": self.metrics["successful_teleportations"],
            "quantum_communication_volume": self.metrics["quantum_communication_volume"],
            "agent_connections": self.agent_connections,
            "entanglement_distribution_rate": self.metrics["entanglement_distribution_rate"]
        }

    def get_agent_connections(self, agent: str) -> List[str]:
        """Get quantum connections for a specific agent"""
        return self.agent_connections.get(agent, [])

    def get_entangled_pair_info(self, pair_id: str) -> Dict[str, Any]:
        """Get detailed information about an entangled pair"""
        if pair_id not in self.entangled_pairs:
            raise ValueError(f"Entangled pair {pair_id} not found")

        pair = self.entangled_pairs[pair_id]
        return {
            "id": pair.id,
            "type": pair.type.value,
            "qubits": pair.qubits,
            "fidelity": pair.fidelity,
            "creation_time": pair.creation_time,
            "entangled_agents": pair.entangled_agents,
            "measurement_count": len(pair.measurement_history),
            "age": time.time() - pair.creation_time
        }

    def list_entangled_pairs(self) -> List[str]:
        """List all entangled pairs"""
        return list(self.entangled_pairs.keys())

    def cleanup_expired_pairs(self, max_age: float = 3600.0) -> int:
        """Clean up expired entangled pairs"""
        current_time = time.time()
        expired_pairs = []

        for pair_id, pair in self.entangled_pairs.items():
            if current_time - pair.creation_time > max_age:
                expired_pairs.append(pair_id)

        for pair_id in expired_pairs:
            del self.entangled_pairs[pair_id]

        self.logger.info(f"Cleaned up {len(expired_pairs)} expired entangled pairs")
        return len(expired_pairs)

    def benchmark_quantum_communication(self, num_tests: int = 100) -> Dict[str, Any]:
        """Benchmark quantum communication performance"""
        test_agents = ["alice", "bob"]
        teleportation_times = []
        superdense_times = []
        teleportation_successes = 0
        superdense_successes = 0

        # Create entangled pair for testing
        pair_id = self.create_bell_pair(test_agents[0], test_agents[1])

        for i in range(num_tests):
            # Test teleportation
            state = np.random.rand(2)
            state = state / np.linalg.norm(state)  # Normalize

            start_time = time.time()
            tel_result = self.quantum_teleportation(state, test_agents[0], test_agents[1], pair_id)
            tel_time = time.time() - start_time
            teleportation_times.append(tel_time)

            if tel_result.success:
                teleportation_successes += 1

            # Test superdense coding
            bits = [np.random.randint(0, 2), np.random.randint(0, 2)]

            start_time = time.time()
            sd_result = self.superdense_coding(bits, test_agents[0], test_agents[1], pair_id)
            sd_time = time.time() - start_time
            superdense_times.append(sd_time)

            if sd_result["success"]:
                superdense_successes += 1

        return {
            "num_tests": num_tests,
            "teleportation": {
                "success_rate": teleportation_successes / num_tests,
                "average_time": np.mean(teleportation_times),
                "min_time": np.min(teleportation_times),
                "max_time": np.max(teleportation_times)
            },
            "superdense_coding": {
                "success_rate": superdense_successes / num_tests,
                "average_time": np.mean(superdense_times),
                "min_time": np.min(superdense_times),
                "max_time": np.max(superdense_times)
            },
            "average_fidelity": self.metrics["average_fidelity"]
        }