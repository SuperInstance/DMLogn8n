"""
Graph Neural Networks for DMLogn8n Social and Relationship Modeling
Advanced GNN architectures for character interactions, social dynamics, and narrative structure
Based on latest research in graph neural networks and social network analysis
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from torch_geometric.nn import (
    GCNConv, GATConv, GraphConv, SAGEConv, GATv2Conv,
    global_mean_pool, global_max_pool, global_add_pool,
    TransformerConv, GeneralConv, PANConv, AGNNConv
)
from torch_geometric.data import Data, Batch
from torch_geometric.utils import add_self_loops, degree
import networkx as nx
from scipy.sparse import csr_matrix
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, roc_auc_score


@dataclass
class GNNConfig:
    """Configuration for Graph Neural Networks"""
    # Graph structure
    num_nodes: int = 1000
    node_feature_dim: int = 128
    edge_feature_dim: int = 64
    num_edge_types: int = 10

    # Model architecture
    hidden_dim: int = 256
    num_layers: int = 4
    num_heads: int = 8
    dropout: float = 0.1

    # GNN type
    gnn_type: str = "gat"  # gcn, gat, sage, transformer, pan, general
    use_edge_features: bool = True
    use_batch_norm: bool = True
    use_residual: bool = True

    # Task-specific
    task_type: str = "node_classification"  # node_classification, link_prediction, graph_classification
    num_classes: int = 10

    # Training
    learning_rate: float = 0.001
    weight_decay: float = 1e-5
    patience: int = 50


class GraphAttentionLayer(nn.Module):
    """Custom Graph Attention Layer with multi-head attention"""
    def __init__(self, in_dim: int, out_dim: int, num_heads: int = 8, dropout: float = 0.1):
        super().__init__()
        self.in_dim = in_dim
        self.out_dim = out_dim
        self.num_heads = num_heads
        self.head_dim = out_dim // num_heads

        # Linear projections
        self.query = nn.Linear(in_dim, out_dim, bias=False)
        self.key = nn.Linear(in_dim, out_dim, bias=False)
        self.value = nn.Linear(in_dim, out_dim, bias=False)

        # Edge feature projection
        self.edge_proj = nn.Linear(in_dim, out_dim, bias=False)

        # Output projection
        self.out_proj = nn.Linear(out_dim, out_dim)

        self.dropout = nn.Dropout(dropout)
        self.layer_norm = nn.LayerNorm(out_dim)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor,
                edge_attr: Optional[torch.Tensor] = None) -> torch.Tensor:

        num_nodes = x.size(0)

        # Project to Q, K, V
        q = self.query(x).view(num_nodes, self.num_heads, self.head_dim)
        k = self.key(x).view(num_nodes, self.num_heads, self.head_dim)
        v = self.value(x).view(num_nodes, self.num_heads, self.head_dim)

        # Edge attention computation
        row, col = edge_index

        # Compute attention scores
        scores = (q[row] * k[col]).sum(dim=-1) / (self.head_dim ** 0.5)

        # Add edge features if available
        if edge_attr is not None:
            edge_features = self.edge_proj(edge_attr).view(-1, self.num_heads, self.head_dim)
            edge_scores = (q[row] * edge_features).sum(dim=-1)
            scores = scores + edge_scores

        # Apply softmax and dropout
        attention_weights = F.softmax(scores, dim=0)
        attention_weights = self.dropout(attention_weights)

        # Aggregate messages
        messages = v[col] * attention_weights.unsqueeze(-1)
        aggregated = torch.zeros_like(q).scatter_add_(0, row.unsqueeze(-1).unsqueeze(-1).expand_as(messages), messages)

        # Reshape and project output
        output = aggregated.view(num_nodes, self.out_dim)
        output = self.out_proj(output)
        output = self.layer_norm(output)

        return output


class HeterogeneousGraphNetwork(nn.Module):
    """Heterogeneous Graph Network for complex social relationships"""
    def __init__(self, config: GNNConfig):
        super().__init__()
        self.config = config

        # Node type embeddings
        self.node_type_embedding = nn.Embedding(10, config.node_feature_dim)

        # Edge type embeddings
        self.edge_type_embedding = nn.Embedding(config.num_edge_types, config.edge_feature_dim)

        # GNN layers for different edge types
        self.gnn_layers = nn.ModuleDict()
        for edge_type in range(config.num_edge_types):
            self.gnn_layers[str(edge_type)] = self._create_gnn_layer(config)

        # Meta-path attention
        self.meta_attention = nn.MultiheadAttention(
            embed_dim=config.hidden_dim,
            num_heads=config.num_heads,
            dropout=config.dropout,
            batch_first=True
        )

        # Node update layers
        self.node_update = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_dim, config.node_feature_dim)
        )

    def _create_gnn_layer(self, config: GNNConfig):
        """Create GNN layer based on configuration"""
        if config.gnn_type == "gat":
            return GATv2Conv(config.node_feature_dim, config.hidden_dim, heads=config.num_heads, dropout=config.dropout)
        elif config.gnn_type == "gcn":
            return GCNConv(config.node_feature_dim, config.hidden_dim)
        elif config.gnn_type == "sage":
            return SAGEConv(config.node_feature_dim, config.hidden_dim)
        elif config.gnn_type == "transformer":
            return TransformerConv(config.node_feature_dim, config.hidden_dim, heads=config.num_heads, dropout=config.dropout)
        else:
            return GCNConv(config.node_feature_dim, config.hidden_dim)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor,
                edge_type: torch.Tensor, node_type: torch.Tensor,
                edge_attr: Optional[torch.Tensor] = None) -> torch.Tensor:

        # Add node type embeddings
        type_emb = self.node_type_embedding(node_type)
        x = x + type_emb

        # Process different edge types
        type_embeddings = []
        for edge_t in range(self.config.num_edge_types):
            mask = edge_type == edge_t
            if mask.sum() > 0:
                # Extract edges of this type
                type_edge_index = edge_index[:, mask]
                type_edge_attr = edge_attr[mask] if edge_attr is not None else None

                # Apply GNN for this edge type
                h = self.gnn_layers[str(edge_t)](x, type_edge_index, type_edge_attr)
                type_embeddings.append(h)

        if len(type_embeddings) > 0:
            # Stack type embeddings
            stacked = torch.stack(type_embeddings, dim=1)  # [num_nodes, num_types, hidden_dim]

            # Meta-path attention
            attended, _ = self.meta_attention(stacked, stacked, stacked)
            attended = attended.mean(dim=1)  # Average over types

            # Node update
            output = self.node_update(attended)
        else:
            output = x

        return output


class TemporalGraphNetwork(nn.Module):
    """Temporal Graph Network for dynamic social relationships"""
    def __init__(self, config: GNNConfig, num_timesteps: int = 10):
        super().__init__()
        self.config = config
        self.num_timesteps = num_timesteps

        # Spatial GNN
        self.spatial_gnn = self._create_spatial_gnn(config)

        # Temporal modeling
        self.temporal_encoder = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(
                d_model=config.hidden_dim,
                nhead=config.num_heads,
                dim_feedforward=config.hidden_dim * 4,
                dropout=config.dropout,
                activation='gelu'
            ),
            num_layers=3
        )

        # Time embedding
        self.time_embedding = nn.Embedding(num_timesteps, config.hidden_dim)

        # Output layers
        self.output_layer = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_dim // 2, config.num_classes)
        )

    def _create_spatial_gnn(self, config: GNNConfig):
        """Create spatial GNN component"""
        layers = nn.ModuleList()
        for i in range(config.num_layers):
            if i == 0:
                layers.append(GATv2Conv(config.node_feature_dim, config.hidden_dim, heads=config.num_heads, dropout=config.dropout))
            else:
                layers.append(GATv2Conv(config.hidden_dim, config.hidden_dim, heads=1, dropout=config.dropout))
        return layers

    def forward(self, x_seq: List[torch.Tensor], edge_index_seq: List[torch.Tensor]) -> torch.Tensor:
        """Process sequence of graphs"""
        temporal_features = []

        for t, (x, edge_index) in enumerate(zip(x_seq, edge_index_seq)):
            # Spatial processing
            h = x
            for layer in self.spatial_gnn:
                h = layer(h, edge_index)
                h = F.relu(h)

            # Add time embedding
            time_emb = self.time_embedding(torch.tensor(t, device=x.device))
            h = h + time_emb.unsqueeze(0)

            temporal_features.append(h)

        # Stack temporal features
        temporal_seq = torch.stack(temporal_features, dim=1)  # [num_nodes, timesteps, hidden_dim]

        # Temporal processing
        temporal_seq = temporal_seq.transpose(0, 1)  # [timesteps, num_nodes, hidden_dim]
        temporal_output = self.temporal_encoder(temporal_seq)

        # Use last timestep
        final_features = temporal_output[-1]

        # Classification
        output = self.output_layer(final_features)

        return output


class SocialDynamicsModel(nn.Module):
    """Advanced model for social dynamics and relationship evolution"""
    def __init__(self, config: GNNConfig):
        super().__init__()
        self.config = config

        # Character embedding
        self.character_embedding = nn.Embedding(1000, config.node_feature_dim)

        # Relationship type embedding
        self.relationship_embedding = nn.Embedding(50, config.edge_feature_dim)

        # Heterogeneous GNN for complex relationships
        self.hetero_gnn = HeterogeneousGraphNetwork(config)

        # Influence propagation network
        self.influence_net = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.ReLU(),
            nn.Linear(config.hidden_dim, config.hidden_dim),
            nn.Sigmoid()
        )

        # Sentiment analysis
        self.sentiment_analyzer = nn.Sequential(
            nn.Linear(config.hidden_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 3)  # Positive, negative, neutral
        )

        # Conflict detection
        self.conflict_detector = nn.Sequential(
            nn.Linear(config.hidden_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )

        # Alliance prediction
        self.alliance_predictor = nn.Sequential(
            nn.Linear(config.hidden_dim * 2, 256),
            nn.ReLU(),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )

    def forward(self, character_ids: torch.Tensor, edge_index: torch.Tensor,
                edge_types: torch.Tensor, character_types: torch.Tensor) -> Dict[str, torch.Tensor]:

        # Character embeddings
        x = self.character_embedding(character_ids)

        # Process through heterogeneous GNN
        node_features = self.hetero_gnn(x, edge_index, edge_types, character_types)

        # Compute influence scores
        influence_scores = self.influence_net(node_features)

        # Sentiment analysis
        sentiment_logits = self.sentiment_analyzer(node_features)

        # Conflict detection
        conflict_scores = self.conflict_detector(node_features)

        # Alliance prediction for connected nodes
        row, col = edge_index
        pair_features = torch.cat([node_features[row], node_features[col]], dim=-1)
        alliance_scores = self.alliance_predictor(pair_features)

        return {
            "node_features": node_features,
            "influence_scores": influence_scores,
            "sentiment_logits": sentiment_logits,
            "conflict_scores": conflict_scores,
            "alliance_scores": alliance_scores
        }


class NarrativeStructureGNN(nn.Module):
    """GNN for modeling narrative structure and story progression"""
    def __init__(self, config: GNNConfig):
        super().__init__()
        self.config = config

        # Story element embeddings
        self.scene_embedding = nn.Embedding(1000, config.node_feature_dim)
        self.character_embedding = nn.Embedding(1000, config.node_feature_dim)
        self.location_embedding = nn.Embedding(500, config.node_feature_dim)
        self.event_embedding = nn.Embedding(200, config.node_feature_dim)

        # Graph construction layers
        self.scene_gnn = GATv2Conv(config.node_feature_dim, config.hidden_dim, heads=config.num_heads)
        self.character_gnn = GATv2Conv(config.node_feature_dim, config.hidden_dim, heads=config.num_heads)
        self.cross_attention = nn.MultiheadAttention(config.hidden_dim, config.num_heads, batch_first=True)

        # Narrative coherence scoring
        self.coherence_scorer = nn.Sequential(
            nn.Linear(config.hidden_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 1),
            nn.Sigmoid()
        )

        # Plot twist prediction
        self.twist_predictor = nn.Sequential(
            nn.Linear(config.hidden_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )

        # Character arc tracking
        self.arc_tracker = nn.LSTM(
            input_size=config.hidden_dim,
            hidden_size=config.hidden_dim // 2,
            num_layers=2,
            batch_first=True,
            bidirectional=True
        )

    def forward(self, scene_ids: torch.Tensor, character_ids: torch.Tensor,
                location_ids: torch.Tensor, event_ids: torch.Tensor,
                scene_edges: torch.Tensor, character_edges: torch.Tensor,
                cross_edges: torch.Tensor) -> Dict[str, torch.Tensor]:

        # Embed different story elements
        scene_features = self.scene_embedding(scene_ids)
        character_features = self.character_embedding(character_ids)
        location_features = self.location_embedding(location_ids)
        event_features = self.event_embedding(event_ids)

        # Combine element features for scenes
        scene_combined = scene_features + location_features + event_features

        # Process scene graph
        scene_graph_features = self.scene_gnn(scene_combined, scene_edges)

        # Process character graph
        character_graph_features = self.character_gnn(character_features, character_edges)

        # Cross-attention between scenes and characters
        scenes_query = scene_graph_features.unsqueeze(0)
        chars_key_value = character_graph_features.unsqueeze(0)

        attended_scenes, _ = self.cross_attention(scenes_query, chars_key_value, chars_key_value)
        attended_scenes = attended_scenes.squeeze(0)

        # Narrative coherence scoring
        coherence_scores = self.coherence_scorer(attended_scenes)

        # Plot twist prediction
        twist_scores = self.twist_predictor(attended_scenes)

        # Character arc tracking (assuming sequence order)
        if character_graph_features.size(0) > 1:
            arc_features, _ = self.arc_tracker(character_graph_features.unsqueeze(0))
            arc_features = arc_features.squeeze(0)
        else:
            arc_features = character_graph_features

        return {
            "scene_features": scene_graph_features,
            "character_features": character_graph_features,
            "attended_scenes": attended_scenes,
            "coherence_scores": coherence_scores,
            "twist_scores": twist_scores,
            "arc_features": arc_features
        }


class GNNTrainer:
    """Trainer for Graph Neural Networks"""
    def __init__(self, model: nn.Module, config: GNNConfig):
        self.model = model
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

        # Optimizer and scheduler
        self.optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay
        )

        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='min', factor=0.5, patience=config.patience, verbose=True
        )

        # Loss functions
        self.classification_loss = nn.CrossEntropyLoss()
        self.regression_loss = nn.MSELoss()
        self.binary_loss = nn.BCELoss()

    def train_step(self, data: Data) -> Dict[str, float]:
        """Single training step"""
        self.model.train()
        self.optimizer.zero_grad()

        data = data.to(self.device)

        # Forward pass
        outputs = self.model(
            data.x, data.edge_index, data.edge_type,
            getattr(data, 'node_type', torch.zeros(data.x.size(0), dtype=torch.long))
        )

        # Compute losses
        total_loss = 0
        losses = {}

        if hasattr(data, 'y') and self.config.task_type == "node_classification":
            cls_loss = self.classification_loss(outputs['node_features'], data.y)
            total_loss += cls_loss
            losses['classification'] = cls_loss.item()

        if hasattr(data, 'conflict_labels'):
            conflict_loss = self.binary_loss(outputs['conflict_scores'].squeeze(), data.conflict_labels.float())
            total_loss += conflict_loss
            losses['conflict'] = conflict_loss.item()

        if hasattr(data, 'alliance_labels'):
            alliance_loss = self.binary_loss(outputs['alliance_scores'].squeeze(), data.alliance_labels.float())
            total_loss += alliance_loss
            losses['alliance'] = alliance_loss.item()

        # Backward pass
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
        self.optimizer.step()

        losses['total'] = total_loss.item()
        return losses

    def evaluate(self, dataloader) -> Dict[str, float]:
        """Evaluate model on validation data"""
        self.model.eval()
        total_loss = 0
        all_predictions = []
        all_labels = []

        with torch.no_grad():
            for data in dataloader:
                data = data.to(self.device)

                outputs = self.model(
                    data.x, data.edge_index, data.edge_type,
                    getattr(data, 'node_type', torch.zeros(data.x.size(0), dtype=torch.long))
                )

                if hasattr(data, 'y') and self.config.task_type == "node_classification":
                    loss = self.classification_loss(outputs['node_features'], data.y)
                    total_loss += loss.item()

                    predictions = F.softmax(outputs['node_features'], dim=1).argmax(dim=1)
                    all_predictions.extend(predictions.cpu().numpy())
                    all_labels.extend(data.y.cpu().numpy())

        avg_loss = total_loss / len(dataloader)

        metrics = {'loss': avg_loss}
        if len(all_predictions) > 0:
            from sklearn.metrics import accuracy_score, f1_score
            metrics['accuracy'] = accuracy_score(all_labels, all_predictions)
            metrics['f1'] = f1_score(all_labels, all_predictions, average='weighted')

        return metrics


# Utility functions for graph construction
def create_social_graph(characters: List[Dict], relationships: List[Dict]) -> Data:
    """Create social graph from character and relationship data"""
    # Create node features
    node_features = []
    node_types = []
    character_ids = []

    for char in characters:
        # Combine character attributes into feature vector
        features = [
            char.get('age', 25) / 100,
            char.get('power', 0.5),
            char.get('morality', 0.5),
            char.get('social_status', 0.5),
            len(char.get('skills', [])) / 10
        ]
        node_features.append(features)
        node_types.append(char.get('type', 0))
        character_ids.append(char['id'])

    x = torch.tensor(node_features, dtype=torch.float)
    node_type = torch.tensor(node_types, dtype=torch.long)

    # Create edges
    edge_index = []
    edge_types = []
    edge_features = []

    char_id_to_idx = {char_id: idx for idx, char_id in enumerate(character_ids)}

    for rel in relationships:
        if rel['source'] in char_id_to_idx and rel['target'] in char_id_to_idx:
            src_idx = char_id_to_idx[rel['source']]
            tgt_idx = char_id_to_idx[rel['target']]

            edge_index.append([src_idx, tgt_idx])
            edge_index.append([tgt_idx, src_idx])  # Make undirected

            edge_types.extend([rel['type'], rel['type']])

            # Edge features
            edge_feat = [
                rel.get('strength', 0.5),
                rel.get('duration', 0) / 100,
                rel.get('trust', 0.5)
            ]
            edge_features.extend([edge_feat, edge_feat])

    edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
    edge_type = torch.tensor(edge_types, dtype=torch.long)
    edge_attr = torch.tensor(edge_features, dtype=torch.float)

    return Data(x=x, edge_index=edge_index, edge_type=edge_type, edge_attr=edge_attr, node_type=node_type)


def visualize_graph(data: Data, node_labels: Optional[List[str]] = None,
                    save_path: Optional[str] = None):
    """Visualize graph structure"""
    G = nx.Graph()

    # Add nodes
    for i in range(data.x.size(0)):
        label = node_labels[i] if node_labels else f"Node {i}"
        G.add_node(i, label=label)

    # Add edges
    edge_index = data.edge_index.t().tolist()
    for src, tgt in edge_index:
        G.add_edge(src, tgt)

    # Draw graph
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=500, font_size=8)
    plt.title("Social Graph Structure")

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    else:
        plt.show()


def create_gnn_config(model_size: str = "base") -> GNNConfig:
    """Create GNN configuration"""
    if model_size == "base":
        return GNNConfig(
            node_feature_dim=128,
            hidden_dim=256,
            num_layers=3,
            num_heads=8,
            gnn_type="gat",
            use_edge_features=True
        )
    elif model_size == "large":
        return GNNConfig(
            node_feature_dim=256,
            hidden_dim=512,
            num_layers=5,
            num_heads=16,
            gnn_type="transformer",
            use_edge_features=True
        )
    else:
        return GNNConfig()


if __name__ == "__main__":
    print("Creating Graph Neural Networks for social modeling...")

    # Create configuration
    config = create_gnn_config("base")
    model = SocialDynamicsModel(config)

    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    # Create sample data
    characters = [
        {'id': 0, 'age': 30, 'power': 0.8, 'morality': 0.7, 'social_status': 0.9, 'type': 0},
        {'id': 1, 'age': 25, 'power': 0.6, 'morality': 0.8, 'social_status': 0.7, 'type': 0},
        {'id': 2, 'age': 45, 'power': 0.9, 'morality': 0.3, 'social_status': 0.8, 'type': 1},
    ]

    relationships = [
        {'source': 0, 'target': 1, 'type': 1, 'strength': 0.8, 'duration': 50, 'trust': 0.9},
        {'source': 1, 'target': 2, 'type': 2, 'strength': 0.3, 'duration': 20, 'trust': 0.2},
        {'source': 0, 'target': 2, 'type': 3, 'strength': 0.1, 'duration': 10, 'trust': 0.1},
    ]

    # Create graph data
    graph_data = create_social_graph(characters, relationships)

    print(f"\nGraph created with {graph_data.x.size(0)} nodes and {graph_data.edge_index.size(1)} edges")

    # Test model
    character_ids = torch.tensor([c['id'] for c in characters])
    print("\nTesting social dynamics model...")
    with torch.no_grad():
        outputs = model(
            character_ids=character_ids,
            edge_index=graph_data.edge_index,
            edge_types=graph_data.edge_type,
            character_types=graph_data.node_type
        )

        print(f"Node features shape: {outputs['node_features'].shape}")
        print(f"Influence scores shape: {outputs['influence_scores'].shape}")
        print(f"Sentiment logits shape: {outputs['sentiment_logits'].shape}")
        print(f"Conflict scores shape: {outputs['conflict_scores'].shape}")
        print(f"Alliance scores shape: {outputs['alliance_scores'].shape}")

    print("\nGraph Neural Networks initialized successfully!")