#!/usr/bin/env python3
"""
Meta-Learning System for Rapid Adaptation
Implements learning to learn and rapid adaptation capabilities
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
import torch.optim as optim
from collections import defaultdict, namedtuple
import math
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MetaLearningConfig:
    """Configuration for meta-learning"""
    ways: int = 5  # Number of classes per task
    shots: int = 5  # Number of examples per class
    meta_lr: float = 1e-3
    inner_lr: float = 1e-2
    inner_steps: int = 5
    meta_batch_size: int = 32
    hidden_dim: int = 256
    embedding_dim: int = 128
    device: str = 'cuda'
    method: str = 'maml'  # 'maml', 'protonet', 'matchingnet', 'relationnet'

# Named tuple for episodes
Episode = namedtuple('Episode', ['support_set', 'query_set', 'task_id'])

class MetaLearningTask(ABC):
    """Abstract base class for meta-learning tasks"""

    def __init__(self, task_id: str):
        self.task_id = task_id

    @abstractmethod
    def sample_episode(self, ways: int, shots: int) -> Episode:
        """Sample an episode for meta-training"""
        pass

    @abstractmethod
    def get_task_embedding(self) -> torch.Tensor:
        """Get task-specific embedding"""
        pass

class PrototypicalNetwork(nn.Module):
    """Prototypical Networks for meta-learning"""

    def __init__(self, input_dim: int, embedding_dim: int, hidden_dim: int):
        super().__init__()
        self.input_dim = input_dim
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim

        # Encoder network
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Linear(hidden_dim, embedding_dim)
        )

        # Distance metric learning
        self.distance_scale = nn.Parameter(torch.tensor(10.0))

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """Encode input to embedding space"""
        return F.normalize(self.encoder(x), dim=1)

    def compute_prototypes(self, support_embeddings: torch.Tensor,
                          support_labels: torch.Tensor, num_classes: int) -> torch.Tensor:
        """Compute class prototypes"""
        prototypes = []
        for class_id in range(num_classes):
            class_mask = (support_labels == class_id)
            class_embeddings = support_embeddings[class_mask]
            prototype = class_embeddings.mean(dim=0)
            prototypes.append(prototype)
        return torch.stack(prototypes)

    def forward(self, query_x: torch.Tensor, support_x: torch.Tensor,
                support_y: torch.Tensor, num_classes: int) -> torch.Tensor:
        """Forward pass for prototypical networks"""
        # Encode support and query sets
        support_embeddings = self.encode(support_x)
        query_embeddings = self.encode(query_x)

        # Compute prototypes
        prototypes = self.compute_prototypes(support_embeddings, support_y, num_classes)

        # Compute distances
        distances = torch.cdist(query_embeddings, prototypes)
        scaled_distances = distances * self.distance_scale

        # Convert to logits
        logits = -scaled_distances
        return logits

class MatchingNetwork(nn.Module):
    """Matching Networks for meta-learning"""

    def __init__(self, input_dim: int, embedding_dim: int, hidden_dim: int):
        super().__init__()
        self.input_dim = input_dim
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim

        # Bi-directional LSTM for attention
        self.lstm = nn.LSTM(input_dim, hidden_dim, bidirectional=True, batch_first=True)
        self.fc = nn.Linear(hidden_dim * 2, embedding_dim)

        # Attention mechanism
        self.attention = nn.MultiheadAttention(embedding_dim, num_heads=8, batch_first=True)

    def embed_support_set(self, support_x: torch.Tensor) -> torch.Tensor:
        """Embed support set using bidirectional LSTM"""
        # Reshape for LSTM
        batch_size, seq_len, input_dim = support_x.shape
        support_x = support_x.view(batch_size * seq_len, input_dim)

        # Pass through LSTM
        embedded, _ = self.lstm(support_x.unsqueeze(1))
        embedded = embedded.squeeze(1)

        # Final linear layer
        embedded = self.fc(embedded)
        embedded = embedded.view(batch_size, seq_len, -1)

        return F.normalize(embedded, dim=-1)

    def forward(self, query_x: torch.Tensor, support_x: torch.Tensor,
                support_y: torch.Tensor) -> torch.Tensor:
        """Forward pass for matching networks"""
        # Embed support set
        support_embeddings = self.embed_support_set(support_x)

        # Embed query set
        query_embeddings = self.embed_support_set(query_x)

        # Attention over support set
        attention_output, attention_weights = self.attention(
            query_embeddings, support_embeddings, support_embeddings
        )

        # Compute weighted sum over support labels
        # This is simplified - actual implementation would use proper attention mechanism
        return attention_output

class RelationNetwork(nn.Module):
    """Relation Networks for meta-learning"""

    def __init__(self, input_dim: int, embedding_dim: int, hidden_dim: int):
        super().__init__()
        self.input_dim = input_dim
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim

        # Feature embedding network
        self.feature_encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Linear(hidden_dim, embedding_dim)
        )

        # Relation network
        self.relation_net = nn.Sequential(
            nn.Linear(embedding_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )

    def embed_features(self, x: torch.Tensor) -> torch.Tensor:
        """Embed features"""
        return F.normalize(self.feature_encoder(x), dim=1)

    def compute_relation_scores(self, query_embeddings: torch.Tensor,
                               support_embeddings: torch.Tensor) -> torch.Tensor:
        """Compute relation scores between query and support"""
        batch_size, num_support, _ = support_embeddings.shape

        # Expand query embeddings for broadcasting
        query_expanded = query_embeddings.unsqueeze(1).expand(-1, num_support, -1)

        # Concatenate query and support embeddings
        concatenated = torch.cat([query_expanded, support_embeddings], dim=-1)

        # Compute relation scores
        scores = self.relation_net(concatenated).squeeze(-1)
        return scores

    def forward(self, query_x: torch.Tensor, support_x: torch.Tensor,
                support_y: torch.Tensor, num_classes: int) -> torch.Tensor:
        """Forward pass for relation networks"""
        # Encode features
        query_embeddings = self.embed_features(query_x)
        support_embeddings = self.embed_features(support_x)

        # Group support embeddings by class
        class_embeddings = []
        for class_id in range(num_classes):
            class_mask = (support_y == class_id)
            if class_mask.any():
                class_embs = support_embeddings[class_mask]
                class_embeddings.append(class_embs.mean(dim=0))
            else:
                class_embeddings.append(torch.zeros_like(query_embeddings[0]))

        class_prototypes = torch.stack(class_embeddings)

        # Compute relation scores
        scores = []
        for query_emb in query_embeddings:
            query_scores = []
            for class_prototype in class_prototypes:
                # Create a support set with just this prototype
                support_set = class_prototype.unsqueeze(0)
                query_set = query_emb.unsqueeze(0)

                score = self.compute_relation_scores(query_set, support_set)
                query_scores.append(score.item())

            scores.append(query_scores)

        return torch.tensor(scores, device=query_x.device)

class MAML(nn.Module):
    """Model-Agnostic Meta-Learning"""

    def __init__(self, base_model: nn.Module, config: MetaLearningConfig):
        super().__init__()
        self.base_model = base_model
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Meta-optimizer
        self.meta_optimizer = optim.Adam(self.base_model.parameters(), lr=config.meta_lr)

        # Training history
        self.meta_losses = []
        self.task_accuracies = []

    def inner_adaptation(self, task_data: Episode) -> nn.Module:
        """Inner loop adaptation for a specific task"""
        adapted_model = copy.deepcopy(self.base_model)
        inner_optimizer = optim.SGD(adapted_model.parameters(), lr=self.config.inner_lr)

        support_x, support_y = task_data.support_set

        # Multiple gradient steps on support set
        for _ in range(self.config.inner_steps):
            inner_optimizer.zero_grad()

            # Forward pass
            predictions = adapted_model(support_x)
            loss = F.cross_entropy(predictions, support_y)

            # Backward pass
            loss.backward()
            inner_optimizer.step()

        return adapted_model

    def meta_update(self, task_batch: List[Episode]) -> Dict[str, float]:
        """Meta-learning update on a batch of tasks"""
        self.meta_optimizer.zero_grad()

        meta_loss = 0
        task_accuracies = []

        for task_data in task_batch:
            # Inner adaptation
            adapted_model = self.inner_adaptation(task_data)

            # Compute meta-loss on query set
            query_x, query_y = task_data.query_set
            query_predictions = adapted_model(query_x)
            task_loss = F.cross_entropy(query_predictions, query_y)

            meta_loss += task_loss / len(task_batch)

            # Calculate task accuracy
            with torch.no_grad():
                accuracy = (query_predictions.argmax(dim=1) == query_y).float().mean()
                task_accuracies.append(accuracy.item())

        # Meta-backward pass
        meta_loss.backward()
        self.meta_optimizer.step()

        # Store metrics
        self.meta_losses.append(meta_loss.item())
        self.task_accuracies.append(np.mean(task_accuracies))

        return {
            'meta_loss': meta_loss.item(),
            'task_accuracy': np.mean(task_accuracies)
        }

class Reptile(nn.Module):
    """Reptile meta-learning algorithm"""

    def __init__(self, base_model: nn.Module, config: MetaLearningConfig):
        super().__init__()
        self.base_model = base_model
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Meta-optimizer
        self.meta_optimizer = optim.SGD(self.base_model.parameters(), lr=config.meta_lr)

        self.meta_losses = []

    def meta_update(self, task_batch: List[Episode]) -> Dict[str, float]:
        """Reptile meta-update"""
        # Store initial weights
        initial_weights = [p.clone() for p in self.base_model.parameters()]

        task_weights = []
        task_losses = []

        # Adapt to each task
        for task_data in task_batch:
            adapted_model = copy.deepcopy(self.base_model)
            inner_optimizer = optim.SGD(adapted_model.parameters(), lr=self.config.inner_lr)

            support_x, support_y = task_data.support_set

            # Inner adaptation
            for _ in range(self.config.inner_steps):
                inner_optimizer.zero_grad()

                predictions = adapted_model(support_x)
                loss = F.cross_entropy(predictions, support_y)
                loss.backward()
                inner_optimizer.step()

            # Compute query loss
            query_x, query_y = task_data.query_set
            with torch.no_grad():
                query_predictions = adapted_model(query_x)
                query_loss = F.cross_entropy(query_predictions, query_y)
                task_losses.append(query_loss.item())

            # Store adapted weights
            task_weights.append([p.clone() for p in adapted_model.parameters()])

        # Reptile update: move towards task-specific weights
        meta_optimizer = optim.SGD(self.base_model.parameters(), lr=self.config.meta_lr)

        for i, param in enumerate(self.base_model.parameters()):
            # Average task weights
            avg_task_weight = sum(task_weights[j][i] for j in range(len(task_weights))) / len(task_weights)

            # Move towards average
            direction = avg_task_weight - param
            param.data += self.config.meta_lr * direction

        avg_task_loss = np.mean(task_losses)
        self.meta_losses.append(avg_task_loss)

        return {'meta_loss': avg_task_loss}

class MetaLearningTrainer:
    """Main trainer for meta-learning algorithms"""

    def __init__(self, config: MetaLearningConfig):
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Initialize model based on method
        self.model = self._create_model()
        self.meta_trainer = self._create_meta_trainer()

        # Training metrics
        self.training_history = {
            'meta_losses': [],
            'task_accuracies': [],
            'adaptation_times': []
        }

    def _create_model(self) -> nn.Module:
        """Create model based on meta-learning method"""
        input_dim = 512  # This should be configured based on actual input
        embedding_dim = self.config.embedding_dim
        hidden_dim = self.config.hidden_dim

        if self.config.method == 'protonet':
            return PrototypicalNetwork(input_dim, embedding_dim, hidden_dim)
        elif self.config.method == 'matchingnet':
            return MatchingNetwork(input_dim, embedding_dim, hidden_dim)
        elif self.config.method == 'relationnet':
            return RelationNetwork(input_dim, embedding_dim, hidden_dim)
        elif self.config.method == 'maml':
            # Create base model for MAML
            base_model = nn.Sequential(
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.BatchNorm1d(hidden_dim),
                nn.Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
                nn.BatchNorm1d(hidden_dim),
                nn.Linear(hidden_dim, self.config.ways)
            )
            return base_model
        else:
            raise ValueError(f"Unknown meta-learning method: {self.config.method}")

    def _create_meta_trainer(self) -> Union[MAML, Reptile]:
        """Create meta-trainer based on method"""
        if self.config.method == 'maml':
            return MAML(self.model, self.config)
        elif self.config.method == 'reptile':
            return Reptile(self.model, self.config)
        else:
            # For other methods, use standard supervised learning
            return None

    def train_episode(self, episode: Episode) -> Dict[str, float]:
        """Train on a single episode"""
        start_time = time.time()

        if self.config.method in ['protonet', 'matchingnet', 'relationnet']:
            return self._train_standard_episode(episode)
        elif self.config.method in ['maml', 'reptile']:
            return self.meta_trainer.meta_update([episode])
        else:
            raise ValueError(f"Unknown method: {self.config.method}")

    def _train_standard_episode(self, episode: Episode) -> Dict[str, float]:
        """Train standard meta-learning models"""
        support_x, support_y = episode.support_set
        query_x, query_y = episode.query_set

        # Forward pass
        if self.config.method == 'protonet':
            logits = self.model(query_x, support_x, support_y, self.config.ways)
        elif self.config.method == 'matchingnet':
            logits = self.model(query_x, support_x, support_y)
        elif self.config.method == 'relationnet':
            logits = self.model(query_x, support_x, support_y, self.config.ways)

        # Compute loss
        loss = F.cross_entropy(logits, query_y)

        # Backward pass
        optimizer = optim.Adam(self.model.parameters(), lr=self.config.meta_lr)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # Calculate accuracy
        with torch.no_grad():
            accuracy = (logits.argmax(dim=1) == query_y).float().mean()

        return {
            'loss': loss.item(),
            'accuracy': accuracy.item()
        }

    def adapt_to_task(self, task_data: Episode, adaptation_steps: Optional[int] = None) -> nn.Module:
        """Adapt model to a specific task"""
        adaptation_steps = adaptation_steps or self.config.inner_steps

        if self.config.method == 'maml':
            return self.meta_trainer.inner_adaptation(task_data)
        else:
            # For other methods, fine-tune on support set
            adapted_model = copy.deepcopy(self.model)
            optimizer = optim.Adam(adapted_model.parameters(), lr=self.config.inner_lr)

            support_x, support_y = task_data.support_set

            for _ in range(adaptation_steps):
                optimizer.zero_grad()

                if self.config.method == 'protonet':
                    logits = adapted_model(task_data.query_set[0], support_x, support_y, self.config.ways)
                else:
                    logits = adapted_model(task_data.query_set[0], support_x, support_y)

                loss = F.cross_entropy(logits, task_data.query_set[1])
                loss.backward()
                optimizer.step()

            return adapted_model

    def evaluate_adaptation(self, adapted_model: nn.Module, task_data: Episode) -> Dict[str, float]:
        """Evaluate adapted model on query set"""
        query_x, query_y = task_data.query_set

        with torch.no_grad():
            if self.config.method == 'protonet':
                logits = adapted_model(query_x, task_data.support_set[0], task_data.support_set[1], self.config.ways)
            else:
                logits = adapted_model(query_x, task_data.support_set[0], task_data.support_set[1])

            predictions = logits.argmax(dim=1)
            accuracy = (predictions == query_y).float().mean()

            loss = F.cross_entropy(logits, query_y)

        return {
            'accuracy': accuracy.item(),
            'loss': loss.item()
        }

    def train(self, task_sampler: Callable[[], List[Episode]], num_episodes: int) -> Dict[str, List[float]]:
        """Train meta-learning model"""
        logger.info(f"Starting meta-training for {num_episodes} episodes")

        for episode_idx in range(num_episodes):
            # Sample batch of tasks
            task_batch = task_sampler()

            # Train on batch
            if self.config.method in ['maml', 'reptile']:
                metrics = self.meta_trainer.meta_update(task_batch)
            else:
                # For other methods, train on each episode
                batch_metrics = []
                for episode in task_batch:
                    metrics = self.train_episode(episode)
                    batch_metrics.append(metrics)

                # Average metrics across batch
                metrics = {
                    key: np.mean([m[key] for m in batch_metrics])
                    for key in batch_metrics[0].keys()
                }

            # Store metrics
            self.training_history['meta_losses'].append(metrics.get('meta_loss', metrics.get('loss', 0)))
            self.training_history['task_accuracies'].append(metrics.get('task_accuracy', metrics.get('accuracy', 0)))

            # Log progress
            if episode_idx % 100 == 0:
                logger.info(f"Episode {episode_idx}: "
                           f"Loss = {metrics.get('meta_loss', metrics.get('loss', 0)):.4f}, "
                           f"Accuracy = {metrics.get('task_accuracy', metrics.get('accuracy', 0)):.4f}")

        return self.training_history

class FastAdaptation:
    """Fast adaptation utilities for meta-learning"""

    @staticmethod
    def few_shot_learning(model: nn.Module, support_data: Tuple[torch.Tensor, torch.Tensor],
                         query_data: Tuple[torch.Tensor, torch.Tensor],
                         adaptation_steps: int = 5, lr: float = 1e-2) -> Dict[str, float]:
        """Perform few-shot learning adaptation"""
        adapted_model = copy.deepcopy(model)
        optimizer = optim.SGD(adapted_model.parameters(), lr=lr)

        support_x, support_y = support_data

        # Adaptation steps
        for _ in range(adaptation_steps):
            optimizer.zero_grad()

            predictions = adapted_model(support_x)
            loss = F.cross_entropy(predictions, support_y)
            loss.backward()
            optimizer.step()

        # Evaluation
        query_x, query_y = query_data
        with torch.no_grad():
            predictions = adapted_model(query_x)
            accuracy = (predictions.argmax(dim=1) == query_y).float().mean()
            loss = F.cross_entropy(predictions, query_y)

        return {
            'accuracy': accuracy.item(),
            'loss': loss.item()
        }

    @staticmethod
    def online_adaptation(model: nn.Module, data_stream: List[Tuple[torch.Tensor, torch.Tensor]],
                         adaptation_lr: float = 1e-3) -> nn.Module:
        """Online adaptation to data stream"""
        adapted_model = copy.deepcopy(model)
        optimizer = optim.Adam(adapted_model.parameters(), lr=adaptation_lr)

        for x, y in data_stream:
            optimizer.zero_grad()

            predictions = adapted_model(x.unsqueeze(0))
            loss = F.cross_entropy(predictions, y.unsqueeze(0))
            loss.backward()
            optimizer.step()

        return adapted_model

# Utility functions
def create_meta_config(ways: int = 5, shots: int = 5, method: str = 'maml') -> MetaLearningConfig:
    """Create meta-learning configuration"""
    return MetaLearningConfig(
        ways=ways,
        shots=shots,
        meta_lr=1e-3,
        inner_lr=1e-2,
        inner_steps=5,
        meta_batch_size=32,
        hidden_dim=256,
        embedding_dim=128,
        device='cuda' if torch.cuda.is_available() else 'cpu',
        method=method
    )

def sample_few_shot_episode(dataset: Dict[int, List[Tuple[torch.Tensor, torch.Tensor]]],
                          ways: int, shots: int) -> Episode:
    """Sample a few-shot learning episode"""
    # Sample random classes
    available_classes = list(dataset.keys())
    selected_classes = random.sample(available_classes, min(ways, len(available_classes)))

    support_data = []
    query_data = []

    for class_id in selected_classes:
        class_data = dataset[class_id]
        if len(class_data) < shots + 5:  # Need support + query samples
            continue

        # Shuffle and split
        random.shuffle(class_data)
        support_samples = class_data[:shots]
        query_samples = class_data[shots:shots+5]

        support_data.extend(support_samples)
        query_data.extend(query_samples)

    # Convert to tensors
    support_x = torch.stack([x for x, y in support_data])
    support_y = torch.tensor([selected_classes.index(y for x, y in [(x, class_id) for class_id in selected_classes for x, y in dataset[class_id] if y == class_id][i]) for i in range(len(support_data))])
    query_x = torch.stack([x for x, y in query_data])
    query_y = torch.tensor([selected_classes.index(y for x, y in [(x, class_id) for class_id in selected_classes for x, y in dataset[class_id] if y == class_id][i]) for i in range(len(query_data))])

    return Episode(
        support_set=(support_x, support_y),
        query_set=(query_x, query_y),
        task_id=f"episode_{random.randint(0, 10000)}"
    )

if __name__ == "__main__":
    # Example usage
    config = create_meta_config(ways=5, shots=5, method='maml')

    # Create meta-learning trainer
    trainer = MetaLearningTrainer(config)

    # Create fast adaptation utility
    fast_adaptation = FastAdaptation()

    print("Meta-Learning System initialized!")
    print(f"Method: {config.method}")
    print(f"Ways: {config.ways}, Shots: {config.shots}")
    print(f"Available methods: maml, reptile, protonet, matchingnet, relationnet")
    print(f"Fast adaptation capabilities: {FastAdaptation.__name__}")
    print(f"Few-shot learning supported: True")
    print(f"Online adaptation supported: True")