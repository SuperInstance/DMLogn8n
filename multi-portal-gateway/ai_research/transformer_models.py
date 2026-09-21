"""
Advanced Transformer Models for DMLogn8n AI Research
Implementing cutting-edge transformer architectures and optimizations
Based on latest research from 2024-2025
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import numpy as np
from typing import Optional, Tuple, Dict, Any, List
from dataclasses import dataclass
from einops import rearrange, repeat
from rotary_embedding_torch import RotaryEmbedding
import flash_attn
from flash_attn import flash_attn_func


@dataclass
class TransformerConfig:
    """Configuration for advanced transformer models"""
    vocab_size: int = 50432
    d_model: int = 2048
    n_layers: int = 24
    n_heads: int = 32
    d_ff: int = 8192
    max_seq_len: int = 8192
    dropout: float = 0.1
    activation: str = "swiglu"
    use_rotary: bool = True
    use_flash_attention: bool = True
    use_moe: bool = False
    moe_num_experts: int = 8
    moe_top_k: int = 2
    use_alibi: bool = False
    tie_word_embeddings: bool = True
    norm_type: str = "rmsnorm"
    init_std: float = 0.02
    use_gradient_checkpointing: bool = True


class RMSNorm(nn.Module):
    """Root Mean Square Layer Normalization"""
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x):
        norm = x.norm(dim=-1, keepdim=True) * (x.shape[-1] ** -0.5)
        return self.weight * x / (norm + self.eps)


class SwiGLU(nn.Module):
    """Swish-Gated Linear Unit activation"""
    def __init__(self, dim: int, hidden_dim: Optional[int] = None):
        super().__init__()
        hidden_dim = hidden_dim or int(dim * 4 / 3)
        self.w1 = nn.Linear(dim, hidden_dim, bias=False)
        self.w2 = nn.Linear(dim, hidden_dim, bias=False)
        self.w3 = nn.Linear(hidden_dim, dim, bias=False)

    def forward(self, x):
        return self.w3(F.silu(self.w1(x)) * self.w2(x))


class RotaryPositionalEmbedding(nn.Module):
    """Rotary Positional Embedding for improved positional encoding"""
    def __init__(self, dim: int, max_seq_len: int = 8192):
        super().__init__()
        self.dim = dim
        self.rotary_emb = RotaryEmbedding(dim)

    def forward(self, x):
        # x shape: (batch_size, seq_len, dim)
        return self.rotary_emb.rotate_queries_or_keys(x)


class MultiHeadAttention(nn.Module):
    """Advanced Multi-Head Attention with Flash Attention and Rotary Embeddings"""
    def __init__(self, config: TransformerConfig):
        super().__init__()
        self.config = config
        self.n_heads = config.n_heads
        self.d_model = config.d_model
        self.d_head = config.d_model // config.n_heads

        self.q_proj = nn.Linear(config.d_model, config.d_model, bias=False)
        self.k_proj = nn.Linear(config.d_model, config.d_model, bias=False)
        self.v_proj = nn.Linear(config.d_model, config.d_model, bias=False)
        self.o_proj = nn.Linear(config.d_model, config.d_model, bias=False)

        self.dropout = nn.Dropout(config.dropout)
        self.use_rotary = config.use_rotary

        if self.use_rotary:
            self.rotary_emb = RotaryPositionalEmbedding(self.d_head, config.max_seq_len)

        # ALiBi (Attention with Linear Biases)
        if config.use_alibi:
            self.alibi = self._build_alibi_bias(config.n_heads, config.max_seq_len)
        else:
            self.alibi = None

    def _build_alibi_bias(self, n_heads: int, max_seq_len: int):
        """Build ALiBi bias matrix"""
        slopes = torch.tensor([2 ** (-8 / n_heads * (i + 1)) for i in range(n_heads)])
        bias = torch.arange(max_seq_len).unsqueeze(0) - torch.arange(max_seq_len).unsqueeze(1)
        bias = bias.abs().unsqueeze(0) * slopes.unsqueeze(1).unsqueeze(2)
        return bias

    def forward(self, x: torch.Tensor, attention_mask: Optional[torch.Tensor] = None):
        batch_size, seq_len, _ = x.shape

        # Project to Q, K, V
        q = self.q_proj(x).view(batch_size, seq_len, self.n_heads, self.d_head).transpose(1, 2)
        k = self.k_proj(x).view(batch_size, seq_len, self.n_heads, self.d_head).transpose(1, 2)
        v = self.v_proj(x).view(batch_size, seq_len, self.n_heads, self.d_head).transpose(1, 2)

        # Apply rotary embeddings
        if self.use_rotary:
            q = self.rotary_emb(q)
            k = self.rotary_emb(k)

        # Flash Attention for efficiency
        if self.config.use_flash_attention:
            attn_output = flash_attn_func(
                q, k, v,
                dropout_p=self.dropout.p if self.training else 0.0,
                softmax_scale=1.0 / math.sqrt(self.d_head)
            )
        else:
            # Standard attention
            scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.d_head)

            # Add ALiBi bias if enabled
            if self.alibi is not None:
                scores = scores + self.alibi[:, :seq_len, :seq_len].to(scores.device)

            if attention_mask is not None:
                scores = scores.masked_fill(attention_mask == 0, float('-inf'))

            attn_weights = F.softmax(scores, dim=-1)
            attn_weights = self.dropout(attn_weights)
            attn_output = torch.matmul(attn_weights, v)

        # Reshape and project output
        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, seq_len, self.d_model)
        output = self.o_proj(attn_output)

        return output


class MoE(nn.Module):
    """Mixture of Experts for sparse activation"""
    def __init__(self, config: TransformerConfig):
        super().__init__()
        self.config = config
        self.num_experts = config.moe_num_experts
        self.top_k = config.moe_top_k

        # Gating network
        self.gate = nn.Linear(config.d_model, config.moe_num_experts, bias=False)

        # Expert networks
        self.experts = nn.ModuleList([
            SwiGLU(config.d_model) for _ in range(config.moe_num_experts)
        ])

    def forward(self, x):
        batch_size, seq_len, dim = x.shape
        x_flat = x.view(-1, dim)

        # Compute gating scores
        gate_logits = self.gate(x_flat)
        gate_scores = F.softmax(gate_logits, dim=-1)

        # Select top-k experts
        top_k_scores, top_k_indices = torch.topk(gate_scores, self.top_k, dim=-1)
        top_k_scores = top_k_scores / top_k_scores.sum(dim=-1, keepdim=True)

        # Expert computation
        expert_outputs = torch.zeros_like(x_flat)
        for i, expert in enumerate(self.experts):
            expert_mask = (top_k_indices == i).any(dim=-1)
            if expert_mask.any():
                expert_input = x_flat[expert_mask]
                expert_output = expert(expert_input)
                expert_weights = top_k_scores[expert_mask][top_k_indices[expert_mask] == i]
                expert_outputs[expert_mask] += expert_output * expert_weights.unsqueeze(-1)

        return expert_outputs.view(batch_size, seq_len, dim)


class TransformerBlock(nn.Module):
    """Advanced Transformer Block with MoE and optimizations"""
    def __init__(self, config: TransformerConfig, layer_idx: int):
        super().__init__()
        self.config = config
        self.layer_idx = layer_idx

        # Attention layer
        self.attention = MultiHeadAttention(config)

        # Feed-forward layer (MoE or standard)
        if config.use_moe:
            self.feed_forward = MoE(config)
        else:
            self.feed_forward = SwiGLU(config.d_model)

        # Normalization layers
        if config.norm_type == "rmsnorm":
            self.attention_norm = RMSNorm(config.d_model)
            self.ffn_norm = RMSNorm(config.d_model)
        else:
            self.attention_norm = nn.LayerNorm(config.d_model)
            self.ffn_norm = nn.LayerNorm(config.d_model)

        # Dropout
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x: torch.Tensor, attention_mask: Optional[torch.Tensor] = None):
        # Pre-normalization
        attn_output = self.attention(self.attention_norm(x), attention_mask)
        x = x + self.dropout(attn_output)

        ffn_output = self.feed_forward(self.ffn_norm(x))
        x = x + self.dropout(ffn_output)

        return x


class AdvancedTransformer(nn.Module):
    """State-of-the-art Transformer model with latest optimizations"""
    def __init__(self, config: TransformerConfig):
        super().__init__()
        self.config = config

        # Embeddings
        self.token_embedding = nn.Embedding(config.vocab_size, config.d_model)
        self.dropout = nn.Dropout(config.dropout)

        # Transformer layers
        self.layers = nn.ModuleList([
            TransformerBlock(config, i) for i in range(config.n_layers)
        ])

        # Final normalization
        if config.norm_type == "rmsnorm":
            self.final_norm = RMSNorm(config.d_model)
        else:
            self.final_norm = nn.LayerNorm(config.d_model)

        # Output projection
        if config.tie_word_embeddings:
            self.output_projection = lambda x: torch.matmul(x, self.token_embedding.weight.t())
        else:
            self.output_projection = nn.Linear(config.d_model, config.vocab_size, bias=False)

        # Initialize weights
        self.apply(self._init_weights)

        # Gradient checkpointing
        if config.use_gradient_checkpointing:
            self.gradient_checkpointing_enable()

    def _init_weights(self, module):
        """Initialize weights with proper scaling"""
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=self.config.init_std)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=self.config.init_std)

    def forward(self,
                input_ids: torch.Tensor,
                attention_mask: Optional[torch.Tensor] = None,
                labels: Optional[torch.Tensor] = None):

        batch_size, seq_len = input_ids.shape

        # Create embeddings
        hidden_states = self.token_embedding(input_ids)
        hidden_states = self.dropout(hidden_states)

        # Process through transformer layers
        for layer in self.layers:
            if self.config.use_gradient_checkpointing and self.training:
                hidden_states = torch.utils.checkpoint.checkpoint(
                    layer, hidden_states, attention_mask
                )
            else:
                hidden_states = layer(hidden_states, attention_mask)

        # Final normalization
        hidden_states = self.final_norm(hidden_states)

        # Compute logits
        logits = self.output_projection(hidden_states)

        # Compute loss if labels provided
        loss = None
        if labels is not None:
            # Shift for language modeling
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))

        return {
            "logits": logits,
            "loss": loss,
            "hidden_states": hidden_states
        }


class GamingOptimizedTransformer(AdvancedTransformer):
    """Transformer specifically optimized for gaming and narrative generation"""
    def __init__(self, config: TransformerConfig):
        # Gaming-specific optimizations
        config.max_seq_len = 4096  # Optimize for typical gaming sequences
        config.n_heads = 32
        config.d_model = 2048
        config.n_layers = 20

        super().__init__(config)

        # Gaming-specific components
        self.character_embedding = nn.Embedding(1000, config.d_model)  # Character IDs
        self.state_embedding = nn.Embedding(100, config.d_model)  # Game states
        self.emotion_embedding = nn.Embedding(50, config.d_model)  # Emotional states

        # Cross-attention for character interactions
        self.character_attention = MultiHeadAttention(config)

        # Action prediction heads
        self.action_head = nn.Linear(config.d_model, 1000)  # Possible actions
        self.dialogue_head = nn.Linear(config.d_model, config.vocab_size)  # Dialogue generation

        # Narrative coherence scoring
        self.coherence_scorer = nn.Sequential(
            nn.Linear(config.d_model, config.d_model // 4),
            nn.ReLU(),
            nn.Linear(config.d_model // 4, 1),
            nn.Sigmoid()
        )

    def forward(self,
                input_ids: torch.Tensor,
                character_ids: Optional[torch.Tensor] = None,
                state_ids: Optional[torch.Tensor] = None,
                emotion_ids: Optional[torch.Tensor] = None,
                attention_mask: Optional[torch.Tensor] = None,
                labels: Optional[torch.Tensor] = None):

        # Standard transformer processing
        outputs = super().forward(input_ids, attention_mask, labels)
        hidden_states = outputs["hidden_states"]

        # Add gaming-specific embeddings
        if character_ids is not None:
            char_emb = self.character_embedding(character_ids)
            hidden_states = hidden_states + char_emb

        if state_ids is not None:
            state_emb = self.state_embedding(state_ids)
            hidden_states = hidden_states + state_emb

        if emotion_ids is not None:
            emotion_emb = self.emotion_embedding(emotion_ids)
            hidden_states = hidden_states + emotion_emb

        # Generate gaming-specific outputs
        action_logits = self.action_head(hidden_states)
        dialogue_logits = self.dialogue_head(hidden_states)
        coherence_score = self.coherence_scorer(hidden_states.mean(dim=1))

        return {
            "logits": outputs["logits"],
            "action_logits": action_logits,
            "dialogue_logits": dialogue_logits,
            "coherence_score": coherence_score,
            "loss": outputs["loss"],
            "hidden_states": hidden_states
        }


# Utility functions for model optimization
def create_optimizer(model, learning_rate: float = 1e-4, weight_decay: float = 0.01):
    """Create optimized AdamW optimizer with cosine decay"""
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=learning_rate,
        weight_decay=weight_decay,
        betas=(0.9, 0.95),
        eps=1e-8
    )
    return optimizer


def create_scheduler(optimizer, warmup_steps: int, total_steps: int):
    """Create cosine learning rate scheduler with warmup"""
    def lr_lambda(current_step):
        if current_step < warmup_steps:
            return float(current_step) / float(max(1, warmup_steps))
        progress = float(current_step - warmup_steps) / float(max(1, total_steps - warmup_steps))
        return 0.5 * (1.0 + math.cos(math.pi * progress))

    return torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)


# Model factory functions
def create_base_transformer(vocab_size: int = 50432) -> AdvancedTransformer:
    """Create base transformer configuration"""
    config = TransformerConfig(
        vocab_size=vocab_size,
        d_model=1024,
        n_layers=12,
        n_heads=16,
        d_ff=4096,
        use_flash_attention=True,
        use_rotary=True,
        use_gradient_checkpointing=True
    )
    return AdvancedTransformer(config)


def create_large_transformer(vocab_size: int = 50432) -> AdvancedTransformer:
    """Create large transformer configuration"""
    config = TransformerConfig(
        vocab_size=vocab_size,
        d_model=2048,
        n_layers=24,
        n_heads=32,
        d_ff=8192,
        use_flash_attention=True,
        use_rotary=True,
        use_moe=True,
        moe_num_experts=8,
        use_gradient_checkpointing=True
    )
    return AdvancedTransformer(config)


def create_gaming_transformer(vocab_size: int = 50432) -> GamingOptimizedTransformer:
    """Create gaming-optimized transformer"""
    config = TransformerConfig(
        vocab_size=vocab_size,
        d_model=2048,
        n_layers=20,
        n_heads=32,
        use_flash_attention=True,
        use_rotary=True,
        use_gradient_checkpointing=True
    )
    return GamingOptimizedTransformer(config)


# Training utilities
class TransformerTrainer:
    """Advanced trainer for transformer models"""
    def __init__(self, model: AdvancedTransformer, device: str = "cuda"):
        self.model = model.to(device)
        self.device = device
        self.scaler = torch.cuda.amp.GradScaler()

    def train_step(self, batch, optimizer, scheduler):
        """Single training step with mixed precision"""
        self.model.train()

        with torch.cuda.amp.autocast():
            outputs = self.model(**batch)
            loss = outputs["loss"]

        # Backward pass with gradient scaling
        optimizer.zero_grad()
        self.scaler.scale(loss).backward()

        # Gradient clipping
        self.scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)

        self.scaler.step(optimizer)
        self.scaler.update()
        scheduler.step()

        return loss.item()

    def evaluate(self, dataloader):
        """Evaluate model on validation data"""
        self.model.eval()
        total_loss = 0
        total_tokens = 0

        with torch.no_grad():
            for batch in dataloader:
                batch = {k: v.to(self.device) for k, v in batch.items()}

                with torch.cuda.amp.autocast():
                    outputs = self.model(**batch)
                    loss = outputs["loss"]

                total_loss += loss.item()
                total_tokens += batch["input_ids"].numel()

        return total_loss / len(dataloader), total_tokens


if __name__ == "__main__":
    # Example usage
    print("Creating advanced transformer models...")

    # Create different model configurations
    base_model = create_base_transformer()
    large_model = create_large_transformer()
    gaming_model = create_gaming_transformer()

    print(f"Base model parameters: {sum(p.numel() for p in base_model.parameters()):,}")
    print(f"Large model parameters: {sum(p.numel() for p in large_model.parameters()):,}")
    print(f"Gaming model parameters: {sum(p.numel() for p in gaming_model.parameters()):,}")

    # Example forward pass
    batch_size, seq_len = 2, 512
    input_ids = torch.randint(0, 50432, (batch_size, seq_len))
    attention_mask = torch.ones(batch_size, seq_len)

    print("\nTesting model forward pass...")
    with torch.no_grad():
        outputs = gaming_model(input_ids, attention_mask=attention_mask)
        print(f"Logits shape: {outputs['logits'].shape}")
        print(f"Action logits shape: {outputs['action_logits'].shape}")
        print(f"Coherence score shape: {outputs['coherence_score'].shape}")

    print("\nTransformer models initialized successfully!")