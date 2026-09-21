"""
DMLogn8n Quantum AI Integration System
======================================

A groundbreaking quantum computing integration system that harnesses quantum algorithms
to enhance AI capabilities beyond classical limits.

Core Capabilities:
- Quantum Machine Learning (QML) algorithms
- Quantum optimization for NP-hard problems
- Quantum entanglement for AI communication
- Quantum cryptography and security
- Hybrid classical-quantum algorithms
- Quantum simulation for complex systems
- Multi-platform quantum hardware support
- Quantum advantage demonstration and benchmarking

Supported Quantum Platforms:
- IBM Quantum (Qiskit)
- Rigetti Computing (Forest)
- IonQ (IonQ Quantum Cloud)
- Google Quantum AI (Cirq)
- Microsoft Azure Quantum
- Amazon Braket

Author: DMLogn8n Quantum AI Research Team
Version: 1.0.0
"""

from .quantum_processor import QuantumProcessor
from .qml_algorithm import QuantumMLAlgorithm
from .quantum_optimizer import QuantumOptimizer
from .quantum_entanglement import QuantumEntanglement
from .quantum_cryptography import QuantumCryptography
from .hybrid_quantum import HybridQuantum
from .quantum_simulation import QuantumSimulation
from .quantum_interface import QuantumInterface

__version__ = "1.0.0"
__author__ = "DMLogn8n Quantum AI Research Team"

# Initialize the quantum AI system
class QuantumAI:
    """Main interface for the DMLogn8n Quantum AI System"""

    def __init__(self, backend="ibm", shots=1024, optimization_level=3):
        self.backend = backend
        self.shots = shots
        self.optimization_level = optimization_level

        # Initialize quantum components
        self.processor = QuantumProcessor(backend=backend, shots=shots)
        self.qml = QuantumMLAlgorithm(processor=self.processor)
        self.optimizer = QuantumOptimizer(processor=self.processor)
        self.entanglement = QuantumEntanglement(processor=self.processor)
        self.cryptography = QuantumCryptography(processor=self.processor)
        self.hybrid = HybridQuantum(processor=self.processor)
        self.simulation = QuantumSimulation(processor=self.processor)
        self.interface = QuantumInterface(backend=backend)

    def benchmark_quantum_advantage(self, problem_size=20):
        """Demonstrate quantum advantage for specific computational tasks"""
        return self.hybrid.benchmark_classical_vs_quantum(problem_size)

    def get_system_status(self):
        """Get comprehensive quantum system status"""
        return {
            "processor_status": self.processor.get_status(),
            "backend_capabilities": self.interface.get_backend_info(),
            "active_circuits": self.processor.get_active_circuits(),
            "system_metrics": self.processor.get_metrics()
        }

    def shutdown(self):
        """Gracefully shutdown quantum system"""
        self.processor.cleanup()
        self.interface.disconnect()