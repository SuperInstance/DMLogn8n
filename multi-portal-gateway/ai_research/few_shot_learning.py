"""
Advanced Few-Shot Learning for DMLogn8n
Few-shot and zero-shot learning capabilities for rapid adaptation with minimal data
Based on latest research in meta-learning and few-shot learning (2024-2025)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
import math
from collections import defaultdict
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, f1_score, classification_report


@dataclass
class FewShotConfig:
    """Configuration for few-shot learning"""
    # Meta-learning parameters
    ways: int = 5  # Number of classes per episode
    shots: int = 5  # Number of examples per class
    query_shots: int = 15  # Number of query examples per class

    # Model architecture
    feature_dim: int = 512
    hidden_dim: int = 256
    num_layers: int = 3
    dropout: float = 0.1
    use_batch_norm: bool = True

    # Meta-learning specific
    inner_lr: float = 0.01  # Inner loop learning rate
    outer_lr: float = 0.001  # Outer loop learning rate
    inner_steps: int = 5  # Inner adaptation steps
    meta_batch_size: int = 4

    # Prototypical networks
    temperature: float = 10.0
    distance_metric: str = "euclidean"  # euclidean, cosine

    # MAML specific
    first_order: bool = False
    learnable_lr: bool = True

    # Zero-shot learning
    use_attributes: bool = True
    attribute_dim: int = 300
    use_semantic_embeddings: bool = True
    embedding_dim: int = 768


class FeatureExtractor(nn.Module):
    """Base feature extractor for few-shot learning"""
    def __init__(self, input_dim: int, config: FewShotConfig):
        super().__init__()
        self.config = config

        layers = []
        in_dim = input_dim

        # Build hidden layers
        for i in range(config.num_layers):
            out_dim = config.hidden_dim if i < config.num_layers - 1 else config.feature_dim

            layers.append(nn.Linear(in_dim, out_dim))

            if config.use_batch_norm:
                layers.append(nn.BatchNorm1d(out_dim))

            layers.append(nn.ReLU())
            layers.append(nn.Dropout(config.dropout))

            in_dim = out_dim

        self.network = nn.Sequential(*layers[:-2])  # Remove final dropout

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)


class PrototypicalNetwork(nn.Module):
    """Prototypical Networks for few-shot classification"""
    def __init__(self, config: FewShotConfig, input_dim: int):
        super().__init__()
        self.config = config

        # Feature extractor
        self.feature_extractor = FeatureExtractor(input_dim, config)

        # Learnable distance metric
        if config.distance_metric == "learned":
            self.distance_proj = nn.Sequential(
                nn.Linear(config.feature_dim, config.feature_dim),
                nn.ReLU(),
                nn.Linear(config.feature_dim, config.feature_dim)
            )
        else:
            self.distance_proj = None

        # Temperature scaling
        if config.temperature > 0:
            self.temperature = nn.Parameter(torch.tensor(config.temperature))
        else:
            self.temperature = None

    def compute_prototypes(self, support_features: torch.Tensor, support_labels: torch.Tensor) -> torch.Tensor:
        """Compute class prototypes from support set"""
        num_classes = self.config.ways
        prototypes = []

        for class_id in range(num_classes):
            # Get features for this class
            class_mask = support_labels == class_id
            class_features = support_features[class_mask]

            # Compute prototype (mean of class features)
            prototype = class_features.mean(dim=0)
            prototypes.append(prototype)

        return torch.stack(prototypes)  # [num_classes, feature_dim]

    def compute_distances(self, query_features: torch.Tensor, prototypes: torch.Tensor) -> torch.Tensor:
        """Compute distances between query features and prototypes"""
        if self.config.distance_metric == "euclidean":
            # Euclidean distance
            distances = torch.cdist(query_features, prototypes, p=2)
        elif self.config.distance_metric == "cosine":
            # Cosine distance
            query_norm = F.normalize(query_features, p=2, dim=-1)
            proto_norm = F.normalize(prototypes, p=2, dim=-1)
            distances = 1 - torch.mm(query_norm, proto_norm.t())
        elif self.config.distance_metric == "learned" and self.distance_proj is not None:
            # Learned distance metric
            query_proj = self.distance_proj(query_features)
            proto_proj = self.distance_proj(prototypes)
            distances = torch.cdist(query_proj, proto_proj, p=2)
        else:
            raise ValueError(f"Unknown distance metric: {self.config.distance_metric}")

        return distances

    def forward(self, support_features: torch.Tensor, support_labels: torch.Tensor,
                query_features: torch.Tensor) -> torch.Tensor:

        # Compute prototypes
        prototypes = self.compute_prototypes(support_features, support_labels)

        # Compute distances
        distances = self.compute_distances(query_features, prototypes)

        # Convert distances to logits (negative distances)
        logits = -distances

        # Apply temperature scaling if available
        if self.temperature is not None:
            logits = logits * self.temperature

        return logits, prototypes


class MAML(nn.Module):
    """Model-Agnostic Meta-Learning implementation"""
    def __init__(self, config: FewShotConfig, input_dim: int, num_classes: int = 1000):
        super().__init__()
        self.config = config

        # Base model for classification
        self.feature_extractor = FeatureExtractor(input_dim, config)
        self.classifier = nn.Linear(config.feature_dim, num_classes)

        # Learnable inner learning rate
        if config.learnable_lr:
            self.inner_lr = nn.Parameter(torch.tensor(config.inner_lr))
        else:
            self.inner_lr = config.inner_lr

        # Store original parameters for gradient computation
        self.register_buffer('adapted_params', None)

    def forward(self, x: torch.Tensor, params: Optional[Dict[str, torch.Tensor]] = None) -> torch.Tensor:
        """Forward pass with optional parameter override"""
        if params is None:
            features = self.feature_extractor(x)
            logits = self.classifier(features)
        else:
            # Use adapted parameters
            features = self.forward_with_params(self.feature_extractor, x, params['feature_extractor'])
            logits = F.linear(features, params['classifier.weight'], params['classifier.bias'])

        return logits

    def forward_with_params(self, module: nn.Module, x: torch.Tensor,
                           params: Dict[str, torch.Tensor]) -> torch.Tensor:
        """Forward pass through module with specific parameters"""
        # This is a simplified version - in practice, you'd need to handle different module types
        if isinstance(module, nn.Linear):
            return F.linear(x, params['weight'], params['bias'])
        elif isinstance(module, nn.Sequential):
            out = x
            for i, layer in enumerate(module):
                if isinstance(layer, nn.Linear):
                    out = F.linear(out, params[f'layer_{i}.weight'], params[f'layer_{i}.bias'])
                elif isinstance(layer, nn.BatchNorm1d):
                    # Skip batch norm during adaptation
                    continue
                elif isinstance(layer, nn.ReLU):
                    out = F.relu(out)
                elif isinstance(layer, nn.Dropout):
                    out = F.dropout(out, training=False)
            return out
        else:
            return module(x)

    def get_parameters(self) -> Dict[str, torch.Tensor]:
        """Get current model parameters"""
        params = {}
        params['feature_extractor'] = {name: param for name, param in self.feature_extractor.named_parameters()}
        params['classifier'] = {name: param for name, param in self.classifier.named_parameters()}
        return params

    def set_parameters(self, params: Dict[str, torch.Tensor]):
        """Set model parameters"""
        for name, param in self.feature_extractor.named_parameters():
            param.data = params['feature_extractor'][name].data.clone()

        for name, param in self.classifier.named_parameters():
            param.data = params['classifier'][name].data.clone()

    def adapt(self, support_x: torch.Tensor, support_y: torch.Tensor,
              num_steps: Optional[int] = None) -> Dict[str, torch.Tensor]:
        """Inner loop adaptation on support set"""
        if num_steps is None:
            num_steps = self.config.inner_steps

        # Get current parameters
        params = self.get_parameters()

        # Gradient descent steps
        for step in range(num_steps):
            # Forward pass
            logits = self.forward(support_x, params)
            loss = F.cross_entropy(logits, support_y)

            # Compute gradients
            grads = torch.autograd.grad(loss, params.values(), create_graph=not self.config.first_order)

            # Update parameters
            with torch.no_grad():
                for (name, param), grad in zip(params.items(), grads):
                    if isinstance(param, dict):
                        for param_name, param_val in param.items():
                            param_val.data -= self.inner_lr * grads_dict[name][param_name]
                    else:
                        param.data -= self.inner_lr * grad

        return params

    def meta_update(self, task_batch: List[Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]],
                   optimizer: torch.optim.Optimizer) -> Dict[str, float]:
        """Meta-learning update on batch of tasks"""
        meta_loss = 0.0
        meta_accuracy = 0.0

        for support_x, support_y, query_x, query_y in task_batch:
            # Adapt to task
            adapted_params = self.adapt(support_x, support_y)

            # Evaluate on query set
            query_logits = self.forward(query_x, adapted_params)
            query_loss = F.cross_entropy(query_logits, query_y)

            # Compute accuracy
            query_pred = query_logits.argmax(dim=-1)
            query_acc = (query_pred == query_y).float().mean()

            meta_loss += query_loss
            meta_accuracy += query_acc

        # Average over tasks
        meta_loss /= len(task_batch)
        meta_accuracy /= len(task_batch)

        # Meta-update
        optimizer.zero_grad()
        meta_loss.backward()
        optimizer.step()

        return {
            'meta_loss': meta_loss.item(),
            'meta_accuracy': meta_accuracy.item()
        }


class RelationNetwork(nn.Module):
    """Relation Networks for few-shot learning"""
    def __init__(self, config: FewShotConfig, input_dim: int):
        super().__init__()
        self.config = config

        # Feature extractor
        self.feature_extractor = FeatureExtractor(input_dim, config)

        # Relation module
        self.relation_module = nn.Sequential(
            nn.Linear(config.feature_dim * 2, config.hidden_dim),
            nn.ReLU(),
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.ReLU(),
            nn.Linear(config.hidden_dim, 1)
        )

    def compute_relations(self, support_features: torch.Tensor, support_labels: torch.Tensor,
                         query_features: torch.Tensor) -> torch.Tensor:
        """Compute relation scores between query and support features"""
        num_classes = self.config.ways
        relations = []

        for class_id in range(num_classes):
            # Get support features for this class
            class_mask = support_labels == class_id
            class_features = support_features[class_mask]

            # Compute relations with all support examples of this class
            class_relations = []
            for support_feat in class_features:
                # Concatenate query and support features
                combined = torch.cat([query_features, support_feat.repeat(len(query_features), 1)], dim=-1)
                relation_score = self.relation_module(combined)
                class_relations.append(relation_score)

            # Average relation scores for this class
            class_relation = torch.stack(class_relations).mean(dim=0)
            relations.append(class_relation)

        return torch.stack(relations, dim=-1)  # [num_queries, num_classes]

    def forward(self, support_features: torch.Tensor, support_labels: torch.Tensor,
                query_features: torch.Tensor) -> torch.Tensor:
        """Forward pass"""
        relation_scores = self.compute_relations(support_features, support_labels, query_features)
        return relation_scores


class ZeroShotLearner(nn.Module):
    """Zero-shot learning using semantic embeddings"""
    def __init__(self, config: FewShotConfig, input_dim: int, class_embeddings: torch.Tensor):
        super().__init__()
        self.config = config

        # Feature extractor
        self.feature_extractor = FeatureExtractor(input_dim, config)

        # Class embeddings (semantic information about classes)
        self.register_buffer('class_embeddings', class_embeddings)  # [num_classes, embedding_dim]

        # Mapping from visual features to semantic space
        self.visual_to_semantic = nn.Sequential(
            nn.Linear(config.feature_dim, config.hidden_dim),
            nn.ReLU(),
            nn.Linear(config.hidden_dim, config.embedding_dim)
        )

        # Attribute predictor (if using attributes)
        if config.use_attributes:
            self.attribute_predictor = nn.Sequential(
                nn.Linear(config.feature_dim, config.hidden_dim),
                nn.ReLU(),
                nn.Linear(config.hidden_dim, config.attribute_dim),
                nn.Sigmoid()
            )

    def forward(self, x: torch.Tensor, class_embeddings: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Forward pass for zero-shot classification"""
        # Extract visual features
        visual_features = self.feature_extractor(x)

        # Map to semantic space
        semantic_features = self.visual_to_semantic(visual_features)

        # Use provided class embeddings or registered ones
        if class_embeddings is None:
            class_embeddings = self.class_embeddings

        # Normalize features and embeddings
        semantic_features = F.normalize(semantic_features, p=2, dim=-1)
        class_embeddings = F.normalize(class_embeddings, p=2, dim=-1)

        # Compute similarity scores
        logits = torch.mm(semantic_features, class_embeddings.t())

        # Scale logits
        logits = logits * 10.0  # Temperature scaling

        return logits

    def predict_attributes(self, x: torch.Tensor) -> torch.Tensor:
        """Predict attributes from visual features"""
        if not self.config.use_attributes:
            raise ValueError("Attribute prediction not enabled")

        visual_features = self.feature_extractor(x)
        attributes = self.attribute_predictor(visual_features)
        return attributes


class MetaLearningTrainer:
    """Trainer for meta-learning algorithms"""
    def __init__(self, model: nn.Module, config: FewShotConfig):
        self.model = model
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.model.to(self.device)

        # Optimizer
        if isinstance(model, MAML):
            self.optimizer = torch.optim.Adam(model.parameters(), lr=config.outer_lr)
        else:
            self.optimizer = torch.optim.Adam(model.parameters(), lr=config.outer_lr)

        # Learning rate scheduler
        self.scheduler = torch.optim.lr_scheduler.StepLR(
            self.optimizer, step_size=1000, gamma=0.5
        )

        # Metrics tracking
        self.train_losses = []
        self.train_accuracies = []
        self.val_accuracies = []

    def create_episode(self, dataset: Dict[str, torch.Tensor], mode: str = "train") -> Tuple:
        """Create a few-shot learning episode"""
        # Sample classes for this episode
        all_classes = list(dataset.keys())
        episode_classes = np.random.choice(all_classes, self.config.ways, replace=False)

        support_data = []
        support_labels = []
        query_data = []
        query_labels = []

        for class_idx, class_name in enumerate(episode_classes):
            class_data = dataset[class_name]

            # Sample support and query examples
            indices = np.random.permutation(len(class_data))
            support_indices = indices[:self.config.shots]
            query_indices = indices[self.config.shots:self.config.shots + self.config.query_shots]

            # Add support examples
            for idx in support_indices:
                support_data.append(class_data[idx])
                support_labels.append(class_idx)

            # Add query examples
            for idx in query_indices:
                query_data.append(class_data[idx])
                query_labels.append(class_idx)

        # Convert to tensors
        support_x = torch.stack(support_data).to(self.device)
        support_y = torch.tensor(support_labels, dtype=torch.long).to(self.device)
        query_x = torch.stack(query_data).to(self.device)
        query_y = torch.tensor(query_labels, dtype=torch.long).to(self.device)

        return support_x, support_y, query_x, query_y

    def train_epoch(self, train_dataset: Dict[str, torch.Tensor]) -> Dict[str, float]:
        """Train for one epoch"""
        self.model.train()
        epoch_losses = []
        epoch_accuracies = []

        if isinstance(self.model, MAML):
            # MAML training
            task_batch = []
            for _ in range(self.config.meta_batch_size):
                support_x, support_y, query_x, query_y = self.create_episode(train_dataset)
                task_batch.append((support_x, support_y, query_x, query_y))

            # Meta-update
            metrics = self.model.meta_update(task_batch, self.optimizer)
            epoch_losses.append(metrics['meta_loss'])
            epoch_accuracies.append(metrics['meta_accuracy'])

        else:
            # Other methods (Prototypical Networks, Relation Networks)
            for _ in range(self.config.meta_batch_size):
                support_x, support_y, query_x, query_y = self.create_episode(train_dataset)

                # Forward pass
                if isinstance(self.model, PrototypicalNetwork):
                    # Extract features
                    support_features = self.model.feature_extractor(support_x)
                    query_features = self.model.feature_extractor(query_x)

                    # Compute logits
                    logits, prototypes = self.model(support_features, support_y, query_features)

                elif isinstance(self.model, RelationNetwork):
                    # Extract features
                    support_features = self.model.feature_extractor(support_x)
                    query_features = self.model.feature_extractor(query_x)

                    # Compute relation scores
                    logits = self.model(support_features, support_y, query_features)

                else:
                    raise ValueError(f"Unknown model type: {type(self.model)}")

                # Compute loss
                loss = F.cross_entropy(logits, query_y)

                # Compute accuracy
                pred = logits.argmax(dim=-1)
                accuracy = (pred == query_y).float().mean()

                # Update
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()

                epoch_losses.append(loss.item())
                epoch_accuracies.append(accuracy.item())

        # Update learning rate
        self.scheduler.step()

        avg_loss = np.mean(epoch_losses)
        avg_accuracy = np.mean(epoch_accuracies)

        self.train_losses.append(avg_loss)
        self.train_accuracies.append(avg_accuracy)

        return {
            'loss': avg_loss,
            'accuracy': avg_accuracy
        }

    def evaluate(self, test_dataset: Dict[str, torch.Tensor], num_episodes: int = 100) -> Dict[str, float]:
        """Evaluate model on test episodes"""
        self.model.eval()
        accuracies = []

        with torch.no_grad():
            for _ in range(num_episodes):
                support_x, support_y, query_x, query_y = self.create_episode(test_dataset, mode="test")

                # Forward pass
                if isinstance(self.model, PrototypicalNetwork):
                    support_features = self.model.feature_extractor(support_x)
                    query_features = self.model.feature_extractor(query_x)
                    logits, _ = self.model(support_features, support_y, query_features)

                elif isinstance(self.model, RelationNetwork):
                    support_features = self.model.feature_extractor(support_x)
                    query_features = self.model.feature_extractor(query_x)
                    logits = self.model(support_features, support_y, query_features)

                elif isinstance(self.model, MAML):
                    # Adapt to support set
                    adapted_params = self.model.adapt(support_x, support_y)
                    logits = self.model(query_x, adapted_params)

                elif isinstance(self.model, ZeroShotLearner):
                    logits = self.model(query_x)

                else:
                    raise ValueError(f"Unknown model type: {type(self.model)}")

                # Compute accuracy
                pred = logits.argmax(dim=-1)
                accuracy = (pred == query_y).float().mean()
                accuracies.append(accuracy.item())

        avg_accuracy = np.mean(accuracies)
        self.val_accuracies.append(avg_accuracy)

        return {
            'accuracy': avg_accuracy,
            'std': np.std(accuracies)
        }

    def plot_training_curves(self, save_path: Optional[str] = None):
        """Plot training and validation curves"""
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))

        # Loss curve
        axes[0].plot(self.train_losses)
        axes[0].set_title('Training Loss')
        axes[0].set_xlabel('Epoch')
        axes[0].set_ylabel('Loss')
        axes[0].grid(True)

        # Accuracy curves
        axes[1].plot(self.train_accuracies, label='Train')
        if self.val_accuracies:
            axes[1].plot(self.val_accuracies, label='Validation')
        axes[1].set_title('Accuracy')
        axes[1].set_xlabel('Epoch')
        axes[1].set_ylabel('Accuracy')
        axes[1].legend()
        axes[1].grid(True)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()


# Utility functions
def create_synthetic_dataset(num_classes: int = 100, samples_per_class: int = 100,
                           feature_dim: int = 512) -> Dict[str, torch.Tensor]:
    """Create synthetic dataset for testing"""
    dataset = {}

    for class_id in range(num_classes):
        # Generate random class center
        class_center = torch.randn(feature_dim)

        # Generate samples around class center
        samples = []
        for _ in range(samples_per_class):
            sample = class_center + torch.randn(feature_dim) * 0.5
            samples.append(sample)

        dataset[f"class_{class_id}"] = torch.stack(samples)

    return dataset


def create_few_shot_config(model_size: str = "base") -> FewShotConfig:
    """Create few-shot learning configuration"""
    if model_size == "base":
        return FewShotConfig(
            ways=5,
            shots=5,
            feature_dim=256,
            hidden_dim=128,
            inner_lr=0.01,
            outer_lr=0.001
        )
    elif model_size == "large":
        return FewShotConfig(
            ways=10,
            shots=10,
            feature_dim=512,
            hidden_dim=256,
            inner_lr=0.005,
            outer_lr=0.0005
        )
    else:
        return FewShotConfig()


def benchmark_models(config: FewShotConfig, train_dataset: Dict[str, torch.Tensor],
                    test_dataset: Dict[str, torch.Tensor], num_epochs: int = 100) -> Dict[str, Dict]:
    """Benchmark different few-shot learning models"""
    input_dim = next(iter(train_dataset.values())).shape[-1]

    models = {
        'Prototypical': PrototypicalNetwork(config, input_dim),
        'Relation': RelationNetwork(config, input_dim),
        'MAML': MAML(config, input_dim)
    }

    results = {}

    for name, model in models.items():
        print(f"\nTraining {name}...")
        trainer = MetaLearningTrainer(model, config)

        # Train
        for epoch in tqdm(range(num_epochs), desc=f"{name} Training"):
            metrics = trainer.train_epoch(train_dataset)

            if epoch % 10 == 0:
                val_metrics = trainer.evaluate(test_dataset, num_episodes=20)
                print(f"Epoch {epoch}: Train Acc = {metrics['accuracy']:.3f}, Val Acc = {val_metrics['accuracy']:.3f}")

        # Final evaluation
        final_metrics = trainer.evaluate(test_dataset, num_episodes=100)
        results[name] = final_metrics

    return results


if __name__ == "__main__":
    print("Creating advanced few-shot learning models...")

    # Create configuration
    config = create_few_shot_config("base")

    # Create synthetic datasets
    train_dataset = create_synthetic_dataset(num_classes=80, samples_per_class=100, feature_dim=256)
    test_dataset = create_synthetic_dataset(num_classes=20, samples_per_class=100, feature_dim=256)

    # Create models
    input_dim = 256
    prototypical_net = PrototypicalNetwork(config, input_dim)
    relation_net = RelationNetwork(config, input_dim)
    maml_model = MAML(config, input_dim)

    print(f"Prototypical network parameters: {sum(p.numel() for p in prototypical_net.parameters()):,}")
    print(f"Relation network parameters: {sum(p.numel() for p in relation_net.parameters()):,}")
    print(f"MAML model parameters: {sum(p.numel() for p in maml_model.parameters()):,}")

    # Test forward passes
    print("\nTesting few-shot learning models...")

    # Create episode
    episode_classes = list(train_dataset.keys())[:config.ways]
    support_data = []
    support_labels = []
    query_data = []
    query_labels = []

    for class_idx, class_name in enumerate(episode_classes):
        class_data = train_dataset[class_name]
        indices = np.random.permutation(len(class_data))

        support_data.extend(class_data[indices[:config.shots]])
        support_labels.extend([class_idx] * config.shots)
        query_data.extend(class_data[indices[config.shots:config.shots + config.query_shots]])
        query_labels.extend([class_idx] * config.query_shots)

    support_x = torch.stack(support_data)
    support_y = torch.tensor(support_labels)
    query_x = torch.stack(query_data)
    query_y = torch.tensor(query_labels)

    # Test Prototypical Networks
    with torch.no_grad():
        support_features = prototypical_net.feature_extractor(support_x)
        query_features = prototypical_net.feature_extractor(query_x)
        proto_logits, prototypes = prototypical_net(support_features, support_y, query_features)

        print(f"Prototypical networks - Prototypes shape: {prototypes.shape}")
        print(f"Prototypical networks - Logits shape: {proto_logits.shape}")

        # Test Relation Networks
        relation_logits = relation_net(support_features, support_y, query_features)
        print(f"Relation networks - Logits shape: {relation_logits.shape}")

        # Test MAML adaptation
        adapted_params = maml_model.adapt(support_x, support_y)
        maml_logits = maml_model(query_x, adapted_params)
        print(f"MAML - Logits shape: {maml_logits.shape}")

    # Create zero-shot learner with synthetic embeddings
    num_classes = 100
    class_embeddings = torch.randn(num_classes, config.embedding_dim)
    zero_shot_learner = ZeroShotLearner(config, input_dim, class_embeddings)

    print(f"Zero-shot learner parameters: {sum(p.numel() for p in zero_shot_learner.parameters()):,}")

    # Test zero-shot learning
    with torch.no_grad():
        zs_logits = zero_shot_learner(query_x)
        print(f"Zero-shot learner - Logits shape: {zs_logits.shape}")

    print("\nFew-shot learning models initialized successfully!")