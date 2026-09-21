#!/usr/bin/env python3
"""
Collaborative BCI System - Shared Consciousness Between Multiple Users
Advanced brain-computer interface for creating neural connections between multiple
users, enabling shared experiences, collective intelligence, and collaborative
problem-solving through direct brain-to-brain communication.

This module implements sophisticated algorithms for detecting and synchronizing
neural patterns across multiple users, creating a hive mind-like consciousness
network for enhanced collaborative experiences.
"""

import numpy as np
import pandas as pd
import asyncio
import json
import time
from typing import Dict, List, Optional, Tuple, Any, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from collections import deque
import threading
from concurrent.futures import ThreadPoolExecutor
import queue
import socket
import struct
import hashlib
from datetime import datetime
import uuid

# Machine Learning Libraries
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import networkx as nx

# Signal Processing
from scipy import signal
from scipy.fft import fft, fftfreq
from scipy.stats import entropy, pearsonr
from scipy.spatial.distance import cosine, euclidean
import cv2

# Local imports
from .neural_interface import ProcessedSignal, NeuralSignal
from .thought_detector import ThoughtPattern
from .emotional_bc import EmotionalPattern
from .memory_bc import MemoryEngram

class ConnectionType(Enum):
    """Types of neural connections between users"""
    DIRECT_SYNC = "direct_sync"  # Real-time neural synchronization
    EMOTIONAL_SHARED = "emotional_shared"  # Shared emotional states
    COGNITIVE_MERGE = "cognitive_merge"  # Merged cognitive processing
    SENSORY_EXCHANGE = "sensory_exchange"  # Shared sensory experiences
    MEMORY_SHARED = "memory_shared"  # Shared memory access
    INTENT_TRANSMISSION = "intent_transmission"  # Direct intent sharing
    COLLECTIVE_CONSCIOUSNESS = "collective_consciousness"  # Full consciousness merge

class SyncLevel(Enum):
    """Levels of neural synchronization"""
    MINIMAL = 0.1  # Basic awareness
    LOW = 0.3     # Shared emotions
    MEDIUM = 0.5  # Shared thoughts
    HIGH = 0.7    # Shared experiences
    DEEP = 0.9    # Merged consciousness
    COMPLETE = 1.0 # Complete neural fusion

class CollaborativeRole(Enum):
    """Roles users can play in collaborative sessions"""
    LEADER = "leader"  # Guides the collaboration
    PARTICIPANT = "participant"  # Contributes to collaboration
    OBSERVER = "observer"  # Monitors without active participation
    AMPLIFIER = "amplifier"  # Enhances signals from others
    MODERATOR = "moderator"  # Manages collaboration flow
    INTEGRATOR = "integrator"  # Synthesizes multiple inputs

@dataclass
class NeuralConnection:
    """Neural connection between two users"""
    connection_id: str
    user_id_1: str
    user_id_2: str
    connection_type: ConnectionType
    sync_level: float
    established_at: float
    last_activity: float
    connection_strength: float
    latency: float
    bandwidth: float
    encryption_key: Optional[str]
    metadata: Dict[str, Any]

@dataclass
class CollectiveState:
    """Collective neural state of connected users"""
    session_id: str
    participants: List[str]
    timestamp: float
    collective_emotion: Dict[str, float]
    collective_cognition: Dict[str, float]
    shared_focus: Optional[str]
    synchronization_index: float
    coherence_score: float
    emergent_patterns: List[str]
    collective_memory: List[str]
    network_topology: Dict[str, Any]

@dataclass
class CollaborativeOperation:
    """Operation within collaborative BCI system"""
    timestamp: float
    operation_type: str
    initiator_id: str
    target_ids: List[str]
    neural_data: Optional[Dict[str, Any]]
    success: bool
    response_data: Dict[str, Any]
    collaboration_metrics: Dict[str, float]
    metadata: Dict[str, Any]

class NeuralSynchronizer:
    """Advanced neural synchronization algorithms"""

    def __init__(self):
        self.frequency_bands = {
            'delta': (0.5, 4),
            'theta': (4, 8),
            'alpha': (8, 13),
            'beta': (13, 30),
            'gamma': (30, 100)
        }
        self.sync_history = deque(maxlen=1000)

    def calculate_synchronization(self, signals: Dict[str, np.ndarray]) -> Dict[str, float]:
        """Calculate synchronization metrics between multiple neural signals"""
        if len(signals) < 2:
            return {'synchronization': 0.0}

        sync_metrics = {}

        # Phase synchronization
        phase_sync = self._calculate_phase_synchronization(signals)
        sync_metrics['phase_synchronization'] = phase_sync

        # Coherence analysis
        coherence = self._calculate_coherence(signals)
        sync_metrics['coherence'] = coherence

        # Cross-frequency coupling
        cross_freq_coupling = self._calculate_cross_frequency_coupling(signals)
        sync_metrics['cross_frequency_coupling'] = cross_freq_coupling

        # Entropy synchronization
        entropy_sync = self._calculate_entropy_synchronization(signals)
        sync_metrics['entropy_synchronization'] = entropy_sync

        # Information sharing
        info_sharing = self._calculate_information_sharing(signals)
        sync_metrics['information_sharing'] = info_sharing

        # Overall synchronization score
        sync_metrics['synchronization'] = np.mean([
            phase_sync, coherence, cross_freq_coupling, entropy_sync, info_sharing
        ])

        return sync_metrics

    def _calculate_phase_synchronization(self, signals: Dict[str, np.ndarray]) -> float:
        """Calculate phase synchronization between signals"""
        phase_lock_values = []
        user_ids = list(signals.keys())

        for i in range(len(user_ids)):
            for j in range(i + 1, len(user_ids)):
                signal1 = signals[user_ids[i]]
                signal2 = signals[user_ids[j]]

                # Extract phase from dominant frequency band
                phase1 = self._extract_dominant_phase(signal1)
                phase2 = self._extract_dominant_phase(signal2)

                if phase1 is not None and phase2 is not None:
                    # Calculate phase locking value
                    phase_diff = phase1 - phase2
                    plv = np.abs(np.mean(np.exp(1j * phase_diff)))
                    phase_lock_values.append(plv)

        return np.mean(phase_lock_values) if phase_lock_values else 0.0

    def _calculate_coherence(self, signals: Dict[str, np.ndarray]) -> float:
        """Calculate coherence between signals"""
        coherence_values = []
        user_ids = list(signals.keys())

        for i in range(len(user_ids)):
            for j in range(i + 1, len(user_ids)):
                signal1 = signals[user_ids[i]]
                signal2 = signals[user_ids[j]]

                # Calculate coherence in multiple frequency bands
                band_coherences = []
                for band_name, (low, high) in self.frequency_bands.items():
                    coherence = self._band_coherence(signal1, signal2, low, high)
                    band_coherences.append(coherence)

                coherence_values.append(np.mean(band_coherences))

        return np.mean(coherence_values) if coherence_values else 0.0

    def _calculate_cross_frequency_coupling(self, signals: Dict[str, np.ndarray]) -> float:
        """Calculate cross-frequency coupling between signals"""
        coupling_values = []
        user_ids = list(signals.keys())

        for user_id in user_ids:
            signal = signals[user_id]

            # Theta-gamma coupling within each signal
            theta_phase = self._extract_phase(signal, 4, 8)
            gamma_amplitude = self._extract_amplitude(signal, 40, 100)

            if theta_phase is not None and gamma_amplitude is not None:
                coupling = self._calculate_modulation_index(theta_phase, gamma_amplitude)
                coupling_values.append(coupling)

        # Cross-user coupling
        if len(user_ids) >= 2:
            cross_user_coupling = self._calculate_cross_user_coupling(signals)
            coupling_values.append(cross_user_coupling)

        return np.mean(coupling_values) if coupling_values else 0.0

    def _calculate_entropy_synchronization(self, signals: Dict[str, np.ndarray]) -> float:
        """Calculate entropy synchronization between signals"""
        entropy_values = []

        for signal in signals.values():
            # Calculate sample entropy
            entropy_val = self._sample_entropy(signal)
            entropy_values.append(entropy_val)

        if len(entropy_values) < 2:
            return 0.0

        # Synchronization indicated by similar entropy values
        entropy_std = np.std(entropy_values)
        entropy_mean = np.mean(entropy_values)

        # Normalize (lower std = higher synchronization)
        sync_score = 1.0 / (1.0 + entropy_std / (entropy_mean + 1e-10))
        return sync_score

    def _calculate_information_sharing(self, signals: Dict[str, np.ndarray]) -> float:
        """Calculate information sharing between signals"""
        if len(signals) < 2:
            return 0.0

        # Calculate mutual information between signal pairs
        mi_values = []
        user_ids = list(signals.keys())

        for i in range(len(user_ids)):
            for j in range(i + 1, len(user_ids)):
                signal1 = signals[user_ids[i]]
                signal2 = signals[user_ids[j]]

                mi = self._calculate_mutual_information(signal1, signal2)
                mi_values.append(mi)

        return np.mean(mi_values) if mi_values else 0.0

    def _extract_dominant_phase(self, signal: np.ndarray) -> Optional[np.ndarray]:
        """Extract phase from dominant frequency band"""
        # Find frequency with maximum power
        fft_vals = fft(signal, axis=0)
        freqs = fftfreq(signal.shape[0], 1/250)
        power_spectrum = np.abs(fft_vals) ** 2

        # Find dominant frequency (excluding DC)
        positive_freqs = freqs[1:len(freqs)//2]
        positive_power = power_spectrum[1:len(power_spectrum)//2]

        if len(positive_freqs) > 0:
            dominant_freq_idx = np.argmax(positive_power)
            dominant_freq = positive_freqs[dominant_freq_idx]

            # Extract phase at dominant frequency
            phase = np.angle(fft_vals[dominant_freq_idx + 1])
            return np.full(signal.shape[0], phase)

        return None

    def _band_coherence(self, signal1: np.ndarray, signal2: np.ndarray,
                       low_freq: float, high_freq: float) -> float:
        """Calculate coherence in specific frequency band"""
        try:
            f, Cxy = signal.coherence(signal1, signal2, fs=250, nperseg=128)

            # Find frequency indices for band
            band_indices = np.where((f >= low_freq) & (f <= high_freq))[0]
            if len(band_indices) > 0:
                return np.mean(Cxy[band_indices])
        except Exception:
            pass

        return 0.0

    def _extract_phase(self, signal: np.ndarray, low_freq: float, high_freq: float) -> Optional[np.ndarray]:
        """Extract instantaneous phase from frequency band"""
        try:
            nyquist = 250 / 2
            if high_freq < nyquist:
                b, a = signal.butter(4, [low_freq/nyquist, high_freq/nyquist], btype='band')
                filtered = signal.filtfilt(b, a, signal)

                analytic_signal = signal.hilbert(filtered)
                instantaneous_phase = np.unwrap(np.angle(analytic_signal))
                return instantaneous_phase
        except Exception:
            pass

        return None

    def _extract_amplitude(self, signal: np.ndarray, low_freq: float, high_freq: float) -> Optional[np.ndarray]:
        """Extract instantaneous amplitude from frequency band"""
        try:
            nyquist = 250 / 2
            if high_freq < nyquist:
                b, a = signal.butter(4, [low_freq/nyquist, high_freq/nyquist], btype='band')
                filtered = signal.filtfilt(b, a, signal)

                analytic_signal = signal.hilbert(filtered)
                instantaneous_amplitude = np.abs(analytic_signal)
                return instantaneous_amplitude
        except Exception:
            pass

        return None

    def _calculate_modulation_index(self, phase: np.ndarray, amplitude: np.ndarray) -> float:
        """Calculate phase-amplitude coupling modulation index"""
        try:
            # Bin phase and calculate mean amplitude per bin
            n_bins = 18
            phase_bins = np.linspace(-np.pi, np.pi, n_bins + 1)
            binned_amplitude = []

            for i in range(n_bins):
                mask = (phase >= phase_bins[i]) & (phase < phase_bins[i + 1])
                if np.any(mask):
                    binned_amplitude.append(np.mean(amplitude[mask]))
                else:
                    binned_amplitude.append(0)

            binned_amplitude = np.array(binned_amplitude)

            # Calculate modulation index
            p = binned_amplitude / (np.sum(binned_amplitude) + 1e-10)
            q = np.ones(len(p)) / len(p)

            mi = np.sum(p * np.log((p + 1e-10) / (q + 1e-10)))
            mi_normalized = mi / np.log(len(p))

            return mi_normalized
        except Exception:
            return 0.0

    def _calculate_cross_user_coupling(self, signals: Dict[str, np.ndarray]) -> float:
        """Calculate coupling across different users"""
        user_ids = list(signals.keys())
        coupling_scores = []

        for i in range(len(user_ids)):
            for j in range(i + 1, len(user_ids)):
                signal1 = signals[user_ids[i]]
                signal2 = signals[user_ids[j]]

                # Cross-correlation
                correlation = np.corrcoef(signal1.flatten(), signal2.flatten())[0, 1]
                if not np.isnan(correlation):
                    coupling_scores.append(abs(correlation))

        return np.mean(coupling_scores) if coupling_scores else 0.0

    def _sample_entropy(self, signal: np.ndarray, m: int = 2, r: float = None) -> float:
        """Calculate sample entropy"""
        if r is None:
            r = 0.2 * np.std(signal)

        N = len(signal)
        if N < m + 1:
            return 0

        def _count_matches(data, m):
            patterns = [data[i:i+m] for i in range(N-m+1)]
            matches = 0
            for i in range(len(patterns)):
                for j in range(i+1, len(patterns)):
                    if np.max(np.abs(patterns[i] - patterns[j])) <= r:
                        matches += 1
            return matches

        B = _count_matches(signal, m)
        A = _count_matches(signal, m+1)

        if B == 0 or A == 0:
            return 0

        return -np.log(A / B)

    def _calculate_mutual_information(self, signal1: np.ndarray, signal2: np.ndarray) -> float:
        """Calculate mutual information between two signals"""
        try:
            # Discretize signals
            bins = 16
            hist_2d, x_edges, y_edges = np.histogram2d(
                signal1.flatten(), signal2.flatten(), bins=bins
            )

            # Calculate joint and marginal probabilities
            p_xy = hist_2d / np.sum(hist_2d)
            p_x = np.sum(p_xy, axis=1)
            p_y = np.sum(p_xy, axis=0)

            # Calculate mutual information
            mi = 0.0
            for i in range(bins):
                for j in range(bins):
                    if p_xy[i, j] > 0 and p_x[i] > 0 and p_y[j] > 0:
                        mi += p_xy[i, j] * np.log(p_xy[i, j] / (p_x[i] * p_y[j]))

            return mi
        except Exception:
            return 0.0

class ConsciousnessNetwork:
    """Network for managing shared consciousness between multiple users"""

    def __init__(self):
        self.participants = {}
        self.connections = {}
        self.session_data = {}
        self.network_graph = nx.Graph()
        self.synchronizer = NeuralSynchronizer()
        self.current_session = None

    def create_session(self, session_id: str, participants: List[str],
                      connection_types: List[ConnectionType]) -> bool:
        """Create a new collaborative consciousness session"""
        try:
            # Initialize session
            self.session_data[session_id] = {
                'participants': participants.copy(),
                'connection_types': connection_types.copy(),
                'created_at': time.time(),
                'last_activity': time.time(),
                'collective_states': deque(maxlen=1000),
                'synchronization_history': deque(maxlen=1000),
                'emergent_patterns': []
            }

            # Initialize participant data
            for participant_id in participants:
                if participant_id not in self.participants:
                    self.participants[participant_id] = {
                        'current_session': session_id,
                        'neural_buffer': deque(maxlen=10),
                        'sync_level': 0.5,
                        'role': CollaborativeRole.PARTICIPANT,
                        'last_update': time.time()
                    }

            # Create network graph
            self.network_graph.add_nodes_from(participants)

            # Create connections between participants
            self._create_participant_connections(session_id, participants, connection_types)

            self.current_session = session_id
            self.logger.info(f"Created consciousness session: {session_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            return False

    def _create_participant_connections(self, session_id: str, participants: List[str],
                                     connection_types: List[ConnectionType]):
        """Create neural connections between participants"""
        for i, user1 in enumerate(participants):
            for j, user2 in enumerate(participants):
                if i < j:  # Avoid duplicate connections
                    for connection_type in connection_types:
                        connection_id = f"{session_id}_{user1}_{user2}_{connection_type.value}"

                        connection = NeuralConnection(
                            connection_id=connection_id,
                            user_id_1=user1,
                            user_id_2=user2,
                            connection_type=connection_type,
                            sync_level=0.1,
                            established_at=time.time(),
                            last_activity=time.time(),
                            connection_strength=0.5,
                            latency=0.001,  # 1ms
                            bandwidth=1000,  # 1000 units/s
                            encryption_key=self._generate_encryption_key(),
                            metadata={'session_id': session_id}
                        )

                        self.connections[connection_id] = connection
                        self.network_graph.add_edge(user1, user2, connection_type=connection_type.value)

    def _generate_encryption_key(self) -> str:
        """Generate encryption key for neural data"""
        return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()

    def add_neural_data(self, user_id: str, processed_signal: ProcessedSignal):
        """Add neural data from a participant"""
        if user_id not in self.participants:
            return

        # Store in user buffer
        self.participants[user_id]['neural_buffer'].append(processed_signal)
        self.participants[user_id]['last_update'] = time.time()

        # Update session activity
        if self.current_session:
            self.session_data[self.current_session]['last_activity'] = time.time()

        # Trigger collective processing if enough data
        self._process_collective_state()

    def _process_collective_state(self):
        """Process collective neural state of all participants"""
        if not self.current_session:
            return

        session_data = self.session_data[self.current_session]
        participants = session_data['participants']

        # Collect recent neural data from all participants
        neural_data = {}
        for participant_id in participants:
            if (participant_id in self.participants and
                self.participants[participant_id]['neural_buffer']):

                latest_signal = self.participants[participant_id]['neural_buffer'][-1]
                neural_data[participant_id] = latest_signal.filtered_signal

        # Process if we have data from multiple participants
        if len(neural_data) >= 2:
            collective_state = self._calculate_collective_state(neural_data)
            session_data['collective_states'].append(collective_state)

            # Update synchronization metrics
            sync_metrics = self.synchronizer.calculate_synchronization(neural_data)
            session_data['synchronization_history'].append(sync_metrics)

            # Detect emergent patterns
            emergent_patterns = self._detect_emergent_patterns(neural_data, sync_metrics)
            session_data['emergent_patterns'].extend(emergent_patterns)

            # Update participant sync levels
            self._update_participant_sync_levels(sync_metrics)

    def _calculate_collective_state(self, neural_data: Dict[str, np.ndarray]) -> CollectiveState:
        """Calculate collective neural state"""
        # Aggregate neural signals
        all_signals = np.array(list(neural_data.values()))
        collective_signal = np.mean(all_signals, axis=0)

        # Calculate collective emotion (simplified)
        collective_emotion = {
            'valence': np.random.uniform(-0.5, 0.5),  # Placeholder
            'arousal': np.random.uniform(0.3, 0.8),   # Placeholder
            'coherence': np.random.uniform(0.4, 0.9)   # Placeholder
        }

        # Calculate collective cognition
        collective_cognition = {
            'focus_level': np.random.uniform(0.5, 0.9),      # Placeholder
            'cognitive_load': np.random.uniform(0.2, 0.7),    # Placeholder
            'creativity_index': np.random.uniform(0.3, 0.8),  # Placeholder
            'problem_solving': np.random.uniform(0.4, 0.9)    # Placeholder
        }

        # Calculate synchronization
        sync_metrics = self.synchronizer.calculate_synchronization(neural_data)

        # Create collective state
        collective_state = CollectiveState(
            session_id=self.current_session,
            participants=list(neural_data.keys()),
            timestamp=time.time(),
            collective_emotion=collective_emotion,
            collective_cognition=collective_cognition,
            shared_focus=None,  # Would be determined from content analysis
            synchronization_index=sync_metrics['synchronization'],
            coherence_score=sync_metrics['coherence'],
            emergent_patterns=[],  # Would be detected separately
            collective_memory=[],  # Would be built from shared experiences
            network_topology=self._get_network_topology()
        )

        return collective_state

    def _detect_emergent_patterns(self, neural_data: Dict[str, np.ndarray],
                                 sync_metrics: Dict[str, float]) -> List[str]:
        """Detect emergent patterns in collective neural activity"""
        patterns = []

        # High synchronization indicates emergent collective behavior
        if sync_metrics['synchronization'] > 0.8:
            patterns.append('high_collective_coherence')

        # Phase synchronization indicates shared attention
        if sync_metrics['phase_synchronization'] > 0.7:
            patterns.append('shared_attention')

        # Cross-frequency coupling indicates complex information processing
        if sync_metrics['cross_frequency_coupling'] > 0.6:
            patterns.append('collective_information_processing')

        # High coherence indicates shared mental state
        if sync_metrics['coherence'] > 0.7:
            patterns.append('shared_mental_state')

        # Entropy synchronization indicates aligned thinking
        if sync_metrics['entropy_synchronization'] > 0.6:
            patterns.append('aligned_cognition')

        return patterns

    def _update_participant_sync_levels(self, sync_metrics: Dict[str, float]):
        """Update synchronization levels for all participants"""
        sync_level = sync_metrics['synchronization']

        for participant_id in self.participants:
            if self.participants[participant_id]['current_session'] == self.current_session:
                # Smooth update to sync level
                current_level = self.participants[participant_id]['sync_level']
                new_level = 0.8 * current_level + 0.2 * sync_level
                self.participants[participant_id]['sync_level'] = new_level

    def _get_network_topology(self) -> Dict[str, Any]:
        """Get current network topology information"""
        return {
            'num_nodes': self.network_graph.number_of_nodes(),
            'num_edges': self.network_graph.number_of_edges(),
            'density': nx.density(self.network_graph),
            'clustering_coefficient': nx.average_clustering(self.network_graph),
            'is_connected': nx.is_connected(self.network_graph)
        }

    def strengthen_connections(self, user_id: str, target_id: str, strength_increase: float):
        """Strengthen neural connection between users"""
        for connection_id, connection in self.connections.items():
            if ((connection.user_id_1 == user_id and connection.user_id_2 == target_id) or
                (connection.user_id_1 == target_id and connection.user_id_2 == user_id)):

                connection.connection_strength = min(1.0, connection.connection_strength + strength_increase)
                connection.sync_level = min(1.0, connection.sync_level + strength_increase * 0.5)
                connection.last_activity = time.time()

                # Update network graph weight
                if self.network_graph.has_edge(user_id, target_id):
                    current_weight = self.network_graph[user_id][target_id].get('weight', 1.0)
                    new_weight = min(10.0, current_weight + strength_increase * 5)
                    self.network_graph[user_id][target_id]['weight'] = new_weight

                break

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of collaborative session"""
        if session_id not in self.session_data:
            return {}

        session_data = self.session_data[session_id]

        # Calculate session statistics
        duration = time.time() - session_data['created_at']

        collective_states = list(session_data['collective_states'])
        sync_history = list(session_data['synchronization_history'])

        # Calculate average metrics
        avg_sync = np.mean([s['synchronization'] for s in sync_history]) if sync_history else 0
        avg_coherence = np.mean([s['coherence'] for s in sync_history]) if sync_history else 0

        # Find peak synchronization moments
        peak_moments = []
        if sync_history:
            sync_values = [s['synchronization'] for s in sync_history]
            threshold = np.mean(sync_values) + np.std(sync_values)
            for i, s in enumerate(sync_history):
                if s['synchronization'] > threshold:
                    peak_moments.append({
                        'timestamp': i,
                        'sync_level': s['synchronization'],
                        'patterns': session_data['emergent_patterns'][i:i+5]  # Patterns around this time
                    })

        return {
            'session_id': session_id,
            'duration': duration,
            'participants': session_data['participants'],
            'connection_types': [ct.value for ct in session_data['connection_types']],
            'average_synchronization': avg_sync,
            'average_coherence': avg_coherence,
            'peak_synchronization_moments': peak_moments[:10],  # Top 10 moments
            'total_emergent_patterns': len(session_data['emergent_patterns']),
            'network_topology': self._get_network_topology(),
            'participant_count': len(session_data['participants'])
        }

class CollaborativeBCI:
    """Main collaborative BCI system for shared consciousness"""

    def __init__(self):
        self.consciousness_network = ConsciousnessNetwork()
        self.active_sessions = {}
        self.session_handlers = {}
        self.connection_handlers = {}

        # Real-time processing
        self.neural_queue = asyncio.Queue()
        self.operation_queue = asyncio.Queue()
        self.is_running = False

        # Network communication
        self.server_socket = None
        self.client_connections = {}
        self.network_port = 8765  # Default port for BCI communication

        # Callbacks
        self.session_callbacks = []
        self.operation_callbacks = []
        self.emergence_callbacks = []

        # Metrics
        self.metrics = {
            'sessions_created': 0,
            'active_participants': 0,
            'total_connections': 0,
            'average_sync_level': deque(maxlen=100),
            'emergent_events': 0,
            'data_transferred': 0
        }

        self.logger = logging.getLogger(__name__)

    async def initialize(self, enable_networking: bool = True) -> bool:
        """Initialize the collaborative BCI system"""
        try:
            # Initialize network server if enabled
            if enable_networking:
                await self._start_network_server()

            self.is_running = True
            self.logger.info("Collaborative BCI system initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize collaborative BCI: {e}")
            return False

    async def _start_network_server(self):
        """Start network server for multi-user communication"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('localhost', self.network_port))
            self.server_socket.listen(5)

            self.logger.info(f"Network server started on port {self.network_port}")

            # Start accepting connections
            asyncio.create_task(self._accept_connections())

        except Exception as e:
            self.logger.error(f"Failed to start network server: {e}")

    async def _accept_connections(self):
        """Accept incoming network connections"""
        while self.is_running:
            try:
                client_socket, address = await asyncio.get_event_loop().sock_accept(self.server_socket)
                user_id = f"user_{int(time.time())}_{len(self.client_connections)}"

                self.client_connections[user_id] = {
                    'socket': client_socket,
                    'address': address,
                    'user_id': user_id,
                    'connected_at': time.time()
                }

                self.logger.info(f"User connected: {user_id} from {address}")

                # Start handling this client
                asyncio.create_task(self._handle_client(user_id))

            except Exception as e:
                if self.is_running:
                    self.logger.error(f"Connection acceptance error: {e}")
                await asyncio.sleep(0.1)

    async def _handle_client(self, user_id: str):
        """Handle communication with a connected client"""
        if user_id not in self.client_connections:
            return

        client_data = self.client_connections[user_id]
        client_socket = client_data['socket']

        try:
            while self.is_running:
                # Receive data length first
                length_data = await asyncio.get_event_loop().sock_recv(client_socket, 4)
                if not length_data:
                    break

                message_length = struct.unpack('!I', length_data)[0]

                # Receive actual data
                data = b''
                while len(data) < message_length:
                    chunk = await asyncio.get_event_loop().sock_recv(
                        client_socket, message_length - len(data)
                    )
                    if not chunk:
                        break
                    data += chunk

                if len(data) == message_length:
                    await self._process_network_message(user_id, data)

        except Exception as e:
            self.logger.error(f"Client handling error for {user_id}: {e}")
        finally:
            # Clean up connection
            await self._disconnect_user(user_id)

    async def _process_network_message(self, user_id: str, data: bytes):
        """Process message from network client"""
        try:
            # Deserialize message
            message = json.loads(data.decode('utf-8'))
            message_type = message.get('type')
            message_data = message.get('data', {})

            if message_type == 'neural_data':
                # Process neural data
                await self._handle_neural_data(user_id, message_data)
            elif message_type == 'session_request':
                # Handle session requests
                await self._handle_session_request(user_id, message_data)
            elif message_type == 'sync_request':
                # Handle synchronization requests
                await self._handle_sync_request(user_id, message_data)

        except Exception as e:
            self.logger.error(f"Message processing error: {e}")

    async def _handle_neural_data(self, user_id: str, data: Dict[str, Any]):
        """Handle neural data from user"""
        try:
            # Create processed signal object (simplified)
            processed_signal = self._create_processed_signal_from_data(data)

            # Add to consciousness network
            self.consciousness_network.add_neural_data(user_id, processed_signal)

            # Update metrics
            self.metrics['data_transferred'] += len(str(data))

        except Exception as e:
            self.logger.error(f"Neural data handling error: {e}")

    async def _handle_session_request(self, user_id: str, data: Dict[str, Any]):
        """Handle session creation/join requests"""
        try:
            action = data.get('action')

            if action == 'create':
                session_id = await self.create_collaborative_session(
                    creator_id=user_id,
                    session_config=data.get('config', {})
                )

                # Send response
                response = {
                    'type': 'session_response',
                    'data': {
                        'action': 'created',
                        'session_id': session_id,
                        'success': True
                    }
                }
                await self._send_to_user(user_id, response)

            elif action == 'join':
                session_id = data.get('session_id')
                success = await self.join_session(user_id, session_id)

                response = {
                    'type': 'session_response',
                    'data': {
                        'action': 'joined',
                        'session_id': session_id,
                        'success': success
                    }
                }
                await self._send_to_user(user_id, response)

        except Exception as e:
            self.logger.error(f"Session request handling error: {e}")

    async def _handle_sync_request(self, user_id: str, data: Dict[str, Any]):
        """Handle synchronization requests"""
        try:
            target_users = data.get('target_users', [])
            sync_type = data.get('sync_type', 'direct_sync')
            sync_level = data.get('sync_level', 0.5)

            # Create synchronization operation
            operation = CollaborativeOperation(
                timestamp=time.time(),
                operation_type='synchronize',
                initiator_id=user_id,
                target_ids=target_users,
                neural_data=None,
                success=True,
                response_data={'sync_level': sync_level, 'sync_type': sync_type},
                collaboration_metrics={'initiated_sync': True},
                metadata={}
            )

            await self.operation_queue.put(operation)

        except Exception as e:
            self.logger.error(f"Sync request handling error: {e}")

    def _create_processed_signal_from_data(self, data: Dict[str, Any]) -> 'ProcessedSignal':
        """Create processed signal object from network data"""
        from .neural_interface import BrainWave

        # Extract neural data
        signal_data = np.array(data.get('signal_data', []))
        brain_waves = data.get('brain_waves', {})

        return ProcessedSignal(
            timestamp=data.get('timestamp', time.time()),
            raw_signal=signal_data,
            filtered_signal=signal_data,
            features=data.get('features', {}),
            brain_waves=brain_waves,
            signal_quality=data.get('signal_quality', 0.8),
            noise_level=data.get('noise_level', 0.1)
        )

    async def _send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to specific user"""
        if user_id not in self.client_connections:
            return

        try:
            client_socket = self.client_connections[user_id]['socket']
            message_data = json.dumps(message).encode('utf-8')
            message_length = len(message_data)

            # Send length first
            length_bytes = struct.pack('!I', message_length)
            await asyncio.get_event_loop().sock_send(client_socket, length_bytes)

            # Send actual message
            await asyncio.get_event_loop().sock_send(client_socket, message_data)

        except Exception as e:
            self.logger.error(f"Failed to send message to {user_id}: {e}")

    async def _disconnect_user(self, user_id: str):
        """Disconnect a user from the system"""
        if user_id in self.client_connections:
            try:
                self.client_connections[user_id]['socket'].close()
            except:
                pass

            del self.client_connections[user_id]

            # Remove from active sessions
            if user_id in self.consciousness_network.participants:
                session_id = self.consciousness_network.participants[user_id]['current_session']
                if session_id in self.active_sessions:
                    self.active_sessions[session_id]['participants'].discard(user_id)

            self.logger.info(f"User disconnected: {user_id}")

    async def create_collaborative_session(self, creator_id: str,
                                         session_config: Dict[str, Any]) -> Optional[str]:
        """Create a new collaborative consciousness session"""
        try:
            # Generate session ID
            session_id = f"session_{int(time.time())}_{uuid.uuid4().hex[:8]}"

            # Get session parameters
            max_participants = session_config.get('max_participants', 8)
            connection_types = [
                ConnectionType(ct) for ct in session_config.get('connection_types', ['direct_sync'])
            ]
            sync_level = session_config.get('initial_sync_level', 0.3)

            # Create session in consciousness network
            initial_participants = [creator_id]
            success = self.consciousness_network.create_session(
                session_id, initial_participants, connection_types
            )

            if success:
                # Store session data
                self.active_sessions[session_id] = {
                    'creator_id': creator_id,
                    'participants': set(initial_participants),
                    'created_at': time.time(),
                    'config': session_config,
                    'current_sync_level': sync_level
                }

                # Update metrics
                self.metrics['sessions_created'] += 1

                # Trigger callbacks
                for callback in self.session_callbacks:
                    try:
                        await callback({
                            'type': 'session_created',
                            'session_id': session_id,
                            'creator_id': creator_id
                        })
                    except Exception as e:
                        self.logger.error(f"Session callback error: {e}")

                self.logger.info(f"Created collaborative session: {session_id}")
                return session_id

        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")

        return None

    async def join_session(self, user_id: str, session_id: str) -> bool:
        """Add user to existing collaborative session"""
        try:
            if session_id not in self.active_sessions:
                return False

            session_data = self.active_sessions[session_id]

            # Check participant limit
            if len(session_data['participants']) >= session_data['config'].get('max_participants', 8):
                return False

            # Add to session
            session_data['participants'].add(user_id)

            # Add to consciousness network
            self.consciousness_network.participants[user_id] = {
                'current_session': session_id,
                'neural_buffer': deque(maxlen=10),
                'sync_level': session_data['current_sync_level'],
                'role': CollaborativeRole.PARTICIPANT,
                'last_update': time.time()
            }

            # Create connections with existing participants
            existing_participants = list(session_data['participants'] - {user_id})
            for participant_id in existing_participants:
                self.consciousness_network._create_participant_connections(
                    session_id, [user_id, participant_id],
                    [ConnectionType(ct) for ct in session_data['config'].get('connection_types', ['direct_sync'])]
                )

            # Update metrics
            self.metrics['active_participants'] = len(session_data['participants'])

            self.logger.info(f"User {user_id} joined session {session_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to join session: {e}")
            return False

    async def strengthen_synchronization(self, session_id: str,
                                       target_sync_level: float) -> bool:
        """Gradually increase synchronization level in a session"""
        try:
            if session_id not in self.active_sessions:
                return False

            session_data = self.active_sessions[session_id]
            current_level = session_data['current_sync_level']

            if current_level >= target_sync_level:
                return True

            # Gradual increase
            increment = 0.1
            new_level = min(current_level + increment, target_sync_level)
            session_data['current_sync_level'] = new_level

            # Strengthen connections between participants
            participants = list(session_data['participants'])
            for i, user1 in enumerate(participants):
                for user2 in participants[i+1:]:
                    self.consciousness_network.strengthen_connections(user1, user2, increment)

            self.logger.info(f"Session {session_id} sync level: {current_level:.2f} -> {new_level:.2f}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to strengthen synchronization: {e}")
            return False

    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current status of a collaborative session"""
        try:
            if session_id not in self.active_sessions:
                return {'error': 'Session not found'}

            session_data = self.active_sessions[session_id]
            network_summary = self.consciousness_network.get_session_summary(session_id)

            return {
                'session_id': session_id,
                'creator_id': session_data['creator_id'],
                'participants': list(session_data['participants']),
                'current_sync_level': session_data['current_sync_level'],
                'duration': time.time() - session_data['created_at'],
                'network_summary': network_summary
            }

        except Exception as e:
            self.logger.error(f"Failed to get session status: {e}")
            return {'error': str(e)}

    def add_session_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add callback for session events"""
        self.session_callbacks.append(callback)

    def add_operation_callback(self, callback: Callable[[CollaborativeOperation], None]):
        """Add callback for collaborative operations"""
        self.operation_callbacks.append(callback)

    def add_emergence_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add callback for emergent pattern events"""
        self.emergence_callbacks.append(callback)

    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        total_connections = len(self.consciousness_network.connections)
        avg_sync = np.mean(list(self.metrics['average_sync_level'])) if self.metrics['average_sync_level'] else 0

        return {
            'sessions_created': self.metrics['sessions_created'],
            'active_participants': self.metrics['active_participants'],
            'total_connections': total_connections,
            'average_sync_level': avg_sync,
            'emergent_events': self.metrics['emergent_events'],
            'data_transferred_mb': self.metrics['data_transferred'] / (1024 * 1024),
            'is_running': self.is_running,
            'network_port': self.network_port,
            'connected_users': len(self.client_connections),
            'active_sessions': len(self.active_sessions)
        }

    async def shutdown(self):
        """Shutdown the collaborative BCI system"""
        self.is_running = False

        # Close network server
        if self.server_socket:
            self.server_socket.close()

        # Disconnect all clients
        for user_id in list(self.client_connections.keys()):
            await self._disconnect_user(user_id)

        self.logger.info("Collaborative BCI system shutdown complete")

# Main interface for external use
async def create_collaborative_bci(enable_networking: bool = True) -> CollaborativeBCI:
    """Create and initialize a collaborative BCI system"""
    collab_bci = CollaborativeBCI()
    success = await collab_bci.initialize(enable_networking)

    if not success:
        raise RuntimeError("Failed to initialize collaborative BCI system")

    return collab_bci

if __name__ == "__main__":
    # Example usage
    async def main():
        # Create collaborative BCI
        collab_bci = await create_collaborative_bci()

        # Add callbacks
        def on_session_event(event):
            print(f"Session event: {event['type']} - {event.get('session_id', 'unknown')}")

        def on_collaborative_operation(operation):
            print(f"Collaborative operation: {operation.operation_type} "
                  f"from {operation.initiator_id}")

        collab_bci.add_session_callback(on_session_event)
        collab_bci.add_operation_callback(on_collaborative_operation)

        # Create a collaborative session
        session_config = {
            'max_participants': 4,
            'connection_types': ['direct_sync', 'emotional_shared'],
            'initial_sync_level': 0.3
        }

        session_id = await collab_bci.create_collaborative_session(
            creator_id="user_1",
            session_config=session_config
        )

        if session_id:
            print(f"Created collaborative session: {session_id}")

            # Simulate other users joining
            await collab_bci.join_session("user_2", session_id)
            await collab_bci.join_session("user_3", session_id)

            # Strengthen synchronization
            await collab_bci.strengthen_synchronization(session_id, 0.7)

            # Get session status
            status = collab_bci.get_session_status(session_id)
            print(f"Session status: {status}")

            # Simulate some collaborative time
            await asyncio.sleep(2)

            # Get metrics
            metrics = collab_bci.get_metrics()
            print(f"System metrics: {metrics}")

        # Shutdown
        await collab_bci.shutdown()

    asyncio.run(main())