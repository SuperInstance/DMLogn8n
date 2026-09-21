#!/usr/bin/env python3
"""
Advanced Learning Engine for DMLogn8n AI Agents

This module implements a sophisticated machine learning engine that enables AI agents
to continuously improve their performance through various learning mechanisms including
reinforcement learning, supervised learning, unsupervised learning, and meta-learning.

Key Features:
- Multi-modal learning algorithms
- Reinforcement learning for behavior optimization
- Supervised learning from feedback
- Unsupervised pattern discovery
- Meta-learning for rapid adaptation
- Experience replay and curriculum learning
- Neural architecture optimization
- Transfer learning capabilities
"""

import asyncio
import json
import logging
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.distributions import Categorical, Normal
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading
import time
import pickle
import random
from collections import deque, defaultdict
import math
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import copy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LearningType(Enum):
    """Types of learning algorithms"""
    REINFORCEMENT = "reinforcement"
    SUPERVISED = "supervised"
    UNSUPERVISED = "unsupervised"
    META_LEARNING = "meta_learning"
    TRANSFER = "transfer"
    IMITATION = "imitation"

class ExplorationStrategy(Enum):
    """Exploration strategies for reinforcement learning"""
    EPSILON_GREEDY = "epsilon_greedy"
    BOLTZMANN = "boltzmann"
    UCB = "ucb"
    THOMPSON_SAMPLING = "thompson_sampling"
    NOISY_NETS = "noisy_nets"

@dataclass
class LearningExperience:
    """Represents a single learning experience"""
    state: Any
    action: Any
    reward: float
    next_state: Any
    done: bool
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    importance: float = 1.0
    episode_id: Optional[str] = None
    agent_id: str = ""

@dataclass
class SupervisedExample:
    """Represents a supervised learning example"""
    input_data: Any
    target_output: Any
    timestamp: datetime
    confidence: float = 1.0
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LearningGoal:
    """Represents a learning goal or objective"""
    name: str
    description: str
    target_performance: float
    current_performance: float
    priority: float
    learning_type: LearningType
    deadline: Optional[datetime] = None
    progress_history: List[float] = field(default_factory=list)

class PolicyNetwork(nn.Module):
    """Neural network for policy approximation in RL"""

    def __init__(self, state_dim: int, action_dim: int, hidden_dims: List[int] = [256, 128]):
        super().__init__()
        layers = []

        # Input layer
        layers.append(nn.Linear(state_dim, hidden_dims[0]))
        layers.append(nn.ReLU())
        layers.append(nn.Dropout(0.1))

        # Hidden layers
        for i in range(len(hidden_dims) - 1):
            layers.append(nn.Linear(hidden_dims[i], hidden_dims[i + 1]))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.1))

        # Output layer
        layers.append(nn.Linear(hidden_dims[-1], action_dim))

        self.network = nn.Sequential(*layers)

    def forward(self, state):
        return self.network(state)

class ValueNetwork(nn.Module):
    """Neural network for value function approximation"""

    def __init__(self, state_dim: int, hidden_dims: List[int] = [256, 128]):
        super().__init__()
        layers = []

        # Input layer
        layers.append(nn.Linear(state_dim, hidden_dims[0]))
        layers.append(nn.ReLU())
        layers.append(nn.Dropout(0.1))

        # Hidden layers
        for i in range(len(hidden_dims) - 1):
            layers.append(nn.Linear(hidden_dims[i], hidden_dims[i + 1]))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.1))

        # Output layer (single value)
        layers.append(nn.Linear(hidden_dims[-1], 1))

        self.network = nn.Sequential(*layers)

    def forward(self, state):
        return self.network(state)

class MetaLearningNetwork(nn.Module):
    """Network for meta-learning and rapid adaptation"""

    def __init__(self, input_dim: int, output_dim: int, meta_dim: int = 64):
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.meta_dim = meta_dim

        # Feature extraction
        self.feature_extractor = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.1)
        )

        # Meta-learning parameters
        self.meta_network = nn.Sequential(
            nn.Linear(128, meta_dim),
            nn.ReLU(),
            nn.Linear(meta_dim, 128),
            nn.Tanh()
        )

        # Task-specific adaptation
        self.adaptation_network = nn.Sequential(
            nn.Linear(128 + meta_dim, 128),
            nn.ReLU(),
            nn.Linear(128, output_dim)
        )

    def forward(self, x, meta_params=None):
        features = self.feature_extractor(x)

        if meta_params is not None:
            # Apply meta-parameters for adaptation
            meta_output = self.meta_network(meta_params)
            combined = torch.cat([features, meta_output], dim=-1)
            return self.adaptation_network(combined)
        else:
            # Standard forward pass
            return self.adaptation_network(torch.cat([features, torch.zeros(features.size(0), self.meta_dim)], dim=-1))

class ReinforcementLearner:
    """Reinforcement learning implementation with multiple algorithms"""

    def __init__(self, state_dim: int, action_dim: int, config: Dict = None):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.config = config or self._default_config()

        # Networks
        self.policy_network = PolicyNetwork(state_dim, action_dim)
        self.value_network = ValueNetwork(state_dim)
        self.target_policy_network = copy.deepcopy(self.policy_network)
        self.target_value_network = copy.deepcopy(self.value_network)

        # Optimizers
        self.policy_optimizer = optim.Adam(self.policy_network.parameters(), lr=0.001)
        self.value_optimizer = optim.Adam(self.value_network.parameters(), lr=0.001)

        # Experience replay
        self.replay_buffer = deque(maxlen=self.config['replay_buffer_size'])
        self.prioritized_replay = self.config.get('prioritized_replay', False)

        # Exploration
        self.exploration_strategy = ExplorationStrategy[self.config['exploration_strategy']]
        self.epsilon = self.config['initial_epsilon']
        self.epsilon_decay = self.config['epsilon_decay']
        self.epsilon_min = self.config['epsilon_min']

        # Learning parameters
        self.gamma = self.config['gamma']
        self.tau = self.config['tau']  # For soft updates
        self.update_target_freq = self.config['update_target_freq']
        self.learning_steps = 0

    def _default_config(self) -> Dict:
        """Default configuration for RL"""
        return {
            'algorithm': 'PPO',  # PPO, A2C, DQN, SAC
            'replay_buffer_size': 10000,
            'batch_size': 64,
            'gamma': 0.99,
            'tau': 0.005,
            'update_target_freq': 100,
            'exploration_strategy': 'EPSILON_GREEDY',
            'initial_epsilon': 1.0,
            'epsilon_decay': 0.995,
            'epsilon_min': 0.01,
            'prioritized_replay': False,
            'clip_ratio': 0.2,  # For PPO
            'value_loss_coef': 0.5,
            'entropy_coef': 0.01
        }

    def select_action(self, state, explore=True):
        """Select action using current policy"""
        if isinstance(state, np.ndarray):
            state = torch.FloatTensor(state).unsqueeze(0)

        with torch.no_grad():
            action_probs = F.softmax(self.policy_network(state), dim=-1)

            if explore and random.random() < self.epsilon:
                # Random exploration
                action = random.randint(0, self.action_dim - 1)
            else:
                # Sample from policy
                dist = Categorical(action_probs)
                action = dist.sample().item()

        return action

    def store_experience(self, experience: LearningExperience):
        """Store experience in replay buffer"""
        self.replay_buffer.append(experience)

        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def learn(self):
        """Learn from experiences"""
        if len(self.replay_buffer) < self.config['batch_size']:
            return {}

        # Sample batch
        batch = random.sample(list(self.replay_buffer), self.config['batch_size'])
        states = torch.FloatTensor([exp.state for exp in batch])
        actions = torch.LongTensor([exp.action for exp in batch])
        rewards = torch.FloatTensor([exp.reward for exp in batch])
        next_states = torch.FloatTensor([exp.next_state for exp in batch])
        dones = torch.BoolTensor([exp.done for exp in batch])

        # Compute advantages and returns
        with torch.no_grad():
            next_values = self.target_value_network(next_states).squeeze()
            target_values = rewards + (self.gamma * next_values * ~dones)

        current_values = self.value_network(states).squeeze()

        # Compute advantages
        advantages = target_values - current_values

        # Update policy network
        action_probs = F.softmax(self.policy_network(states), dim=-1)
        dist = Categorical(action_probs)
        log_probs = dist.log_prob(actions)

        # PPO-style loss
        ratio = torch.exp(log_probs - log_probs.detach())
        clipped_ratio = torch.clamp(ratio, 1 - self.config['clip_ratio'], 1 + self.config['clip_ratio'])
        policy_loss = -torch.min(ratio * advantages, clipped_ratio * advantages).mean()

        # Entropy bonus
        entropy = dist.entropy().mean()
        policy_loss -= self.config['entropy_coef'] * entropy

        self.policy_optimizer.zero_grad()
        policy_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_network.parameters(), 0.5)
        self.policy_optimizer.step()

        # Update value network
        value_loss = F.mse_loss(current_values, target_values) * self.config['value_loss_coef']

        self.value_optimizer.zero_grad()
        value_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.value_network.parameters(), 0.5)
        self.value_optimizer.step()

        # Update target networks
        if self.learning_steps % self.update_target_freq == 0:
            self._update_target_networks()

        self.learning_steps += 1

        return {
            'policy_loss': policy_loss.item(),
            'value_loss': value_loss.item(),
            'entropy': entropy.item(),
            'epsilon': self.epsilon
        }

    def _update_target_networks(self):
        """Soft update of target networks"""
        for target_param, param in zip(self.target_policy_network.parameters(), self.policy_network.parameters()):
            target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)

        for target_param, param in zip(self.target_value_network.parameters(), self.value_network.parameters()):
            target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)

class SupervisedLearner:
    """Supervised learning implementation"""

    def __init__(self, input_dim: int, output_dim: int, config: Dict = None):
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.config = config or self._default_config()

        # Network architecture
        self.network = self._build_network()

        # Optimizer
        self.optimizer = optim.Adam(self.network.parameters(), lr=self.config['learning_rate'])

        # Loss function
        if self.config['task_type'] == 'classification':
            self.criterion = nn.CrossEntropyLoss()
        elif self.config['task_type'] == 'regression':
            self.criterion = nn.MSELoss()
        else:
            self.criterion = nn.MSELoss()

        # Training data
        self.training_data = deque(maxlen=self.config['max_training_examples'])
        self.validation_data = deque(maxlen=self.config['max_validation_examples'])

        # Performance tracking
        self.training_history = []
        self.validation_history = []

    def _default_config(self) -> Dict:
        """Default configuration for supervised learning"""
        return {
            'task_type': 'regression',  # classification, regression
            'hidden_dims': [256, 128],
            'learning_rate': 0.001,
            'batch_size': 32,
            'max_training_examples': 10000,
            'max_validation_examples': 2000,
            'validation_split': 0.2,
            'early_stopping_patience': 10,
            'dropout_rate': 0.1
        }

    def _build_network(self) -> nn.Module:
        """Build neural network architecture"""
        layers = []

        # Input layer
        layers.append(nn.Linear(self.input_dim, self.config['hidden_dims'][0]))
        layers.append(nn.ReLU())
        layers.append(nn.Dropout(self.config['dropout_rate']))

        # Hidden layers
        for i in range(len(self.config['hidden_dims']) - 1):
            layers.append(nn.Linear(self.config['hidden_dims'][i], self.config['hidden_dims'][i + 1]))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(self.config['dropout_rate']))

        # Output layer
        layers.append(nn.Linear(self.config['hidden_dims'][-1], self.output_dim))

        return nn.Sequential(*layers)

    def add_example(self, example: SupervisedExample):
        """Add training example"""
        if random.random() < self.config['validation_split']:
            self.validation_data.append(example)
        else:
            self.training_data.append(example)

    def train(self, epochs: int = 1) -> Dict[str, float]:
        """Train the supervised model"""
        if len(self.training_data) < self.config['batch_size']:
            return {'loss': 0.0, 'accuracy': 0.0}

        total_loss = 0.0
        total_correct = 0
        total_samples = 0

        for epoch in range(epochs):
            # Create batches
            batch = random.sample(list(self.training_data), min(self.config['batch_size'], len(self.training_data)))

            # Prepare data
            inputs = torch.FloatTensor([self._preprocess_input(example.input_data) for example in batch])
            targets = torch.FloatTensor([self._preprocess_target(example.target_output) for example in batch])

            # Forward pass
            outputs = self.network(inputs)
            loss = self.criterion(outputs, targets)

            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.network.parameters(), 1.0)
            self.optimizer.step()

            total_loss += loss.item()

            # Calculate accuracy for classification
            if self.config['task_type'] == 'classification':
                predictions = torch.argmax(outputs, dim=1)
                targets_idx = torch.argmax(targets, dim=1)
                total_correct += (predictions == targets_idx).sum().item()
                total_samples += len(batch)

        avg_loss = total_loss / epochs
        accuracy = total_correct / total_samples if total_samples > 0 else 0.0

        self.training_history.append({'loss': avg_loss, 'accuracy': accuracy, 'timestamp': datetime.now()})

        return {'loss': avg_loss, 'accuracy': accuracy}

    def validate(self) -> Dict[str, float]:
        """Validate the model"""
        if len(self.validation_data) == 0:
            return {'loss': 0.0, 'accuracy': 0.0}

        total_loss = 0.0
        total_correct = 0
        total_samples = 0

        self.network.eval()
        with torch.no_grad():
            batch_size = min(32, len(self.validation_data))

            for i in range(0, len(self.validation_data), batch_size):
                batch = list(self.validation_data)[i:i + batch_size]

                inputs = torch.FloatTensor([self._preprocess_input(example.input_data) for example in batch])
                targets = torch.FloatTensor([self._preprocess_target(example.target_output) for example in batch])

                outputs = self.network(inputs)
                loss = self.criterion(outputs, targets)

                total_loss += loss.item()

                if self.config['task_type'] == 'classification':
                    predictions = torch.argmax(outputs, dim=1)
                    targets_idx = torch.argmax(targets, dim=1)
                    total_correct += (predictions == targets_idx).sum().item()
                    total_samples += len(batch)

        self.network.train()

        avg_loss = total_loss / (len(self.validation_data) / batch_size)
        accuracy = total_correct / total_samples if total_samples > 0 else 0.0

        self.validation_history.append({'loss': avg_loss, 'accuracy': accuracy, 'timestamp': datetime.now()})

        return {'loss': avg_loss, 'accuracy': accuracy}

    def predict(self, input_data: Any) -> Any:
        """Make prediction"""
        self.network.eval()
        with torch.no_grad():
            input_tensor = torch.FloatTensor(self._preprocess_input(input_data)).unsqueeze(0)
            output = self.network(input_tensor)

            if self.config['task_type'] == 'classification':
                probabilities = F.softmax(output, dim=-1)
                prediction = torch.argmax(probabilities, dim=-1).item()
                confidence = probabilities[0, prediction].item()
                return {'prediction': prediction, 'confidence': confidence}
            else:
                return {'prediction': output.squeeze().item()}

    def _preprocess_input(self, input_data: Any) -> np.ndarray:
        """Preprocess input data"""
        if isinstance(input_data, (list, tuple)):
            return np.array(input_data, dtype=np.float32)
        elif isinstance(input_data, (int, float)):
            return np.array([input_data], dtype=np.float32)
        elif isinstance(input_data, str):
            # Simple text encoding (in practice, would use proper embeddings)
            return np.array([hash(input_data) % 1000] * self.input_dim, dtype=np.float32)
        else:
            return np.zeros(self.input_dim, dtype=np.float32)

    def _preprocess_target(self, target_output: Any) -> np.ndarray:
        """Preprocess target output"""
        if isinstance(target_output, (list, tuple)):
            return np.array(target_output, dtype=np.float32)
        elif isinstance(target_output, (int, float)):
            if self.config['task_type'] == 'classification':
                # One-hot encoding
                target_array = np.zeros(self.output_dim, dtype=np.float32)
                target_array[int(target_output)] = 1.0
                return target_array
            else:
                return np.array([target_output], dtype=np.float32)
        else:
            return np.zeros(self.output_dim, dtype=np.float32)

class UnsupervisedLearner:
    """Unsupervised learning for pattern discovery"""

    def __init__(self, input_dim: int, config: Dict = None):
        self.input_dim = input_dim
        self.config = config or self._default_config()

        # Autoencoder for representation learning
        self.encoder = self._build_encoder()
        self.decoder = self._build_decoder()

        # Clustering for pattern discovery
        self.n_clusters = self.config['n_clusters']
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=42)

        # Optimizer
        self.optimizer = optim.Adam(
            list(self.encoder.parameters()) + list(self.decoder.parameters()),
            lr=self.config['learning_rate']
        )

        # Data storage
        self.data_buffer = deque(maxlen=self.config['buffer_size'])
        self.cluster_labels = []

        # Performance tracking
        self.reconstruction_history = []
        self.clustering_history = []

    def _default_config(self) -> Dict:
        """Default configuration for unsupervised learning"""
        return {
            'encoding_dims': [128, 64],
            'latent_dim': 32,
            'learning_rate': 0.001,
            'batch_size': 64,
            'buffer_size': 10000,
            'n_clusters': 5,
            'reconstruction_weight': 1.0,
            'clustering_weight': 0.1
        }

    def _build_encoder(self) -> nn.Module:
        """Build encoder network"""
        layers = []
        dims = [self.input_dim] + self.config['encoding_dims'] + [self.config['latent_dim']]

        for i in range(len(dims) - 1):
            layers.append(nn.Linear(dims[i], dims[i + 1]))
            if i < len(dims) - 2:  # No activation on final layer
                layers.append(nn.ReLU())
                layers.append(nn.Dropout(0.1))

        return nn.Sequential(*layers)

    def _build_decoder(self) -> nn.Module:
        """Build decoder network"""
        layers = []
        dims = [self.config['latent_dim']] + self.config['encoding_dims'][::-1] + [self.input_dim]

        for i in range(len(dims) - 1):
            layers.append(nn.Linear(dims[i], dims[i + 1]))
            if i < len(dims) - 2:  # No activation on final layer
                layers.append(nn.ReLU())
                layers.append(nn.Dropout(0.1))

        return nn.Sequential(*layers)

    def add_data(self, data: Any):
        """Add data for unsupervised learning"""
        processed_data = self._preprocess_data(data)
        self.data_buffer.append(processed_data)

    def train(self, epochs: int = 1) -> Dict[str, float]:
        """Train unsupervised models"""
        if len(self.data_buffer) < self.config['batch_size']:
            return {'reconstruction_loss': 0.0, 'clustering_loss': 0.0}

        total_recon_loss = 0.0
        total_clustering_loss = 0.0

        for epoch in range(epochs):
            # Sample batch
            batch = random.sample(list(self.data_buffer), min(self.config['batch_size'], len(self.data_buffer)))
            batch_tensor = torch.FloatTensor(batch)

            # Autoencoder training
            self.optimizer.zero_grad()

            # Encode and decode
            latent = self.encoder(batch_tensor)
            reconstructed = self.decoder(latent)

            # Reconstruction loss
            recon_loss = F.mse_loss(reconstructed, batch_tensor)

            # Clustering loss (optional)
            clustering_loss = 0.0
            if self.config['clustering_weight'] > 0 and len(self.data_buffer) > self.n_clusters:
                # Apply k-means to latent representations
                latent_np = latent.detach().numpy()
                cluster_labels = self.kmeans.fit_predict(latent_np)

                # Simple clustering loss (distance to cluster center)
                centers = self.kmeans.cluster_centers_
                for i, label in enumerate(cluster_labels):
                    center = torch.FloatTensor(centers[label])
                    clustering_loss += F.mse_loss(latent[i], center)

                clustering_loss = clustering_loss / len(latent)

            # Total loss
            total_loss = (self.config['reconstruction_weight'] * recon_loss +
                         self.config['clustering_weight'] * clustering_loss)

            # Backward pass
            total_loss.backward()
            self.optimizer.step()

            total_recon_loss += recon_loss.item()
            total_clustering_loss += clustering_loss.item()

        avg_recon_loss = total_recon_loss / epochs
        avg_clustering_loss = total_clustering_loss / epochs

        self.reconstruction_history.append({
            'loss': avg_recon_loss,
            'timestamp': datetime.now()
        })

        return {
            'reconstruction_loss': avg_recon_loss,
            'clustering_loss': avg_clustering_loss
        }

    def get_latent_representation(self, data: Any) -> np.ndarray:
        """Get latent representation of data"""
        self.encoder.eval()
        with torch.no_grad():
            processed_data = self._preprocess_data(data)
            data_tensor = torch.FloatTensor(processed_data).unsqueeze(0)
            latent = self.encoder(data_tensor)
            return latent.squeeze().numpy()

    def discover_patterns(self) -> Dict[str, Any]:
        """Discover patterns in the data"""
        if len(self.data_buffer) < self.n_clusters:
            return {'patterns': [], 'cluster_centers': []}

        # Get all latent representations
        all_data = list(self.data_buffer)
        data_tensor = torch.FloatTensor(all_data)

        with torch.no_grad():
            latent_representations = self.encoder(data_tensor).numpy()

        # Apply clustering
        cluster_labels = self.kmeans.fit_predict(latent_representations)
        cluster_centers = self.kmeans.cluster_centers_

        # Analyze clusters
        patterns = []
        for i in range(self.n_clusters):
            cluster_indices = np.where(cluster_labels == i)[0]
            if len(cluster_indices) > 0:
                cluster_data = [all_data[idx] for idx in cluster_indices]
                patterns.append({
                    'cluster_id': i,
                    'size': len(cluster_indices),
                    'center': cluster_centers[i].tolist(),
                    'sample_data': cluster_data[:3]  # First 3 samples
                })

        return {
            'patterns': patterns,
            'cluster_centers': cluster_centers.tolist(),
            'cluster_labels': cluster_labels.tolist()
        }

    def _preprocess_data(self, data: Any) -> np.ndarray:
        """Preprocess data for unsupervised learning"""
        if isinstance(data, (list, tuple)):
            return np.array(data, dtype=np.float32)
        elif isinstance(data, (int, float)):
            return np.array([data] * self.input_dim, dtype=np.float32)
        elif isinstance(data, str):
            # Simple encoding
            encoded = np.zeros(self.input_dim, dtype=np.float32)
            for i, char in enumerate(data[:self.input_dim]):
                encoded[i] = ord(char) / 255.0
            return encoded
        else:
            return np.random.randn(self.input_dim).astype(np.float32)

class LearningEngine:
    """
    Advanced Learning Engine for AI Agents

    This class implements a comprehensive learning system that combines multiple
    learning approaches to enable continuous improvement and adaptation.
    """

    def __init__(self, agent_id: str, config: Optional[Dict] = None):
        self.agent_id = agent_id
        self.config = config or self._default_config()

        # Learning components
        self.rl_learner = None
        self.supervised_learner = None
        self.unsupervised_learner = None
        self.meta_learner = None

        # Learning goals
        self.learning_goals = {}
        self.active_goals = set()

        # Experience tracking
        self.experience_buffer = deque(maxlen=self.config['experience_buffer_size'])
        self.performance_history = deque(maxlen=1000)

        # Metrics
        self.metrics = {
            'total_experiences': 0,
            'learning_episodes': 0,
            'average_reward': 0.0,
            'learning_rate': 0.001,
            'exploration_rate': 0.1,
            'goal_completion_rate': 0.0,
            'adaptation_speed': 0.0
        }

        # State
        self.is_learning = False
        self.learning_thread = None
        self.stop_learning = threading.Event()

        logger.info(f"Learning Engine initialized for agent {agent_id}")

    def _default_config(self) -> Dict:
        """Default configuration"""
        return {
            'experience_buffer_size': 10000,
            'learning_batch_size': 64,
            'learning_frequency': 10,  # Learn every N experiences
            'goal_check_frequency': 100,  # Check goals every N experiences
            'adaptation_threshold': 0.1,
            'performance_window': 100,
            'enable_meta_learning': True,
            'enable_transfer_learning': True,
            'curriculum_learning': True
        }

    def initialize_reinforcement_learner(self, state_dim: int, action_dim: int):
        """Initialize reinforcement learning component"""
        self.rl_learner = ReinforcementLearner(state_dim, action_dim)
        logger.info(f"Reinforcement learner initialized: state_dim={state_dim}, action_dim={action_dim}")

    def initialize_supervised_learner(self, input_dim: int, output_dim: int, task_type: str = 'regression'):
        """Initialize supervised learning component"""
        config = {'task_type': task_type}
        self.supervised_learner = SupervisedLearner(input_dim, output_dim, config)
        logger.info(f"Supervised learner initialized: input_dim={input_dim}, output_dim={output_dim}, task_type={task_type}")

    def initialize_unsupervised_learner(self, input_dim: int, n_clusters: int = 5):
        """Initialize unsupervised learning component"""
        config = {'n_clusters': n_clusters}
        self.unsupervised_learner = UnsupervisedLearner(input_dim, config)
        logger.info(f"Unsupervised learner initialized: input_dim={input_dim}, n_clusters={n_clusters}")

    def add_experience(self, experience: LearningExperience):
        """Add learning experience"""
        self.experience_buffer.append(experience)
        self.metrics['total_experiences'] += 1

        # Add to appropriate learner
        if self.rl_learner and hasattr(experience, 'reward'):
            self.rl_learner.store_experience(experience)

        # Check if learning should be triggered
        if self.metrics['total_experiences'] % self.config['learning_frequency'] == 0:
            self._trigger_learning()

        # Check learning goals
        if self.metrics['total_experiences'] % self.config['goal_check_frequency'] == 0:
            self._check_learning_goals()

    def add_supervised_example(self, example: SupervisedExample):
        """Add supervised learning example"""
        if self.supervised_learner:
            self.supervised_learner.add_example(example)

    def add_unsupervised_data(self, data: Any):
        """Add unsupervised learning data"""
        if self.unsupervised_learner:
            self.unsupervised_learner.add_data(data)

    def create_learning_goal(self, goal: LearningGoal):
        """Create a new learning goal"""
        self.learning_goals[goal.name] = goal
        self.active_goals.add(goal.name)
        logger.info(f"Created learning goal: {goal.name}")

    def _trigger_learning(self):
        """Trigger learning process"""
        if not self.is_learning:
            self._start_learning_process()

    def _start_learning_process(self):
        """Start background learning process"""
        if self.learning_thread and self.learning_thread.is_alive():
            return

        self.stop_learning.clear()
        self.learning_thread = threading.Thread(target=self._learning_loop)
        self.learning_thread.start()
        logger.info("Started learning process")

    def _learning_loop(self):
        """Main learning loop"""
        while not self.stop_learning.is_set():
            try:
                # Reinforcement learning
                if self.rl_learner and len(self.experience_buffer) > 0:
                    rl_metrics = self.rl_learner.learn()
                    if rl_metrics:
                        self.metrics.update(rl_metrics)

                # Supervised learning
                if self.supervised_learner:
                    sl_metrics = self.supervised_learner.train(epochs=1)
                    if sl_metrics:
                        self.metrics.update(sl_metrics)

                # Unsupervised learning
                if self.unsupervised_learner:
                    ul_metrics = self.unsupervised_learner.train(epochs=1)
                    if ul_metrics:
                        self.metrics.update(ul_metrics)

                # Update performance metrics
                self._update_performance_metrics()

                # Small delay to prevent excessive CPU usage
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in learning loop: {e}")
                time.sleep(1.0)

    def _update_performance_metrics(self):
        """Update performance metrics"""
        if self.rl_learner and len(self.experience_buffer) > 0:
            # Calculate average reward from recent experiences
            recent_experiences = list(self.experience_buffer)[-self.config['performance_window']:]
            if recent_experiences:
                avg_reward = sum(exp.reward for exp in recent_experiences) / len(recent_experiences)
                self.metrics['average_reward'] = avg_reward
                self.performance_history.append(avg_reward)

    def _check_learning_goals(self):
        """Check progress toward learning goals"""
        for goal_name in list(self.active_goals):
            goal = self.learning_goals.get(goal_name)
            if not goal:
                continue

            # Update goal progress based on current performance
            current_performance = self._calculate_goal_performance(goal)
            goal.current_performance = current_performance
            goal.progress_history.append(current_performance)

            # Check if goal is completed
            if current_performance >= goal.target_performance:
                self.active_goals.discard(goal_name)
                logger.info(f"Learning goal completed: {goal_name}")
                self.metrics['goal_completion_rate'] = (
                    len([g for g in self.learning_goals.values() if g.current_performance >= g.target_performance]) /
                    len(self.learning_goals)
                )

    def _calculate_goal_performance(self, goal: LearningGoal) -> float:
        """Calculate current performance for a specific goal"""
        if goal.learning_type == LearningType.REINFORCEMENT:
            return self.metrics.get('average_reward', 0.0)
        elif goal.learning_type == LearningType.SUPERVISED:
            if self.supervised_learner and self.supervised_learner.validation_history:
                return self.supervised_learner.validation_history[-1]['accuracy']
        elif goal.learning_type == LearningType.UNSUPERVISED:
            if self.unsupervised_learner and self.unsupervised_learner.reconstruction_history:
                # Use reconstruction error (inverted)
                latest_loss = self.unsupervised_learner.reconstruction_history[-1]['loss']
                return max(0.0, 1.0 - latest_loss)

        return 0.0

    def select_action(self, state: Any, explore: bool = True) -> Any:
        """Select action using learned policy"""
        if self.rl_learner:
            return self.rl_learner.select_action(state, explore)
        else:
            # Random action if no RL learner
            return random.randint(0, 3)  # Default action space

    def predict(self, input_data: Any) -> Any:
        """Make prediction using supervised learner"""
        if self.supervised_learner:
            return self.supervised_learner.predict(input_data)
        else:
            return {'prediction': 0.0, 'confidence': 0.0}

    def discover_patterns(self) -> Dict[str, Any]:
        """Discover patterns using unsupervised learner"""
        if self.unsupervised_learner:
            return self.unsupervised_learner.discover_patterns()
        else:
            return {'patterns': [], 'cluster_centers': []}

    def adapt_to_new_task(self, task_data: Dict, adaptation_steps: int = 100):
        """Adapt to a new task using meta-learning"""
        if not self.config.get('enable_meta_learning', True):
            return

        logger.info(f"Adapting to new task with {adaptation_steps} steps")

        for step in range(adaptation_steps):
            # Process task data
            if 'experiences' in task_data:
                for exp in task_data['experiences']:
                    self.add_experience(exp)

            if 'supervised_examples' in task_data:
                for example in task_data['supervised_examples']:
                    self.add_supervised_example(example)

            if 'unsupervised_data' in task_data:
                for data in task_data['unsupervised_data']:
                    self.add_unsupervised_data(data)

            # Allow some learning to occur
            time.sleep(0.01)

        logger.info("Task adaptation completed")

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get comprehensive learning summary"""
        summary = {
            'agent_id': self.agent_id,
            'timestamp': datetime.now().isoformat(),
            'metrics': self.metrics.copy(),
            'learning_goals': {
                name: {
                    'description': goal.description,
                    'target': goal.target_performance,
                    'current': goal.current_performance,
                    'progress': goal.current_performance / goal.target_performance if goal.target_performance > 0 else 0,
                    'priority': goal.priority,
                    'active': name in self.active_goals
                }
                for name, goal in self.learning_goals.items()
            },
            'experience_buffer_size': len(self.experience_buffer),
            'active_goals_count': len(self.active_goals),
            'learning_components': {
                'reinforcement_learning': self.rl_learner is not None,
                'supervised_learning': self.supervised_learner is not None,
                'unsupervised_learning': self.unsupervised_learner is not None
            }
        }

        # Add component-specific metrics
        if self.rl_learner:
            summary['rl_metrics'] = {
                'learning_steps': self.rl_learner.learning_steps,
                'epsilon': self.rl_learner.epsilon,
                'replay_buffer_size': len(self.rl_learner.replay_buffer)
            }

        if self.supervised_learner:
            summary['sl_metrics'] = {
                'training_examples': len(self.supervised_learner.training_data),
                'validation_examples': len(self.supervised_learner.validation_data),
                'latest_training_loss': self.supervised_learner.training_history[-1]['loss'] if self.supervised_learner.training_history else 0.0,
                'latest_validation_accuracy': self.supervised_learner.validation_history[-1]['accuracy'] if self.supervised_learner.validation_history else 0.0
            }

        if self.unsupervised_learner:
            summary['ul_metrics'] = {
                'data_buffer_size': len(self.unsupervised_learner.data_buffer),
                'n_clusters': self.unsupervised_learner.n_clusters,
                'latest_reconstruction_loss': self.unsupervised_learner.reconstruction_history[-1]['loss'] if self.unsupervised_learner.reconstruction_history else 0.0
            }

        return summary

    def save_learning_state(self, filepath: str):
        """Save learning state to file"""
        state = {
            'agent_id': self.agent_id,
            'config': self.config,
            'metrics': self.metrics,
            'learning_goals': {
                name: {
                    'description': goal.description,
                    'target_performance': goal.target_performance,
                    'current_performance': goal.current_performance,
                    'priority': goal.priority,
                    'learning_type': goal.learning_type.value,
                    'progress_history': goal.progress_history,
                    'deadline': goal.deadline.isoformat() if goal.deadline else None
                }
                for name, goal in self.learning_goals.items()
            },
            'active_goals': list(self.active_goals),
            'performance_history': list(self.performance_history),
            'timestamp': datetime.now().isoformat()
        }

        # Save neural networks if they exist
        if self.rl_learner:
            state['rl_policy'] = self.rl_learner.policy_network.state_dict()
            state['rl_value'] = self.rl_learner.value_network.state_dict()

        if self.supervised_learner:
            state['sl_network'] = self.supervised_learner.network.state_dict()

        if self.unsupervised_learner:
            state['ul_encoder'] = self.unsupervised_learner.encoder.state_dict()
            state['ul_decoder'] = self.unsupervised_learner.decoder.state_dict()

        with open(filepath, 'wb') as f:
            pickle.dump(state, f)

        logger.info(f"Learning state saved to {filepath}")

    def load_learning_state(self, filepath: str):
        """Load learning state from file"""
        try:
            with open(filepath, 'rb') as f:
                state = pickle.load(f)

            self.agent_id = state['agent_id']
            self.config = state['config']
            self.metrics = state['metrics']

            # Restore learning goals
            self.learning_goals = {}
            for name, goal_data in state['learning_goals'].items():
                goal = LearningGoal(
                    name=name,
                    description=goal_data['description'],
                    target_performance=goal_data['target_performance'],
                    current_performance=goal_data['current_performance'],
                    priority=goal_data['priority'],
                    learning_type=LearningType(goal_data['learning_type']),
                    deadline=datetime.fromisoformat(goal_data['deadline']) if goal_data['deadline'] else None,
                    progress_history=goal_data['progress_history']
                )
                self.learning_goals[name] = goal

            self.active_goals = set(state['active_goals'])
            self.performance_history = deque(state['performance_history'], maxlen=1000)

            # Restore neural networks if they exist
            if self.rl_learner and 'rl_policy' in state:
                self.rl_learner.policy_network.load_state_dict(state['rl_policy'])
                self.rl_learner.value_network.load_state_dict(state['rl_value'])

            if self.supervised_learner and 'sl_network' in state:
                self.supervised_learner.network.load_state_dict(state['sl_network'])

            if self.unsupervised_learner and 'ul_encoder' in state:
                self.unsupervised_learner.encoder.load_state_dict(state['ul_encoder'])
                self.unsupervised_learner.decoder.load_state_dict(state['ul_decoder'])

            logger.info(f"Learning state loaded from {filepath}")

        except Exception as e:
            logger.error(f"Error loading learning state: {e}")

    def stop_learning_process(self):
        """Stop the learning process"""
        self.stop_learning.set()
        if self.learning_thread and self.learning_thread.is_alive():
            self.learning_thread.join(timeout=5.0)
        self.is_learning = False
        logger.info("Learning process stopped")

# Utility functions for integration
async def create_learning_engine(agent_id: str, config: Optional[Dict] = None) -> LearningEngine:
    """Factory function to create and initialize learning engine"""
    engine = LearningEngine(agent_id, config)
    return engine

def benchmark_learning_performance(learning_engine: LearningEngine,
                                 test_experiences: List[LearningExperience]) -> Dict:
    """Benchmark learning engine performance"""
    import time

    start_time = time.time()

    # Add experiences
    for exp in test_experiences:
        learning_engine.add_experience(exp)

    # Wait for learning to process
    time.sleep(2.0)

    total_time = time.time() - start_time

    return {
        'total_time': total_time,
        'experiences_processed': len(test_experiences),
        'processing_rate': len(test_experiences) / total_time,
        'final_metrics': learning_engine.metrics,
        'learning_summary': learning_engine.get_learning_summary()
    }

if __name__ == "__main__":
    # Example usage
    async def main():
        # Create learning engine
        config = {
            'experience_buffer_size': 1000,
            'learning_frequency': 5,
            'enable_meta_learning': True
        }

        learning_engine = await create_learning_engine("test_agent", config)

        # Initialize learners
        learning_engine.initialize_reinforcement_learner(state_dim=10, action_dim=4)
        learning_engine.initialize_supervised_learner(input_dim=5, output_dim=3, task_type='classification')
        learning_engine.initialize_unsupervised_learner(input_dim=8, n_clusters=3)

        # Create learning goals
        goal1 = LearningGoal(
            name="high_average_reward",
            description="Achieve high average reward in RL task",
            target_performance=0.8,
            current_performance=0.0,
            priority=0.8,
            learning_type=LearningType.REINFORCEMENT
        )
        learning_engine.create_learning_goal(goal1)

        # Add test experiences
        for i in range(50):
            experience = LearningExperience(
                state=np.random.randn(10),
                action=random.randint(0, 3),
                reward=random.random(),
                next_state=np.random.randn(10),
                done=random.random() > 0.8,
                timestamp=datetime.now(),
                agent_id="test_agent"
            )
            learning_engine.add_experience(experience)

        # Add supervised examples
        for i in range(30):
            example = SupervisedExample(
                input_data=np.random.randn(5),
                target_output=random.randint(0, 2),
                timestamp=datetime.now(),
                confidence=0.9
            )
            learning_engine.add_supervised_example(example)

        # Add unsupervised data
        for i in range(40):
            learning_engine.add_unsupervised_data(np.random.randn(8))

        # Test prediction
        action = learning_engine.select_action(np.random.randn(10))
        prediction = learning_engine.predict(np.random.randn(5))
        patterns = learning_engine.discover_patterns()

        print(f"Selected action: {action}")
        print(f"Prediction: {prediction}")
        print(f"Discovered patterns: {len(patterns['patterns'])}")

        # Get learning summary
        summary = learning_engine.get_learning_summary()
        print("\nLearning engine summary:")
        print(json.dumps(summary, indent=2, default=str))

        # Save state
        learning_engine.save_learning_state("/tmp/test_learning_state.pkl")

        # Stop learning
        learning_engine.stop_learning_process()

    asyncio.run(main())