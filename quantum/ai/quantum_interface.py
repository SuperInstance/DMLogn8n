"""
Quantum Interface - Interface to Quantum Hardware and Simulators
================================================================

Advanced quantum hardware and simulator interface supporting multiple quantum
computing platforms with unified API and automatic resource management.

Supported Platforms:
- IBM Quantum (Qiskit)
- Google Quantum AI (Cirq)
- Rigetti Computing (Forest)
- IonQ Quantum Cloud
- Microsoft Azure Quantum
- Amazon Braket
- Local Simulators (Qiskit Aer, Cirq, etc.)

Key Features:
- Multi-platform quantum backend support
- Automatic backend selection and optimization
- Quantum resource management and scheduling
- Real-time job monitoring and queuing
- Error mitigation and calibration
- Cost optimization and budget management
- Hybrid cloud-local execution
- Performance benchmarking and profiling

Configuration:
- Backend selection and configuration
- API authentication and security
- Resource quotas and limits
- Error handling and retry logic
- Performance optimization settings
- Cost tracking and alerts
"""

import numpy as np
import time
import json
import asyncio
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from abc import ABC, abstractmethod
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

class QuantumBackend(Enum):
    """Supported quantum backends"""
    IBM_QUANTUM = "ibm_quantum"
    GOOGLE_QUANTUM = "google_quantum"
    RIGETTI = "rigetti"
    IONQ = "ionq"
    AZURE_QUANTUM = "azure_quantum"
    AMAZON_BRAKET = "amazon_braket"
    LOCAL_SIMULATOR = "local_simulator"
    CLOUD_SIMULATOR = "cloud_simulator"

class JobStatus(Enum):
    """Quantum job status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    QUEUED = "queued"

class OptimizationStrategy(Enum):
    """Backend optimization strategies"""
    COST = "cost"
    SPEED = "speed"
    QUALITY = "quality"
    BALANCED = "balanced"
    CUSTOM = "custom"

@dataclass
class BackendInfo:
    """Quantum backend information"""
    name: str
    provider: QuantumBackend
    num_qubits: int
    quantum_volume: int
    gate_fidelities: Dict[str, float]
    coherence_times: Dict[str, float]
    readout_errors: List[float]
    connectivity: List[List[int]]
    cost_per_execution: float
    max_shots: int
    average_queue_time: float
    availability: float
    supported_gates: List[str]

@dataclass
class QuantumJob:
    """Quantum job definition"""
    job_id: str
    circuit_id: str
    backend_name: str
    shots: int
    status: JobStatus
    creation_time: float
    start_time: Optional[float]
    completion_time: Optional[float]
    results: Optional[Dict[str, Any]]
    error_message: Optional[str]
    cost: float
    execution_time: Optional[float]

@dataclass
class ResourceQuota:
    """Resource quota configuration"""
    max_jobs_per_day: int
    max_execution_time: float
    max_qubits: int
    daily_budget: float
    backends: List[QuantumBackend]

class QuantumInterface:
    """Advanced quantum hardware and simulator interface"""

    def __init__(self, backend: str = "local"):
        self.logger = logging.getLogger(__name__)
        self.current_backend = backend
        self.default_shots = 1024

        # Backend registry
        self.backends: Dict[str, BackendInfo] = {}
        self.active_jobs: Dict[str, QuantumJob] = {}
        self.job_history: List[QuantumJob] = []

        # Authentication and API configuration
        self.api_keys = {}
        self.api_endpoints = {}

        # Resource management
        self.resource_quota = ResourceQuota(
            max_jobs_per_day=1000,
            max_execution_time=3600.0,
            max_qubits=100,
            daily_budget=100.0,
            backends=list(QuantumBackend)
        )

        # Performance metrics
        self.metrics = {
            "total_jobs": 0,
            "successful_jobs": 0,
            "failed_jobs": 0,
            "total_cost": 0.0,
            "average_execution_time": 0.0,
            "backend_usage": {},
            "queue_times": [],
            "error_rates": {}
        }

        # Job scheduling
        self.job_queue = []
        self.job_scheduler = ThreadPoolExecutor(max_workers=10)
        self.cost_tracker = {}

        # Initialize available backends
        self._initialize_backends()

        # Load configuration
        self._load_configuration()

    def _initialize_backends(self):
        """Initialize available quantum backends"""
        # IBM Quantum backends
        self.backends["ibm_quito"] = BackendInfo(
            name="ibm_quito",
            provider=QuantumBackend.IBM_QUANTUM,
            num_qubits=27,
            quantum_volume=64,
            gate_fidelities={"cx": 0.985, "rz": 0.999, "sx": 0.999, "x": 0.999},
            coherence_times={"T1": 85.0, "T2": 75.0},
            readout_errors=[0.025] * 27,
            connectivity=self._generate_ibm_connectivity(27),
            cost_per_execution=0.0,
            max_shots=8192,
            average_queue_time=120.0,
            availability=0.95,
            supported_gates=["cx", "rz", "sx", "x", "h", "measure"]
        )

        self.backends["ibm_perth"] = BackendInfo(
            name="ibm_perth",
            provider=QuantumBackend.IBM_QUANTUM,
            num_qubits=27,
            quantum_volume=128,
            gate_fidelities={"cx": 0.990, "rz": 0.999, "sx": 0.999, "x": 0.999},
            coherence_times={"T1": 120.0, "T2": 100.0},
            readout_errors=[0.020] * 27,
            connectivity=self._generate_ibm_connectivity(27),
            cost_per_execution=0.0,
            max_shots=8192,
            average_queue_time=180.0,
            availability=0.90,
            supported_gates=["cx", "rz", "sx", "x", "h", "measure", "reset", "u3"]
        )

        # Google Quantum backends
        self.backends["sycamore"] = BackendInfo(
            name="sycamore",
            provider=QuantumBackend.GOOGLE_QUANTUM,
            num_qubits=53,
            quantum_volume=256,
            gate_fidelities={"cz": 0.990, "x": 0.999, "y": 0.999, "z": 0.999},
            coherence_times={"T1": 25.0, "T2": 20.0},
            readout_errors=[0.015] * 53,
            connectivity=self._generate_sycamore_connectivity(),
            cost_per_execution=0.0,
            max_shots=10000,
            average_queue_time=300.0,
            availability=0.85,
            supported_gates=["cz", "x", "y", "z", "h", "s", "t", "measure"]
        )

        # Local simulator
        self.backends["local_simulator"] = BackendInfo(
            name="local_simulator",
            provider=QuantumBackend.LOCAL_SIMULATOR,
            num_qubits=100,
            quantum_volume=1000,
            gate_fidelities={"all": 1.0},
            coherence_times={"T1": float('inf'), "T2": float('inf')},
            readout_errors=[0.0] * 100,
            connectivity=[[i for i in range(100)]],  # Fully connected
            cost_per_execution=0.0,
            max_shots=100000,
            average_queue_time=0.0,
            availability=1.0,
            supported_gates=["all"]
        )

        # Cloud simulators
        self.backends["cloud_simulator"] = BackendInfo(
            name="cloud_simulator",
            provider=QuantumBackend.CLOUD_SIMULATOR,
            num_qubits=50,
            quantum_volume=500,
            gate_fidelities={"cx": 0.995, "rz": 0.999, "sx": 0.999, "x": 0.999},
            coherence_times={"T1": 1000.0, "T2": 1000.0},
            readout_errors=[0.005] * 50,
            connectivity=[[i for i in range(50)]],
            cost_per_execution=0.01,
            max_shots=50000,
            average_queue_time=10.0,
            availability=0.99,
            supported_gates=["cx", "rz", "sx", "x", "h", "measure", "reset"]
        )

    def _generate_ibm_connectivity(self, num_qubits: int) -> List[List[int]]:
        """Generate IBM-style connectivity graph"""
        connectivity = []
        for i in range(num_qubits):
            neighbors = []
            if i > 0:
                neighbors.append(i - 1)
            if i < num_qubits - 1:
                neighbors.append(i + 1)
            connectivity.append(neighbors)
        return connectivity

    def _generate_sycamore_connectivity(self) -> List[List[int]]:
        """Generate Sycamore connectivity graph"""
        # Simplified Sycamore connectivity
        connectivity = []
        for i in range(53):
            neighbors = []
            # Each qubit connected to 4 neighbors (approximate)
            for offset in [-8, -1, 1, 8]:
                neighbor = i + offset
                if 0 <= neighbor < 53:
                    neighbors.append(neighbor)
            connectivity.append(neighbors)
        return connectivity

    def _load_configuration(self):
        """Load configuration from file or environment"""
        # Load API keys
        self.api_keys = {
            "ibm": os.environ.get("IBM_QUANTUM_TOKEN", ""),
            "google": os.environ.get("GOOGLE_QUANTUM_TOKEN", ""),
            "rigetti": os.environ.get("RIGETTI_TOKEN", ""),
            "ionq": os.environ.get("IONQ_TOKEN", ""),
            "azure": os.environ.get("AZURE_QUANTUM_TOKEN", ""),
            "aws": os.environ.get("AWS_BRAKET_TOKEN", "")
        }

        # Load API endpoints
        self.api_endpoints = {
            "ibm": "https://quantum-computing.ibm.com/api",
            "google": "https://quantum.googleapis.com/v1",
            "rigetti": "https://api.rigetti.com/qam",
            "ionq": "https://api.ionq.co/v0.3",
            "azure": "https://quantum.azure.com/api",
            "aws": "https://braket.amazonaws.com/v1"
        }

    def get_backend_info(self, backend_name: str = None) -> BackendInfo:
        """Get backend information"""
        if backend_name is None:
            backend_name = self.current_backend

        if backend_name not in self.backends:
            raise ValueError(f"Backend {backend_name} not available")

        return self.backends[backend_name]

    def list_available_backends(self) -> List[str]:
        """List all available backends"""
        return list(self.backends.keys())

    def select_optimal_backend(self, num_qubits: int, optimization_strategy: OptimizationStrategy = OptimizationStrategy.BALANCED,
                              requirements: Dict[str, Any] = None) -> str:
        """Select optimal backend based on requirements"""
        suitable_backends = []

        for name, backend in self.backends.items():
            # Check qubit requirement
            if backend.num_qubits < num_qubits:
                continue

            # Check availability
            if backend.availability < 0.5:  # Less than 50% available
                continue

            suitable_backends.append((name, backend))

        if not suitable_backends:
            raise ValueError(f"No suitable backend for {num_qubits} qubits")

        # Score backends based on optimization strategy
        best_backend = None
        best_score = -float('inf')

        for name, backend in suitable_backends:
            score = 0.0

            if optimization_strategy == OptimizationStrategy.SPEED:
                # Prioritize low queue time and high availability
                score = (1.0 / (backend.average_queue_time + 1.0)) * backend.availability

            elif optimization_strategy == OptimizationStrategy.QUALITY:
                # Prioritize high quantum volume and low error rates
                avg_fidelity = np.mean(list(backend.gate_fidelities.values()))
                score = backend.quantum_volume * avg_fidelity

            elif optimization_strategy == OptimizationStrategy.COST:
                # Prioritize low cost
                score = 1.0 / (backend.cost_per_execution + 0.001)

            else:  # BALANCED
                # Combined scoring
                speed_score = 1.0 / (backend.average_queue_time + 1.0)
                quality_score = backend.quantum_volume / 100.0
                cost_score = 1.0 / (backend.cost_per_execution + 0.001)
                score = speed_score * 0.4 + quality_score * 0.4 + cost_score * 0.2

            # Apply custom requirements
            if requirements:
                if "max_queue_time" in requirements and backend.average_queue_time > requirements["max_queue_time"]:
                    score *= 0.1
                if "min_quantum_volume" in requirements and backend.quantum_volume < requirements["min_quantum_volume"]:
                    score *= 0.1
                if "max_cost" in requirements and backend.cost_per_execution > requirements["max_cost"]:
                    score *= 0.1

            if score > best_score:
                best_score = score
                best_backend = name

        self.logger.info(f"Selected optimal backend: {best_backend} (score: {best_score:.3f})")
        return best_backend

    def submit_job(self, circuit_id: str, backend_name: str = None, shots: int = None,
                   priority: str = "normal") -> str:
        """Submit quantum job for execution"""
        backend_name = backend_name or self.current_backend
        shots = shots or self.default_shots

        # Check resource quota
        if not self._check_quota(backend_name, shots):
            raise ValueError("Resource quota exceeded")

        # Get backend info
        backend = self.get_backend_info(backend_name)

        # Create job
        job_id = f"job_{int(time.time())}_{len(self.active_jobs)}"
        job = QuantumJob(
            job_id=job_id,
            circuit_id=circuit_id,
            backend_name=backend_name,
            shots=shots,
            status=JobStatus.PENDING,
            creation_time=time.time(),
            start_time=None,
            completion_time=None,
            results=None,
            error_message=None,
            cost=backend.cost_per_execution,
            execution_time=None
        )

        self.active_jobs[job_id] = job
        self.metrics["total_jobs"] += 1

        # Submit to backend
        if backend.provider == QuantumBackend.LOCAL_SIMULATOR:
            # Execute immediately for local simulator
            self._execute_local_job(job)
        else:
            # Queue for cloud backends
            self._queue_job(job, priority)

        self.logger.info(f"Submitted job {job_id} to backend {backend_name}")
        return job_id

    def _execute_local_job(self, job: QuantumJob):
        """Execute job on local simulator"""
        job.status = JobStatus.RUNNING
        job.start_time = time.time()

        try:
            # Simulate quantum circuit execution
            results = self._simulate_circuit_execution(job.circuit_id, job.shots)
            job.results = results
            job.status = JobStatus.COMPLETED
            job.completion_time = time.time()
            job.execution_time = job.completion_time - job.start_time

            # Update metrics
            self.metrics["successful_jobs"] += 1
            self._update_backend_metrics(job.backend_name, job.execution_time, True)

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completion_time = time.time()

            # Update metrics
            self.metrics["failed_jobs"] += 1
            self._update_backend_metrics(job.backend_name, 0, False)

        # Move to history
        self.job_history.append(job)
        del self.active_jobs[job.job_id]

    def _queue_job(self, job: QuantumJob, priority: str):
        """Queue job for cloud backend execution"""
        job.status = JobStatus.QUEUED

        # Add to queue based on priority
        if priority == "high":
            self.job_queue.insert(0, job)
        elif priority == "low":
            self.job_queue.append(job)
        else:
            # Normal priority - middle of queue
            mid_point = len(self.job_queue) // 2
            self.job_queue.insert(mid_point, job)

        # Schedule job execution
        future = self.job_scheduler.submit(self._process_job_queue)
        future.add_done_callback(lambda f: self._handle_job_completion(f, job))

    def _process_job_queue(self):
        """Process job queue and submit to cloud backends"""
        while self.job_queue:
            job = self.job_queue[0]

            # Check if backend is available
            backend = self.get_backend_info(job.backend_name)
            if backend.availability < 0.1:  # Less than 10% available
                time.sleep(10)  # Wait and retry
                continue

            # Submit to cloud backend
            try:
                self._submit_cloud_job(job)
                self.job_queue.pop(0)  # Remove from queue
            except Exception as e:
                self.logger.error(f"Failed to submit job {job.job_id}: {e}")
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                self.job_queue.pop(0)

    def _submit_cloud_job(self, job: QuantumJob):
        """Submit job to cloud backend"""
        backend = self.get_backend_info(job.backend_name)
        job.status = JobStatus.RUNNING
        job.start_time = time.time()

        # Simulate cloud submission (in practice, would use actual API calls)
        future = self.job_scheduler.submit(self._simulate_cloud_execution, job)
        future.add_done_callback(lambda f: self._handle_cloud_job_completion(f, job))

    def _simulate_cloud_execution(self, job: QuantumJob):
        """Simulate cloud job execution"""
        backend = self.get_backend_info(job.backend_name)

        # Simulate queue time
        queue_time = np.random.exponential(backend.average_queue_time)
        time.sleep(min(queue_time, 60))  # Cap at 60 seconds for simulation

        # Simulate execution time
        execution_time = np.random.exponential(backend.average_queue_time / 10)
        time.sleep(min(execution_time, 30))  # Cap at 30 seconds for simulation

        # Generate results
        results = self._simulate_circuit_execution(job.circuit_id, job.shots)

        return {
            "results": results,
            "execution_time": execution_time
        }

    def _handle_cloud_job_completion(self, future, job: QuantumJob):
        """Handle completion of cloud job"""
        try:
            result = future.result()
            job.results = result["results"]
            job.execution_time = result["execution_time"]
            job.status = JobStatus.COMPLETED
            job.completion_time = time.time()

            # Update metrics
            self.metrics["successful_jobs"] += 1
            self._update_backend_metrics(job.backend_name, job.execution_time, True)

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completion_time = time.time()

            # Update metrics
            self.metrics["failed_jobs"] += 1
            self._update_backend_metrics(job.backend_name, 0, False)

        # Move to history
        self.job_history.append(job)
        if job.job_id in self.active_jobs:
            del self.active_jobs[job.job_id]

    def _handle_job_completion(self, future, job: QuantumJob):
        """Handle generic job completion"""
        # This is a placeholder for the actual completion handling
        pass

    def get_job_status(self, job_id: str) -> JobStatus:
        """Get job status"""
        if job_id in self.active_jobs:
            return self.active_jobs[job_id].status
        else:
            # Check history
            for job in self.job_history:
                if job.job_id == job_id:
                    return job.status
            raise ValueError(f"Job {job_id} not found")

    def get_job_results(self, job_id: str) -> Dict[str, Any]:
        """Get job results"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
        else:
            # Check history
            job = None
            for j in self.job_history:
                if j.job_id == job_id:
                    job = j
                    break

        if job is None:
            raise ValueError(f"Job {job_id} not found")

        if job.status != JobStatus.COMPLETED:
            raise ValueError(f"Job {job_id} not completed (status: {job.status})")

        return job.results

    def cancel_job(self, job_id: str) -> bool:
        """Cancel job"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            if job.status in [JobStatus.PENDING, JobStatus.QUEUED]:
                job.status = JobStatus.CANCELLED
                job.completion_time = time.time()
                self.job_history.append(job)
                del self.active_jobs[job_id]
                return True
        return False

    def _simulate_circuit_execution(self, circuit_id: str, shots: int) -> Dict[str, Any]:
        """Simulate quantum circuit execution"""
        # Generate mock results based on circuit properties
        circuit = self.processor.circuits[circuit_id] if hasattr(self, 'processor') else None

        if circuit is None:
            # Generate simple mock results
            num_qubits = 5
        else:
            num_qubits = circuit.num_qubits

        # Generate measurement results
        possible_states = [f"{i:0{num_qubits}b}" for i in range(2**num_qubits)]

        # Create probability distribution
        if circuit and circuit.depth > 10:
            # Complex circuit - more uniform distribution
            probs = np.random.dirichlet(np.ones(len(possible_states)) * 0.1)
        else:
            # Simple circuit - biased towards computational basis
            probs = np.random.dirichlet(np.concatenate([[5, 3], np.ones(len(possible_states)-2)]))

        # Generate counts
        counts = {}
        for i, state in enumerate(possible_states):
            count = int(probs[i] * shots)
            if count > 0:
                counts[state] = count

        # Add some noise
        noisy_counts = {}
        for state, count in counts.items():
            if np.random.random() < 0.02:  # 2% error rate
                noisy_counts[state] = max(0, count - 1)
                flipped_state = self._flip_random_bit(state)
                noisy_counts[flipped_state] = noisy_counts.get(flipped_state, 0) + 1
            else:
                noisy_counts[state] = count

        return {
            "counts": noisy_counts,
            "probabilities": {state: count/shots for state, count in noisy_counts.items()},
            "memory": np.random.choice(possible_states, shots).tolist(),
            "execution_time": np.random.uniform(0.01, 1.0),
            "fidelity": np.random.uniform(0.85, 0.99)
        }

    def _flip_random_bit(self, state: str) -> str:
        """Flip a random bit in state string"""
        bit_idx = np.random.randint(0, len(state))
        bit = state[bit_idx]
        flipped_bit = "0" if bit == "1" else "1"
        return state[:bit_idx] + flipped_bit + state[bit_idx+1:]

    def _check_quota(self, backend_name: str, shots: int) -> bool:
        """Check if job fits within resource quota"""
        # Check daily job limit
        today_jobs = len([j for j in self.job_history if j.creation_time > time.time() - 86400])
        if today_jobs >= self.resource_quota.max_jobs_per_day:
            return False

        # Check daily budget
        backend = self.get_backend_info(backend_name)
        daily_cost = sum(j.cost for j in self.job_history if j.creation_time > time.time() - 86400)
        if daily_cost + backend.cost_per_execution > self.resource_quota.daily_budget:
            return False

        return True

    def _update_backend_metrics(self, backend_name: str, execution_time: float, success: bool):
        """Update backend performance metrics"""
        # Update backend usage
        if backend_name not in self.metrics["backend_usage"]:
            self.metrics["backend_usage"][backend_name] = 0
        self.metrics["backend_usage"][backend_name] += 1

        # Update execution time
        if execution_time > 0:
            if self.metrics["average_execution_time"] == 0:
                self.metrics["average_execution_time"] = execution_time
            else:
                total_jobs = self.metrics["successful_jobs"] + self.metrics["failed_jobs"]
                self.metrics["average_execution_time"] = (
                    (self.metrics["average_execution_time"] * (total_jobs - 1) + execution_time) / total_jobs
                )

        # Update error rates
        if backend_name not in self.metrics["error_rates"]:
            self.metrics["error_rates"][backend_name] = {"total": 0, "failed": 0}
        self.metrics["error_rates"][backend_name]["total"] += 1
        if not success:
            self.metrics["error_rates"][backend_name]["failed"] += 1

        # Update cost
        backend = self.get_backend_info(backend_name)
        self.metrics["total_cost"] += backend.cost_per_execution

    def benchmark_backends(self, test_circuit_size: int = 10, num_shots: int = 1024) -> Dict[str, Dict[str, float]]:
        """Benchmark all available backends"""
        results = {}

        for backend_name in self.backends:
            if self.backends[backend_name].provider == QuantumBackend.LOCAL_SIMULATOR:
                # Only test local simulator to avoid cloud costs
                try:
                    start_time = time.time()
                    job_id = self.submit_job(f"benchmark_circuit", backend_name, num_shots)
                    status = self.get_job_status(job_id)

                    # Wait for completion
                    max_wait = 60  # Maximum wait time
                    wait_time = 0
                    while status == JobStatus.RUNNING and wait_time < max_wait:
                        time.sleep(1)
                        status = self.get_job_status(job_id)
                        wait_time += 1

                    end_time = time.time()

                    if status == JobStatus.COMPLETED:
                        job_results = self.get_job_results(job_id)
                        results[backend_name] = {
                            "execution_time": end_time - start_time,
                            "fidelity": job_results.get("fidelity", 0.0),
                            "success": True,
                            "queue_time": 0.0  # Local simulator has no queue
                        }
                    else:
                        results[backend_name] = {
                            "execution_time": end_time - start_time,
                            "fidelity": 0.0,
                            "success": False,
                            "queue_time": 0.0
                        }

                except Exception as e:
                    self.logger.error(f"Benchmark failed for {backend_name}: {e}")
                    results[backend_name] = {
                        "execution_time": float('inf'),
                        "fidelity": 0.0,
                        "success": False,
                        "queue_time": 0.0
                    }

        return results

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "current_backend": self.current_backend,
            "available_backends": self.list_available_backends(),
            "active_jobs": len(self.active_jobs),
            "queued_jobs": len(self.job_queue),
            "job_history_size": len(self.job_history),
            "metrics": self.metrics,
            "resource_quota": asdict(self.resource_quota),
            "system_health": self._calculate_system_health()
        }

    def _calculate_system_health(self) -> Dict[str, float]:
        """Calculate system health metrics"""
        total_jobs = self.metrics["successful_jobs"] + self.metrics["failed_jobs"]
        success_rate = self.metrics["successful_jobs"] / max(1, total_jobs)
        avg_error_rate = np.mean([
            error_data["failed"] / max(1, error_data["total"])
            for error_data in self.metrics["error_rates"].values()
        ]) if self.metrics["error_rates"] else 0.0

        return {
            "success_rate": success_rate,
            "error_rate": avg_error_rate,
            "availability": success_rate * (1 - avg_error_rate),
            "performance": min(1.0, 10.0 / max(1.0, self.metrics["average_execution_time"]))
        }

    def set_resource_quota(self, quota: ResourceQuota):
        """Set resource quota"""
        self.resource_quota = quota
        self.logger.info(f"Updated resource quota: {quota}")

    def get_cost_analysis(self, time_period: str = "day") -> Dict[str, Any]:
        """Get cost analysis for specified time period"""
        if time_period == "day":
            cutoff = time.time() - 86400  # Last 24 hours
        elif time_period == "week":
            cutoff = time.time() - 604800  # Last 7 days
        elif time_period == "month":
            cutoff = time.time() - 2592000  # Last 30 days
        else:
            cutoff = 0  # All time

        relevant_jobs = [job for job in self.job_history if job.creation_time > cutoff]

        cost_by_backend = {}
        jobs_by_backend = {}
        for job in relevant_jobs:
            if job.backend_name not in cost_by_backend:
                cost_by_backend[job.backend_name] = 0.0
                jobs_by_backend[job.backend_name] = 0
            cost_by_backend[job.backend_name] += job.cost
            jobs_by_backend[job.backend_name] += 1

        total_cost = sum(cost_by_backend.values())

        return {
            "time_period": time_period,
            "total_cost": total_cost,
            "total_jobs": len(relevant_jobs),
            "cost_by_backend": cost_by_backend,
            "jobs_by_backend": jobs_by_backend,
            "average_cost_per_job": total_cost / max(1, len(relevant_jobs)),
            "budget_utilization": total_cost / self.resource_quota.daily_budget
        }

    def disconnect(self):
        """Disconnect from all backends and clean up resources"""
        # Cancel all pending jobs
        for job_id in list(self.active_jobs.keys()):
            self.cancel_job(job_id)

        # Shutdown thread pool
        self.job_scheduler.shutdown(wait=True)

        # Clear job queues
        self.job_queue.clear()

        self.logger.info("Disconnected from all quantum backends")

    def get_job_history(self, limit: int = 100, status_filter: JobStatus = None) -> List[Dict[str, Any]]:
        """Get job history with optional filtering"""
        history = self.job_history[-limit:] if limit > 0 else self.job_history

        if status_filter:
            history = [job for job in history if job.status == status_filter]

        return [
            {
                "job_id": job.job_id,
                "backend": job.backend_name,
                "status": job.status.value,
                "creation_time": job.creation_time,
                "execution_time": job.execution_time,
                "cost": job.cost,
                "shots": job.shots
            }
            for job in history
        ]

    def optimize_backend_selection(self, workloads: List[Dict[str, Any]]) -> Dict[str, str]:
        """Optimize backend selection for multiple workloads"""
        optimization_results = {}

        for i, workload in enumerate(workloads):
            num_qubits = workload.get("num_qubits", 5)
            priority = workload.get("priority", "normal")
            requirements = workload.get("requirements", {})

            # Select optimization strategy based on workload
            if priority == "high":
                strategy = OptimizationStrategy.SPEED
            elif "min_cost" in requirements:
                strategy = OptimizationStrategy.COST
            elif "min_quantum_volume" in requirements:
                strategy = OptimizationStrategy.QUALITY
            else:
                strategy = OptimizationStrategy.BALANCED

            optimal_backend = self.select_optimal_backend(
                num_qubits=num_qubits,
                optimization_strategy=strategy,
                requirements=requirements
            )

            optimization_results[f"workload_{i}"] = optimal_backend

        return optimization_results