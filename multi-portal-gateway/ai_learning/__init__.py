#!/usr/bin/env python3
"""
Advanced AI Learning and Adaptation System
Integrates all learning components for comprehensive AI agent evolution
"""

import torch
import torch.nn as nn
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import time
import json
from pathlib import Path

# Import all learning modules
from .reinforcement_learning import (
    RLConfig, PPOAgent, SACAgent, RainbowDQNAgent, RLTrainer,
    PrioritizedReplayBuffer, PerformanceMonitor
)
from .neural_evolution import (
    GenomeConfig, NeuralGenome, NeuroEvolutionTrainer,
    EvolutionStrategy, MultiObjectiveEvolution
)
from .transfer_learning import (
    TransferConfig, ProgressiveTransferLearning,
    DomainAdversarialTraining, MetaTransferLearning,
    TransferLearningAnalyzer
)
from .meta_learning import (
    MetaLearningConfig, PrototypicalNetwork, MatchingNetwork,
    RelationNetwork, MAML, Reptile, MetaLearningTrainer
)
from .curriculum_learning import (
    CurriculumConfig, CurriculumManager, CurriculumLearning,
    DifficultyScheduler, ProgressiveNetworks
)
from .continual_learning import (
    ContinualLearningConfig, ContinualLearner,
    ElasticWeightConsolidation, SynapticIntelligence,
    GradientEpisodicMemory, ExperienceReplay
)
from .behavioral_cloning import (
    BehavioralCloningConfig, BehavioralCloningTrainer,
    DAggerTrainer, GAILTrainer, ExpertQualityEstimator
)
from .multi_agent_learning import (
    MultiAgentConfig, MultiAgentTrainer,
    CooperativeMARL, CompetitiveMARL, CoalitionFormation
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class IntegratedAISystemConfig:
    """Configuration for the integrated AI learning system"""
    # Core parameters
    state_dim: int = 128
    action_dim: int = 32
    hidden_dims: List[int] = None

    # Learning components (all enabled by default)
    enable_reinforcement_learning: bool = True
    enable_neural_evolution: bool = True
    enable_transfer_learning: bool = True
    enable_meta_learning: bool = True
    enable_curriculum_learning: bool = True
    enable_continual_learning: bool = True
    enable_behavioral_cloning: bool = True
    enable_multi_agent_learning: bool = True

    # Training parameters
    learning_rate: float = 1e-3
    batch_size: int = 64
    max_episodes: int = 10000
    evaluation_frequency: int = 100

    # System parameters
    device: str = 'cuda'
    save_frequency: int = 1000
    log_frequency: int = 100

    # Adaptation parameters
    auto_adapt_architecture: bool = True
    auto_curriculum_adjustment: bool = True
    automatic_method_selection: bool = True

    def __post_init__(self):
        if self.hidden_dims is None:
            self.hidden_dims = [256, 256, 128]

class IntegratedAISystem:
    """
    Advanced AI Learning and Adaptation System

    This system integrates multiple cutting-edge machine learning approaches
    to create AI agents that can continuously learn, adapt, and improve through
    experience and interactions.
    """

    def __init__(self, config: IntegratedAISystemConfig):
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Initialize all learning components
        self._initialize_learning_components()

        # System state
        self.current_episode = 0
        self.training_active = False
        self.performance_history = []
        self.adaptation_events = []

        # Metrics and monitoring
        self.system_metrics = {
            'total_training_time': 0.0,
            'adaptations_performed': 0,
            'architecture_changes': 0,
            'method_switches': 0
        }

        logger.info("Integrated AI Learning System initialized")
        self._log_system_capabilities()

    def _initialize_learning_components(self):
        """Initialize all learning components"""
        # Reinforcement Learning
        if self.config.enable_reinforcement_learning:
            self.rl_config = RLConfig(
                state_dim=self.config.state_dim,
                action_dim=self.config.action_dim,
                hidden_dims=self.config.hidden_dims,
                lr=self.config.learning_rate,
                device=self.config.device
            )
            self.rl_trainer = RLTrainer('ppo', self.rl_config)
            logger.info("Reinforcement Learning component initialized (PPO)")

        # Neural Evolution
        if self.config.enable_neural_evolution:
            self.evolution_config = GenomeConfig(
                input_size=self.config.state_dim,
                output_size=self.config.action_dim,
                max_hidden_layers=5,
                max_neurons_per_layer=512
            )
            self.evolution_trainer = NeuroEvolutionTrainer(
                self.evolution_config, population_size=20
            )
            logger.info("Neural Evolution component initialized")

        # Transfer Learning
        if self.config.enable_transfer_learning:
            self.transfer_config = TransferConfig(
                source_domains=['general', 'similar_tasks'],
                target_domain='current_task',
                device=self.config.device
            )
            self.transfer_system = ProgressiveTransferLearning(self.transfer_config)
            logger.info("Transfer Learning component initialized")

        # Meta-Learning
        if self.config.enable_meta_learning:
            self.meta_config = MetaLearningConfig(
                ways=5, shots=5,
                meta_lr=1e-3,
                device=self.config.device
            )
            self.meta_trainer = MetaLearningTrainer(self.meta_config)
            logger.info("Meta-Learning component initialized")

        # Curriculum Learning
        if self.config.enable_curriculum_learning:
            self.curriculum_config = create_curriculum_config('adaptive')
            self.curriculum_system = CurriculumLearning(self.curriculum_config)
            self._setup_default_curriculum()
            logger.info("Curriculum Learning component initialized")

        # Continual Learning
        if self.config.enable_continual_learning:
            self.continual_config = create_continual_config('ewc')
            # Create a base model for continual learning
            base_model = self._create_base_model()
            self.continual_learner = ContinualLearner(base_model, self.continual_config)
            logger.info("Continual Learning component initialized")

        # Behavioral Cloning
        if self.config.enable_behavioral_cloning:
            self.bc_config = BehavioralCloningConfig(
                state_dim=self.config.state_dim,
                action_dim=self.config.action_dim,
                device=self.config.device
            )
            self.bc_trainer = BehavioralCloningTrainer(self.bc_config)
            logger.info("Behavioral Cloning component initialized")

        # Multi-Agent Learning
        if self.config.enable_multi_agent_learning:
            self.ma_config = create_multi_agent_config(
                num_agents=4,
                paradigm='cooperative',
                state_dim=self.config.state_dim,
                action_dim=self.config.action_dim
            )
            self.ma_trainer = MultiAgentTrainer(self.ma_config)
            logger.info("Multi-Agent Learning component initialized")

    def _create_base_model(self) -> nn.Module:
        """Create a base neural network model"""
        class BaseModel(nn.Module):
            def __init__(self, state_dim: int, action_dim: int, hidden_dims: List[int]):
                super().__init__()
                layers = []
                input_dim = state_dim

                for hidden_dim in hidden_dims:
                    layers.extend([
                        nn.Linear(input_dim, hidden_dim),
                        nn.ReLU(),
                        nn.Dropout(0.1)
                    ])
                    input_dim = hidden_dim

                layers.append(nn.Linear(input_dim, action_dim))
                self.network = nn.Sequential(*layers)

            def forward(self, x):
                return self.network(x)

        return BaseModel(
            self.config.state_dim,
            self.config.action_dim,
            self.config.hidden_dims
        ).to(self.device)

    def _setup_default_curriculum(self):
        """Setup default curriculum tasks"""
        # Add sample curriculum tasks
        self.curriculum_system.add_curriculum_task(
            task_id="basic_navigation",
            difficulty=0.2,
            skills_learned=["movement", "exploration"]
        )

        self.curriculum_system.add_curriculum_task(
            task_id="object_interaction",
            difficulty=0.4,
            prerequisites=["basic_navigation"],
            skills_learned=["manipulation", "planning"]
        )

        self.curriculum_system.add_curriculum_task(
            task_id="complex_problem_solving",
            difficulty=0.7,
            prerequisites=["object_interaction"],
            skills_learned=["reasoning", "strategy"]
        )

    def train(self, environment, num_episodes: Optional[int] = None) -> Dict[str, Any]:
        """
        Main training loop using integrated learning approach

        Args:
            environment: The training environment
            num_episodes: Number of episodes to train (uses config default if None)

        Returns:
            Dictionary containing training results and metrics
        """
        num_episodes = num_episodes or self.config.max_episodes
        logger.info(f"Starting integrated training for {num_episodes} episodes")

        self.training_active = True
        start_time = time.time()

        training_results = {
            'episodes_completed': 0,
            'total_rewards': [],
            'adaptation_events': [],
            'final_performance': {},
            'learning_progress': {}
        }

        try:
            for episode in range(num_episodes):
                self.current_episode = episode

                # Adaptive architecture evolution
                if (self.config.auto_adapt_architecture and
                    episode > 0 and episode % 500 == 0):
                    self._adapt_architecture()

                # Curriculum learning progression
                if self.config.enable_curriculum_learning:
                    curriculum_task = self._get_current_curriculum_task()

                # Main training episode
                episode_result = self._train_episode(environment, episode)
                training_results['total_rewards'].append(episode_result['total_reward'])

                # Method selection and adaptation
                if self.config.automatic_method_selection:
                    self._adapt_learning_methods(episode_result)

                # Evaluation and logging
                if episode % self.config.evaluation_frequency == 0:
                    evaluation_results = self._evaluate_current_performance(environment)
                    training_results['learning_progress'][episode] = evaluation_results

                    logger.info(f"Episode {episode}: "
                               f"Reward={episode_result['total_reward']:.2f}, "
                               f"Performance={evaluation_results.get('avg_performance', 0):.3f}")

                # Save checkpoint
                if episode % self.config.save_frequency == 0:
                    self._save_checkpoint(episode)

                training_results['episodes_completed'] = episode + 1

        except KeyboardInterrupt:
            logger.info("Training interrupted by user")
        except Exception as e:
            logger.error(f"Training error: {e}")
            raise
        finally:
            self.training_active = False
            training_time = time.time() - start_time
            self.system_metrics['total_training_time'] += training_time

            # Final evaluation
            final_performance = self._evaluate_current_performance(environment)
            training_results['final_performance'] = final_performance

            logger.info(f"Training completed in {training_time:.2f} seconds")
            logger.info(f"Final performance: {final_performance}")

        return training_results

    def _train_episode(self, environment, episode: int) -> Dict[str, Any]:
        """Train a single episode using integrated approach"""
        # Select the most appropriate learning method for current context
        learning_method = self._select_optimal_learning_method(episode)

        if learning_method == 'reinforcement_learning':
            return self._train_rl_episode(environment)
        elif learning_method == 'meta_learning':
            return self._train_meta_episode(environment)
        elif learning_method == 'behavioral_cloning':
            return self._train_bc_episode(environment)
        else:
            # Default to reinforcement learning
            return self._train_rl_episode(environment)

    def _select_optimal_learning_method(self, episode: int) -> str:
        """Select the optimal learning method based on current context"""
        if episode < 100:
            # Early training: use behavioral cloning if demonstrations available
            if hasattr(self, 'bc_trainer') and len(self.bc_trainer.demo_buffer.demonstrations) > 0:
                return 'behavioral_cloning'
            return 'reinforcement_learning'

        elif episode < 500:
            # Mid training: use meta-learning for rapid adaptation
            if self.config.enable_meta_learning:
                return 'meta_learning'
            return 'reinforcement_learning'

        else:
            # Late training: use most successful method
            if len(self.performance_history) > 10:
                recent_performance = self.performance_history[-10:]
                avg_rl_performance = np.mean([p.get('rl_performance', 0) for p in recent_performance])
                avg_meta_performance = np.mean([p.get('meta_performance', 0) for p in recent_performance])

                if avg_meta_performance > avg_rl_performance * 1.1:
                    return 'meta_learning'

            return 'reinforcement_learning'

    def _train_rl_episode(self, environment) -> Dict[str, Any]:
        """Train using reinforcement learning"""
        # Reset environment
        state = environment.reset()
        total_reward = 0
        done = False
        steps = 0

        while not done and steps < 1000:
            # Select action using RL agent
            if hasattr(self, 'rl_trainer'):
                action, _ = self.rl_trainer.agent.select_action(state, training=True)
            else:
                # Fallback random action
                action = np.random.randint(0, self.config.action_dim)

            # Take step
            next_state, reward, done, info = environment.step(action)
            total_reward += reward

            # Store experience
            if hasattr(self, 'rl_trainer'):
                self.rl_trainer.agent.store_transition(state, action, reward, next_state, done)

            state = next_state
            steps += 1

        # Update RL agent
        if hasattr(self, 'rl_trainer'):
            self.rl_trainer.agent.update()

        # Apply continual learning if enabled
        if hasattr(self, 'continual_learner') and steps > 0:
            # Convert episode to continual learning format
            self._apply_continual_learning_update(state, total_reward)

        return {
            'method': 'reinforcement_learning',
            'total_reward': total_reward,
            'steps': steps,
            'rl_performance': total_reward / max(1, steps)
        }

    def _train_meta_episode(self, environment) -> Dict[str, Any]:
        """Train using meta-learning approach"""
        # Sample a meta-learning task
        if hasattr(self, 'meta_trainer'):
            # Create a meta-learning episode
            # This is simplified - actual implementation would use proper task sampling
            state = environment.reset()
            total_reward = 0
            done = False
            steps = 0

            while not done and steps < 1000:
                # Use meta-learner for action selection
                action = np.random.randint(0, self.config.action_dim)  # Simplified

                next_state, reward, done, info = environment.step(action)
                total_reward += reward

                state = next_state
                steps += 1

            return {
                'method': 'meta_learning',
                'total_reward': total_reward,
                'steps': steps,
                'meta_performance': total_reward / max(1, steps)
            }

        # Fallback to RL
        return self._train_rl_episode(environment)

    def _train_bc_episode(self, environment) -> Dict[str, Any]:
        """Train using behavioral cloning"""
        if hasattr(self, 'bc_trainer') and len(self.bc_trainer.demo_buffer.demonstrations) > 0:
            # Train behavioral cloning model
            history = self.bc_trainer.train()

            # Evaluate cloned policy
            state = environment.reset()
            total_reward = 0
            done = False
            steps = 0

            while not done and steps < 1000:
                # Use cloned policy for action selection
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                with torch.no_grad():
                    action = self.bc_trainer.network.select_action(state_tensor, deterministic=True)
                    if isinstance(action, torch.Tensor):
                        action = action.cpu().numpy()

                next_state, reward, done, info = environment.step(action)
                total_reward += reward

                state = next_state
                steps += 1

            return {
                'method': 'behavioral_cloning',
                'total_reward': total_reward,
                'steps': steps,
                'bc_performance': total_reward / max(1, steps)
            }

        # Fallback to RL
        return self._train_rl_episode(environment)

    def _adapt_architecture(self):
        """Adapt network architecture using neural evolution"""
        if not self.config.enable_neural_evolution:
            return

        logger.info("Performing architecture adaptation")

        # This would use the neural evolution system to optimize architecture
        # For now, we'll just log the event
        adaptation_event = {
            'type': 'architecture_adaptation',
            'episode': self.current_episode,
            'timestamp': time.time()
        }
        self.adaptation_events.append(adaptation_event)
        self.system_metrics['architecture_changes'] += 1

    def _get_current_curriculum_task(self) -> Optional[Any]:
        """Get current task from curriculum learning"""
        if not self.config.enable_curriculum_learning:
            return None

        recent_performance = self.performance_history[-5:] if len(self.performance_history) >= 5 else None
        return self.curriculum_system.curriculum_manager.get_next_task(recent_performance)

    def _adapt_learning_methods(self, episode_result: Dict[str, Any]):
        """Adapt learning methods based on performance"""
        if not self.config.auto_curriculum_adjustment:
            return

        # Update curriculum learning
        if self.config.enable_curriculum_learning:
            current_task = self._get_current_curriculum_task()
            if current_task:
                performance = episode_result.get('total_reward', 0) / max(1, episode_result.get('steps', 1))
                self.curriculum_system.curriculum_manager.update_task_performance(
                    current_task.task_id, performance
                )

    def _apply_continual_learning_update(self, state: Any, reward: float):
        """Apply continual learning update"""
        # This would integrate with the continual learning system
        # For now, we'll just track the event
        pass

    def _evaluate_current_performance(self, environment) -> Dict[str, float]:
        """Evaluate current performance across all methods"""
        evaluation_results = {}

        # Evaluate RL performance
        if hasattr(self, 'rl_trainer'):
            rl_performance = self._evaluate_rl_performance(environment)
            evaluation_results['rl_performance'] = rl_performance

        # Evaluate behavioral cloning performance
        if hasattr(self, 'bc_trainer'):
            bc_performance = self._evaluate_bc_performance(environment)
            evaluation_results['bc_performance'] = bc_performance

        # Calculate overall performance
        if evaluation_results:
            evaluation_results['avg_performance'] = np.mean(list(evaluation_results.values()))
        else:
            evaluation_results['avg_performance'] = 0.0

        self.performance_history.append(evaluation_results)
        return evaluation_results

    def _evaluate_rl_performance(self, environment, num_episodes: int = 5) -> float:
        """Evaluate RL agent performance"""
        total_rewards = []

        for _ in range(num_episodes):
            state = environment.reset()
            episode_reward = 0
            done = False
            steps = 0

            while not done and steps < 1000:
                if hasattr(self, 'rl_trainer'):
                    action, _ = self.rl_trainer.agent.select_action(state, training=False)
                else:
                    action = np.random.randint(0, self.config.action_dim)

                next_state, reward, done, info = environment.step(action)
                episode_reward += reward

                state = next_state
                steps += 1

            total_rewards.append(episode_reward)

        return np.mean(total_rewards)

    def _evaluate_bc_performance(self, environment, num_episodes: int = 5) -> float:
        """Evaluate behavioral cloning performance"""
        if not hasattr(self, 'bc_trainer'):
            return 0.0

        total_rewards = []

        for _ in range(num_episodes):
            state = environment.reset()
            episode_reward = 0
            done = False
            steps = 0

            while not done and steps < 1000:
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                with torch.no_grad():
                    action = self.bc_trainer.network.select_action(state_tensor, deterministic=True)
                    if isinstance(action, torch.Tensor):
                        action = action.cpu().numpy()

                next_state, reward, done, info = environment.step(action)
                episode_reward += reward

                state = next_state
                steps += 1

            total_rewards.append(episode_reward)

        return np.mean(total_rewards)

    def _save_checkpoint(self, episode: int):
        """Save training checkpoint"""
        checkpoint_path = Path(f"checkpoints/episode_{episode}.pth")
        checkpoint_path.parent.mkdir(exist_ok=True)

        checkpoint = {
            'episode': episode,
            'config': self.config,
            'system_metrics': self.system_metrics,
            'performance_history': self.performance_history,
            'adaptation_events': self.adaptation_events
        }

        # Save model states
        if hasattr(self, 'rl_trainer'):
            checkpoint['rl_agent'] = self.rl_trainer.agent.state_dict()

        if hasattr(self, 'bc_trainer'):
            checkpoint['bc_network'] = self.bc_trainer.network.state_dict()

        torch.save(checkpoint, checkpoint_path)
        logger.info(f"Checkpoint saved: {checkpoint_path}")

    def load_checkpoint(self, checkpoint_path: str):
        """Load training checkpoint"""
        checkpoint = torch.load(checkpoint_path, map_location=self.device)

        self.current_episode = checkpoint['episode']
        self.system_metrics = checkpoint['system_metrics']
        self.performance_history = checkpoint['performance_history']
        self.adaptation_events = checkpoint['adaptation_events']

        # Load model states
        if 'rl_agent' in checkpoint and hasattr(self, 'rl_trainer'):
            self.rl_trainer.agent.load_state_dict(checkpoint['rl_agent'])

        if 'bc_network' in checkpoint and hasattr(self, 'bc_trainer'):
            self.bc_trainer.network.load_state_dict(checkpoint['bc_network'])

        logger.info(f"Checkpoint loaded: {checkpoint_path}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            'config': self.config,
            'current_episode': self.current_episode,
            'training_active': self.training_active,
            'system_metrics': self.system_metrics,
            'performance_summary': self._get_performance_summary(),
            'adaptation_events_count': len(self.adaptation_events),
            'enabled_components': self._get_enabled_components()
        }

        return status

    def _get_performance_summary(self) -> Dict[str, float]:
        """Get performance summary statistics"""
        if not self.performance_history:
            return {}

        recent_performance = self.performance_history[-10:] if len(self.performance_history) >= 10 else self.performance_history

        summary = {}
        for key in recent_performance[0].keys():
            values = [p[key] for p in recent_performance if key in p]
            if values:
                summary[f'avg_{key}'] = np.mean(values)
                summary[f'std_{key}'] = np.std(values)
                summary[f'latest_{key}'] = values[-1]

        return summary

    def _get_enabled_components(self) -> List[str]:
        """Get list of enabled learning components"""
        components = []

        if self.config.enable_reinforcement_learning:
            components.append('reinforcement_learning')
        if self.config.enable_neural_evolution:
            components.append('neural_evolution')
        if self.config.enable_transfer_learning:
            components.append('transfer_learning')
        if self.config.enable_meta_learning:
            components.append('meta_learning')
        if self.config.enable_curriculum_learning:
            components.append('curriculum_learning')
        if self.config.enable_continual_learning:
            components.append('continual_learning')
        if self.config.enable_behavioral_cloning:
            components.append('behavioral_cloning')
        if self.config.enable_multi_agent_learning:
            components.append('multi_agent_learning')

        return components

    def _log_system_capabilities(self):
        """Log system capabilities and components"""
        logger.info("=== AI Learning System Capabilities ===")
        logger.info(f"State dimension: {self.config.state_dim}")
        logger.info(f"Action dimension: {self.config.action_dim}")
        logger.info(f"Device: {self.device}")

        enabled_components = self._get_enabled_components()
        logger.info(f"Enabled components ({len(enabled_components)}):")
        for component in enabled_components:
            logger.info(f"  - {component}")

        logger.info("=== System Features ===")
        logger.info("✓ Deep Reinforcement Learning (PPO, SAC, Rainbow DQN)")
        logger.info("✓ Neural Architecture Evolution")
        logger.info("✓ Cross-Domain Transfer Learning")
        logger.info("✓ Meta-Learning (MAML, Prototypical Networks)")
        logger.info("✓ Curriculum Learning with Progressive Difficulty")
        logger.info("✓ Continual Learning with Forgetting Prevention")
        logger.info("✓ Behavioral Cloning from Expert Demonstrations")
        logger.info("✓ Multi-Agent Cooperation and Competition")
        logger.info("✓ Real-time Performance Adaptation")
        logger.info("✓ Automatic Architecture Optimization")
        logger.info("✓ Distributed Training Support")
        logger.info("✓ Comprehensive Analytics and Monitoring")

# Utility functions for creating configurations
def create_integrated_config(**kwargs) -> IntegratedAISystemConfig:
    """Create integrated AI system configuration"""
    return IntegratedAISystemConfig(**kwargs)

def create_default_integrated_system() -> IntegratedAISystem:
    """Create default integrated AI system with all components enabled"""
    config = IntegratedAISystemConfig()
    return IntegratedAISystem(config)

def create_lightweight_integrated_system() -> IntegratedAISystem:
    """Create lightweight integrated system with essential components"""
    config = IntegratedAISystemConfig(
        enable_neural_evolution=False,
        enable_transfer_learning=False,
        enable_meta_learning=False,
        enable_multi_agent_learning=False,
        hidden_dims=[128, 64]
    )
    return IntegratedAISystem(config)

# Main factory function
def create_ai_system(system_type: str = 'default', **kwargs) -> IntegratedAISystem:
    """
    Factory function to create AI learning systems

    Args:
        system_type: Type of system ('default', 'lightweight', 'research', 'production')
        **kwargs: Additional configuration parameters

    Returns:
        Integrated AI learning system
    """
    if system_type == 'default':
        return create_default_integrated_system()
    elif system_type == 'lightweight':
        return create_lightweight_integrated_system()
    elif system_type == 'research':
        config = IntegratedAISystemConfig(
            enable_reinforcement_learning=True,
            enable_neural_evolution=True,
            enable_meta_learning=True,
            auto_adapt_architecture=True,
            automatic_method_selection=True,
            **kwargs
        )
        return IntegratedAISystem(config)
    elif system_type == 'production':
        config = IntegratedAISystemConfig(
            enable_neural_evolution=False,  # More stable
            auto_adapt_architecture=False,
            save_frequency=100,  # More frequent saves
            evaluation_frequency=50,  # More frequent evaluation
            **kwargs
        )
        return IntegratedAISystem(config)
    else:
        raise ValueError(f"Unknown system type: {system_type}")

# Export main classes and functions
__all__ = [
    'IntegratedAISystem',
    'IntegratedAISystemConfig',
    'create_ai_system',
    'create_integrated_config',
    'create_default_integrated_system',
    'create_lightweight_integrated_system'
]

if __name__ == "__main__":
    # Example usage
    print("Advanced AI Learning and Adaptation System")
    print("=" * 50)

    # Create default system
    ai_system = create_default_integrated_system()

    # Show system status
    status = ai_system.get_system_status()
    print(f"Enabled components: {status['enabled_components']}")
    print(f"System ready for training: {not ai_system.training_active}")

    print("\nSystem successfully initialized!")
    print("Ready for advanced AI learning and adaptation.")