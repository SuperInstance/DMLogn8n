"""
Advanced Reinforcement Learning for DMLogn8n
Cutting-edge RL algorithms with novel exploration strategies and optimization techniques
Based on latest research in deep reinforcement learning (2024-2025)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from collections import deque, namedtuple
import random
import math
from abc import ABC, abstractmethod
import gymnasium as gym
from gymnasium import spaces
import matplotlib.pyplot as plt
from tqdm import tqdm


@dataclass
class RLConfig:
    """Configuration for reinforcement learning algorithms"""
    # Environment
    state_dim: int = 512
    action_dim: int = 100
    max_action: float = 1.0

    # Network architecture
    hidden_dim: int = 512
    num_layers: int = 3
    activation: str = "relu"
    use_layer_norm: bool = True

    # Training parameters
    batch_size: int = 256
    learning_rate: float = 3e-4
    gamma: float = 0.99
    tau: float = 0.005  # For soft updates

    # Algorithm-specific
    buffer_size: int = 1000000
    exploration_noise: float = 0.1
    policy_noise: float = 0.2
    noise_clip: float = 0.5
    policy_update_freq: int = 2

    # Advanced features
    use_prioritized_replay: bool = True
    use_distributional_rl: bool = False
    use_curiosity: bool = True
    use_hindsight: bool = False
    use_curriculum: bool = True


class ReplayBuffer:
    """Advanced replay buffer with prioritization and support for various experiences"""
    def __init__(self, config: RLConfig):
        self.config = config
        self.buffer_size = config.buffer_size
        self.batch_size = config.batch_size

        # Basic buffer
        self.states = deque(maxlen=self.buffer_size)
        self.actions = deque(maxlen=self.buffer_size)
        self.rewards = deque(maxlen=self.buffer_size)
        self.next_states = deque(maxlen=self.buffer_size)
        self.dones = deque(maxlen=self.buffer_size)

        # Prioritized replay
        if config.use_prioritized_replay:
            self.priorities = deque(maxlen=self.buffer_size)
            self.alpha = 0.6
            self.beta = 0.4
            self.max_priority = 1.0

        # Hindsight experience replay
        if config.use_hindsight:
            self.hindsight_buffer = []

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def add(self, state: np.ndarray, action: np.ndarray, reward: float,
            next_state: np.ndarray, done: bool, info: Optional[Dict] = None):
        """Add experience to buffer"""
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.next_states.append(next_state)
        self.dones.append(done)

        if self.config.use_prioritized_replay:
            self.priorities.append(self.max_priority)

        # Store hindsight goals if available
        if self.config.use_hindsight and info and 'goal' in info:
            self.hindsight_buffer.append({
                'state': state,
                'action': action,
                'goal': info['goal'],
                'achieved_goal': info.get('achieved_goal', state)
            })

    def sample(self) -> Dict[str, torch.Tensor]:
        """Sample batch from buffer"""
        batch_size = min(self.batch_size, len(self.states))

        if self.config.use_prioritized_replay:
            # Prioritized sampling
            priorities = np.array(self.priorities)
            probabilities = priorities ** self.alpha
            probabilities /= probabilities.sum()

            indices = np.random.choice(
                len(self.states), batch_size, p=probabilities, replace=False
            )

            # Importance sampling weights
            weights = (len(self.states) * probabilities[indices]) ** (-self.beta)
            weights /= weights.max()

            batch_indices = indices
            is_weights = torch.tensor(weights, dtype=torch.float32, device=self.device)
        else:
            # Uniform sampling
            batch_indices = np.random.choice(len(self.states), batch_size, replace=False)
            is_weights = torch.ones(batch_size, device=self.device)

        # Gather samples
        states = np.array([self.states[i] for i in batch_indices])
        actions = np.array([self.actions[i] for i in batch_indices])
        rewards = np.array([self.rewards[i] for i in batch_indices])
        next_states = np.array([self.next_states[i] for i in batch_indices])
        dones = np.array([self.dones[i] for i in batch_indices])

        return {
            'states': torch.tensor(states, dtype=torch.float32, device=self.device),
            'actions': torch.tensor(actions, dtype=torch.float32, device=self.device),
            'rewards': torch.tensor(rewards, dtype=torch.float32, device=self.device),
            'next_states': torch.tensor(next_states, dtype=torch.float32, device=self.device),
            'dones': torch.tensor(dones, dtype=torch.float32, device=self.device),
            'indices': batch_indices,
            'weights': is_weights
        }

    def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray):
        """Update priorities for sampled indices"""
        if self.config.use_prioritized_replay:
            for idx, error in zip(indices, td_errors):
                priority = abs(error) + 1e-6
                self.priorities[idx] = priority
                self.max_priority = max(self.max_priority, priority)

    def __len__(self):
        return len(self.states)


class NoisyLinear(nn.Module):
    """Noisy linear layer for exploration"""
    def __init__(self, in_features: int, out_features: int, sigma_init: float = 0.017):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.sigma_init = sigma_init

        # Weight parameters
        self.weight_mu = nn.Parameter(torch.Tensor(out_features, in_features))
        self.weight_sigma = nn.Parameter(torch.Tensor(out_features, in_features))

        # Bias parameters
        self.bias_mu = nn.Parameter(torch.Tensor(out_features))
        self.bias_sigma = nn.Parameter(torch.Tensor(out_features))

        # Noise buffers
        self.register_buffer('weight_epsilon', torch.Tensor(out_features, in_features))
        self.register_buffer('bias_epsilon', torch.Tensor(out_features))

        self.reset_parameters()
        self.reset_noise()

    def reset_parameters(self):
        mu_range = 1 / math.sqrt(self.in_features)
        self.weight_mu.data.uniform_(-mu_range, mu_range)
        self.bias_mu.data.uniform_(-mu_range, mu_range)

        self.weight_sigma.data.fill_(self.sigma_init)
        self.bias_sigma.data.fill_(self.sigma_init)

    def reset_noise(self):
        epsilon_in = self._scale_noise(self.in_features)
        epsilon_out = self._scale_noise(self.out_features)

        self.weight_epsilon.copy_(epsilon_out.ger(epsilon_in))
        self.bias_epsilon.copy_(epsilon_out)

    def _scale_noise(self, size: int) -> torch.Tensor:
        x = torch.randn(size)
        return x.sign().mul_(x.abs().sqrt_())

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if self.training:
            weight = self.weight_mu + self.weight_sigma * self.weight_epsilon
            bias = self.bias_mu + self.bias_sigma * self.bias_epsilon
        else:
            weight = self.weight_mu
            bias = self.bias_mu

        return F.linear(x, weight, bias)


class MLPNetwork(nn.Module):
    """Multi-layer perceptron with various activation functions"""
    def __init__(self, input_dim: int, output_dim: int, hidden_dim: int = 256,
                 num_layers: int = 2, activation: str = "relu",
                 use_layer_norm: bool = True, noisy: bool = False):
        super().__init__()

        layers = []
        in_dim = input_dim

        # Hidden layers
        for i in range(num_layers):
            out_dim = hidden_dim

            if noisy:
                layer = NoisyLinear(in_dim, out_dim)
            else:
                layer = nn.Linear(in_dim, out_dim)

            layers.append(layer)

            if use_layer_norm:
                layers.append(nn.LayerNorm(out_dim))

            # Activation function
            if activation == "relu":
                layers.append(nn.ReLU())
            elif activation == "gelu":
                layers.append(nn.GELU())
            elif activation == "tanh":
                layers.append(nn.Tanh())
            elif activation == "swish":
                layers.append(nn.SiLU())

            in_dim = out_dim

        # Output layer
        if noisy:
            layers.append(NoisyLinear(in_dim, output_dim))
        else:
            layers.append(nn.Linear(in_dim, output_dim))

        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)


class CuriosityModule(nn.Module):
    """Curiosity-driven exploration using forward dynamics models"""
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 256):
        super().__init__()

        # Feature encoder
        self.feature_encoder = MLPNetwork(
            state_dim, hidden_dim, hidden_dim//2, 2, "relu", False
        )

        # Forward model (predict next state features)
        self.forward_model = MLPNetwork(
            hidden_dim + action_dim, hidden_dim, hidden_dim, 2, "relu", False
        )

        # Inverse model (predict action from state transitions)
        self.inverse_model = MLPNetwork(
            hidden_dim * 2, action_dim, hidden_dim, 2, "relu", False
        )

    def forward(self, state: torch.Tensor, action: torch.Tensor,
                next_state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        # Encode states
        state_features = self.feature_encoder(state)
        next_state_features = self.feature_encoder(next_state)

        # Forward prediction
        forward_input = torch.cat([state_features, action], dim=-1)
        predicted_next_features = self.forward_model(forward_input)

        # Inverse prediction
        inverse_input = torch.cat([state_features, next_state_features], dim=-1)
        predicted_action = self.inverse_model(inverse_input)

        # Intrinsic reward (prediction error)
        intrinsic_reward = F.mse_loss(predicted_next_features, next_state_features, reduction='none')
        intrinsic_reward = intrinsic_reward.mean(dim=-1)

        return intrinsic_reward, predicted_action


class DistributionalQNetwork(nn.Module):
    """Distributional Q-Network for better value approximation"""
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 256,
                 num_atoms: int = 51, v_min: float = -10.0, v_max: float = 10.0):
        super().__init__()

        self.action_dim = action_dim
        self.num_atoms = num_atoms
        self.v_min = v_min
        self.v_max = v_max

        # Network
        self.feature_net = MLPNetwork(state_dim, hidden_dim, hidden_dim, 2, "relu", False)

        # Value distribution heads for each action
        self.value_heads = nn.ModuleList([
            nn.Linear(hidden_dim, num_atoms) for _ in range(action_dim)
        ])

        # Support vector (value atoms)
        self.register_buffer('support', torch.linspace(v_min, v_max, num_atoms))

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        features = self.feature_net(state)

        # Get distribution for each action
        distributions = []
        for head in self.value_heads:
            dist = head(features)
            dist = F.softmax(dist, dim=-1)
            distributions.append(dist)

        return torch.stack(distributions, dim=1)  # [batch, action, atoms]

    def get_q_values(self, state: torch.Tensor) -> torch.Tensor:
        """Get Q values from distribution"""
        dist = self.forward(state)
        q_values = torch.sum(dist * self.support, dim=-1)
        return q_values


class TD3Agent:
    """Twin Delayed Deep Deterministic Policy Gradient with enhancements"""
    def __init__(self, config: RLConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Actor network
        self.actor = MLPNetwork(
            config.state_dim, config.action_dim, config.hidden_dim,
            config.num_layers, config.activation, config.use_layer_norm
        ).to(self.device)

        # Critic networks (twin critics)
        self.critic1 = MLPNetwork(
            config.state_dim + config.action_dim, 1, config.hidden_dim,
            config.num_layers, config.activation, config.use_layer_norm
        ).to(self.device)

        self.critic2 = MLPNetwork(
            config.state_dim + config.action_dim, 1, config.hidden_dim,
            config.num_layers, config.activation, config.use_layer_norm
        ).to(self.device)

        # Target networks
        self.actor_target = MLPNetwork(
            config.state_dim, config.action_dim, config.hidden_dim,
            config.num_layers, config.activation, config.use_layer_norm
        ).to(self.device)

        self.critic1_target = MLPNetwork(
            config.state_dim + config.action_dim, 1, config.hidden_dim,
            config.num_layers, config.activation, config.use_layer_norm
        ).to(self.device)

        self.critic2_target = MLPNetwork(
            config.state_dim + config.action_dim, 1, config.hidden_dim,
            config.num_layers, config.activation, config.use_layer_norm
        ).to(self.device)

        # Copy weights to target networks
        self._copy_weights(self.actor, self.actor_target)
        self._copy_weights(self.critic1, self.critic1_target)
        self._copy_weights(self.critic2, self.critic2_target)

        # Optimizers
        self.actor_optimizer = torch.optim.Adam(self.actor.parameters(), lr=config.learning_rate)
        self.critic1_optimizer = torch.optim.Adam(self.critic1.parameters(), lr=config.learning_rate)
        self.critic2_optimizer = torch.optim.Adam(self.critic2.parameters(), lr=config.learning_rate)

        # Experience replay
        self.replay_buffer = ReplayBuffer(config)

        # Curiosity module
        if config.use_curiosity:
            self.curiosity = CuriosityModule(config.state_dim, config.action_dim, config.hidden_dim)
            self.curiosity_optimizer = torch.optim.Adam(self.curiosity.parameters(), lr=config.learning_rate)

        # Training parameters
        self.total_steps = 0
        self.policy_update_freq = config.policy_update_freq

    def _copy_weights(self, source: nn.Module, target: nn.Module):
        """Copy weights from source to target network"""
        target.load_state_dict(source.state_dict())

    def _soft_update(self, source: nn.Module, target: nn.Module, tau: float):
        """Soft update of target network"""
        for target_param, source_param in zip(target.parameters(), source.parameters()):
            target_param.data.copy_(tau * source_param.data + (1 - tau) * target_param.data)

    def select_action(self, state: np.ndarray, noise: float = None) -> np.ndarray:
        """Select action with optional exploration noise"""
        state_tensor = torch.tensor(state, dtype=torch.float32, device=self.device).unsqueeze(0)

        with torch.no_grad():
            action = self.actor(state_tensor).cpu().numpy().flatten()

        if noise is None:
            noise = self.config.exploration_noise

        # Add exploration noise
        action += np.random.normal(0, noise, size=action.shape)
        action = np.clip(action, -self.config.max_action, self.config.max_action)

        return action

    def train_step(self) -> Dict[str, float]:
        """Single training step"""
        if len(self.replay_buffer) < self.config.batch_size:
            return {}

        # Sample from replay buffer
        batch = self.replay_buffer.sample()
        states = batch['states']
        actions = batch['actions']
        rewards = batch['rewards']
        next_states = batch['next_states']
        dones = batch['dones']
        weights = batch['weights']
        indices = batch['indices']

        # Compute target Q values
        with torch.no_grad():
            # Target policy smoothing
            noise = torch.randn_like(actions) * self.config.policy_noise
            noise = torch.clamp(noise, -self.config.noise_clip, self.config.noise_clip)

            next_actions = self.actor_target(next_states) + noise
            next_actions = torch.clamp(next_actions, -self.config.max_action, self.config.max_action)

            # Target Q values
            target_q1 = self.critic1_target(next_states, next_actions)
            target_q2 = self.critic2_target(next_states, next_actions)
            target_q = torch.min(target_q1, target_q2)

            target_q = rewards + (1 - dones) * self.config.gamma * target_q

        # Compute current Q values
        current_q1 = self.critic1(states, actions)
        current_q2 = self.critic2(states, actions)

        # Compute critic losses
        critic1_loss = F.mse_loss(current_q1, target_q)
        critic2_loss = F.mse_loss(current_q2, target_q)

        # Update critics
        self.critic1_optimizer.zero_grad()
        critic1_loss.backward()
        self.critic1_optimizer.step()

        self.critic2_optimizer.zero_grad()
        critic2_loss.backward()
        self.critic2_optimizer.step()

        # Update actor and target networks
        actor_loss = 0
        if self.total_steps % self.policy_update_freq == 0:
            # Compute actor loss
            actor_loss = -self.critic1(states, self.actor(states)).mean()

            self.actor_optimizer.zero_grad()
            actor_loss.backward()
            self.actor_optimizer.step()

            # Update target networks
            self._soft_update(self.actor, self.actor_target, self.config.tau)
            self._soft_update(self.critic1, self.critic1_target, self.config.tau)
            self._soft_update(self.critic2, self.critic2_target, self.config.tau)

        # Train curiosity module
        curiosity_loss = 0
        if self.config.use_curiosity:
            intrinsic_reward, predicted_action = self.curiosity(states, actions, next_states)

            # Curiosity loss
            forward_loss = F.mse_loss(predicted_action, actions)

            self.curiosity_optimizer.zero_grad()
            forward_loss.backward()
            self.curiosity_optimizer.step()

            curiosity_loss = forward_loss.item()

        # Update priorities if using prioritized replay
        if self.config.use_prioritized_replay:
            td_errors = torch.abs(current_q1 - target_q).detach().cpu().numpy()
            self.replay_buffer.update_priorities(indices, td_errors)

        self.total_steps += 1

        return {
            'critic1_loss': critic1_loss.item(),
            'critic2_loss': critic2_loss.item(),
            'actor_loss': actor_loss.item() if isinstance(actor_loss, torch.Tensor) else actor_loss,
            'curiosity_loss': curiosity_loss
        }


class PPOAgent:
    """Proximal Policy Optimization with enhancements"""
    def __init__(self, config: RLConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Actor network
        self.actor = MLPNetwork(
            config.state_dim, config.action_dim, config.hidden_dim,
            config.num_layers, config.activation, config.use_layer_norm, noisy=True
        ).to(self.device)

        # Critic network
        self.critic = MLPNetwork(
            config.state_dim, 1, config.hidden_dim,
            config.num_layers, config.activation, config.use_layer_norm
        ).to(self.device)

        # Optimizer
        self.optimizer = torch.optim.Adam(
            list(self.actor.parameters()) + list(self.critic.parameters()),
            lr=config.learning_rate
        )

        # Experience storage
        self.states = []
        self.actions = []
        self.rewards = []
        self.log_probs = []
        self.values = []
        self.dones = []
        self.advantages = []

        # PPO parameters
        self.clip_epsilon = 0.2
        self.entropy_coef = 0.01
        self.value_coef = 0.5
        self.gae_lambda = 0.95

    def select_action(self, state: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Select action and return log probability and value"""
        state_tensor = torch.tensor(state, dtype=torch.float32, device=self.device).unsqueeze(0)

        with torch.no_grad():
            # Get action distribution
            action_logits = self.actor(state_tensor)
            action_dist = torch.distributions.Categorical(logits=action_logits)

            # Sample action
            action = action_dist.sample()

            # Get log probability and value
            log_prob = action_dist.log_prob(action)
            value = self.critic(state_tensor)

        return (
            action.cpu().numpy().flatten(),
            log_prob.cpu().numpy().flatten(),
            value.cpu().numpy().flatten()
        )

    def store_experience(self, state: np.ndarray, action: np.ndarray, reward: float,
                        log_prob: float, value: float, done: bool):
        """Store experience for PPO update"""
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.log_probs.append(log_prob)
        self.values.append(value)
        self.dones.append(done)

    def compute_advantages(self, next_value: float):
        """Compute Generalized Advantage Estimation (GAE)"""
        advantages = []
        advantage = 0

        # Process in reverse order
        for i in reversed(range(len(self.rewards))):
            if i == len(self.rewards) - 1:
                next_val = next_value
            else:
                next_val = self.values[i + 1]

            delta = self.rewards[i] + self.config.gamma * next_val * (1 - self.dones[i]) - self.values[i]
            advantage = delta + self.config.gamma * self.gae_lambda * (1 - self.dones[i]) * advantage
            advantages.insert(0, advantage)

        self.advantages = advantages

    def update(self, epochs: int = 10, batch_size: int = 64) -> Dict[str, float]:
        """Update policy using PPO"""
        if len(self.states) == 0:
            return {}

        # Convert to tensors
        states = torch.tensor(np.array(self.states), dtype=torch.float32, device=self.device)
        actions = torch.tensor(np.array(self.actions), dtype=torch.long, device=self.device)
        old_log_probs = torch.tensor(np.array(self.log_probs), dtype=torch.float32, device=self.device)
        old_values = torch.tensor(np.array(self.values), dtype=torch.float32, device=self.device)
        advantages = torch.tensor(np.array(self.advantages), dtype=torch.float32, device=self.device)
        rewards = torch.tensor(np.array(self.rewards), dtype=torch.float32, device=self.device)

        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        # Compute returns
        returns = advantages + old_values

        total_actor_loss = 0
        total_critic_loss = 0
        total_entropy_loss = 0

        # PPO update epochs
        for epoch in range(epochs):
            # Create batches
            indices = torch.randperm(len(states))

            for i in range(0, len(states), batch_size):
                batch_indices = indices[i:i + batch_size]

                # Get current policy
                action_logits = self.actor(states[batch_indices])
                action_dist = torch.distributions.Categorical(logits=action_logits)

                current_values = self.critic(states[batch_indices]).squeeze(-1)

                # Compute log probabilities
                current_log_probs = action_dist.log_prob(actions[batch_indices])

                # Entropy
                entropy = action_dist.entropy().mean()

                # PPO ratio
                ratio = torch.exp(current_log_probs - old_log_probs[batch_indices])

                # Clipped surrogate objective
                surr1 = ratio * advantages[batch_indices]
                surr2 = torch.clamp(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon) * advantages[batch_indices]
                actor_loss = -torch.min(surr1, surr2).mean()

                # Value function loss
                critic_loss = F.mse_loss(current_values, returns[batch_indices])

                # Total loss
                total_loss = actor_loss + self.value_coef * critic_loss - self.entropy_coef * entropy

                # Update
                self.optimizer.zero_grad()
                total_loss.backward()
                torch.nn.utils.clip_grad_norm_(self.actor.parameters(), 0.5)
                torch.nn.utils.clip_grad_norm_(self.critic.parameters(), 0.5)
                self.optimizer.step()

                total_actor_loss += actor_loss.item()
                total_critic_loss += critic_loss.item()
                total_entropy_loss += entropy.item()

        # Clear experience buffer
        self.states.clear()
        self.actions.clear()
        self.rewards.clear()
        self.log_probs.clear()
        self.values.clear()
        self.dones.clear()
        self.advantages.clear()

        # Reset noisy layers
        for module in self.actor.modules():
            if isinstance(module, NoisyLinear):
                module.reset_noise()

        num_updates = (epochs * len(states)) // batch_size
        return {
            'actor_loss': total_actor_loss / num_updates,
            'critic_loss': total_critic_loss / num_updates,
            'entropy': total_entropy_loss / num_updates
        }


class GamingEnvironment(gym.Env):
    """Custom gaming environment for DMLogn8n"""
    def __init__(self, config: RLConfig):
        super().__init__()

        self.config = config
        self.state_dim = config.state_dim
        self.action_dim = config.action_dim

        # Action and observation spaces
        self.action_space = spaces.Box(
            low=-config.max_action,
            high=config.max_action,
            shape=(config.action_dim,),
            dtype=np.float32
        )

        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(config.state_dim,),
            dtype=np.float32
        )

        # Environment state
        self.current_state = None
        self.step_count = 0
        self.max_steps = 1000

    def reset(self, seed=None):
        """Reset environment"""
        super().reset(seed=seed)

        # Initialize random state
        self.current_state = np.random.randn(self.state_dim)
        self.step_count = 0

        return self.current_state, {}

    def step(self, action: np.ndarray):
        """Take environment step"""
        if self.current_state is None:
            raise RuntimeError("Environment not reset")

        # Simulate environment dynamics
        next_state = self.current_state + 0.1 * action + np.random.randn(self.state_dim) * 0.01

        # Compute reward (based on action and state)
        reward = np.sum(action * self.current_state) + np.random.randn() * 0.1

        # Check if episode is done
        done = self.step_count >= self.max_steps
        truncated = False

        # Update state
        self.current_state = next_state
        self.step_count += 1

        return next_state, reward, done, truncated, {}


class CurriculumLearning:
    """Curriculum learning for progressive difficulty"""
    def __init__(self, initial_difficulty: float = 0.1, max_difficulty: float = 1.0,
                 update_frequency: int = 1000, success_threshold: float = 0.8):
        self.current_difficulty = initial_difficulty
        self.max_difficulty = max_difficulty
        self.update_frequency = update_frequency
        self.success_threshold = success_threshold

        self.episode_rewards = deque(maxlen=update_frequency)
        self.update_count = 0

    def update(self, episode_reward: float):
        """Update curriculum difficulty"""
        self.episode_rewards.append(episode_reward)
        self.update_count += 1

        if self.update_count % self.update_frequency == 0:
            # Check if agent is performing well
            avg_reward = np.mean(self.episode_rewards)
            if avg_reward > self.success_threshold:
                # Increase difficulty
                self.current_difficulty = min(
                    self.current_difficulty * 1.1,
                    self.max_difficulty
                )

    def get_environment_params(self) -> Dict[str, float]:
        """Get current environment parameters based on difficulty"""
        return {
            'noise_level': 0.1 * (1 - self.current_difficulty),
            'reward_scale': self.current_difficulty,
            'action_perturbation': 0.2 * (1 - self.current_difficulty)
        }


# Utility functions
def train_agent(agent: Union[TD3Agent, PPOAgent], env: gym.Env, episodes: int = 1000) -> Dict[str, List[float]]:
    """Train reinforcement learning agent"""
    episode_rewards = []
    episode_lengths = []

    curriculum = CurriculumLearning() if isinstance(agent, TD3Agent) else None

    for episode in tqdm(range(episodes), desc="Training"):
        state, _ = env.reset()
        total_reward = 0
        steps = 0

        if isinstance(agent, TD3Agent):
            # TD3 training loop
            while True:
                # Select action
                action = agent.select_action(state)

                # Take step
                next_state, reward, done, truncated, info = env.step(action)

                # Store experience
                agent.replay_buffer.add(state, action, reward, next_state, done, info)

                # Train
                if len(agent.replay_buffer) > agent.config.batch_size:
                    losses = agent.train_step()

                state = next_state
                total_reward += reward
                steps += 1

                if done or truncated:
                    break

        elif isinstance(agent, PPOAgent):
            # PPO training loop
            while True:
                # Select action
                action, log_prob, value = agent.select_action(state)

                # Take step
                next_state, reward, done, truncated, info = env.step(action)

                # Store experience
                agent.store_experience(state, action, reward, log_prob, value, done)

                state = next_state
                total_reward += reward
                steps += 1

                if done or truncated:
                    # Get final value
                    final_value = 0.0
                    if not done:
                        final_state_tensor = torch.tensor(state, dtype=torch.float32, device=agent.device).unsqueeze(0)
                        with torch.no_grad():
                            final_value = agent.critic(final_state_tensor).item()

                    # Compute advantages and update
                    agent.compute_advantages(final_value)
                    losses = agent.update()

                    break

        episode_rewards.append(total_reward)
        episode_lengths.append(steps)

        # Update curriculum
        if curriculum is not None:
            curriculum.update(total_reward)

        # Logging
        if episode % 100 == 0:
            avg_reward = np.mean(episode_rewards[-100:])
            print(f"Episode {episode}: Average reward (last 100): {avg_reward:.2f}")

    return {
        'episode_rewards': episode_rewards,
        'episode_lengths': episode_lengths
    }


def create_rl_config(model_size: str = "base") -> RLConfig:
    """Create RL configuration"""
    if model_size == "base":
        return RLConfig(
            state_dim=256,
            action_dim=50,
            hidden_dim=256,
            buffer_size=500000,
            batch_size=128
        )
    elif model_size == "large":
        return RLConfig(
            state_dim=512,
            action_dim=100,
            hidden_dim=512,
            buffer_size=1000000,
            batch_size=256
        )
    else:
        return RLConfig()


if __name__ == "__main__":
    print("Creating advanced reinforcement learning agents...")

    # Create configuration and agents
    config = create_rl_config("base")
    env = GamingEnvironment(config)

    td3_agent = TD3Agent(config)
    ppo_agent = PPOAgent(config)

    print(f"TD3 agent parameters: {sum(p.numel() for p in td3_agent.actor.parameters()) + sum(p.numel() for p in td3_agent.critic1.parameters()):,}")
    print(f"PPO agent parameters: {sum(p.numel() for p in ppo_agent.actor.parameters()) + sum(p.numel() for p in ppo_agent.critic.parameters()):,}")

    # Test agents
    print("\nTesting TD3 agent...")
    state, _ = env.reset()
    action = td3_agent.select_action(state)
    print(f"TD3 action shape: {action.shape}")

    print("\nTesting PPO agent...")
    state, _ = env.reset()
    action, log_prob, value = ppo_agent.select_action(state)
    print(f"PPO action shape: {action.shape}")
    print(f"PPO log prob: {log_prob}")
    print(f"PPO value: {value}")

    # Test training step
    print("\nTesting TD3 training...")
    for _ in range(10):
        state, _ = env.reset()
        action = td3_agent.select_action(state)
        next_state, reward, done, _, _ = env.step(action)
        td3_agent.replay_buffer.add(state, action, reward, next_state, done)

    losses = td3_agent.train_step()
    print(f"TD3 training losses: {losses}")

    print("\nReinforcement learning agents initialized successfully!")