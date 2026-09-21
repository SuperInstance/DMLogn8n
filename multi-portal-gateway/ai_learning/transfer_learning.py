#!/usr/bin/env python3
"""
Transfer Learning Framework for Cross-Domain Knowledge Transfer
Enables knowledge transfer between different domains and tasks
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
import torch.nn.utils as nn_utils
import torch.optim as optim
from collections import defaultdict, OrderedDict
import json
import time
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TransferConfig:
    """Configuration for transfer learning"""
    source_domains: List[str]
    target_domain: str
    adaptation_method: str = 'fine_tuning'  # 'fine_tuning', 'feature_extraction', 'domain_adaptation'
    freeze_layers: List[str] = None
    learning_rate_ratio: float = 0.1  # Target domain LR / Source domain LR
    weight_decay: float = 1e-4
    adaptation_steps: int = 1000
    batch_size: int = 32
    device: str = 'cuda'

    def __post_init__(self):
        if self.freeze_layers is None:
            self.freeze_layers = []

class DomainAdapter(nn.Module):
    """Domain adaptation module"""

    def __init__(self, feature_dim: int, num_domains: int):
        super().__init__()
        self.feature_dim = feature_dim
        self.num_domains = num_domains

        # Domain discriminator
        self.domain_classifier = nn.Sequential(
            nn.Linear(feature_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, num_domains)
        )

        # Domain-specific batch normalization
        self.domain_bn = nn.ModuleDict({
            f'domain_{i}': nn.BatchNorm1d(feature_dim)
            for i in range(num_domains)
        })

        # Domain-specific feature transformations
        self.domain_transforms = nn.ModuleDict({
            f'domain_{i}': nn.Sequential(
                nn.Linear(feature_dim, feature_dim),
                nn.ReLU(),
                nn.Linear(feature_dim, feature_dim)
            )
            for i in range(num_domains)
        })

    def forward(self, features: torch.Tensor, domain_id: int, use_classifier: bool = True):
        """Forward pass with domain-specific processing"""
        # Domain-specific batch normalization
        if f'domain_{domain_id}' in self.domain_bn:
            features = self.domain_bn[f'domain_{domain_id}'](features)

        # Domain-specific feature transformation
        if f'domain_{domain_id}' in self.domain_transforms:
            features = self.domain_transforms[f'domain_{domain_id}'](features)

        # Domain classification (for adversarial training)
        domain_pred = None
        if use_classifier:
            domain_pred = self.domain_classifier(features)

        return features, domain_pred

class KnowledgeDistillation(nn.Module):
    """Knowledge distillation for transfer learning"""

    def __init__(self, temperature: float = 4.0, alpha: float = 0.7):
        super().__init__()
        self.temperature = temperature
        self.alpha = alpha

    def distillation_loss(self, student_outputs: torch.Tensor,
                         teacher_outputs: torch.Tensor,
                         labels: torch.Tensor) -> torch.Tensor:
        """Calculate distillation loss"""
        # Soft targets from teacher
        soft_targets = F.softmax(teacher_outputs / self.temperature, dim=1)
        soft_student = F.log_softmax(student_outputs / self.temperature, dim=1)

        # Distillation loss
        distill_loss = F.kl_div(soft_student, soft_targets, reduction='batchmean')
        distill_loss *= (self.temperature ** 2)

        # Standard cross-entropy loss
        hard_loss = F.cross_entropy(student_outputs, labels)

        # Combined loss
        total_loss = self.alpha * distill_loss + (1 - self.alpha) * hard_loss

        return total_loss, distill_loss, hard_loss

class FeatureExtractor(nn.Module):
    """Feature extractor for transfer learning"""

    def __init__(self, backbone: nn.Module, feature_dim: int):
        super().__init__()
        self.backbone = backbone
        self.feature_dim = feature_dim

        # Remove final classification layer if present
        self._remove_classification_layer()

        # Add feature projection head
        self.feature_projection = nn.Sequential(
            nn.Linear(self._get_backbone_output_dim(), 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, feature_dim)
        )

    def _remove_classification_layer(self):
        """Remove final classification layer from backbone"""
        if hasattr(self.backbone, 'classifier'):
            self.backbone.classifier = nn.Identity()
        elif hasattr(self.backbone, 'fc'):
            self.backbone.fc = nn.Identity()

    def _get_backbone_output_dim(self) -> int:
        """Get output dimension of backbone"""
        # This should be implemented based on the specific backbone
        return 2048  # Default for ResNet-like architectures

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Extract features"""
        features = self.backbone(x)
        projected_features = self.feature_projection(features)
        return F.normalize(projected_features, dim=1)

class TransferableModel(nn.Module):
    """Base class for transferable models"""

    def __init__(self, config: TransferConfig):
        super().__init__()
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Model components
        self.feature_extractor = None
        self.task_head = None
        self.domain_adapter = None

        # Training history
        self.training_history = {
            'source_domains': {},
            'target_domain': {},
            'transfer_metrics': []
        }

    def freeze_layers(self, layer_names: List[str]):
        """Freeze specified layers"""
        for name, param in self.named_parameters():
            for layer_name in layer_names:
                if layer_name in name:
                    param.requires_grad = False
                    logger.info(f"Frozen layer: {name}")

    def unfreeze_layers(self, layer_names: List[str]):
        """Unfreeze specified layers"""
        for name, param in self.named_parameters():
            for layer_name in layer_names:
                if layer_name in name:
                    param.requires_grad = True
                    logger.info(f"Unfrozen layer: {name}")

    def get_transferable_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extract transferable features"""
        if self.feature_extractor is None:
            raise ValueError("Feature extractor not initialized")

        return self.feature_extractor(x)

class ProgressiveTransferLearning:
    """Progressive transfer learning across multiple domains"""

    def __init__(self, config: TransferConfig):
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Store models for each domain
        self.domain_models = {}
        self.shared_knowledge = None
        self.transfer_history = []

        # Knowledge distillation
        self.distillation = KnowledgeDistillation()

    def add_source_model(self, domain: str, model: nn.Module):
        """Add a pre-trained source model"""
        self.domain_models[domain] = model.to(self.device)
        logger.info(f"Added source model for domain: {domain}")

    def transfer_to_target(self, target_model: nn.Module,
                          source_domains: Optional[List[str]] = None,
                          transfer_method: str = 'ensemble') -> nn.Module:
        """Transfer knowledge from source domains to target"""
        source_domains = source_domains or self.config.source_domains

        if transfer_method == 'ensemble':
            return self._ensemble_transfer(target_model, source_domains)
        elif transfer_method == 'progressive':
            return self._progressive_transfer(target_model, source_domains)
        elif transfer_method == 'attention_weighted':
            return self._attention_weighted_transfer(target_model, source_domains)
        else:
            raise ValueError(f"Unknown transfer method: {transfer_method}")

    def _ensemble_transfer(self, target_model: nn.Module, source_domains: List[str]) -> nn.Module:
        """Ensemble knowledge transfer from multiple sources"""
        target_dict = target_model.state_dict()

        for domain in source_domains:
            if domain not in self.domain_models:
                logger.warning(f"Source model for domain {domain} not found")
                continue

            source_model = self.domain_models[domain]
            source_dict = source_model.state_dict()

            # Average weights for shared layers
            for key in target_dict:
                if key in source_dict:
                    # Progressive blending
                    alpha = 1.0 / len(source_domains)
                    target_dict[key] = (1 - alpha) * target_dict[key] + alpha * source_dict[key]

        target_model.load_state_dict(target_dict)
        return target_model

    def _progressive_transfer(self, target_model: nn.Module, source_domains: List[str]) -> nn.Module:
        """Progressive transfer through domain chain"""
        current_model = copy.deepcopy(self.domain_models[source_domains[0]])

        for i, domain in enumerate(source_domains[1:], 1):
            next_model = self.domain_models[domain]

            # Gradual transfer with interpolation
            current_dict = current_model.state_dict()
            next_dict = next_model.state_dict()

            interpolation_factor = i / len(source_domains)

            for key in current_dict:
                if key in next_dict:
                    current_dict[key] = (1 - interpolation_factor) * current_dict[key] + interpolation_factor * next_dict[key]

            current_model.load_state_dict(current_dict)

        # Transfer to target
        target_dict = target_model.state_dict()
        current_dict = current_model.state_dict()

        for key in target_dict:
            if key in current_dict:
                target_dict[key] = 0.7 * current_dict[key] + 0.3 * target_dict[key]

        target_model.load_state_dict(target_dict)
        return target_model

    def _attention_weighted_transfer(self, target_model: nn.Module, source_domains: List[str]) -> nn.Module:
        """Attention-weighted knowledge transfer"""
        # Learn attention weights for each source domain
        attention_weights = nn.Parameter(torch.ones(len(source_domains)) / len(source_domains))
        attention_weights = F.softmax(attention_weights, dim=0)

        target_dict = target_model.state_dict()

        for i, domain in enumerate(source_domains):
            if domain not in self.domain_models:
                continue

            source_model = self.domain_models[domain]
            source_dict = source_model.state_dict()

            weight = attention_weights[i].item()

            for key in target_dict:
                if key in source_dict:
                    target_dict[key] = (1 - weight) * target_dict[key] + weight * source_dict[key]

        target_model.load_state_dict(target_dict)
        return target_model

class DomainAdversarialTraining:
    """Domain adversarial training for domain adaptation"""

    def __init__(self, feature_extractor: nn.Module, classifier: nn.Module,
                 domain_discriminator: nn.Module, config: TransferConfig):
        self.feature_extractor = feature_extractor
        self.classifier = classifier
        self.domain_discriminator = domain_discriminator
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')

        # Optimizers
        self.feature_optimizer = optim.Adam(
            self.feature_extractor.parameters(),
            lr=config.learning_rate_ratio * 1e-3
        )
        self.classifier_optimizer = optim.Adam(
            self.classifier.parameters(),
            lr=1e-3
        )
        self.domain_optimizer = optim.Adam(
            self.domain_discriminator.parameters(),
            lr=1e-3
        )

    def train_step(self, source_data: Tuple[torch.Tensor, torch.Tensor],
                   target_data: torch.Tensor) -> Dict[str, float]:
        """Single training step"""
        source_x, source_y = source_data
        target_x = target_data

        # Move to device
        source_x, source_y = source_x.to(self.device), source_y.to(self.device)
        target_x = target_x.to(self.device)

        # Train feature extractor and classifier on source
        self.feature_optimizer.zero_grad()
        self.classifier_optimizer.zero_grad()

        source_features = self.feature_extractor(source_x)
        source_pred = self.classifier(source_features)
        task_loss = F.cross_entropy(source_pred, source_y)

        task_loss.backward()
        self.feature_optimizer.step()
        self.classifier_optimizer.step()

        # Train domain discriminator
        self.domain_optimizer.zero_grad()

        # Source domain features (label = 0)
        source_features = self.feature_extractor(source_x).detach()
        source_domain_pred = self.domain_discriminator(source_features)
        source_domain_loss = F.cross_entropy(source_domain_pred, torch.zeros(source_x.size(0), dtype=torch.long, device=self.device))

        # Target domain features (label = 1)
        target_features = self.feature_extractor(target_x).detach()
        target_domain_pred = self.domain_discriminator(target_features)
        target_domain_loss = F.cross_entropy(target_domain_pred, torch.ones(target_x.size(0), dtype=torch.long, device=self.device))

        domain_loss = (source_domain_loss + target_domain_loss) / 2
        domain_loss.backward()
        self.domain_optimizer.step()

        # Train feature extractor to confuse domain discriminator
        self.feature_optimizer.zero_grad()

        # Source domain
        source_features = self.feature_extractor(source_x)
        source_domain_pred = self.domain_discriminator(source_features)
        source_adv_loss = F.cross_entropy(source_domain_pred, torch.ones(source_x.size(0), dtype=torch.long, device=self.device))

        # Target domain
        target_features = self.feature_extractor(target_x)
        target_domain_pred = self.domain_discriminator(target_features)
        target_adv_loss = F.cross_entropy(target_domain_pred, torch.zeros(target_x.size(0), dtype=torch.long, device=self.device))

        adv_loss = (source_adv_loss + target_adv_loss) / 2
        adv_loss.backward()
        self.feature_optimizer.step()

        return {
            'task_loss': task_loss.item(),
            'domain_loss': domain_loss.item(),
            'adversarial_loss': adv_loss.item()
        }

class MetaTransferLearning:
    """Meta-learning for transfer learning"""

    def __init__(self, config: TransferConfig):
        self.config = config
        self.device = torch.device(config.device if torch.cuda.is_available() else 'cpu')
        self.meta_network = None
        self.adaptation_history = []

    def create_meta_network(self, base_model: nn.Module, meta_config: Dict[str, Any]):
        """Create meta-network for fast adaptation"""
        self.meta_network = MetaNetwork(base_model, meta_config).to(self.device)

    def meta_train(self, task_distributions: List[Tuple[str, Any]],
                  meta_optimizer: optim.Optimizer,
                  num_meta_iterations: int = 1000) -> Dict[str, List[float]]:
        """Meta-training across multiple tasks"""
        meta_losses = []
        task_losses = []

        for iteration in range(num_meta_iterations):
            meta_optimizer.zero_grad()

            # Sample tasks
            sampled_tasks = random.sample(task_distributions, min(5, len(task_distributions)))

            iteration_loss = 0

            for task_name, task_data in sampled_tasks:
                # Adapt to task
                adapted_model, adaptation_loss = self._adapt_to_task(task_data)

                # Compute meta-loss
                meta_loss = self._compute_meta_loss(adapted_model, task_data)
                meta_loss = meta_loss / len(sampled_tasks)
                meta_loss.backward(retain_graph=True)

                iteration_loss += meta_loss.item()
                task_losses.append(adaption_loss)

            meta_optimizer.step()
            meta_losses.append(iteration_loss)

            if iteration % 100 == 0:
                logger.info(f"Meta iteration {iteration}: Loss = {iteration_loss:.4f}")

        return {
            'meta_losses': meta_losses,
            'task_losses': task_losses
        }

    def _adapt_to_task(self, task_data: Any) -> Tuple[nn.Module, float]:
        """Adapt meta-network to specific task"""
        # Implementation for task-specific adaptation
        adapted_model = copy.deepcopy(self.meta_network)
        adaptation_loss = 0.0

        # Fast adaptation (e.g., few-shot learning)
        # This would be implemented based on specific adaptation strategy

        return adapted_model, adaptation_loss

    def _compute_meta_loss(self, adapted_model: nn.Module, task_data: Any) -> torch.Tensor:
        """Compute meta-loss for adapted model"""
        # Implementation for meta-loss computation
        # This would evaluate the adapted model on task data
        return torch.tensor(0.0, device=self.device)

class MetaNetwork(nn.Module):
    """Meta-network for fast adaptation"""

    def __init__(self, base_model: nn.Module, meta_config: Dict[str, Any]):
        super().__init__()
        self.base_model = base_model
        self.meta_config = meta_config

        # Meta-parameters for adaptation
        self.meta_layers = nn.ModuleDict()

        # Create meta-layers for fast adaptation
        for name, param in base_model.named_parameters():
            if 'weight' in name or 'bias' in name:
                self.meta_layers[name] = nn.Parameter(param.data.clone())

    def forward(self, x: torch.Tensor, adaptation_params: Optional[Dict[str, torch.Tensor]] = None) -> torch.Tensor:
        """Forward pass with optional adaptation parameters"""
        if adaptation_params is None:
            return self.base_model(x)

        # Apply adaptation parameters
        # This would implement the specific adaptation strategy
        return self.base_model(x)

class TransferLearningAnalyzer:
    """Analyze transfer learning performance"""

    def __init__(self):
        self.transfer_metrics = defaultdict(list)
        self.analysis_results = {}

    def log_transfer_step(self, source_domain: str, target_domain: str,
                         metrics: Dict[str, float]):
        """Log transfer learning metrics"""
        step_data = {
            'source_domain': source_domain,
            'target_domain': target_domain,
            'timestamp': time.time(),
            **metrics
        }
        self.transfer_metrics[f"{source_domain}_to_{target_domain}"].append(step_data)

    def analyze_transfer_effectiveness(self, source_domain: str, target_domain: str) -> Dict[str, Any]:
        """Analyze effectiveness of transfer learning"""
        key = f"{source_domain}_to_{target_domain}"
        if key not in self.transfer_metrics:
            return {"error": "No transfer data found"}

        steps = self.transfer_metrics[key]

        # Calculate improvement metrics
        initial_performance = steps[0].get('target_performance', 0)
        final_performance = steps[-1].get('target_performance', 0)
        improvement = final_performance - initial_performance
        improvement_rate = improvement / max(1, len(steps))

        # Calculate convergence metrics
        convergence_step = self._find_convergence_step(steps)

        analysis = {
            'source_domain': source_domain,
            'target_domain': target_domain,
            'initial_performance': initial_performance,
            'final_performance': final_performance,
            'improvement': improvement,
            'improvement_rate': improvement_rate,
            'convergence_step': convergence_step,
            'total_steps': len(steps),
            'transfer_efficiency': improvement / max(1, convergence_step) if convergence_step else 0
        }

        self.analysis_results[key] = analysis
        return analysis

    def _find_convergence_step(self, steps: List[Dict[str, Any]], window_size: int = 10) -> int:
        """Find convergence step based on performance plateau"""
        if len(steps) < window_size:
            return len(steps)

        performances = [step.get('target_performance', 0) for step in steps]

        for i in range(window_size, len(performances)):
            window = performances[i-window_size:i]
            variance = np.var(window)
            if variance < 0.01:  # Threshold for convergence
                return i

        return len(steps)

    def generate_transfer_report(self) -> str:
        """Generate comprehensive transfer learning report"""
        report = ["=== Transfer Learning Analysis Report ===\n"]

        for key, analysis in self.analysis_results.items():
            report.append(f"Transfer: {key}")
            report.append(f"  Improvement: {analysis['improvement']:.4f}")
            report.append(f"  Efficiency: {analysis['transfer_efficiency']:.6f}")
            report.append(f"  Convergence: Step {analysis['convergence_step']}")
            report.append("")

        return "\n".join(report)

# Utility functions
def create_transfer_config(source_domains: List[str], target_domain: str) -> TransferConfig:
    """Create transfer learning configuration"""
    return TransferConfig(
        source_domains=source_domains,
        target_domain=target_domain,
        adaptation_method='fine_tuning',
        learning_rate_ratio=0.1,
        adaptation_steps=1000,
        device='cuda' if torch.cuda.is_available() else 'cpu'
    )

def calculate_domain_similarity(model1: nn.Module, model2: nn.Module,
                               sample_data: torch.Tensor) -> float:
    """Calculate similarity between two domains based on model representations"""
    device = sample_data.device

    # Extract features from both models
    with torch.no_grad():
        features1 = model1.get_transferable_features(sample_data.to(device))
        features2 = model2.get_transferable_features(sample_data.to(device))

    # Calculate cosine similarity
    similarity = F.cosine_similarity(features1, features2, dim=1).mean().item()

    return similarity

def create_domain_adapter(input_dim: int, num_domains: int) -> DomainAdapter:
    """Create domain adapter for multi-domain learning"""
    return DomainAdapter(input_dim, num_domains)

if __name__ == "__main__":
    # Example usage
    config = create_transfer_config(
        source_domains=['vision', 'nlp', 'audio'],
        target_domain='multimodal'
    )

    # Create progressive transfer learning system
    transfer_system = ProgressiveTransferLearning(config)

    # Create transfer learning analyzer
    analyzer = TransferLearningAnalyzer()

    print("Transfer Learning Framework initialized!")
    print(f"Source domains: {config.source_domains}")
    print(f"Target domain: {config.target_domain}")
    print(f"Adaptation method: {config.adaptation_method}")
    print(f"Available transfer methods: ensemble, progressive, attention_weighted")
    print(f"Domain adversarial training supported: {DomainAdversarialTraining.__name__}")
    print(f"Meta-transfer learning supported: {MetaTransferLearning.__name__}")