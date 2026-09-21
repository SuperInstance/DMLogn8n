#!/usr/bin/env python3
"""
Multi-Agent Learning System for Cooperation and Competition
Implements learning paradigms for multiple interacting agents
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
import networkx as nx
import copy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiAgentParadigm(Enum):
    """Types of multi-agent learning paradigms"""
    COOPERATIVE = "cooperative"
    COMPETITIVE = "competitive"
    MIXED_MOTIVATION = "mixed_motivation"
    COALITION = "coalition"
    COMMUNICATION = "communication"
    HIERARCHICAL = "hierarchical"

@dataclass
class MultiAgentConfig:
    """Configuration for multi-agent learning"""
    paradigm: MultiAgentParadigm = MultiAgentParadigm.COOPERATIVE
    num_agents: int = 4
    state_dim: int = 20
    action_dim: int = 5
    hidden_dims: List[int] = field(default_factory=lambda: [256, 256])
    lr: float = 1e-3
    gamma: float = 0.99
    batch_size: int = 64
    buffer_size: int = 100000
    device: str = 'cuda'
    communication_dim: int = 32
    shared_reward: bool = True
    competitive_scoring: bool = False
    coalition_size: int = 2

class AgentObservation:
    """Represents an agent's observation in multi-agent environment"""

    def __init__(self, local_state: np.ndarray, global_state: Optional[np.ndarray] = None,
                 agent_states: Optional[Dict[int, np.ndarray]] = None,
                 communications: Optional[Dict[int, np.ndarray]] = None):
        self.local_state = local_state
        self.global_state = global_state
        self.agent_states = agent_states or {}
        self.communications = communications or {}
        self.timestamp = time.time()

    def get_combined_observation(self) -> np.ndarray:
        """Get combined observation vector"""
        obs_parts = [self.local_state]

        if self.global_state is not None:
            obs_parts.append(self.global_state)

        # Add other agent states (sorted by agent ID)
        for agent_id in sorted(self.agent_states.keys()):
            obs_parts.append(self.agent_states[agent_id])

        # Add communications (sorted by sender ID)
        for sender_id in sorted(self.communications.keys()):
            obs_parts.append(self.communications[sender_id])

        return np.concatenate(obs_parts)

class CommunicationProtocol:
    """Communication protocol between agents"""

    def __init__(self, communication_dim: int, max_agents: int = 10):
        self.communication_dim = communication_dim
        self.max_agents = max_agents
        self.message_buffer = defaultdict(list)
        self.communication_graph = nx.DiGraph()

    def send_message(self, sender_id: int, receiver_id: int, message: np.ndarray):
        """Send message from one agent to another"""
        if len(message) != self.communication_dim:
            raise ValueError(f"Message dimension {len(message)} != communication_dim {self.communication_dim}")

        self.message_buffer[receiver_id].append({
            'sender_id': sender_id,
            'message': message.copy(),
            'timestamp': time.time()
        })

        # Update communication graph
        self.communication_graph.add_edge(sender_id, receiver_id)

    def get_messages(self, receiver_id: int, max_messages: int = 5) -> Dict[int, np.ndarray]:
        """Get messages for an agent"""
        messages = self.message_buffer[receiver_id][-max_messages:]
        self.message_buffer[receiver_id] = self.message_buffer[receiver_id][max_messages:]

        # Convert to dict format
        message_dict = {}
        for msg in messages:
            message_dict[msg['sender_id']] = msg['message']

        return message_dict

    def broadcast(self, sender_id: int, message: np.ndarray, exclude: List[int] = None):
        """Broadcast message to all agents"""
        exclude = exclude or []
        for receiver_id in range(self.max_agents):
            if receiver_id != sender_id and receiver_id not in exclude:
                self.send_message(sender_id, receiver_id, message)

class MultiAgentNetwork(nn.Module):
    """Neural network for multi-agent learning"""

    def __init__(self, agent_id: int, config: MultiAgentConfig):
        super().__init__()
        self.agent_id = agent_id
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Calculate input dimension
        self.input_dim = self._calculate_input_dim()

        # Build policy network
        self.policy_layers = self._build_network()
        self.value_layers = self._build_value_network()

        # Communication module
        self.communication_encoder = nn.Sequential(
            nn.Linear(config.communication_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32)
        )

        # Attention mechanism for other agents
        self.attention = nn.MultiheadAttention(
            embed_dim=64, num_heads=4, batch_first=True
        )

    def _calculate_input_dim(self) -> int:
        """Calculate input dimension based on observation structure"""
        base_dim = self.config.state_dim
        global_dim = self.config.state_dim if self.config.paradigm in [MultiAgentParadigm.COOPERATIVE, MultiAgentParadigm.COMMUNICATION] else 0
        other_agents_dim = self.config.state_dim * (self.config.num_agents - 1)
        comm_dim = self.config.communication_dim * (self.config.num_agents - 1)

        return base_dim + global_dim + other_agents_dim + comm_dim

    def _build_network(self) -> nn.Sequential:
        """Build policy network"""
        layers = []
        input_dim = self.input_dim

        for hidden_dim in self.config.hidden_dims:
            layers.extend([
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.1)
            ])
            input_dim = hidden_dim

        # Output layer
        layers.append(nn.Linear(input_dim, self.config.action_dim))

        return nn.Sequential(*layers)

    def _build_value_network(self) -> nn.Sequential:
        """Build value network"""
        layers = []
        input_dim = self.input_dim

        for hidden_dim in self.config.hidden_dims:
            layers.extend([
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.1)
            ])
            input_dim = hidden_dim

        # Output layer (single value)
        layers.append(nn.Linear(input_dim, 1))

        return nn.Sequential(*layers)

    def forward(self, observation: AgentObservation) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass through network"""
        # Get combined observation
        obs_vector = observation.get_combined_observation()
        obs_tensor = torch.FloatTensor(obs_vector).unsqueeze(0).to(self.device)

        # Process other agents with attention
        if observation.agent_states:
            agent_states = []
            for agent_id in sorted(observation.agent_states.keys()):
                if agent_id != self.agent_id:
                    state_vector = observation.agent_states[agent_id]
                    state_tensor = torch.FloatTensor(state_vector).unsqueeze(0).to(self.device)
                    agent_states.append(state_tensor)

            if agent_states:
                agent_states_tensor = torch.cat(agent_states, dim=0).unsqueeze(0)
                attended_features, _ = self.attention(agent_states_tensor, agent_states_tensor, agent_states_tensor)
                attended_mean = attended_features.mean(dim=1)
                obs_tensor = torch.cat([obs_tensor, attended_mean], dim=1)

        # Policy and value
        policy_logits = self.policy_layers(obs_tensor)
        value = self.value_layers(obs_tensor)

        return policy_logits.squeeze(0), value.squeeze(0)

    def generate_communication(self, observation: AgentObservation) -> np.ndarray:
        """Generate communication message"""
        obs_vector = observation.get_combined_observation()
        obs_tensor = torch.FloatTensor(obs_vector).unsqueeze(0).to(self.device)

        with torch.no_grad():
            policy_output = self.policy_layers(obs_tensor)
            message = self.communication_encoder(policy_output)
            message = F.tanh(message)

        return message.cpu().numpy().squeeze()

class CooperativeMARL:
    """Cooperative Multi-Agent Reinforcement Learning"""

    def __init__(self, config: MultiAgentConfig):
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Create agents
        self.agents = {}
        for agent_id in range(config.num_agents):
            self.agents[agent_id] = MultiAgentNetwork(agent_id, config).to(self.device)

        # Optimizers
        self.optimizers = {}
        for agent_id, agent in self.agents.items():
            self.optimizers[agent_id] = optim.Adam(agent.parameters(), lr=config.lr)

        # Communication protocol
        self.communication = CommunicationProtocol(config.communication_dim, config.num_agents)

        # Shared replay buffer
        self.replay_buffer = deque(maxlen=config.buffer_size)

        # Training metrics
        self.training_history = {
            'team_rewards': [],
            'individual_rewards': defaultdict(list),
            'communication_events': 0,
            'cooperation_scores': []
        }

    def select_actions(self, observations: Dict[int, AgentObservation],
                      training: bool = True) -> Dict[int, np.ndarray]:
        """Select actions for all agents"""
        actions = {}
        communications = {}

        # First pass: generate communications
        if self.config.paradigm == MultiAgentParadigm.COMMUNICATION:
            for agent_id, obs in observations.items():
                message = self.agents[agent_id].generate_communication(obs)
                communications[agent_id] = message

            # Exchange communications
            for sender_id, message in communications.items():
                self.communication.broadcast(sender_id, message, exclude=[sender_id])

        # Second pass: select actions with communications
        for agent_id, obs in observations.items():
            # Add received communications to observation
            if self.config.paradigm == MultiAgentParadigm.COMMUNICATION:
                received_messages = self.communication.get_messages(agent_id)
                obs.communications = received_messages

            # Get action from agent
            with torch.no_grad():
                policy_logits, _ = self.agents[agent_id](obs)

                if training:
                    action_probs = F.softmax(policy_logits, dim=0)
                    action = torch.multinomial(action_probs, 1).item()
                else:
                    action = torch.argmax(policy_logits).item()

            actions[agent_id] = action

        return actions

    def store_transitions(self, transitions: List[Dict[str, Any]]):
        """Store transitions in replay buffer"""
        for transition in transitions:
            self.replay_buffer.append(transition)

    def train_step(self) -> Dict[str, float]:
        """Perform one training step"""
        if len(self.replay_buffer) < self.config.batch_size:
            return {}

        # Sample batch
        batch = random.sample(list(self.replay_buffer), self.config.batch_size)

        # Organize batch by agent
        agent_batches = defaultdict(list)
        for transition in batch:
            agent_id = transition['agent_id']
            agent_batches[agent_id].append(transition)

        # Train each agent
        total_loss = 0.0
        agent_losses = {}

        for agent_id, agent_batch in agent_batches.items():
            loss = self._train_agent(agent_id, agent_batch)
            agent_losses[agent_id] = loss
            total_loss += loss

        avg_loss = total_loss / len(agent_batches)

        return {
            'total_loss': avg_loss,
            'agent_losses': agent_losses
        }

    def _train_agent(self, agent_id: int, batch: List[Dict[str, Any]]) -> float:
        """Train individual agent"""
        if len(batch) == 0:
            return 0.0

        agent = self.agents[agent_id]
        optimizer = self.optimizers[agent_id]

        optimizer.zero_grad()

        total_loss = 0.0

        for transition in batch:
            obs = transition['observation']
            action = transition['action']
            reward = transition['reward']
            next_obs = transition['next_observation']
            done = transition['done']

            # Forward pass
            policy_logits, value = agent(obs)

            # Policy loss
            action_tensor = torch.tensor(action, dtype=torch.long, device=self.device)
            policy_loss = F.cross_entropy(policy_logits.unsqueeze(0), action_tensor.unsqueeze(0))

            # Value loss
            reward_tensor = torch.tensor(reward, dtype=torch.float32, device=self.device)
            value_loss = F.mse_loss(value.unsqueeze(0), reward_tensor.unsqueeze(0))

            # Total loss
            transition_loss = policy_loss + 0.5 * value_loss
            total_loss += transition_loss

        # Backward pass
        total_loss = total_loss / len(batch)
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(agent.parameters(), 1.0)
        optimizer.step()

        return total_loss.item()

class CompetitiveMARL:
    """Competitive Multi-Agent Reinforcement Learning"""

    def __init__(self, config: MultiAgentConfig):
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Create agents with competitive objectives
        self.agents = {}
        for agent_id in range(config.num_agents):
            self.agents[agent_id] = MultiAgentNetwork(agent_id, config).to(self.device)

        # Optimizers
        self.optimizers = {}
        for agent_id, agent in self.agents.items():
            self.optimizers[agent_id] = optim.Adam(agent.parameters(), lr=config.lr)

        # Training metrics
        self.training_history = {
            'agent_rewards': defaultdict(list),
            'win_rates': defaultdict(float),
            'competitive_scores': defaultdict(list)
        }

    def select_actions(self, observations: Dict[int, AgentObservation],
                      training: bool = True) -> Dict[int, np.ndarray]:
        """Select actions for competitive environment"""
        actions = {}

        for agent_id, obs in observations.items():
            with torch.no_grad():
                policy_logits, _ = self.agents[agent_id](obs)

                if training:
                    # Add exploration
                    action_probs = F.softmax(policy_logits, dim=0)
                    action = torch.multinomial(action_probs, 1).item()
                else:
                    action = torch.argmax(policy_logits).item()

                actions[agent_id] = action

        return actions

    def update_competitive_scores(self, agent_rewards: Dict[int, float]):
        """Update competitive learning metrics"""
        for agent_id, reward in agent_rewards.items():
            self.training_history['agent_rewards'][agent_id].append(reward)

            # Update win rate (simplified)
            if len(self.training_history['agent_rewards'][agent_id]) > 10:
                recent_rewards = self.training_history['agent_rewards'][agent_id][-10:]
                wins = sum(1 for r in recent_rewards if r > 0)
                win_rate = wins / len(recent_rewards)
                self.training_history['win_rates'][agent_id] = win_rate

class CoalitionFormation:
    """Coalition formation and learning"""

    def __init__(self, config: MultiAgentConfig):
        self.config = config
        self.num_agents = config.num_agents
        self.coalition_size = config.coalition_size

        # Track coalitions
        self.current_coalitions = []
        self.coalition_values = {}
        self.coalition_history = []

        # Agent capabilities
        self.agent_capabilities = {i: np.random.rand(5) for i in range(self.num_agents)}

    def form_coalitions(self, agent_values: Dict[int, float]) -> List[List[int]]:
        """Form coalitions based on agent values"""
        # Sort agents by value
        sorted_agents = sorted(agent_values.items(), key=lambda x: x[1], reverse=True)

        # Form coalitions using greedy approach
        coalitions = []
        remaining_agents = set(range(self.num_agents))

        while len(remaining_agents) >= self.coalition_size:
            # Find best coalition
            best_coalition = None
            best_value = -float('inf')

            for coalition_size in range(1, min(self.coalition_size, len(remaining_agents)) + 1):
                from itertools import combinations
                for coalition in combinations(remaining_agents, coalition_size):
                    coalition_value = self._evaluate_coalition(coalition)
                    if coalition_value > best_value:
                        best_value = coalition_value
                        best_coalition = coalition

            if best_coalition:
                coalitions.append(list(best_coalition))
                remaining_agents -= set(best_coalition)
            else:
                break

        # Add remaining agents as individual coalitions
        for agent in remaining_agents:
            coalitions.append([agent])

        self.current_coalitions = coalitions
        self.coalition_history.append(coalitions.copy())

        return coalitions

    def _evaluate_coalition(self, coalition: Tuple[int, ...]) -> float:
        """Evaluate the value of a coalition"""
        if len(coalition) == 1:
            return self.agent_capabilities[coalition[0]].sum()

        # Synergy bonus for coalitions
        synergy_bonus = 0.1 * (len(coalition) - 1)
        total_capability = sum(self.agent_capabilities[agent] for agent in coalition)

        return total_capability.sum() + synergy_bonus

    def get_coalition_rewards(self, coalition_rewards: Dict[int, float]) -> Dict[int, float]:
        """Distribute rewards among coalition members"""
        agent_rewards = {}

        for coalition in self.current_coalitions:
            if len(coalition) == 1:
                # Individual agent
                agent_id = coalition[0]
                agent_rewards[agent_id] = coalition_rewards.get(agent_id, 0.0)
            else:
                # Distribute coalition reward
                coalition_id = tuple(sorted(coalition))
                total_reward = coalition_rewards.get(coalition_id, 0.0)

                # Distribute based on capability contribution
                total_capability = sum(self.agent_capabilities[agent].sum() for agent in coalition)
                for agent_id in coalition:
                    agent_capability = self.agent_capabilities[agent_id].sum()
                    agent_share = agent_capability / total_capability
                    agent_rewards[agent_id] = total_reward * agent_share

        return agent_rewards

class HierarchicalMARL:
    """Hierarchical Multi-Agent Reinforcement Learning"""

    def __init__(self, config: MultiAgentConfig):
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Create hierarchy levels
        self.hierarchy_levels = self._create_hierarchy()
        self.level_managers = {}

        # Create agents for each level
        for level, agent_ids in self.hierarchy_levels.items():
            self.level_managers[level] = {}
            for agent_id in agent_ids:
                agent_config = copy.deepcopy(config)
                agent_config.num_agents = len(agent_ids)  # Adjust for level
                self.level_managers[level][agent_id] = MultiAgentNetwork(agent_id, agent_config).to(self.device)

    def _create_hierarchy(self) -> Dict[int, List[int]]:
        """Create hierarchical structure"""
        hierarchy = {}
        num_agents = self.config.num_agents

        # Level 0: Individual agents
        hierarchy[0] = list(range(num_agents))

        # Level 1: Groups of 2-3 agents
        if num_agents > 3:
            groups = []
            for i in range(0, num_agents, 2):
                if i + 1 < num_agents:
                    groups.append([i, i + 1])
                else:
                    groups.append([i])
            hierarchy[1] = groups

        # Level 2: Top level (if enough agents)
        if num_agents > 6:
            hierarchy[2] = [list(range(num_agents))]

        return hierarchy

    def hierarchical_action_selection(self, observations: Dict[int, AgentObservation]) -> Dict[int, np.ndarray]:
        """Select actions using hierarchical decision making"""
        actions = {}

        # Bottom-up action selection
        for level in sorted(self.hierarchy_levels.keys(), reverse=True):
            level_observations = self._prepare_level_observations(level, observations, actions)

            for agent_id in self.hierarchy_levels[level]:
                if agent_id in level_observations:
                    agent = self.level_managers[level][agent_id]
                    obs = level_observations[agent_id]

                    with torch.no_grad():
                        policy_logits, _ = agent(obs)
                        action = torch.argmax(policy_logits).item()

                    if level == 0:
                        # Individual agent actions
                        actions[agent_id] = action
                    else:
                        # Higher level actions influence lower levels
                        pass  # Implementation depends on specific hierarchy design

        return actions

    def _prepare_level_observations(self, level: int, observations: Dict[int, AgentObservation],
                                  current_actions: Dict[int, np.ndarray]) -> Dict[int, AgentObservation]:
        """Prepare observations for specific hierarchy level"""
        level_observations = {}

        if level == 0:
            # Individual agent level
            level_observations = observations
        else:
            # Higher levels - combine observations from lower levels
            for agent_id in self.hierarchy_levels[level]:
                # Create combined observation for this level's agent
                combined_states = []
                combined_metadata = {}

                for sub_agent_id in self.hierarchy_levels.get(level - 1, []):
                    if sub_agent_id in observations:
                        combined_states.append(observations[sub_agent_id].local_state)
                        if sub_agent_id in current_actions:
                            combined_metadata[f'action_{sub_agent_id}'] = current_actions[sub_agent_id]

                if combined_states:
                    combined_state = np.concatenate(combined_states)
                    level_obs = AgentObservation(
                        local_state=combined_state,
                        metadata=combined_metadata
                    )
                    level_observations[agent_id] = level_obs

        return level_observations

class MultiAgentTrainer:
    """Main multi-agent training system"""

    def __init__(self, config: MultiAgentConfig):
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Initialize appropriate learning paradigm
        if config.paradigm == MultiAgentParadigm.COOPERATIVE:
            self.marl_system = CooperativeMARL(config)
        elif config.paradigm == MultiAgentParadigm.COMPETITIVE:
            self.marl_system = CompetitiveMARL(config)
        elif config.paradigm == MultiAgentParadigm.COALITION:
            self.marl_system = CoalitionFormation(config)
        elif config.paradigm == MultiAgentParadigm.HIERARCHICAL:
            self.marl_system = HierarchicalMARL(config)
        else:
            # Default to cooperative
            self.marl_system = CooperativeMARL(config)

        # Training metrics
        self.global_metrics = {
            'episodes': 0,
            'total_steps': 0,
            'paradigm': config.paradigm.value
        }

    def train_episode(self, environment, max_steps: int = 1000) -> Dict[str, Any]:
        """Train one episode"""
        # Reset environment and get initial observations
        observations = environment.reset()
        episode_rewards = defaultdict(list)
        episode_transitions = []

        for step in range(max_steps):
            # Select actions
            if hasattr(self.marl_system, 'select_actions'):
                actions = self.marl_system.select_actions(observations, training=True)
            else:
                # Handle other paradigms
                actions = {}

            # Take environment step
            next_observations, rewards, dones, info = environment.step(actions)

            # Store transitions
            for agent_id in observations:
                if agent_id in rewards:
                    transition = {
                        'agent_id': agent_id,
                        'observation': observations[agent_id],
                        'action': actions[agent_id],
                        'reward': rewards[agent_id],
                        'next_observation': next_observations[agent_id],
                        'done': dones.get(agent_id, False)
                    }
                    episode_transitions.append(transition)
                    episode_rewards[agent_id].append(rewards[agent_id])

            # Update system if applicable
            if hasattr(self.marl_system, 'store_transitions'):
                self.marl_system.store_transitions(episode_transitions)

            observations = next_observations

            # Check if all agents are done
            if all(dones.values()):
                break

        # Perform training step
        training_metrics = {}
        if hasattr(self.marl_system, 'train_step'):
            training_metrics = self.marl_system.train_step()

        # Calculate episode metrics
        episode_summary = {
            'total_steps': step + 1,
            'agent_rewards': {agent_id: sum(rewards) for agent_id, rewards in episode_rewards.items()},
            'training_metrics': training_metrics
        }

        # Update global metrics
        self.global_metrics['episodes'] += 1
        self.global_metrics['total_steps'] += step + 1

        # Update system-specific metrics
        if hasattr(self.marl_system, 'training_history'):
            if 'agent_rewards' in self.marl_system.training_history:
                for agent_id, reward in episode_summary['agent_rewards'].items():
                    self.marl_system.training_history['agent_rewards'][agent_id].append(reward)

        return episode_summary

    def evaluate(self, environment, num_episodes: int = 10) -> Dict[str, Any]:
        """Evaluate multi-agent system"""
        evaluation_metrics = {
            'episodes': num_episodes,
            'agent_performances': defaultdict(list),
            'team_performance': [],
            'cooperation_metrics': []
        }

        for episode in range(num_episodes):
            observations = environment.reset()
            episode_rewards = defaultdict(list)
            cooperation_events = 0

            for step in range(1000):  # Max steps per episode
                # Select actions (evaluation mode)
                if hasattr(self.marl_system, 'select_actions'):
                    actions = self.marl_system.select_actions(observations, training=False)
                else:
                    actions = {}

                # Take environment step
                next_observations, rewards, dones, info = environment.step(actions)

                # Track rewards
                for agent_id in rewards:
                    episode_rewards[agent_id].append(rewards[agent_id])

                # Track cooperation events (if applicable)
                if 'cooperation_event' in info:
                    cooperation_events += info['cooperation_event']

                observations = next_observations

                if all(dones.values()):
                    break

            # Record episode metrics
            for agent_id, rewards in episode_rewards.items():
                total_reward = sum(rewards)
                evaluation_metrics['agent_performances'][agent_id].append(total_reward)

            evaluation_metrics['team_performance'].append(sum(sum(rewards) for rewards in episode_rewards.values()))
            evaluation_metrics['cooperation_metrics'].append(cooperation_events)

        # Calculate averages
        avg_performances = {}
        for agent_id, performances in evaluation_metrics['agent_performances'].items():
            avg_performances[agent_id] = np.mean(performances)

        evaluation_metrics['average_agent_performances'] = avg_performances
        evaluation_metrics['average_team_performance'] = np.mean(evaluation_metrics['team_performance'])
        evaluation_metrics['average_cooperation'] = np.mean(evaluation_metrics['cooperation_metrics'])

        return evaluation_metrics

# Utility functions
def create_multi_agent_config(num_agents: int = 4, paradigm: str = 'cooperative',
                            state_dim: int = 20, action_dim: int = 5) -> MultiAgentConfig:
    """Create multi-agent learning configuration"""
    return MultiAgentConfig(
        paradigm=MultiAgentParadigm(paradigm),
        num_agents=num_agents,
        state_dim=state_dim,
        action_dim=action_dim,
        hidden_dims=[256, 256],
        lr=1e-3,
        gamma=0.99,
        batch_size=64,
        buffer_size=100000,
        device='cuda' if torch.cuda.is_available() else 'cpu',
        communication_dim=32,
        shared_reward=paradigm == 'cooperative',
        competitive_scoring=paradigm == 'competitive',
        coalition_size=min(2, num_agents // 2)
    )

def create_multi_agent_environment(num_agents: int, state_dim: int, action_dim: int):
    """Create a simple multi-agent environment for testing"""
    class SimpleMultiAgentEnv:
        def __init__(self, num_agents, state_dim, action_dim):
            self.num_agents = num_agents
            self.state_dim = state_dim
            self.action_dim = action_dim
            self.step_count = 0

        def reset(self):
            self.step_count = 0
            observations = {}
            for agent_id in range(self.num_agents):
                local_state = np.random.randn(state_dim)
                global_state = np.random.randn(state_dim) if agent_id == 0 else None
                observations[agent_id] = AgentObservation(local_state, global_state)
            return observations

        def step(self, actions):
            self.step_count += 1
            next_observations = {}
            rewards = {}
            dones = {}

            for agent_id in range(self.num_agents):
                local_state = np.random.randn(state_dim)
                global_state = np.random.randn(state_dim) if agent_id == 0 else None
                next_observations[agent_id] = AgentObservation(local_state, global_state)

                # Simple reward function
                reward = np.random.randn()
                rewards[agent_id] = reward

                # Done after 100 steps
                dones[agent_id] = self.step_count >= 100

            info = {'cooperation_event': np.random.rand() > 0.8}

            return next_observations, rewards, dones, info

    return SimpleMultiAgentEnv(num_agents, state_dim, action_dim)

if __name__ == "__main__":
    # Example usage
    config = create_multi_agent_config(
        num_agents=4,
        paradigm='cooperative',
        state_dim=20,
        action_dim=5
    )

    # Create multi-agent trainer
    trainer = MultiAgentTrainer(config)

    # Create test environment
    env = create_multi_agent_environment(config.num_agents, config.state_dim, config.action_dim)

    print("Multi-Agent Learning System initialized!")
    print(f"Paradigm: {config.paradigm.value}")
    print(f"Number of agents: {config.num_agents}")
    print(f"State dimension: {config.state_dim}")
    print(f"Action dimension: {config.action_dim}")
    print(f"Available paradigms: Cooperative, Competitive, Mixed-Motivation, Coalition, Communication, Hierarchical")
    print(f"Communication protocol: {CommunicationProtocol.__name__}")
    print(f"Coalition formation: {CoalitionFormation.__name__}")
    print(f"Hierarchical learning: {HierarchicalMARL.__name__}")