"""
Advanced Continual Learning for DMLogn8n
Lifelong learning with neural plasticity and catastrophic forgetting prevention
Based on latest research in continual learning and neural plasticity (2024-2025)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import math
from collections import defaultdict, deque
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, confusion_matrix
import seaborn as sns
from copy import deepcopy


@dataclass
class ContinualConfig:
    """Configuration for continual learning"""
    # Network architecture
    input_dim: int = 512
    hidden_dim: int = 256
    output_dim: int = 100
    num_layers: int = 3
    dropout: float = 0.1

    # Learning parameters
    learning_rate: float = 0.001
    batch_size: int = 32
    memory_size: int = 1000
    rehearsal_ratio: float = 0.1

    # Elastic Weight Consolidation (EWC)
    ewc_lambda: float = 1000.0
    ewc_fisher_samples: int = 200

    # Synaptic Intelligence
    si_lambda: float = 1.0
    si_normalization: bool = True

    # Memory Replay
    memory_strategy: str = "reservoir"  # reservoir, herding, balanced
    replay_batch_size: int = 32

    # Dynamic Architecture
    growth_threshold: float = 0.8
    prune_threshold: float = 0.01
    max_units: int = 1000

    # Neural Plasticity
    plasticity_type: str = "hebbian"  # hebbian, oja, homeostatic
    plasticity_lr: float = 0.01
    homeostatic_target: float = 0.1

    # Progressive Networks
    use_progressive: bool = False
    freeze_previous: bool = True


class PlasticityLayer(nn.Module):
    """Neural plasticity layer implementing various learning rules"""
    def __init__(self, in_dim: int, out_dim: int, config: ContinualConfig):
        super().__init__()
        self.config = config

        # Standard linear layer
        self.linear = nn.Linear(in_dim, out_dim)

        # Plasticity parameters
        if config.plasticity_type == "hebbian":
            self.hebbian_lr = nn.Parameter(torch.tensor(config.plasticity_lr))
        elif config.plasticity_type == "oja":
            self.oja_lr = nn.Parameter(torch.tensor(config.plasticity_lr))
        elif config.plasticity_type == "homeostatic":
            self.homeostatic_lr = nn.Parameter(torch.tensor(config.plasticity_lr))
            self.target_rate = config.homeostatic_target
            self.activity_history = deque(maxlen=100)

        # Plasticity weights
        self.plastic_weights = nn.Parameter(torch.zeros(out_dim, in_dim))
        self.register_buffer('hebbian_trace', torch.zeros(out_dim, in_dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Standard linear transformation
        output = self.linear(x)

        # Add plastic component
        if self.config.plasticity_type == "hebbian":
            plastic_output = F.linear(x, self.plastic_weights)
            output = output + plastic_output

        elif self.config.plasticity_type == "oja":
            plastic_output = F.linear(x, self.plastic_weights)
            output = output + plastic_output

        elif self.config.plasticity_type == "homeostatic":
            plastic_output = F.linear(x, self.plastic_weights)
            output = output + plastic_output

            # Track activity for homeostatic plasticity
            mean_activity = output.mean().item()
            self.activity_history.append(mean_activity)

        return output

    def update_plasticity(self, x: torch.Tensor, output: torch.Tensor):
        """Update plastic weights based on learning rule"""
        if self.training:
            if self.config.plasticity_type == "hebbian":
                # Hebbian learning: Δw = η * (pre * post)
                with torch.no_grad():
                    # Outer product of input and output
                    hebbian_update = torch.outer(output.mean(dim=0), x.mean(dim=0))
                    self.hebbian_trace = 0.9 * self.hebbian_trace + 0.1 * hebbian_update
                    self.plastic_weights.data += self.hebbian_lr * self.hebbian_trace

            elif self.config.plasticity_type == "oja":
                # Oja's rule: Δw = η * (pre * post - w * post²)
                with torch.no_grad():
                    oja_update = torch.outer(output.mean(dim=0), x.mean(dim=0))
                    normalization = torch.norm(self.plastic_weights, dim=1, keepdim=True) * (output.mean(dim=0) ** 2).mean()
                    self.plastic_weights.data += self.oja_lr * (oja_update - normalization)

            elif self.config.plasticity_type == "homeostatic":
                # Homeostatic plasticity: maintain average activity
                if len(self.activity_history) > 10:
                    avg_activity = np.mean(self.activity_history)
                    deviation = avg_activity - self.target_rate

                    with torch.no_grad():
                        # Adjust plastic weights to regulate activity
                        regulation = -deviation * torch.sign(self.plastic_weights)
                        self.plastic_weights.data += self.homeostatic_lr * regulation


class ExperienceReplay:
    """Advanced experience replay for continual learning"""
    def __init__(self, config: ContinualConfig):
        self.config = config
        self.memory_size = config.memory_size
        self.memory_strategy = config.memory_strategy

        # Memory buffers
        self.experience_buffer = []
        self.task_memories = defaultdict(list)
        self.class_balancers = defaultdict(int)

    def add_experience(self, x: torch.Tensor, y: torch.Tensor, task_id: int, class_id: Optional[int] = None):
        """Add experience to memory"""
        experience = {
            'x': x.detach().cpu(),
            'y': y.detach().cpu(),
            'task_id': task_id,
            'class_id': class_id
        }

        if self.memory_strategy == "reservoir":
            # Reservoir sampling
            if len(self.experience_buffer) < self.memory_size:
                self.experience_buffer.append(experience)
            else:
                # Random replacement
                idx = np.random.randint(0, len(self.experience_buffer) + 1)
                if idx < len(self.experience_buffer):
                    self.experience_buffer[idx] = experience

        elif self.memory_strategy == "herding":
            # Herding - select diverse examples
            self.task_memories[task_id].append(experience)

            # Keep only most diverse examples
            if len(self.task_memories[task_id]) > self.memory_size // 10:  # Per task limit
                self.task_memories[task_id] = self._select_diverse_examples(
                    self.task_memories[task_id]
                )

        elif self.memory_strategy == "balanced":
            # Class-balanced sampling
            if class_id is not None:
                self.class_balancers[class_id] += 1

            # Ensure class balance
            self._ensure_class_balance(experience)

        # Update main buffer
        self.experience_buffer = self._consolidate_memory()

    def _select_diverse_examples(self, experiences: List[Dict]) -> List[Dict]:
        """Select diverse examples using k-means-like clustering"""
        if len(experiences) <= self.memory_size // 10:
            return experiences

        # Convert to tensor
        x_stack = torch.stack([exp['x'] for exp in experiences])

        # Simple diversity selection (farthest first traversal)
        selected = []
        remaining = list(range(len(experiences)))

        # Select first example randomly
        first_idx = np.random.choice(remaining)
        selected.append(first_idx)
        remaining.remove(first_idx)

        # Select farthest examples
        while len(selected) < self.memory_size // 10 and remaining:
            distances = []
            for idx in remaining:
                # Compute minimum distance to selected examples
                min_dist = min(
                    torch.norm(x_stack[idx] - x_stack[sel_idx]).item()
                    for sel_idx in selected
                )
                distances.append(min_dist)

            # Select farthest example
            farthest_idx = remaining[np.argmax(distances)]
            selected.append(farthest_idx)
            remaining.remove(farthest_idx)

        return [experiences[i] for i in selected]

    def _ensure_class_balance(self, new_experience: Dict):
        """Ensure class balance in memory"""
        # This is a simplified implementation
        # In practice, you'd maintain class-specific quotas
        pass

    def _consolidate_memory(self) -> List[Dict]:
        """Consolidate memory from different strategies"""
        all_experiences = []

        # Add experiences from task memories
        for task_experiences in self.task_memories.values():
            all_experiences.extend(task_experiences)

        # Add experiences from main buffer
        all_experiences.extend(self.experience_buffer)

        # Limit total size
        if len(all_experiences) > self.memory_size:
            # Random sampling to maintain size
            indices = np.random.choice(len(all_experiences), self.memory_size, replace=False)
            all_experiences = [all_experiences[i] for i in indices]

        return all_experiences

    def sample_batch(self, batch_size: int) -> Optional[Tuple[torch.Tensor, torch.Tensor, torch.Tensor]]:
        """Sample a batch from memory"""
        if len(self.experience_buffer) == 0:
            return None

        # Sample experiences
        indices = np.random.choice(len(self.experience_buffer), min(batch_size, len(self.experience_buffer)), replace=False)
        batch = [self.experience_buffer[i] for i in indices]

        # Stack tensors
        x_batch = torch.stack([exp['x'] for exp in batch])
        y_batch = torch.stack([exp['y'] for exp in batch])
        task_ids = torch.tensor([exp['task_id'] for exp in batch])

        return x_batch, y_batch, task_ids


class EWCRegularizer:
    """Elastic Weight Consolidation for catastrophic forgetting prevention"""
    def __init__(self, model: nn.Module, config: ContinualConfig):
        self.model = model
        self.config = config
        self.fisher_information = {}
        self.optimal_params = {}

    def compute_fisher_information(self, dataloader, task_id: int):
        """Compute Fisher information matrix for current task"""
        self.model.eval()

        # Initialize Fisher information
        fisher = {}
        for name, param in self.model.named_parameters():
            fisher[name] = torch.zeros_like(param.data)

        # Sample data to compute Fisher
        num_samples = min(len(dataloader), self.config.ewc_fisher_samples)
        samples_processed = 0

        with torch.no_grad():
            for batch in dataloader:
                if samples_processed >= num_samples:
                    break

                x, y = batch
                if isinstance(x, tuple):
                    x = x[0]

                # Forward pass
                output = self.model(x)
                log_probs = F.log_softmax(output, dim=-1)

                # Sample from output distribution
                sample = torch.multinomial(torch.exp(log_probs), 1).squeeze()

                # Compute gradients
                log_likelihood = F.nll_loss(log_probs, sample, reduction='sum')
                grads = torch.autograd.grad(log_likelihood, self.model.parameters(), create_graph=False)

                # Accumulate Fisher information
                for (name, param), grad in zip(self.model.named_parameters(), grads):
                    if grad is not None:
                        fisher[name] += grad.pow(2)

                samples_processed += x.size(0)

        # Normalize Fisher information
        for name in fisher:
            fisher[name] /= num_samples

        # Store Fisher information and optimal parameters
        self.fisher_information[task_id] = fisher
        self.optimal_params[task_id] = {
            name: param.data.clone() for name, param in self.model.named_parameters()
        }

    def ewc_loss(self) -> torch.Tensor:
        """Compute EWC regularization loss"""
        ewc_loss = 0.0

        for task_id in self.fisher_information:
            for name, param in self.model.named_parameters():
                if name in self.fisher_information[task_id]:
                    fisher = self.fisher_information[task_id][name]
                    optimal = self.optimal_params[task_id][name]

                    # EWC loss term
                    ewc_loss += (fisher * (param - optimal).pow(2)).sum()

        return self.config.ewc_lambda * ewc_loss


class SIRegularizer:
    """Synaptic Intelligence regularizer"""
    def __init__(self, model: nn.Module, config: ContinualConfig):
        self.model = model
        self.config = config

        # Initialize SI parameters
        self.omega = {}
        self.theta = {}
        self.cumulative_grads = {}

        for name, param in self.model.named_parameters():
            self.omega[name] = torch.zeros_like(param.data)
            self.theta[name] = param.data.clone()
            self.cumulative_grads[name] = torch.zeros_like(param.data)

    def update_cumulative_gradients(self):
        """Update cumulative gradients after each parameter update"""
        for name, param in self.model.named_parameters():
            if param.grad is not None:
                # Update cumulative gradients
                self.cumulative_grads[name] += param.grad.data.pow(2)

    def compute_omega(self):
        """Compute importance weights after task completion"""
        for name, param in self.model.named_parameters():
            if self.cumulative_grads[name].sum() > 0:
                # Compute importance weight
                delta_theta = param.data - self.theta[name]
                self.omega[name] = self.cumulative_grads[name] / (delta_theta.pow(2) + 1e-8)

                # Update stored parameters
                self.theta[name] = param.data.clone()

                # Reset cumulative gradients
                self.cumulative_grads[name] = torch.zeros_like(param.data)

    def si_loss(self) -> torch.Tensor:
        """Compute Synaptic Intelligence regularization loss"""
        si_loss = 0.0

        for name, param in self.model.named_parameters():
            if name in self.omega:
                delta_theta = param.data - self.theta[name]
                si_loss += (self.omega[name] * delta_theta.pow(2)).sum()

        return self.config.si_lambda * si_loss


class ProgressiveNetwork(nn.Module):
    """Progressive Networks for lifelong learning"""
    def __init__(self, config: ContinualConfig):
        super().__init__()
        self.config = config

        self.columns = nn.ModuleList()
        self.lateral_connections = nn.ModuleDict()
        self.task_id_mapping = {}

        # Add first column
        self.add_column(0)

    def add_column(self, task_id: int):
        """Add new column for new task"""
        # Create new network column
        column = nn.ModuleList()

        # Input layer
        column.append(nn.Linear(self.config.input_dim, self.config.hidden_dim))

        # Hidden layers
        for _ in range(self.config.num_layers - 1):
            column.append(nn.Linear(self.config.hidden_dim, self.config.hidden_dim))

        # Output layer
        column.append(nn.Linear(self.config.hidden_dim, self.config.output_dim))

        self.columns.append(column)
        self.task_id_mapping[task_id] = len(self.columns) - 1

        # Add lateral connections from previous columns
        if len(self.columns) > 1:
            for prev_col_idx in range(len(self.columns) - 1):
                lateral_name = f"col_{prev_col_idx}_to_col_{len(self.columns)-1}"
                self.lateral_connections[lateral_name] = nn.ModuleList()

                for layer_idx in range(len(column)):
                    if layer_idx > 0:  # Don't connect to input layer
                        lateral_layer = nn.Linear(self.config.hidden_dim, self.config.hidden_dim)
                        self.lateral_connections[lateral_name].append(lateral_layer)

        # Freeze previous columns if specified
        if self.config.freeze_previous and len(self.columns) > 1:
            for prev_col in self.columns[:-1]:
                for param in prev_col.parameters():
                    param.requires_grad = False

    def forward(self, x: torch.Tensor, task_id: int) -> torch.Tensor:
        """Forward pass for specific task"""
        if task_id not in self.task_id_mapping:
            raise ValueError(f"Task {task_id} not found. Available tasks: {list(self.task_id_mapping.keys())}")

        col_idx = self.task_id_mapping[task_id]
        column = self.columns[col_idx]

        # Forward through column with lateral connections
        output = x
        for layer_idx, layer in enumerate(column):
            # Standard forward
            output = layer(output)
            if layer_idx < len(column) - 1:  # No activation on output layer
                output = F.relu(output)

            # Add lateral connections
            if layer_idx > 0 and col_idx > 0:
                lateral_sum = torch.zeros_like(output)

                for prev_col_idx in range(col_idx):
                    lateral_name = f"col_{prev_col_idx}_to_col_{col_idx}"
                    if lateral_name in self.lateral_connections:
                        lateral_layers = self.lateral_connections[lateral_name]

                        # Forward through previous column to get lateral input
                        lateral_input = x
                        prev_column = self.columns[prev_col_idx]
                        with torch.no_grad():
                            for prev_layer_idx, prev_layer in enumerate(prev_column):
                                lateral_input = prev_layer(lateral_input)
                                if prev_layer_idx < len(prev_column) - 1:
                                    lateral_input = F.relu(lateral_input)

                                if prev_layer_idx == layer_idx - 1:
                                    break

                        # Apply lateral connection
                        lateral_layer = lateral_layers[layer_idx - 1]
                        lateral_output = lateral_layer(lateral_input)
                        lateral_sum = lateral_sum + lateral_output

                # Add lateral input
                output = output + lateral_sum

        return output


class ContinualLearner(nn.Module):
    """Advanced continual learning system combining multiple techniques"""
    def __init__(self, config: ContinualConfig):
        super().__init__()
        self.config = config

        # Base network with plasticity
        self.layers = nn.ModuleList()
        in_dim = config.input_dim

        for i in range(config.num_layers):
            out_dim = config.hidden_dim if i < config.num_layers - 1 else config.output_dim
            layer = PlasticityLayer(in_dim, out_dim, config)
            self.layers.append(layer)
            in_dim = out_dim

        # Regularization methods
        self.ewc_regularizer = EWCRegularizer(self, config) if config.ewc_lambda > 0 else None
        self.si_regularizer = SIRegularizer(self, config) if config.si_lambda > 0 else None

        # Experience replay
        self.replay_buffer = ExperienceReplay(config)

        # Progressive network (optional)
        if config.use_progressive:
            self.progressive_net = ProgressiveNetwork(config)

        # Task tracking
        self.learned_tasks = []
        self.task_performance = {}

        # Neural plasticity tracking
        self.plasticity_metrics = defaultdict(list)

    def forward(self, x: torch.Tensor, task_id: Optional[int] = None) -> torch.Tensor:
        """Forward pass"""
        if self.config.use_progressive and task_id is not None:
            return self.progressive_net(x, task_id)

        # Standard forward through plasticity layers
        for layer in self.layers:
            output = layer(x)
            x = output

        return output

    def learn_task(self, dataloader, task_id: int, num_epochs: int = 10) -> Dict[str, float]:
        """Learn a new task"""
        print(f"Learning task {task_id}...")

        self.train()
        optimizer = torch.optim.Adam(self.parameters(), lr=self.config.learning_rate)

        # Track performance
        task_losses = []
        task_accuracies = []

        for epoch in range(num_epochs):
            epoch_losses = []
            correct = 0
            total = 0

            for batch in dataloader:
                # Handle different batch formats
                if isinstance(batch, (list, tuple)):
                    x, y = batch[0], batch[1]
                else:
                    x, y = batch.x, batch.y

                # Move to device
                if hasattr(x, 'to'):
                    x = x.to(next(self.parameters()).device)
                    y = y.to(next(self.parameters()).device)

                optimizer.zero_grad()

                # Forward pass
                output = self.forward(x, task_id)

                # Main task loss
                task_loss = F.cross_entropy(output, y)

                # Add regularization losses
                total_loss = task_loss

                if self.ewc_regularizer:
                    total_loss += self.ewc_regularizer.ewc_loss()

                if self.si_regularizer:
                    total_loss += self.si_regularizer.si_loss()

                # Backward pass
                total_loss.backward()

                # Update cumulative gradients for SI
                if self.si_regularizer:
                    self.si_regularizer.update_cumulative_gradients()

                # Clip gradients
                torch.nn.utils.clip_grad_norm_(self.parameters(), max_norm=1.0)

                optimizer.step()

                # Update plasticity
                for layer in self.layers:
                    if isinstance(layer, PlasticityLayer):
                        layer.update_plasticity(x, output)

                # Track metrics
                epoch_losses.append(task_loss.item())

                with torch.no_grad():
                    pred = output.argmax(dim=-1)
                    correct += (pred == y).sum().item()
                    total += y.size(0)

            # Compute epoch metrics
            epoch_loss = np.mean(epoch_losses)
            epoch_accuracy = correct / total

            task_losses.append(epoch_loss)
            task_accuracies.append(epoch_accuracy)

            # Add experiences to replay buffer
            self._add_batch_to_memory(x, y, task_id)

            print(f"Epoch {epoch+1}/{num_epochs}: Loss = {epoch_loss:.4f}, Accuracy = {epoch_accuracy:.4f}")

        # Post-task updates
        self._post_task_updates(task_id, dataloader)

        # Store task performance
        self.task_performance[task_id] = {
            'final_accuracy': task_accuracies[-1],
            'losses': task_losses,
            'accuracies': task_accuracies
        }

        return {
            'final_accuracy': task_accuracies[-1],
            'final_loss': task_losses[-1]
        }

    def _add_batch_to_memory(self, x: torch.Tensor, y: torch.Tensor, task_id: int):
        """Add batch experiences to replay buffer"""
        for i in range(x.size(0)):
            class_id = y[i].item() if y.dim() > 0 else y.item()
            self.replay_buffer.add_experience(x[i], y[i], task_id, class_id)

    def _post_task_updates(self, task_id: int, dataloader):
        """Perform post-task updates"""
        # Add to learned tasks
        self.learned_tasks.append(task_id)

        # Compute Fisher information for EWC
        if self.ewc_regularizer:
            print("Computing Fisher information for EWC...")
            self.ewc_regularizer.compute_fisher_information(dataloader, task_id)

        # Compute omega for SI
        if self.si_regularizer:
            print("Computing importance weights for SI...")
            self.si_regularizer.compute_omega()

        # Add progressive network column if enabled
        if self.config.use_progressive:
            print("Adding progressive network column...")
            self.progressive_net.add_column(task_id)

    def evaluate_all_tasks(self, test_dataloaders: Dict[int, Any]) -> Dict[str, float]:
        """Evaluate performance on all learned tasks"""
        self.eval()
        results = {}

        with torch.no_grad():
            for task_id, dataloader in test_dataloaders.items():
                if task_id not in self.learned_tasks:
                    continue

                correct = 0
                total = 0
                total_loss = 0

                for batch in dataloader:
                    if isinstance(batch, (list, tuple)):
                        x, y = batch[0], batch[1]
                    else:
                        x, y = batch.x, batch.y

                    if hasattr(x, 'to'):
                        x = x.to(next(self.parameters()).device)
                        y = y.to(next(self.parameters()).device)

                    output = self.forward(x, task_id)
                    loss = F.cross_entropy(output, y)

                    pred = output.argmax(dim=-1)
                    correct += (pred == y).sum().item()
                    total += y.size(0)
                    total_loss += loss.item()

                accuracy = correct / total
                avg_loss = total_loss / len(dataloader)

                results[f'task_{task_id}_accuracy'] = accuracy
                results[f'task_{task_id}_loss'] = avg_loss

        # Compute average performance
        accuracies = [results[f'task_{tid}_accuracy'] for tid in self.learned_tasks if f'task_{tid}_accuracy' in results]
        if accuracies:
            results['average_accuracy'] = np.mean(accuracies)
            results['forgetting'] = max(self.task_performance[tid]['final_accuracy'] for tid in self.learned_tasks if tid in self.task_performance) - np.mean(accuracies)

        return results

    def plot_learning_curves(self, save_path: Optional[str] = None):
        """Plot learning curves and forgetting analysis"""
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))

        # Task performance over time
        ax1 = axes[0, 0]
        for task_id in self.learned_tasks:
            if task_id in self.task_performance:
                performance = self.task_performance[task_id]
                ax1.plot(performance['accuracies'], label=f'Task {task_id}')
        ax1.set_title('Task Learning Curves')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Accuracy')
        ax1.legend()
        ax1.grid(True)

        # Final performance comparison
        ax2 = axes[0, 1]
        task_ids = list(self.task_performance.keys())
        final_accuracies = [self.task_performance[tid]['final_accuracy'] for tid in task_ids]
        ax2.bar(task_ids, final_accuracies)
        ax2.set_title('Final Task Performance')
        ax2.set_xlabel('Task ID')
        ax2.set_ylabel('Final Accuracy')
        ax2.grid(True)

        # Memory usage
        ax3 = axes[1, 0]
        memory_sizes = [len(self.replay_buffer.experience_buffer) for _ in range(len(self.learned_tasks))]
        ax3.plot(range(1, len(self.learned_tasks) + 1), memory_sizes, 'o-')
        ax3.set_title('Memory Buffer Size')
        ax3.set_xlabel('Number of Tasks')
        ax3.set_ylabel('Buffer Size')
        ax3.grid(True)

        # Plasticity metrics
        ax4 = axes[1, 1]
        if self.plasticity_metrics:
            for metric_name, values in self.plasticity_metrics.items():
                if values:
                    ax4.plot(values, label=metric_name)
            ax4.set_title('Neural Plasticity Metrics')
            ax4.set_xlabel('Time')
            ax4.set_ylabel('Metric Value')
            ax4.legend()
            ax4.grid(True)
        else:
            ax4.text(0.5, 0.5, 'Plasticity metrics\nnot available', ha='center', va='center')
            ax4.set_title('Neural Plasticity Metrics')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()


def create_continual_config(model_size: str = "base") -> ContinualConfig:
    """Create continual learning configuration"""
    if model_size == "base":
        return ContinualConfig(
            input_dim=256,
            hidden_dim=128,
            output_dim=50,
            memory_size=1000,
            ewc_lambda=100.0,
            si_lambda=0.1
        )
    elif model_size == "large":
        return ContinualConfig(
            input_dim=512,
            hidden_dim=256,
            output_dim=100,
            memory_size=5000,
            ewc_lambda=1000.0,
            si_lambda=1.0
        )
    else:
        return ContinualConfig()


def create_synthetic_task(task_id: int, num_classes: int, num_samples: int, input_dim: int) -> Tuple[torch.Tensor, torch.Tensor]:
    """Create synthetic task data for testing"""
    # Generate class centers
    class_centers = torch.randn(num_classes, input_dim)

    # Generate samples
    data = []
    labels = []

    for class_id in range(num_classes):
        center = class_centers[class_id]
        for _ in range(num_samples // num_classes):
            sample = center + torch.randn(input_dim) * 0.5
            data.append(sample)
            labels.append(class_id)

    data = torch.stack(data)
    labels = torch.tensor(labels)

    return data, labels


if __name__ == "__main__":
    print("Creating advanced continual learning system...")

    # Create configuration and model
    config = create_continual_config("base")
    model = ContinualLearner(config)

    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    # Create synthetic tasks
    tasks = {}
    test_tasks = {}
    for task_id in range(3):
        train_data, train_labels = create_synthetic_task(task_id, 5, 500, config.input_dim)
        test_data, test_labels = create_synthetic_task(task_id, 5, 100, config.input_dim)

        tasks[task_id] = list(zip(train_data, train_labels))
        test_tasks[task_id] = list(zip(test_data, test_labels))

    # Test learning on multiple tasks
    print("\nTesting continual learning...")

    for task_id, task_data in tasks.items():
        # Create simple dataloader
        dataloader = [(torch.stack([x for x, _ in task_data[i*32:(i+1)*32]]),
                       torch.stack([y for _, y in task_data[i*32:(i+1)*32]]))
                      for i in range(0, len(task_data), 32)]

        # Learn task
        metrics = model.learn_task(dataloader, task_id, num_epochs=3)
        print(f"Task {task_id} learned with final accuracy: {metrics['final_accuracy']:.3f}")

        # Evaluate on all tasks so far
        test_dataloaders = {}
        for test_task_id, test_data in test_tasks.items():
            if test_task_id <= task_id:
                test_dataloaders[test_task_id] = [(torch.stack([x for x, _ in test_data]),
                                                   torch.stack([y for _, y in test_data]))]

        all_results = model.evaluate_all_tasks(test_dataloaders)
        print(f"Average accuracy after task {task_id}: {all_results.get('average_accuracy', 0):.3f}")
        if 'forgetting' in all_results:
            print(f"Forgetting: {all_results['forgetting']:.3f}")

    # Test forward pass
    print("\nTesting model forward pass...")
    test_input = torch.randn(10, config.input_dim)
    with torch.no_grad():
        output = model(test_input, task_id=0)
        print(f"Output shape: {output.shape}")

    print("\nContinual learning system initialized successfully!")