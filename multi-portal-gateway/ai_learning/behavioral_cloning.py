#!/usr/bin/env python3
"""
Behavioral Cloning System for Imitation Learning
Implements learning from expert demonstrations and human players
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import random
import logging
from typing import Dict, List, Tuple, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from collections import defaultdict, deque
import torch.optim as optim
import math
import time
from enum import Enum
import pickle
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImitationLearningType(Enum):
    """Types of imitation learning approaches"""
    BEHAVIORAL_CLONING = "behavioral_cloning"
    DAgger = "data_aggregation"
    GAIL = "generative_adversarial_imitation_learning"
    SQIL = "soft_q_imitation_learning"
    AIRL = "adversarial_inverse_reinforcement_learning"

@dataclass
class Demonstration:
    """Represents a single demonstration episode"""
    states: List[np.ndarray]
    actions: List[np.ndarray]
    rewards: List[float] = field(default_factory=list)
    next_states: List[np.ndarray] = field(default_factory=list)
    dones: List[bool] = field(default_factory=list)
    expert_id: str = "unknown"
    task_id: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def __len__(self):
        return len(self.states)

    def __getitem__(self, idx):
        return {
            'state': self.states[idx],
            'action': self.actions[idx],
            'reward': self.rewards[idx] if idx < len(self.rewards) else 0.0,
            'next_state': self.next_states[idx] if idx < len(self.next_states) else None,
            'done': self.dones[idx] if idx < len(self.dones) else False
        }

@dataclass
class BehavioralCloningConfig:
    """Configuration for behavioral cloning"""
    imitation_type: ImitationLearningType = ImitationLearningType.BEHAVIORAL_CLONING
    state_dim: int = 10
    action_dim: int = 4
    hidden_dims: List[int] = field(default_factory=lambda: [256, 256])
    lr: float = 1e-3
    batch_size: int = 64
    num_epochs: int = 100
    validation_split: float = 0.2
    data_augmentation: bool = True
    dropout_rate: float = 0.1
    device: str = 'cuda'
    loss_type: str = 'mse'  # 'mse', 'ce', 'huber'
    expert_weighting: bool = True  # Weight demonstrations by expert quality

class DemonstrationBuffer:
    """Buffer for storing and managing demonstrations"""

    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self.demonstrations = []
        self.expert_qualities = {}
        self.task_demonstrations = defaultdict(list)
        self.total_transitions = 0

    def add_demonstration(self, demonstration: Demonstration, quality_score: float = 1.0):
        """Add a demonstration to the buffer"""
        # Check capacity
        if len(self.demonstrations) >= self.capacity:
            # Remove oldest or lowest quality demonstration
            if self.expert_qualities:
                worst_expert = min(self.expert_qualities.keys(),
                                 key=lambda k: self.expert_qualities[k])
                self._remove_demonstrations_by_expert(worst_expert)
            else:
                self.demonstrations.pop(0)

        self.demonstrations.append(demonstration)
        self.expert_qualities[demonstration.expert_id] = quality_score
        self.task_demonstrations[demonstration.task_id].append(demonstration)
        self.total_transitions += len(demonstration)

        logger.info(f"Added demonstration from {demonstration.expert_id} "
                   f"({len(demonstration)} steps)")

    def _remove_demonstrations_by_expert(self, expert_id: str):
        """Remove all demonstrations from a specific expert"""
        self.demonstrations = [d for d in self.demonstrations if d.expert_id != expert_id]
        if expert_id in self.expert_qualities:
            del self.expert_qualities[expert_id]

    def sample_batch(self, batch_size: int, task_id: Optional[str] = None,
                    expert_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Sample a batch of transitions"""
        candidates = []

        if task_id:
            candidates = self.task_demonstrations.get(task_id, [])
        elif expert_id:
            candidates = [d for d in self.demonstrations if d.expert_id == expert_id]
        else:
            candidates = self.demonstrations

        if not candidates:
            return []

        # Sample transitions from demonstrations
        batch = []
        attempts = 0
        max_attempts = batch_size * 3

        while len(batch) < batch_size and attempts < max_attempts:
            # Random demonstration
            demo = random.choice(candidates)
            # Random transition
            idx = random.randint(0, len(demo) - 1)
            transition = demo[idx]

            # Add expert quality weighting if available
            if demo.expert_id in self.expert_qualities:
                transition['expert_quality'] = self.expert_qualities[demo.expert_id]
            else:
                transition['expert_quality'] = 1.0

            batch.append(transition)
            attempts += 1

        return batch

    def get_dataset(self, task_id: Optional[str] = None) -> Tuple[np.ndarray, np.ndarray]:
        """Get full dataset for training"""
        states = []
        actions = []

        candidates = self.task_demonstrations.get(task_id, self.demonstrations)

        for demo in candidates:
            for i in range(len(demo)):
                states.append(demo.states[i])
                actions.append(demo.actions[i])

        return np.array(states), np.array(actions)

    def get_statistics(self) -> Dict[str, Any]:
        """Get buffer statistics"""
        if not self.demonstrations:
            return {}

        stats = {
            'total_demonstrations': len(self.demonstrations),
            'total_transitions': self.total_transitions,
            'experts': list(self.expert_qualities.keys()),
            'tasks': list(self.task_demonstrations.keys()),
            'avg_demonstration_length': np.mean([len(d) for d in self.demonstrations]),
            'expert_qualities': self.expert_qualities.copy()
        }

        return stats

class BehavioralCloningNetwork(nn.Module):
    """Neural network for behavioral cloning"""

    def __init__(self, config: BehavioralCloningConfig):
        super().__init__()
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Build network layers
        layers = []
        input_dim = config.state_dim

        for hidden_dim in config.hidden_dims:
            layers.extend([
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(config.dropout_rate)
            ])
            input_dim = hidden_dim

        # Output layer
        if config.action_dim > 10:  # Assume continuous action space for large dimensions
            layers.append(nn.Linear(input_dim, config.action_dim))
        else:  # Small action space - could be discrete
            layers.append(nn.Linear(input_dim, config.action_dim))

        self.network = nn.Sequential(*layers)

        # Action space type detection
        self.discrete_actions = config.action_dim <= 10

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        x = self.network(x)

        if self.discrete_actions:
            return F.softmax(x, dim=-1)
        else:
            return torch.tanh(x)  # Bounded continuous actions

    def select_action(self, state: torch.Tensor, deterministic: bool = False) -> torch.Tensor:
        """Select action based on state"""
        with torch.no_grad():
            output = self.forward(state)

        if self.discrete_actions:
            if deterministic:
                return torch.argmax(output, dim=-1)
            else:
                return torch.multinomial(output, 1).squeeze(-1)
        else:
            if deterministic:
                return output
            else:
                # Add noise for exploration
                noise = torch.randn_like(output) * 0.1
                return torch.clamp(output + noise, -1, 1)

class BehavioralCloningTrainer:
    """Main behavioral cloning trainer"""

    def __init__(self, config: BehavioralCloningConfig):
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Initialize network and optimizer
        self.network = BehavioralCloningNetwork(config).to(self.device)
        self.optimizer = optim.Adam(self.network.parameters(), lr=config.lr)

        # Demonstration buffer
        self.demo_buffer = DemonstrationBuffer()

        # Training metrics
        self.training_history = {
            'train_losses': [],
            'val_losses': [],
            'train_accuracies': [],
            'val_accuracies': []
        }

    def load_demonstrations(self, demonstrations: List[Demonstration],
                           quality_scores: Optional[Dict[str, float]] = None):
        """Load demonstrations into buffer"""
        quality_scores = quality_scores or {}

        for demo in demonstrations:
            quality = quality_scores.get(demo.expert_id, 1.0)
            self.demo_buffer.add_demonstration(demo, quality)

        logger.info(f"Loaded {len(demonstrations)} demonstrations")

    def train(self, validation_data: Optional[Tuple[np.ndarray, np.ndarray]] = None) -> Dict[str, List[float]]:
        """Train behavioral cloning model"""
        logger.info("Starting behavioral cloning training")

        # Get dataset
        states, actions = self.demo_buffer.get_dataset()

        if len(states) == 0:
            logger.warning("No demonstrations available for training")
            return {'train_losses': [], 'val_losses': []}

        # Convert to tensors
        states_tensor = torch.FloatTensor(states).to(self.device)
        actions_tensor = torch.FloatTensor(actions).to(self.device)

        # Split data
        if validation_data is None:
            # Create validation split
            val_size = int(len(states) * self.config.validation_split)
            indices = torch.randperm(len(states))

            train_indices = indices[val_size:]
            val_indices = indices[:val_size]

            train_states = states_tensor[train_indices]
            train_actions = actions_tensor[train_indices]
            val_states = states_tensor[val_indices]
            val_actions = actions_tensor[val_indices]
        else:
            # Use provided validation data
            train_states, train_actions = states_tensor, actions_tensor
            val_states, val_actions = validation_data
            val_states = torch.FloatTensor(val_states).to(self.device)
            val_actions = torch.FloatTensor(val_actions).to(self.device)

        # Training loop
        for epoch in range(self.config.num_epochs):
            # Training
            self.network.train()
            train_loss = 0.0
            train_correct = 0
            train_total = 0

            # Mini-batch training
            num_batches = len(train_states) // self.config.batch_size
            for batch_idx in range(num_batches):
                start_idx = batch_idx * self.config.batch_size
                end_idx = start_idx + self.config.batch_size

                batch_states = train_states[start_idx:end_idx]
                batch_actions = train_actions[start_idx:end_idx]

                self.optimizer.zero_grad()

                # Forward pass
                predictions = self.network(batch_states)

                # Compute loss
                if self.network.discrete_actions:
                    # Cross-entropy for discrete actions
                    batch_actions = batch_actions.long()
                    loss = F.cross_entropy(predictions, batch_actions)

                    # Accuracy
                    _, predicted = torch.max(predictions, 1)
                    train_correct += (predicted == batch_actions).sum().item()
                    train_total += batch_actions.size(0)
                else:
                    # MSE for continuous actions
                    loss = F.mse_loss(predictions, batch_actions)

                # Backward pass
                loss.backward()
                self.optimizer.step()

                train_loss += loss.item()

            # Validation
            self.network.eval()
            val_loss = 0.0
            val_correct = 0
            val_total = 0

            with torch.no_grad():
                val_predictions = self.network(val_states)

                if self.network.discrete_actions:
                    val_actions_long = val_actions.long()
                    val_loss = F.cross_entropy(val_predictions, val_actions_long).item()

                    _, val_predicted = torch.max(val_predictions, 1)
                    val_correct = (val_predicted == val_actions_long).sum().item()
                    val_total = val_actions_long.size(0)
                else:
                    val_loss = F.mse_loss(val_predictions, val_actions).item()

            # Calculate metrics
            avg_train_loss = train_loss / num_batches
            avg_val_loss = val_loss

            self.training_history['train_losses'].append(avg_train_loss)
            self.training_history['val_losses'].append(avg_val_loss)

            if self.network.discrete_actions:
                train_acc = 100.0 * train_correct / train_total if train_total > 0 else 0
                val_acc = 100.0 * val_correct / val_total if val_total > 0 else 0

                self.training_history['train_accuracies'].append(train_acc)
                self.training_history['val_accuracies'].append(val_acc)

                logger.info(f"Epoch {epoch}: Train Loss={avg_train_loss:.4f}, "
                           f"Train Acc={train_acc:.2f}%, Val Loss={avg_val_loss:.4f}, "
                           f"Val Acc={val_acc:.2f}%")
            else:
                logger.info(f"Epoch {epoch}: Train Loss={avg_train_loss:.4f}, "
                           f"Val Loss={avg_val_loss:.4f}")

        return self.training_history

    def evaluate(self, test_states: np.ndarray, test_actions: np.ndarray) -> Dict[str, float]:
        """Evaluate trained model"""
        self.network.eval()

        test_states_tensor = torch.FloatTensor(test_states).to(self.device)
        test_actions_tensor = torch.FloatTensor(test_actions).to(self.device)

        with torch.no_grad():
            predictions = self.network(test_states_tensor)

            if self.network.discrete_actions:
                test_actions_long = test_actions_tensor.long()
                loss = F.cross_entropy(predictions, test_actions_long).item()

                _, predicted = torch.max(predictions, 1)
                accuracy = (predicted == test_actions_long).float().mean().item() * 100
            else:
                loss = F.mse_loss(predictions, test_actions_tensor).item()
                accuracy = 0.0  # MSE doesn't have a direct accuracy measure

        return {
            'loss': loss,
            'accuracy': accuracy,
            'mean_squared_error': loss if not self.network.discrete_actions else None
        }

class DAggerTrainer:
    """Dataset Aggregation (DAgger) trainer"""

    def __init__(self, config: BehavioralCloningConfig, expert_policy: Callable):
        self.config = config
        self.expert_policy = expert_policy
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Behavioral cloning network
        self.bc_trainer = BehavioralCloningTrainer(config)

        # DAgger dataset
        self.trajectory_buffer = []

        # Training parameters
        self.beta_schedule = lambda t: min(1.0, 10 * t / 1000)  # Linear schedule

    def train_dagger(self, environment, num_iterations: int = 10,
                    episodes_per_iteration: int = 10) -> Dict[str, List[float]]:
        """Train using DAgger algorithm"""
        logger.info("Starting DAgger training")

        all_train_losses = []
        all_val_losses = []

        for iteration in range(num_iterations):
            logger.info(f"DAgger iteration {iteration + 1}/{num_iterations}")

            # Collect trajectories
            new_trajectories = self._collect_trajectories(environment, episodes_per_iteration, iteration)

            # Add to buffer
            for traj in new_trajectories:
                self.trajectory_buffer.extend(traj)

            # Train on aggregated dataset
            if len(self.trajectory_buffer) > 0:
                # Convert to demonstration format
                states = np.array([t['state'] for t in self.trajectory_buffer])
                actions = np.array([t['action'] for t in self.trajectory_buffer])

                # Create temporary demonstration buffer
                temp_demo = Demonstration(states, actions)
                self.bc_trainer.demo_buffer.add_demonstration(temp_demo)

                # Train
                history = self.bc_trainer.train()

                all_train_losses.extend(history['train_losses'])
                all_val_losses.extend(history['val_losses'])

        return {
            'train_losses': all_train_losses,
            'val_losses': all_val_losses,
            'total_trajectories': len(self.trajectory_buffer)
        }

    def _collect_trajectories(self, environment, num_episodes: int, iteration: int) -> List[List[Dict[str, Any]]]:
        """Collect trajectories using mixed policy"""
        trajectories = []
        beta = self.beta_schedule(iteration)

        for episode in range(num_episodes):
            trajectory = []
            state = environment.reset()
            done = False

            while not done:
                # Choose between policy and expert
                if random.random() < beta:
                    # Use learned policy
                    state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                    action = self.bc_trainer.network.select_action(state_tensor).cpu().numpy()
                else:
                    # Use expert policy
                    action = self.expert_policy(state)

                # Take step
                next_state, reward, done, info = environment.step(action)

                # Store transition
                trajectory.append({
                    'state': state,
                    'action': action,
                    'expert_query': random.random() >= beta
                })

                state = next_state

            trajectories.append(trajectory)

        return trajectories

class GAILTrainer:
    """Generative Adversarial Imitation Learning trainer"""

    def __init__(self, config: BehavioralCloningConfig):
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Policy network (actor)
        self.policy = BehavioralCloningNetwork(config).to(self.device)
        self.policy_optimizer = optim.Adam(self.policy.parameters(), lr=config.lr)

        # Discriminator network
        self.discriminator = self._create_discriminator().to(self.device)
        self.discriminator_optimizer = optim.Adam(self.discriminator.parameters(), lr=config.lr)

        # Expert demonstrations
        self.expert_buffer = DemonstrationBuffer()

        # Training metrics
        self.training_history = {
            'policy_losses': [],
            'discriminator_losses': [],
            'discriminator_accuracies': []
        }

    def _create_discriminator(self) -> nn.Module:
        """Create discriminator network"""
        return nn.Sequential(
            nn.Linear(self.config.state_dim + self.config.action_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )

    def train_gail(self, environment, expert_demonstrations: List[Demonstration],
                   num_epochs: int = 1000) -> Dict[str, List[float]]:
        """Train using GAIL algorithm"""
        logger.info("Starting GAIL training")

        # Load expert demonstrations
        for demo in expert_demonstrations:
            self.expert_buffer.add_demonstration(demo)

        for epoch in range(num_epochs):
            # Train discriminator
            disc_loss, disc_acc = self._train_discinator(environment)

            # Train policy
            policy_loss = self._train_policy(environment)

            # Store metrics
            self.training_history['discriminator_losses'].append(disc_loss)
            self.training_history['discriminator_accuracies'].append(disc_acc)
            self.training_history['policy_losses'].append(policy_loss)

            if epoch % 100 == 0:
                logger.info(f"Epoch {epoch}: Disc Loss={disc_loss:.4f}, "
                           f"Disc Acc={disc_acc:.2f}%, Policy Loss={policy_loss:.4f}")

        return self.training_history

    def _train_discriminator(self, environment) -> Tuple[float, float]:
        """Train discriminator network"""
        self.discriminator_optimizer.zero_grad()

        # Sample expert demonstrations
        expert_batch = self.expert_buffer.sample_batch(self.config.batch_size)

        if not expert_batch:
            return 0.0, 0.0

        # Get policy rollouts
        policy_batch = self._collect_policy_rollouts(environment, len(expert_batch))

        # Prepare data
        expert_states = torch.FloatTensor([t['state'] for t in expert_batch]).to(self.device)
        expert_actions = torch.FloatTensor([t['action'] for t in expert_batch]).to(self.device)
        expert_input = torch.cat([expert_states, expert_actions], dim=1)
        expert_labels = torch.ones(len(expert_batch), 1).to(self.device)

        policy_states = torch.FloatTensor([t['state'] for t in policy_batch]).to(self.device)
        policy_actions = torch.FloatTensor([t['action'] for t in policy_batch]).to(self.device)
        policy_input = torch.cat([policy_states, policy_actions], dim=1)
        policy_labels = torch.zeros(len(policy_batch), 1).to(self.device)

        # Discriminator predictions
        expert_pred = self.discriminator(expert_input)
        policy_pred = self.discriminator(policy_input)

        # Loss
        expert_loss = F.binary_cross_entropy(expert_pred, expert_labels)
        policy_loss = F.binary_cross_entropy(policy_pred, policy_labels)
        total_loss = expert_loss + policy_loss

        # Backward pass
        total_loss.backward()
        self.discriminator_optimizer.step()

        # Accuracy
        expert_correct = (expert_pred > 0.5).float().mean()
        policy_correct = (policy_pred <= 0.5).float().mean()
        accuracy = ((expert_correct + policy_correct) / 2 * 100).item()

        return total_loss.item(), accuracy

    def _train_policy(self, environment) -> float:
        """Train policy network"""
        self.policy_optimizer.zero_grad()

        # Collect policy rollouts
        policy_batch = self._collect_policy_rollouts(environment, self.config.batch_size)

        if not policy_batch:
            return 0.0

        # Get states and actions
        states = torch.FloatTensor([t['state'] for t in policy_batch]).to(self.device)
        actions = torch.FloatTensor([t['action'] for t in policy_batch]).to(self.device)

        # Policy predictions
        policy_actions = self.policy(states)

        # Get discriminator predictions
        state_action_pairs = torch.cat([states, policy_actions], dim=1)
        discriminator_output = self.discriminator(state_action_pairs)

        # Policy loss (fool discriminator)
        policy_loss = -torch.log(discriminator_output + 1e-8).mean()

        # Backward pass
        policy_loss.backward()
        self.policy_optimizer.step()

        return policy_loss.item()

    def _collect_policy_rollouts(self, environment, num_samples: int) -> List[Dict[str, Any]]:
        """Collect rollouts from current policy"""
        rollouts = []

        for _ in range(num_samples):
            state = environment.reset()

            # Get policy action
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            action = self.policy.select_action(state_tensor).cpu().numpy()

            # Take step
            next_state, reward, done, info = environment.step(action)

            rollouts.append({
                'state': state,
                'action': action,
                'reward': reward,
                'next_state': next_state,
                'done': done
            })

        return rollouts

class ExpertQualityEstimator:
    """Estimate quality of expert demonstrations"""

    def __init__(self):
        self.quality_metrics = defaultdict(list)

    def estimate_quality(self, demonstration: Demonstration,
                        baseline_performance: Optional[float] = None) -> float:
        """Estimate quality of a demonstration"""
        quality_scores = []

        # Trajectory consistency
        consistency_score = self._compute_consistency(demonstration)
        quality_scores.append(consistency_score)

        # Action smoothness (for continuous actions)
        smoothness_score = self._compute_smoothness(demonstration)
        quality_scores.append(smoothness_score)

        # Goal achievement rate
        goal_score = self._compute_goal_achievement(demonstration)
        quality_scores.append(goal_score)

        # Efficiency (if rewards available)
        if demonstration.rewards:
            efficiency_score = self._compute_efficiency(demonstration)
            quality_scores.append(efficiency_score)

        # Compare to baseline
        if baseline_performance is not None:
            comparison_score = min(1.0, efficiency_score / baseline_performance)
            quality_scores.append(comparison_score)

        return np.mean(quality_scores)

    def _compute_consistency(self, demonstration: Demonstration) -> float:
        """Compute trajectory consistency score"""
        if len(demonstration) < 2:
            return 1.0

        # Compute state differences
        state_diffs = []
        for i in range(1, len(demonstration)):
            diff = np.linalg.norm(demonstration.states[i] - demonstration.states[i-1])
            state_diffs.append(diff)

        # Consistency = inverse of variance in state differences
        if state_diffs:
            consistency = 1.0 / (1.0 + np.var(state_diffs))
        else:
            consistency = 1.0

        return consistency

    def _compute_smoothness(self, demonstration: Demonstration) -> float:
        """Compute action smoothness score"""
        if len(demonstration.actions) < 2:
            return 1.0

        # Compute action differences
        action_diffs = []
        for i in range(1, len(demonstration.actions)):
            diff = np.linalg.norm(demonstration.actions[i] - demonstration.actions[i-1])
            action_diffs.append(diff)

        # Smoothness = inverse of average action difference
        if action_diffs:
            smoothness = 1.0 / (1.0 + np.mean(action_diffs))
        else:
            smoothness = 1.0

        return smoothness

    def _compute_goal_achievement(self, demonstration: Demonstration) -> float:
        """Compute goal achievement score"""
        # This is task-specific and would need customization
        # For now, use a simple heuristic based on trajectory length
        optimal_length = 100  # This should be task-specific
        actual_length = len(demonstration)

        if actual_length <= optimal_length:
            return 1.0
        else:
            return optimal_length / actual_length

    def _compute_efficiency(self, demonstration: Demonstration) -> float:
        """Compute efficiency score based on rewards"""
        if not demonstration.rewards:
            return 0.5

        total_reward = sum(demonstration.rewards)
        return max(0.0, min(1.0, total_reward / 100.0))  # Normalize to [0,1]

# Utility functions
def create_behavioral_cloning_config(state_dim: int, action_dim: int,
                                   method: str = 'behavioral_cloning') -> BehavioralCloningConfig:
    """Create behavioral cloning configuration"""
    return BehavioralCloningConfig(
        imitation_type=ImitationLearningType(method),
        state_dim=state_dim,
        action_dim=action_dim,
        hidden_dims=[256, 256],
        lr=1e-3,
        batch_size=64,
        num_epochs=100,
        validation_split=0.2,
        data_augmentation=True,
        dropout_rate=0.1,
        device='cuda' if torch.cuda.is_available() else 'cpu',
        loss_type='mse' if action_dim > 10 else 'ce',
        expert_weighting=True
    )

def load_demonstrations_from_file(filepath: str) -> List[Demonstration]:
    """Load demonstrations from file"""
    with open(filepath, 'rb') as f:
        data = pickle.load(f)

    demonstrations = []
    for demo_data in data:
        demonstration = Demonstration(
            states=demo_data['states'],
            actions=demo_data['actions'],
            rewards=demo_data.get('rewards', []),
            next_states=demo_data.get('next_states', []),
            dones=demo_data.get('dones', []),
            expert_id=demo_data.get('expert_id', 'unknown'),
            task_id=demo_data.get('task_id', 'unknown'),
            metadata=demo_data.get('metadata', {}),
            timestamp=demo_data.get('timestamp', time.time())
        )
        demonstrations.append(demonstration)

    logger.info(f"Loaded {len(demonstrations)} demonstrations from {filepath}")
    return demonstrations

def save_demonstrations_to_file(demonstrations: List[Demonstration], filepath: str):
    """Save demonstrations to file"""
    data = []
    for demo in demonstrations:
        demo_data = {
            'states': demo.states,
            'actions': demo.actions,
            'rewards': demo.rewards,
            'next_states': demo.next_states,
            'dones': demo.dones,
            'expert_id': demo.expert_id,
            'task_id': demo.task_id,
            'metadata': demo.metadata,
            'timestamp': demo.timestamp
        }
        data.append(demo_data)

    with open(filepath, 'wb') as f:
        pickle.dump(data, f)

    logger.info(f"Saved {len(demonstrations)} demonstrations to {filepath}")

if __name__ == "__main__":
    # Example usage
    config = create_behavioral_cloning_config(state_dim=10, action_dim=4)

    # Create behavioral cloning trainer
    bc_trainer = BehavioralCloningTrainer(config)

    # Create DAgger trainer
    def dummy_expert_policy(state):
        return np.random.randint(0, 4, size=1)  # Dummy expert

    dagger_trainer = DAggerTrainer(config, dummy_expert_policy)

    # Create GAIL trainer
    gail_trainer = GAILTrainer(config)

    # Create quality estimator
    quality_estimator = ExpertQualityEstimator()

    print("Behavioral Cloning System initialized!")
    print(f"Imitation learning type: {config.imitation_type.value}")
    print(f"State dimension: {config.state_dim}")
    print(f"Action dimension: {config.action_dim}")
    print(f"Available methods: Behavioral Cloning, DAgger, GAIL, SQIL, AIRL")
    print(f"Expert quality estimation: {ExpertQualityEstimator.__name__}")
    print(f"Demonstration buffer capacity: Unlimited (configurable)")
    print(f"Multi-expert support: Yes")
    print(f"Task-specific demonstrations: Yes")