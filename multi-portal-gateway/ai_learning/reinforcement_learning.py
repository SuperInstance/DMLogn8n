#!/usr/bin/env python3
"""
Advanced Reinforcement Learning Implementation
Implements state-of-the-art RL algorithms for AI agent training
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
import random
from collections import deque, namedtuple
from typing import Dict, List, Tuple, Optional, Any
import logging
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Experience tuple for replay buffer
Experience = namedtuple('Experience',
                      ['state', 'action', 'reward', 'next_state', 'done', 'info'])

@dataclass
class RLConfig:
    """Configuration for RL algorithms"""
    state_dim: int
    action_dim: int
    hidden_dims: List[int] = (256, 256)
    lr: float = 3e-4
    gamma: float = 0.99
    tau: float = 0.005
    alpha: float = 0.2
    buffer_size: int = 1000000
    batch_size: int = 256
    max_grad_norm: float = 0.5
    device: str = 'cuda'

class PrioritizedReplayBuffer:
    """Prioritized Experience Replay Buffer"""

    def __init__(self, capacity: int, alpha: float = 0.6, beta: float = 0.4):
        self.capacity = capacity
        self.alpha = alpha
        self.beta = beta
        self.beta_increment = 0.001
        self.epsilon = 1e-6

        self.buffer = []
        self.priorities = np.zeros(capacity, dtype=np.float32)
        self.position = 0
        self.size = 0

    def push(self, state, action, reward, next_state, done, info=None):
        """Add experience to buffer"""
        experience = Experience(state, action, reward, next_state, done, info)

        max_priority = self.priorities.max() if self.buffer else 1.0

        if self.size < self.capacity:
            self.buffer.append(experience)
            self.size += 1
        else:
            self.buffer[self.position] = experience

        self.priorities[self.position] = max_priority
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size: int):
        """Sample batch with priority-based sampling"""
        if self.size == 0:
            return None, None, None

        priorities = self.priorities[:self.size]
        probabilities = priorities ** self.alpha
        probabilities /= probabilities.sum()

        indices = np.random.choice(self.size, batch_size, p=probabilities)

        # Importance sampling weights
        weights = (self.size * probabilities[indices]) ** (-self.beta)
        weights /= weights.max()

        experiences = [self.buffer[idx] for idx in indices]

        self.beta = min(1.0, self.beta + self.beta_increment)

        return experiences, indices, weights

    def update_priorities(self, indices, priorities):
        """Update priorities after learning"""
        for idx, priority in zip(indices, priorities):
            self.priorities[idx] = priority + self.epsilon

    def __len__(self):
        return self.size

class NoisyLinear(nn.Module):
    """Noisy linear layer for exploration"""

    def __init__(self, in_features: int, out_features: int, std_init: float = 0.5):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.std_init = std_init

        self.weight_mu = nn.Parameter(torch.empty(out_features, in_features))
        self.weight_sigma = nn.Parameter(torch.empty(out_features, in_features))
        self.bias_mu = nn.Parameter(torch.empty(out_features))
        self.bias_sigma = nn.Parameter(torch.empty(out_features))

        self.register_buffer('weight_epsilon', torch.empty(out_features, in_features))
        self.register_buffer('bias_epsilon', torch.empty(out_features))

        self.reset_parameters()
        self.reset_noise()

    def reset_parameters(self):
        """Reset parameters"""
        mu_range = 1 / np.sqrt(self.in_features)
        self.weight_mu.data.uniform_(-mu_range, mu_range)
        self.bias_mu.data.uniform_(-mu_range, mu_range)
        self.weight_sigma.data.fill_(self.std_init * mu_range)
        self.bias_sigma.data.fill_(self.std_init * mu_range)

    def reset_noise(self):
        """Reset noise for exploration"""
        epsilon_in = self._scale_noise(self.in_features)
        epsilon_out = self._scale_noise(self.out_features)
        self.weight_epsilon.copy_(epsilon_out.ger(epsilon_in))
        self.bias_epsilon.copy_(epsilon_out)

    def _scale_noise(self, size: int):
        """Scale noise"""
        x = torch.randn(size)
        return x.sign().mul_(x.abs().sqrt_())

    def forward(self, x: torch.Tensor):
        """Forward pass with noise"""
        if self.training:
            weight = self.weight_mu + self.weight_sigma * self.weight_epsilon
            bias = self.bias_mu + self.bias_sigma * self.bias_epsilon
        else:
            weight = self.weight_mu
            bias = self.bias_mu

        return F.linear(x, weight, bias)

class DuelingNetwork(nn.Module):
    """Dueling DQN architecture"""

    def __init__(self, state_dim: int, action_dim: int, hidden_dims: Tuple[int]):
        super().__init__()

        # Shared feature layers
        layers = []
        input_dim = state_dim

        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.1)
            ])
            input_dim = hidden_dim

        self.feature_layer = nn.Sequential(*layers)

        # Value stream
        self.value_stream = nn.Sequential(
            nn.Linear(input_dim, hidden_dims[-1]),
            nn.ReLU(),
            nn.Linear(hidden_dims[-1], 1)
        )

        # Advantage stream
        self.advantage_stream = nn.Sequential(
            nn.Linear(input_dim, hidden_dims[-1]),
            nn.ReLU(),
            nn.Linear(hidden_dims[-1], action_dim)
        )

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        features = self.feature_layer(state)
        values = self.value_stream(features)
        advantages = self.advantage_stream(features)

        # Dueling architecture: Q = V + (A - mean(A))
        q_values = values + (advantages - advantages.mean(dim=1, keepdim=True))
        return q_values

class RainbowDQN(nn.Module):
    """Rainbow DQN with multiple improvements"""

    def __init__(self, state_dim: int, action_dim: int, config: RLConfig):
        super().__init__()
        self.config = config

        # Use noisy layers for exploration
        self.layers = nn.ModuleList()

        # Input layer
        self.layers.append(NoisyLinear(state_dim, config.hidden_dims[0]))

        # Hidden layers
        for i in range(len(config.hidden_dims) - 1):
            self.layers.append(NoisyLinear(config.hidden_dims[i], config.hidden_dims[i + 1]))

        # Output layer
        self.layers.append(NoisyLinear(config.hidden_dims[-1], action_dim))

        # Distributional RL support
        self.support = torch.linspace(-10, 10, 51).to(config.device)
        self.num_atoms = len(self.support)

        # Distributional layers
        dist_layers = []
        input_dim = state_dim
        for hidden_dim in config.hidden_dims:
            dist_layers.extend([
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU()
            ])
            input_dim = hidden_dim
        dist_layers.append(nn.Linear(input_dim, action_dim * self.num_atoms))

        self.dist_layers = nn.Sequential(*dist_layers)

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        x = state
        for i, layer in enumerate(self.layers[:-1]):
            x = F.relu(layer(x))
        return self.layers[-1](x)

    def forward_dist(self, state: torch.Tensor) -> torch.Tensor:
        """Distributional forward pass"""
        x = self.dist_layers(state)
        x = x.view(-1, self.config.action_dim, self.num_atoms)
        return F.softmax(x, dim=-1)

    def reset_noise(self):
        """Reset noise in all noisy layers"""
        for layer in self.layers:
            if hasattr(layer, 'reset_noise'):
                layer.reset_noise()

class ActorCriticNetwork(nn.Module):
    """Actor-Critic network for PPO/SAC"""

    def __init__(self, state_dim: int, action_dim: int, config: RLConfig, discrete: bool = False):
        super().__init__()
        self.config = config
        self.discrete = discrete

        # Shared layers
        layers = []
        input_dim = state_dim

        for hidden_dim in config.hidden_dims:
            layers.extend([
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.1)
            ])
            input_dim = hidden_dim

        self.shared_layers = nn.Sequential(*layers)

        # Actor head (policy)
        if discrete:
            self.actor_head = nn.Sequential(
                nn.Linear(input_dim, action_dim),
                nn.Softmax(dim=-1)
            )
        else:
            self.actor_head = nn.Sequential(
                nn.Linear(input_dim, action_dim),
                nn.Tanh()
            )

        # Critic head (value function)
        self.critic_head = nn.Linear(input_dim, 1)

    def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass"""
        features = self.shared_layers(state)
        policy = self.actor_head(features)
        value = self.critic_head(features)
        return policy, value

class PPOAgent:
    """Proximal Policy Optimization Agent"""

    def __init__(self, config: RLConfig, discrete: bool = False):
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Networks
        self.network = ActorCriticNetwork(config.state_dim, config.action_dim, config, discrete).to(self.device)
        self.optimizer = optim.Adam(self.network.parameters(), lr=config.lr)

        # PPO hyperparameters
        self.clip_epsilon = 0.2
        self.entropy_coef = 0.01
        self.value_coef = 0.5
        self.max_grad_norm = config.max_grad_norm

        # Storage for trajectories
        self.states = []
        self.actions = []
        self.rewards = []
        self.log_probs = []
        self.values = []
        self.dones = []
        self.advantages = []
        self.returns = []

    def select_action(self, state: np.ndarray, training: bool = True) -> Tuple[np.ndarray, float]:
        """Select action using policy"""
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)

        with torch.no_grad():
            policy, value = self.network(state_tensor)

        if self.network.discrete:
            action_dist = torch.distributions.Categorical(policy)
            action = action_dist.sample()
            log_prob = action_dist.log_prob(action)
            action = action.cpu().numpy()
        else:
            action_dist = torch.distributions.Normal(policy, torch.exp(self.network.log_std))
            action = action_dist.sample()
            log_prob = action_dist.log_prob(action).sum(dim=-1)
            action = action.cpu().numpy()

        if not training:
            if not self.network.discrete:
                action = policy.cpu().numpy()
            else:
                action = torch.argmax(policy, dim=-1).cpu().numpy()

        return action, log_prob.item() if training else 0.0

    def store_transition(self, state, action, reward, next_state, done, log_prob, value):
        """Store transition for PPO update"""
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.dones.append(done)
        self.log_probs.append(log_prob)
        self.values.append(value)

    def compute_returns_and_advantages(self, next_value: float = 0.0):
        """Compute returns and advantages using GAE"""
        returns = []
        advantages = []

        # Add bootstrap value
        values = self.values + [next_value]

        gae = 0
        for i in reversed(range(len(self.rewards))):
            delta = self.rewards[i] + self.config.gamma * values[i + 1] * (1 - self.dones[i]) - values[i]
            gae = delta + self.config.gamma * 0.95 * (1 - self.dones[i]) * gae
            advantages.insert(0, gae)
            returns.insert(0, gae + values[i])

        self.advantages = advantages
        self.returns = returns

    def update(self, epochs: int = 10, batch_size: int = 64):
        """Update PPO agent"""
        if len(self.states) == 0:
            return

        # Convert to tensors
        states = torch.FloatTensor(np.array(self.states)).to(self.device)
        actions = torch.FloatTensor(np.array(self.actions)).to(self.device)
        old_log_probs = torch.FloatTensor(self.log_probs).to(self.device)
        old_values = torch.FloatTensor(self.values).to(self.device)
        returns = torch.FloatTensor(self.returns).to(self.device)
        advantages = torch.FloatTensor(self.advantages).to(self.device)

        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        # PPO update
        for epoch in range(epochs):
            # Create mini-batches
            indices = torch.randperm(len(states))

            for start in range(0, len(states), batch_size):
                end = start + batch_size
                batch_indices = indices[start:end]

                batch_states = states[batch_indices]
                batch_actions = actions[batch_indices]
                batch_old_log_probs = old_log_probs[batch_indices]
                batch_old_values = old_values[batch_indices]
                batch_returns = returns[batch_indices]
                batch_advantages = advantages[batch_indices]

                # Forward pass
                policy, values = self.network(batch_states)

                # Calculate log probabilities
                if self.network.discrete:
                    action_dist = torch.distributions.Categorical(policy)
                    new_log_probs = action_dist.log_prob(batch_actions.long())
                    entropy = action_dist.entropy().mean()
                else:
                    action_dist = torch.distributions.Normal(policy, torch.exp(self.network.log_std))
                    new_log_probs = action_dist.log_prob(batch_actions).sum(dim=-1)
                    entropy = action_dist.entropy().sum(dim=-1).mean()

                # Policy loss (clipped surrogate objective)
                ratio = torch.exp(new_log_probs - batch_old_log_probs)
                surr1 = ratio * batch_advantages
                surr2 = torch.clamp(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon) * batch_advantages
                policy_loss = -torch.min(surr1, surr2).mean()

                # Value loss
                value_loss = F.mse_loss(values.squeeze(), batch_returns)

                # Total loss
                loss = policy_loss + self.value_coef * value_loss - self.entropy_coef * entropy

                # Optimization step
                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.network.parameters(), self.max_grad_norm)
                self.optimizer.step()

        # Clear storage
        self.clear_storage()

    def clear_storage(self):
        """Clear trajectory storage"""
        self.states.clear()
        self.actions.clear()
        self.rewards.clear()
        self.log_probs.clear()
        self.values.clear()
        self.dones.clear()
        self.advantages.clear()
        self.returns.clear()

class SACAgent:
    """Soft Actor-Critic Agent"""

    def __init__(self, config: RLConfig):
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Networks
        self.actor = ActorCriticNetwork(config.state_dim, config.action_dim, config, discrete=False).to(self.device)
        self.critic1 = ActorCriticNetwork(config.state_dim, config.action_dim, config, discrete=False).to(self.device)
        self.critic2 = ActorCriticNetwork(config.state_dim, config.action_dim, config, discrete=False).to(self.device)
        self.critic1_target = ActorCriticNetwork(config.state_dim, config.action_dim, config, discrete=False).to(self.device)
        self.critic2_target = ActorCriticNetwork(config.state_dim, config.action_dim, config, discrete=False).to(self.device)

        # Initialize target networks
        self.critic1_target.load_state_dict(self.critic1.state_dict())
        self.critic2_target.load_state_dict(self.critic2.state_dict())

        # Optimizers
        self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=config.lr)
        self.critic1_optimizer = optim.Adam(self.critic1.parameters(), lr=config.lr)
        self.critic2_optimizer = optim.Adam(self.critic2.parameters(), lr=config.lr)

        # SAC parameters
        self.log_alpha = torch.tensor(np.log(config.alpha), requires_grad=True, device=self.device)
        self.alpha_optimizer = optim.Adam([self.log_alpha], lr=config.lr)
        self.target_entropy = -config.action_dim  # Target entropy

        # Replay buffer
        self.replay_buffer = PrioritizedReplayBuffer(config.buffer_size)

        # Log std for continuous actions
        self.actor.log_std = nn.Parameter(torch.zeros(config.action_dim))

    def select_action(self, state: np.ndarray, training: bool = True) -> np.ndarray:
        """Select action using policy"""
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)

        with torch.no_grad():
            policy, _ = self.actor(state_tensor)

        if training:
            # Add exploration noise
            noise = torch.randn_like(policy) * 0.1
            action = torch.clamp(policy + noise, -1, 1)
        else:
            action = policy

        return action.cpu().numpy()

    def store_transition(self, state, action, reward, next_state, done):
        """Store transition in replay buffer"""
        self.replay_buffer.push(state, action, reward, next_state, done)

    def update(self, batch_size: Optional[int] = None):
        """Update SAC agent"""
        if len(self.replay_buffer) < (batch_size or self.config.batch_size):
            return

        batch_size = batch_size or self.config.batch_size

        # Sample from replay buffer
        experiences, indices, weights = self.replay_buffer.sample(batch_size)
        if experiences is None:
            return

        # Convert to tensors
        states = torch.FloatTensor([e.state for e in experiences]).to(self.device)
        actions = torch.FloatTensor([e.action for e in experiences]).to(self.device)
        rewards = torch.FloatTensor([e.reward for e in experiences]).to(self.device)
        next_states = torch.FloatTensor([e.next_state for e in experiences]).to(self.device)
        dones = torch.FloatTensor([e.done for e in experiences]).to(self.device)
        weights = torch.FloatTensor(weights).to(self.device)

        # Update critic networks
        with torch.no_grad():
            next_policy, _ = self.actor(next_states)
            next_action = torch.clamp(next_policy + torch.randn_like(next_policy) * 0.1, -1, 1)

            next_q1, _ = self.critic1_target(next_states)
            next_q2, _ = self.critic2_target(next_states)
            next_q = torch.min(next_q1, next_q2)

            target_q = rewards + (1 - dones) * self.config.gamma * next_q

        # Current Q values
        current_q1, _ = self.critic1(states)
        current_q2, _ = self.critic2(states)

        # Get Q values for taken actions
        current_q1 = current_q1.gather(1, actions.long().unsqueeze(-1)).squeeze(-1)
        current_q2 = current_q2.gather(1, actions.long().unsqueeze(-1)).squeeze(-1)

        # Critic losses
        critic1_loss = (weights * F.mse_loss(current_q1, target_q, reduction='none')).mean()
        critic2_loss = (weights * F.mse_loss(current_q2, target_q, reduction='none')).mean()

        # Update critics
        self.critic1_optimizer.zero_grad()
        critic1_loss.backward()
        self.critic1_optimizer.step()

        self.critic2_optimizer.zero_grad()
        critic2_loss.backward()
        self.critic2_optimizer.step()

        # Update actor
        policy, _ = self.actor(states)
        q1, _ = self.critic1(states)
        q2, _ = self.critic2(states)
        q = torch.min(q1, q2)

        actor_loss = (self.log_alpha.exp() * policy.log() - q).mean()

        self.actor_optimizer.zero_grad()
        actor_loss.backward()
        self.actor_optimizer.step()

        # Update alpha
        alpha_loss = -(self.log_alpha.exp() * (policy.log() + self.target_entropy).detach()).mean()

        self.alpha_optimizer.zero_grad()
        alpha_loss.backward()
        self.alpha_optimizer.step()

        # Update target networks
        for target_param, param in zip(self.critic1_target.parameters(), self.critic1.parameters()):
            target_param.data.copy_(self.config.tau * param.data + (1 - self.config.tau) * target_param.data)

        for target_param, param in zip(self.critic2_target.parameters(), self.critic2.parameters()):
            target_param.data.copy_(self.config.tau * param.data + (1 - self.config.tau) * target_param.data)

        # Update priorities
        td_errors = torch.abs(current_q1 - target_q).detach().cpu().numpy()
        self.replay_buffer.update_priorities(indices, td_errors)

class RainbowDQNAgent:
    """Rainbow DQN Agent"""

    def __init__(self, config: RLConfig):
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Networks
        self.q_network = RainbowDQN(config.state_dim, config.action_dim, config).to(self.device)
        self.target_network = RainbowDQN(config.state_dim, config.action_dim, config).to(self.device)
        self.target_network.load_state_dict(self.q_network.state_dict())

        # Optimizer
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=config.lr)

        # Replay buffer
        self.replay_buffer = PrioritizedReplayBuffer(config.buffer_size)

        # Training parameters
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.update_target_every = 1000
        self.steps = 0

    def select_action(self, state: np.ndarray, training: bool = True) -> int:
        """Select action using epsilon-greedy or noisy network"""
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)

        if training and random.random() < self.epsilon:
            return random.randint(0, self.config.action_dim - 1)

        with torch.no_grad():
            q_values = self.q_network(state_tensor)
            return q_values.argmax().item()

    def store_transition(self, state, action, reward, next_state, done):
        """Store transition in replay buffer"""
        self.replay_buffer.push(state, action, reward, next_state, done)

    def update(self, batch_size: Optional[int] = None):
        """Update Rainbow DQN agent"""
        if len(self.replay_buffer) < (batch_size or self.config.batch_size):
            return

        batch_size = batch_size or self.config.batch_size

        # Sample from replay buffer
        experiences, indices, weights = self.replay_buffer.sample(batch_size)
        if experiences is None:
            return

        # Convert to tensors
        states = torch.FloatTensor([e.state for e in experiences]).to(self.device)
        actions = torch.LongTensor([e.action for e in experiences]).to(self.device)
        rewards = torch.FloatTensor([e.reward for e in experiences]).to(self.device)
        next_states = torch.FloatTensor([e.next_state for e in experiences]).to(self.device)
        dones = torch.FloatTensor([e.done for e in experiences]).to(self.device)
        weights = torch.FloatTensor(weights).to(self.device)

        # Double DQN target
        with torch.no_grad():
            next_actions = self.q_network(next_states).argmax(dim=1)
            next_q_values = self.target_network(next_states).gather(1, next_actions.unsqueeze(-1)).squeeze(-1)
            target_q_values = rewards + (1 - dones) * self.config.gamma * next_q_values

        # Current Q values
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(-1)).squeeze(-1)

        # TD errors for priority update
        td_errors = torch.abs(current_q_values - target_q_values).detach().cpu().numpy()

        # Loss with importance sampling weights
        loss = (weights * F.mse_loss(current_q_values, target_q_values, reduction='none')).mean()

        # Optimization
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), self.config.max_grad_norm)
        self.optimizer.step()

        # Update priorities
        self.replay_buffer.update_priorities(indices, td_errors)

        # Update target network
        self.steps += 1
        if self.steps % self.update_target_every == 0:
            self.target_network.load_state_dict(self.q_network.state_dict())

        # Decay epsilon
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

        # Reset noise
        self.q_network.reset_noise()

class RLTrainer:
    """Unified RL training interface"""

    def __init__(self, algorithm: str, config: RLConfig, **kwargs):
        self.algorithm = algorithm
        self.config = config

        # Initialize agent based on algorithm
        if algorithm == 'ppo':
            self.agent = PPOAgent(config, discrete=kwargs.get('discrete', False))
        elif algorithm == 'sac':
            self.agent = SACAgent(config)
        elif algorithm == 'rainbow_dqn':
            self.agent = RainbowDQNAgent(config)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

        # Training metrics
        self.episode_rewards = []
        self.losses = []
        self.steps = 0

    def train_episode(self, env, max_steps: int = 1000) -> float:
        """Train for one episode"""
        state = env.reset()
        episode_reward = 0
        done = False

        for step in range(max_steps):
            # Select action
            action, log_prob, value = 0, 0, 0
            if self.algorithm == 'ppo':
                action, log_prob = self.agent.select_action(state, training=True)
                _, value = self.agent.network(torch.FloatTensor(state).unsqueeze(0).to(self.agent.device))
                value = value.item()
            else:
                action = self.agent.select_action(state, training=True)

            # Take step
            next_state, reward, done, info = env.step(action)
            episode_reward += reward

            # Store transition
            if self.algorithm == 'ppo':
                self.agent.store_transition(state, action, reward, next_state, done, log_prob, value)
            else:
                self.agent.store_transition(state, action, reward, next_state, done)

            # Update agent
            if self.algorithm in ['sac', 'rainbow_dqn']:
                self.agent.update()

            state = next_state
            self.steps += 1

            if done:
                break

        # PPO update at episode end
        if self.algorithm == 'ppo':
            self.agent.compute_returns_and_advantages()
            self.agent.update()

        self.episode_rewards.append(episode_reward)
        return episode_reward

    def evaluate(self, env, num_episodes: int = 10) -> Dict[str, float]:
        """Evaluate agent performance"""
        total_rewards = []

        for _ in range(num_episodes):
            state = env.reset()
            episode_reward = 0
            done = False

            while not done:
                action, _, _ = 0, 0, 0
                if self.algorithm == 'ppo':
                    action, _ = self.agent.select_action(state, training=False)
                else:
                    action = self.agent.select_action(state, training=False)

                state, reward, done, _ = env.step(action)
                episode_reward += reward

            total_rewards.append(episode_reward)

        return {
            'mean_reward': np.mean(total_rewards),
            'std_reward': np.std(total_rewards),
            'min_reward': np.min(total_rewards),
            'max_reward': np.max(total_rewards)
        }

    def save_model(self, filepath: str):
        """Save model checkpoint"""
        torch.save({
            'agent_state_dict': self.agent.__dict__,
            'config': self.config,
            'algorithm': self.algorithm,
            'episode_rewards': self.episode_rewards,
            'steps': self.steps
        }, filepath)
        logger.info(f"Model saved to {filepath}")

    def load_model(self, filepath: str):
        """Load model checkpoint"""
        checkpoint = torch.load(filepath, map_location=self.agent.device)
        self.agent.__dict__.update(checkpoint['agent_state_dict'])
        self.episode_rewards = checkpoint['episode_rewards']
        self.steps = checkpoint['steps']
        logger.info(f"Model loaded from {filepath}")

# Utility functions for distributed training
class DistributedRLTrainer:
    """Distributed RL training across multiple GPUs/nodes"""

    def __init__(self, algorithm: str, config: RLConfig, world_size: int = 1):
        self.algorithm = algorithm
        self.config = config
        self.world_size = world_size

        # Initialize distributed training if multiple GPUs
        if world_size > 1 and torch.cuda.is_available():
            self._init_distributed()

        # Create agents for each worker
        self.agents = []
        for i in range(world_size):
            agent_config = RLConfig(**config.__dict__)
            agent_config.device = f'cuda:{i}' if torch.cuda.is_available() else 'cpu'

            if algorithm == 'ppo':
                agent = PPOAgent(agent_config)
            elif algorithm == 'sac':
                agent = SACAgent(agent_config)
            elif algorithm == 'rainbow_dqn':
                agent = RainbowDQNAgent(agent_config)

            self.agents.append(agent)

    def _init_distributed(self):
        """Initialize distributed training"""
        if not torch.distributed.is_initialized():
            torch.distributed.init_process_group(backend='nccl')

    def train_distributed(self, envs, sync_frequency: int = 100):
        """Train agents in distributed manner"""
        # Implementation for distributed training
        # This would involve gradient synchronization across workers
        pass

# Factory function for creating agents
def create_rl_agent(algorithm: str, config: RLConfig, **kwargs) -> Any:
    """Factory function to create RL agents"""
    trainer = RLTrainer(algorithm, config, **kwargs)
    return trainer.agent

# Performance monitoring
class PerformanceMonitor:
    """Monitor and log training performance"""

    def __init__(self):
        self.metrics = {
            'episode_rewards': [],
            'losses': [],
            'q_values': [],
            'entropy': [],
            'exploration_rate': []
        }

    def log_metrics(self, **kwargs):
        """Log training metrics"""
        for key, value in kwargs.items():
            if key in self.metrics:
                self.metrics[key].append(value)

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        summary = {}
        for key, values in self.metrics.items():
            if values:
                summary[key] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'latest': values[-1]
                }
        return summary

if __name__ == "__main__":
    # Example usage
    config = RLConfig(
        state_dim=10,
        action_dim=4,
        hidden_dims=(256, 256),
        lr=3e-4,
        device='cuda' if torch.cuda.is_available() else 'cpu'
    )

    # Create PPO agent
    ppo_trainer = RLTrainer('ppo', config, discrete=True)
    logger.info("PPO Agent created successfully")

    # Create SAC agent
    sac_trainer = RLTrainer('sac', config)
    logger.info("SAC Agent created successfully")

    # Create Rainbow DQN agent
    rainbow_trainer = RLTrainer('rainbow_dqn', config)
    logger.info("Rainbow DQN Agent created successfully")

    print("Advanced Reinforcement Learning System initialized!")
    print(f"Available algorithms: PPO, SAC, Rainbow DQN")
    print(f"Device: {config.device}")
    print(f"State dimension: {config.state_dim}")
    print(f"Action dimension: {config.action_dim}")