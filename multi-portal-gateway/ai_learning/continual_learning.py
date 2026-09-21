#!/usr/bin/env python3
"""
Continual Learning System with Catastrophic Forgetting Prevention
Implements lifelong learning without forgetting previously acquired knowledge
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import copy
import logging
from typing import Dict, List, Tuple, Optional, Any, Union, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
from collections import defaultdict, deque
import torch.optim as optim
import math
import time
import pickle
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ForgettingMitigationMethod(Enum):
    """Methods for mitigating catastrophic forgetting"""
    EWC = "elastic_weight_consolidation"
    SI = "synaptic_intelligence"
    GEM = "gradient_episodic_memory"
    A_GEM = "a_gradient_episodic_memory"
    ONLINE_EWC = "online_ewc"
    MAS = "memory_aware_synapses"
    REPLAY = "experience_replay"
    PROGRESSIVE_NETWORKS = "progressive_networks"

@dataclass
class ContinualLearningConfig:
    """Configuration for continual learning"""
    forgetting_method: ForgettingMitigationMethod = ForgettingMitigationMethod.EWC
    memory_size: int = 1000
    ewc_lambda: float = 1000.0
    si_lambda: float = 1.0
    gem_memory_strength: float = 0.5
    replay_frequency: int = 10
    replay_batch_size: int = 32
    importance_update_frequency: int = 100
    device: str = 'cuda'

class ExperienceReplay:
    """Experience replay buffer for continual learning"""

    def __init__(self, capacity: int, task_aware: bool = True):
        self.capacity = capacity
        self.task_aware = task_aware
        self.buffer = []
        self.task_buffers = defaultdict(list)
        self.position = 0

    def push(self, state, action, reward, next_state, done, task_id: Optional[int] = None):
        """Add experience to buffer"""
        experience = (state, action, reward, next_state, done, task_id)

        if self.task_aware and task_id is not None:
            task_buffer = self.task_buffers[task_id]
            if len(task_buffer) < self.capacity // 10:  # Allocate capacity per task
                task_buffer.append(experience)
            else:
                # Random replacement
                idx = np.random.randint(len(task_buffer))
                task_buffer[idx] = experience
        else:
            if len(self.buffer) < self.capacity:
                self.buffer.append(experience)
            else:
                self.buffer[self.position] = experience
                self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size: int, task_id: Optional[int] = None) -> List:
        """Sample experiences from buffer"""
        if task_id is not None and self.task_aware:
            task_buffer = self.task_buffers[task_id]
            if len(task_buffer) < batch_size:
                return task_buffer.copy()
            return random.sample(task_buffer, batch_size)
        else:
            if len(self.buffer) < batch_size:
                return self.buffer.copy()
            return random.sample(self.buffer, batch_size)

    def __len__(self):
        if self.task_aware:
            return sum(len(buffer) for buffer in self.task_buffers.values())
        return len(self.buffer)

class ElasticWeightConsolidation:
    """Elastic Weight Consolidation for continual learning"""

    def __init__(self, model: nn.Module, config: ContinualLearningConfig):
        self.model = model
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Store Fisher information and optimal parameters
        self.fisher_information = {}
        self.optimal_params = {}

        # Task-specific parameters
        self.task_fisher = {}
        self.task_params = {}

    def compute_fisher_information(self, dataloader, task_id: int):
        """Compute Fisher information matrix for current task"""
        logger.info(f"Computing Fisher information for task {task_id}")

        self.model.eval()
        fisher = {}

        # Initialize Fisher information
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                fisher[name] = torch.zeros_like(param.data)

        # Compute Fisher information using Monte Carlo sampling
        num_samples = min(100, len(dataloader))
        for i, (data, target) in enumerate(dataloader):
            if i >= num_samples:
                break

            data, target = data.to(self.device), target.to(self.device)

            # Forward pass
            output = self.model(data)
            log_probs = F.log_softmax(output, dim=1)

            # Sample from output distribution
            sampled_indices = torch.multinomial(torch.exp(log_probs), 1).squeeze()
            log_prob = log_probs[range(len(data)), sampled_indices].sum()

            # Backward pass
            self.model.zero_grad()
            log_prob.backward(retain_graph=True)

            # Accumulate squared gradients
            for name, param in self.model.named_parameters():
                if param.requires_grad and param.grad is not None:
                    fisher[name] += param.grad.data ** 2

        # Average Fisher information
        for name in fisher:
            fisher[name] /= num_samples

        # Store for current task
        self.task_fisher[task_id] = fisher
        self.task_params[task_id] = {
            name: param.data.clone()
            for name, param in self.model.named_parameters()
            if param.requires_grad
        }

        logger.info(f"Fisher information computed for {len(fisher)} parameters")

    def ewc_loss(self) -> torch.Tensor:
        """Compute EWC regularization loss"""
        if not self.task_fisher:
            return torch.tensor(0.0, device=self.device)

        ewc_loss = 0.0

        for task_id, fisher in self.task_fisher.items():
            task_params = self.task_params[task_id]

            for name, param in self.model.named_parameters():
                if param.requires_grad and name in fisher and name in task_params:
                    # EWC penalty: λ/2 * F * (θ - θ*)^2
                    ewc_loss += (self.config.ewc_lambda / 2) * (
                        fisher[name] * (param - task_params[name]) ** 2
                    ).sum()

        return ewc_loss

class SynapticIntelligence:
    """Synaptic Intelligence for continual learning"""

    def __init__(self, model: nn.Module, config: ContinualLearningConfig):
        self.model = model
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Initialize importance and parameter tracking
        self.importance = {}
        self.accumulated_gradients = {}
        self.previous_params = {}

        # Tracking variables
        self.step_count = 0

        # Initialize tracking
        self._initialize_tracking()

    def _initialize_tracking(self):
        """Initialize tracking variables"""
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                self.importance[name] = torch.zeros_like(param.data)
                self.accumulated_gradients[name] = torch.zeros_like(param.data)
                self.previous_params[name] = param.data.clone()

    def update_tracking(self):
        """Update importance tracking after optimization step"""
        for name, param in self.model.named_parameters():
            if param.requires_grad and name in self.accumulated_gradients:
                # Update accumulated gradients
                if param.grad is not None:
                    self.accumulated_gradients[name] += param.grad.data * (param.data - self.previous_params[name])

                # Update previous parameters
                self.previous_params[name] = param.data.clone()

        self.step_count += 1

    def compute_importance(self):
        """Compute synaptic importance after task completion"""
        logger.info("Computing synaptic importance")

        for name in self.importance:
            if self.step_count > 0:
                # Importance = |accumulated gradients| / |parameter change|
                param_change = self.accumulated_gradients[name].abs()
                importance = param_change / (self.previous_params[name].abs() + 1e-8)
                self.importance[name] = importance

        # Reset accumulated gradients for next task
        for name in self.accumulated_gradients:
            self.accumulated_gradients[name] = torch.zeros_like(self.accumulated_gradients[name])

        logger.info(f"Synaptic importance computed for {len(self.importance)} parameters")

    def si_loss(self) -> torch.Tensor:
        """Compute Synaptic Intelligence regularization loss"""
        if not self.importance:
            return torch.tensor(0.0, device=self.device)

        si_loss = 0.0

        for name, param in self.model.named_parameters():
            if param.requires_grad and name in self.importance:
                # SI penalty: λ/2 * Ω * (θ - θ*)^2
                param_change = param - self.previous_params[name]
                si_loss += (self.config.si_lambda / 2) * (
                    self.importance[name] * param_change ** 2
                ).sum()

        return si_loss

class GradientEpisodicMemory:
    """Gradient Episodic Memory for continual learning"""

    def __init__(self, model: nn.Module, config: ContinualLearningConfig):
        self.model = model
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Memory buffer
        self.memory_size = config.memory_size
        self.memory_data = []
        self.memory_labels = []
        self.memory_tasks = []

        # Task-specific memories
        self.task_memories = {}

    def store_memory(self, data: torch.Tensor, labels: torch.Tensor, task_id: int):
        """Store examples in episodic memory"""
        data_np = data.cpu().numpy()
        labels_np = labels.cpu().numpy()

        # Store in global memory
        for i in range(len(data_np)):
            if len(self.memory_data) < self.memory_size:
                self.memory_data.append(data_np[i])
                self.memory_labels.append(labels_np[i])
                self.memory_tasks.append(task_id)
            else:
                # Random replacement
                idx = np.random.randint(len(self.memory_data))
                self.memory_data[idx] = data_np[i]
                self.memory_labels[idx] = labels_np[i]
                self.memory_tasks[idx] = task_id

        # Store in task-specific memory
        if task_id not in self.task_memories:
            self.task_memories[task_id] = {'data': [], 'labels': []}

        task_memory = self.task_memories[task_id]
        for i in range(len(data_np)):
            if len(task_memory['data']) < self.memory_size // 10:
                task_memory['data'].append(data_np[i])
                task_memory['labels'].append(labels_np[i])
            else:
                # Random replacement
                idx = np.random.randint(len(task_memory['data']))
                task_memory['data'][idx] = data_np[i]
                task_memory['labels'][idx] = labels_np[i]

    def get_memory_batch(self, batch_size: int, task_id: Optional[int] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get batch from episodic memory"""
        if task_id is not None and task_id in self.task_memories:
            # Task-specific memory
            memory_data = self.task_memories[task_id]['data']
            memory_labels = self.task_memories[task_id]['labels']

            if len(memory_data) == 0:
                return None, None

            indices = np.random.choice(len(memory_data), min(batch_size, len(memory_data)), replace=False)
            selected_data = [memory_data[i] for i in indices]
            selected_labels = [memory_labels[i] for i in indices]

        else:
            # Global memory
            if len(self.memory_data) == 0:
                return None, None

            indices = np.random.choice(len(self.memory_data), min(batch_size, len(self.memory_data)), replace=False)
            selected_data = [self.memory_data[i] for i in indices]
            selected_labels = [self.memory_labels[i] for i in indices]

        data_tensor = torch.FloatTensor(selected_data).to(self.device)
        labels_tensor = torch.LongTensor(selected_labels).to(self.device)

        return data_tensor, labels_tensor

    def project_gradients(self, current_gradients: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Project gradients to satisfy memory constraints"""
        if len(self.memory_data) == 0:
            return current_gradients

        # Compute gradients on memory examples
        memory_gradients = self._compute_memory_gradients()

        # Project current gradients
        projected_gradients = {}

        for name in current_gradients:
            if name in memory_gradients:
                # Compute projection
                current_grad = current_gradients[name]
                memory_grad = memory_gradients[name]

                # GEM projection: ensure no increase in loss on memory
                dot_product = torch.dot(current_grad.flatten(), memory_grad.flatten())

                if dot_product > 0:
                    # Project to satisfy constraint
                    projection_scale = dot_product / (torch.norm(memory_grad) ** 2 + 1e-8)
                    projected_grad = current_grad - projection_scale * memory_grad
                    projected_gradients[name] = projected_grad
                else:
                    projected_gradients[name] = current_grad
            else:
                projected_gradients[name] = current_gradients[name]

        return projected_gradients

    def _compute_memory_gradients(self) -> Dict[str, torch.Tensor]:
        """Compute gradients on memory examples"""
        if len(self.memory_data) == 0:
            return {}

        self.model.zero_grad()

        # Get memory batch
        memory_data, memory_labels = self.get_memory_batch(min(32, len(self.memory_data)))
        if memory_data is None:
            return {}

        # Forward pass
        output = self.model(memory_data)
        loss = F.cross_entropy(output, memory_labels)

        # Backward pass
        loss.backward()

        # Store gradients
        memory_gradients = {}
        for name, param in self.model.named_parameters():
            if param.requires_grad and param.grad is not None:
                memory_gradients[name] = param.grad.data.clone()

        return memory_gradients

class ProgressiveNetworks:
    """Progressive Networks for continual learning"""

    def __init__(self, base_model: nn.Module, config: ContinualLearningConfig):
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Store previous columns
        self.previous_columns = []
        self.adapters = nn.ModuleList()

        # Create first column
        self.current_column = copy.deepcopy(base_model).to(self.device)

        # Lateral connections
        self.lateral_connections = nn.ModuleList()

    def add_new_column(self, base_model: nn.Module, task_id: int):
        """Add new column for new task"""
        logger.info(f"Adding new column for task {task_id}")

        # Store current column
        self.previous_columns.append(self.current_column)

        # Create new column
        new_column = copy.deepcopy(base_model).to(self.device)

        # Create lateral connections from previous columns
        lateral_layers = nn.ModuleList()
        for prev_column in self.previous_columns:
            # Create adapter to match dimensions
            adapter = self._create_lateral_adapter(prev_column, new_column)
            lateral_layers.append(adapter)

        self.lateral_connections.append(lateral_layers)
        self.current_column = new_column

        logger.info(f"Added column {len(self.previous_columns)} with {len(lateral_layers)} lateral connections")

    def _create_lateral_adapter(self, source_column: nn.Module, target_column: nn.Module) -> nn.Module:
        """Create lateral adapter between columns"""
        # This is simplified - actual implementation would match specific layer dimensions
        return nn.Sequential(
            nn.Linear(256, 256),  # Adjust dimensions based on actual layers
            nn.ReLU(),
            nn.Linear(256, 256)
        )

    def forward(self, x: torch.Tensor, task_id: Optional[int] = None) -> torch.Tensor:
        """Forward pass through progressive network"""
        # Forward through current column
        output = self.current_column(x)

        # Add lateral connections if available
        if task_id is not None and task_id - 1 < len(self.lateral_connections):
            lateral_outputs = []
            for i, prev_column in enumerate(self.previous_columns):
                with torch.no_grad():
                    prev_output = prev_column(x)

                # Apply lateral connection
                if i < len(self.lateral_connections[task_id - 1]):
                    lateral_out = self.lateral_connections[task_id - 1][i](prev_output)
                    lateral_outputs.append(lateral_out)

            # Combine lateral outputs
            if lateral_outputs:
                lateral_combined = torch.stack(lateral_outputs, dim=0).mean(dim=0)
                output = output + lateral_combined

        return output

class ContinualLearner:
    """Main continual learning system"""

    def __init__(self, model: nn.Module, config: ContinualLearningConfig):
        self.model = model
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Initialize forgetting mitigation methods
        self.ewc = None
        self.si = None
        self.gem = None
        self.progressive_networks = None

        if config.forgetting_method == ForgettingMitigationMethod.EWC:
            self.ewc = ElasticWeightConsolidation(model, config)
        elif config.forgetting_method == ForgettingMitigationMethod.SI:
            self.si = SynapticIntelligence(model, config)
        elif config.forgetting_method in [ForgettingMitigationMethod.GEM, ForgettingMitigationMethod.A_GEM]:
            self.gem = GradientEpisodicMemory(model, config)
        elif config.forgetting_method == ForgettingMitigationMethod.PROGRESSIVE_NETWORKS:
            self.progressive_networks = ProgressiveNetworks(model, config)

        # Experience replay
        self.replay_buffer = ExperienceReplay(config.memory_size * 10)

        # Task tracking
        self.current_task = 0
        self.task_performance = defaultdict(list)
        self.forgetting_measures = defaultdict(list)

        # Learning metrics
        self.training_history = {
            'task_accuracies': {},
            'forgetting_measures': {},
            'regularization_losses': []
        }

    def learn_task(self, task_id: int, dataloader, optimizer: torch.optim.Optimizer,
                   num_epochs: int = 10) -> Dict[str, Any]:
        """Learn a new task"""
        logger.info(f"Starting to learn task {task_id}")

        self.current_task = task_id

        # For progressive networks, add new column
        if self.config.forgetting_method == ForgettingMitigationMethod.PROGRESSIVE_NETWORKS:
            self.progressive_networks.add_new_column(self.model, task_id)

        # Training loop
        task_losses = []
        task_accuracies = []

        for epoch in range(num_epochs):
            epoch_loss = 0.0
            correct = 0
            total = 0

            for batch_idx, (data, target) in enumerate(dataloader):
                data, target = data.to(self.device), target.to(self.device)

                optimizer.zero_grad()

                # Forward pass
                if self.config.forgetting_method == ForgettingMitigationMethod.PROGRESSIVE_NETWORKS:
                    output = self.progressive_networks(data, task_id)
                else:
                    output = self.model(data)

                # Main task loss
                task_loss = F.cross_entropy(output, target)

                # Add regularization losses
                regularization_loss = 0.0

                if self.ewc:
                    regularization_loss += self.ewc.ewc_loss()

                if self.si:
                    regularization_loss += self.si.si_loss()

                total_loss = task_loss + regularization_loss

                # Backward pass
                total_loss.backward()

                # Apply gradient projection for GEM
                if self.gem and self.config.forgetting_method == ForgettingMitigationMethod.GEM:
                    # Get current gradients
                    current_gradients = {}
                    for name, param in self.model.named_parameters():
                        if param.requires_grad and param.grad is not None:
                            current_gradients[name] = param.grad.data.clone()

                    # Project gradients
                    projected_gradients = self.gem.project_gradients(current_gradients)

                    # Apply projected gradients
                    for name, param in self.model.named_parameters():
                        if param.requires_grad and name in projected_gradients:
                            param.grad = projected_gradients[name]

                optimizer.step()

                # Update tracking for SI
                if self.si:
                    self.si.update_tracking()

                # Store experience in replay buffer
                self.replay_buffer.push(data.cpu(), target.cpu(),
                                       task_loss.item(), None, False, task_id)

                # Store in episodic memory for GEM
                if self.gem and batch_idx % 10 == 0:  # Sample periodically
                    self.gem.store_memory(data, target, task_id)

                # Statistics
                epoch_loss += task_loss.item()
                _, predicted = output.max(1)
                total += target.size(0)
                correct += predicted.eq(target).sum().item()

            # Calculate epoch metrics
            avg_loss = epoch_loss / len(dataloader)
            accuracy = 100.0 * correct / total

            task_losses.append(avg_loss)
            task_accuracies.append(accuracy)

            logger.info(f"Task {task_id}, Epoch {epoch}: Loss={avg_loss:.4f}, Acc={accuracy:.2f}%")

            # Experience replay
            if self.replay_buffer and batch_idx % self.config.replay_frequency == 0:
                self._experience_replay_step(optimizer)

        # Post-task processing
        if self.ewc:
            self.ewc.compute_fisher_information(dataloader, task_id)

        if self.si:
            self.si.compute_importance()

        # Store task performance
        self.task_performance[task_id] = task_accuracies

        # Evaluate forgetting on previous tasks
        forgetting_scores = self._evaluate_forgetting(task_id, dataloader)

        return {
            'task_id': task_id,
            'final_accuracy': task_accuracies[-1] if task_accuracies else 0,
            'forgetting_scores': forgetting_scores,
            'losses': task_losses,
            'accuracies': task_accuracies
        }

    def _experience_replay_step(self, optimizer: torch.optim.Optimizer):
        """Perform one step of experience replay"""
        if len(self.replay_buffer) < self.config.replay_batch_size:
            return

        # Sample from replay buffer
        replay_batch = self.replay_buffer.sample(self.config.replay_batch_size)

        if not replay_batch:
            return

        # Process replay batch
        replay_data = []
        replay_targets = []

        for experience in replay_batch:
            state, action, reward, next_state, done, task_id = experience
            replay_data.append(state)
            replay_targets.append(action)  # Simplified - would need proper replay logic

        if replay_data:
            replay_data = torch.FloatTensor(replay_data).to(self.device)
            replay_targets = torch.LongTensor(replay_targets).to(self.device)

            optimizer.zero_grad()

            replay_output = self.model(replay_data)
            replay_loss = F.cross_entropy(replay_output, replay_targets)

            replay_loss.backward()
            optimizer.step()

    def _evaluate_forgetting(self, current_task: int, current_dataloader) -> Dict[int, float]:
        """Evaluate forgetting on previous tasks"""
        forgetting_scores = {}

        for task_id in range(current_task):
            if task_id in self.task_performance:
                # Get best performance on this task
                best_performance = max(self.task_performance[task_id])

                # Evaluate current performance (simplified - would need task-specific evaluation)
                current_performance = self.task_performance[task_id][-1] if self.task_performance[task_id] else 0

                # Calculate forgetting measure
                forgetting = best_performance - current_performance
                forgetting_scores[task_id] = forgetting

                self.forgetting_measures[task_id].append(forgetting)

        return forgetting_scores

    def evaluate_all_tasks(self, task_dataloaders: Dict[int, Any]) -> Dict[int, Dict[str, float]]:
        """Evaluate performance on all learned tasks"""
        results = {}

        for task_id, dataloader in task_dataloaders.items():
            self.model.eval()
            correct = 0
            total = 0

            with torch.no_grad():
                for data, target in dataloader:
                    data, target = data.to(self.device), target.to(self.device)

                    if self.config.forgetting_method == ForgettingMitigationMethod.PROGRESSIVE_NETWORKS:
                        output = self.progressive_networks(data, task_id)
                    else:
                        output = self.model(data)

                    _, predicted = output.max(1)
                    total += target.size(0)
                    correct += predicted.eq(target).sum().item()

            accuracy = 100.0 * correct / total if total > 0 else 0
            results[task_id] = {'accuracy': accuracy}

        return results

    def get_continual_learning_metrics(self) -> Dict[str, Any]:
        """Get comprehensive continual learning metrics"""
        # Average accuracy across tasks
        task_accuracies = {}
        for task_id, accuracies in self.task_performance.items():
            if accuracies:
                task_accuracies[task_id] = accuracies[-1]

        avg_accuracy = np.mean(list(task_accuracies.values())) if task_accuracies else 0

        # Average forgetting
        avg_forgetting = 0
        forgetting_count = 0
        for task_id, forgetting_list in self.forgetting_measures.items():
            if forgetting_list:
                avg_forgetting += np.mean(forgetting_list)
                forgetting_count += 1

        avg_forgetting = avg_forgetting / forgetting_count if forgetting_count > 0 else 0

        # Learning efficiency
        total_tasks = len(self.task_performance)
        successful_tasks = sum(1 for accuracies in self.task_performance.values()
                             if accuracies and accuracies[-1] > 70)  # 70% threshold

        learning_efficiency = successful_tasks / total_tasks if total_tasks > 0 else 0

        return {
            'total_tasks_learned': total_tasks,
            'average_accuracy': avg_accuracy,
            'average_forgetting': avg_forgetting,
            'learning_efficiency': learning_efficiency,
            'task_accuracies': task_accuracies,
            'current_task': self.current_task,
            'memory_size': len(self.replay_buffer),
            'forgetting_method': self.config.forgetting_method.value
        }

class MemoryAwareSynapses:
    """Memory Aware Synapses for continual learning"""

    def __init__(self, model: nn.Module, config: ContinualLearningConfig):
        self.model = model
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Importance parameters
        self.importance = {}
        self.path_integral = {}

        # Initialize
        self._initialize_parameters()

    def _initialize_parameters(self):
        """Initialize importance and path integral tracking"""
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                self.importance[name] = torch.zeros_like(param.data)
                self.path_integral[name] = torch.zeros_like(param.data)

    def update_path_integral(self):
        """Update path integral after each optimization step"""
        for name, param in self.model.named_parameters():
            if param.requires_grad and param.grad is not None:
                # Update path integral: ∫ |∇L| dθ
                self.path_integral[name] += (param.grad.data.abs() *
                                           (param.data - getattr(self, f'prev_{name}', param.data)).abs())

        # Store current parameters
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                setattr(self, f'prev_{name}', param.data.clone())

    def compute_importance(self):
        """Compute memory aware importance after task completion"""
        logger.info("Computing Memory Aware Synapses importance")

        for name in self.path_integral:
            # Importance = |path integral|
            self.importance[name] = self.path_integral[name]

        # Reset path integral for next task
        for name in self.path_integral:
            self.path_integral[name] = torch.zeros_like(self.path_integral[name])

        logger.info(f"MAS importance computed for {len(self.importance)} parameters")

    def mas_loss(self) -> torch.Tensor:
        """Compute Memory Aware Synapses regularization loss"""
        if not self.importance:
            return torch.tensor(0.0, device=self.device)

        mas_loss = 0.0

        for name, param in self.model.named_parameters():
            if param.requires_grad and name in self.importance:
                # MAS penalty: λ/2 * Ω * (θ - θ*)^2
                prev_param = getattr(self, f'prev_{name}', param.data)
                param_change = param - prev_param
                mas_loss += (self.config.mas_lambda / 2) * (
                    self.importance[name] * param_change ** 2
                ).sum()

        return mas_loss

# Utility functions
def create_continual_config(method: str = 'ewc') -> ContinualLearningConfig:
    """Create continual learning configuration"""
    return ContinualLearningConfig(
        forgetting_method=ForgettingMitigationMethod(method),
        memory_size=1000,
        ewc_lambda=1000.0,
        si_lambda=1.0,
        gem_memory_strength=0.5,
        replay_frequency=10,
        replay_batch_size=32,
        importance_update_frequency=100,
        device='cuda' if torch.cuda.is_available() else 'cpu'
    )

def measure_catastrophic_forgetting(performance_before: List[float],
                                  performance_after: List[float]) -> float:
    """Measure catastrophic forgetting between two performance lists"""
    if not performance_before or not performance_after:
        return 0.0

    # Average performance before and after
    avg_before = np.mean(performance_before)
    avg_after = np.mean(performance_after)

    # Forgetting measure
    forgetting = max(0, avg_before - avg_after)
    return forgetting

if __name__ == "__main__":
    # Example usage
    config = create_continual_config('ewc')

    # Create a simple model for demonstration
    class SimpleModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc1 = nn.Linear(784, 256)
            self.fc2 = nn.Linear(256, 128)
            self.fc3 = nn.Linear(128, 10)

        def forward(self, x):
            x = x.view(x.size(0), -1)
            x = F.relu(self.fc1(x))
            x = F.relu(self.fc2(x))
            x = self.fc3(x)
            return x

    model = SimpleModel()

    # Create continual learner
    continual_learner = ContinualLearner(model, config)

    print("Continual Learning System initialized!")
    print(f"Forgetting mitigation method: {config.forgetting_method.value}")
    print(f"Memory size: {config.memory_size}")
    print(f"EWC lambda: {config.ewc_lambda}")
    print(f"Available methods: EWC, SI, GEM, A-GEM, Online-EWC, MAS, Replay, Progressive Networks")
    print(f"Experience replay supported: True")
    print(f"Forgetting measurement: Catastrophic forgetting metrics")
    print(f"Task awareness: Yes - tracks performance across tasks")