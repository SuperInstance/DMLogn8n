"""
Advanced Diffusion Models for DMLogn8n Content Creation
State-of-the-art generative AI using diffusion models for images, text, and audio
Based on latest research in diffusion models and generative AI (2024-2025)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from einops import rearrange, repeat
import math
from functools import partial
import torchvision.transforms as transforms
from PIL import Image
import matplotlib.pyplot as plt
from tqdm import tqdm


@dataclass
class DiffusionConfig:
    """Configuration for diffusion models"""
    # General diffusion parameters
    num_timesteps: int = 1000
    beta_start: float = 1e-4
    beta_end: float = 2e-2
    beta_schedule: str = "linear"  # linear, cosine, scaled_linear
    predict_eps: bool = False

    # Model architecture
    model_dim: int = 512
    num_layers: int = 8
    num_heads: int = 8
    dropout: float = 0.1

    # Image generation
    image_size: int = 256
    channels: int = 3
    unet_dim_mults: Tuple[int, ...] = (1, 2, 4, 8)

    # Text generation
    vocab_size: int = 50432
    max_seq_len: int = 512
    text_dim: int = 768

    # Audio generation
    sample_rate: int = 16000
    audio_length: float = 5.0
    mel_channels: int = 128

    # Conditioning
    use_conditional: bool = True
    condition_dim: int = 512

    # Training
    learning_rate: float = 1e-4
    weight_decay: float = 1e-5
    ema_decay: float = 0.9999
    gradient_clip: float = 1.0


class NoiseScheduler:
    """Advanced noise scheduler for diffusion models"""
    def __init__(self, config: DiffusionConfig):
        self.config = config
        self.num_timesteps = config.num_timesteps

        # Create beta schedule
        if config.beta_schedule == "linear":
            betas = torch.linspace(config.beta_start, config.beta_end, config.num_timesteps)
        elif config.beta_schedule == "cosine":
            betas = self._cosine_beta_schedule(config.num_timesteps)
        elif config.beta_schedule == "scaled_linear":
            betas = torch.linspace(config.beta_start**0.5, config.beta_end**0.5, config.num_timesteps) ** 2
        else:
            raise ValueError(f"Unknown beta schedule: {config.beta_schedule}")

        self.betas = betas
        self.alphas = 1.0 - betas
        self.alphas_cumprod = torch.cumprod(self.alphas, axis=0)
        self.alphas_cumprod_prev = F.pad(self.alphas_cumprod[:-1], (1, 0), value=1.0)

        # Pre-compute useful values
        self.sqrt_alphas_cumprod = torch.sqrt(self.alphas_cumprod)
        self.sqrt_one_minus_alphas_cumprod = torch.sqrt(1.0 - self.alphas_cumprod)
        self.sqrt_recip_alphas = torch.sqrt(1.0 / self.alphas)

        # Pre-compute posterior variance
        self.posterior_variance = (
            self.betas * (1.0 - self.alphas_cumprod_prev) / (1.0 - self.alphas_cumprod)
        )

    def _cosine_beta_schedule(self, timesteps: int, s: float = 0.008):
        """Cosine beta schedule"""
        steps = timesteps + 1
        x = torch.linspace(0, timesteps, steps, dtype=torch.float64)
        alphas_cumprod = torch.cos(((x / timesteps) + s) / (1 + s) * math.pi * 0.5) ** 2
        alphas_cumprod = alphas_cumprod / alphas_cumprod[0]
        betas = 1 - (alphas_cumprod[1:] / alphas_cumprod[:-1])
        return torch.clip(betas, 0, 0.999)

    def add_noise(self, original: torch.Tensor, noise: torch.Tensor, timesteps: torch.Tensor) -> torch.Tensor:
        """Add noise to original data at specified timesteps"""
        sqrt_alphas_cumprod = self.sqrt_alphas_cumprod[timesteps].to(original.device)
        sqrt_one_minus_alphas_cumprod = self.sqrt_one_minus_alphas_cumprod[timesteps].to(original.device)

        # Reshape for broadcasting
        sqrt_alphas_cumprod = sqrt_alphas_cumprod.view(-1, *([1] * (original.dim() - 1)))
        sqrt_one_minus_alphas_cumprod = sqrt_one_minus_alphas_cumprod.view(-1, *([1] * (original.dim() - 1)))

        return sqrt_alphas_cumprod * original + sqrt_one_minus_alphas_cumprod * noise

    def sample_timestep(self, batch_size: int, device: torch.device) -> torch.Tensor:
        """Sample random timesteps"""
        return torch.randint(0, self.num_timesteps, (batch_size,), device=device)

    def get_variance(self, timestep: int) -> torch.Tensor:
        """Get variance for given timestep"""
        if timestep == 0:
            return torch.tensor(0.0)
        return self.posterior_variance[timestep]

    def step(self, model_output: torch.Tensor, timestep: int, sample: torch.Tensor) -> torch.Tensor:
        """Single denoising step"""
        t = torch.tensor([timestep], device=sample.device)

        # Compute coefficients
        beta_t = self.betas[t].to(sample.device)
        sqrt_one_minus_alpha_cumprod_t = self.sqrt_one_minus_alphas_cumprod[t].to(sample.device)
        sqrt_recip_alpha_t = self.sqrt_recip_alphas[t].to(sample.device)

        # Predict previous sample mean
        pred_prev_sample = sqrt_recip_alpha_t * (
            sample - beta_t / sqrt_one_minus_alpha_cumprod_t * model_output
        )

        if timestep > 0:
            variance = self.get_variance(timestep)
            noise = torch.randn_like(sample)
            pred_prev_sample = pred_prev_sample + (0.5 * variance) ** 0.5 * noise

        return pred_prev_sample


class SinusoidalPositionEmbeddings(nn.Module):
    """Sinusoidal positional embeddings for timesteps"""
    def __init__(self, dim: int):
        super().__init__()
        self.dim = dim

    def forward(self, time: torch.Tensor) -> torch.Tensor:
        device = time.device
        half_dim = self.dim // 2
        embeddings = math.log(10000) / (half_dim - 1)
        embeddings = torch.exp(torch.arange(half_dim, device=device) * -embeddings)
        embeddings = time[:, None] * embeddings[None, :]
        embeddings = torch.cat((embeddings.sin(), embeddings.cos()), dim=-1)
        return embeddings


class ResidualBlock(nn.Module):
    """Residual block with time and conditioning"""
    def __init__(self, dim: int, time_dim: int, condition_dim: Optional[int] = None, dropout: float = 0.1):
        super().__init__()
        self.norm1 = nn.GroupNorm(8, dim)
        self.conv1 = nn.Conv2d(dim, dim, 3, padding=1)
        self.norm2 = nn.GroupNorm(8, dim)
        self.conv2 = nn.Conv2d(dim, dim, 3, padding=1)

        # Time embedding
        self.time_mlp = nn.Sequential(
            SinusoidalPositionEmbeddings(time_dim),
            nn.Linear(time_dim, dim * 2),
            nn.GELU(),
            nn.Linear(dim * 2, dim)
        )

        # Conditioning
        if condition_dim is not None:
            self.condition_mlp = nn.Sequential(
                nn.Linear(condition_dim, dim * 2),
                nn.GELU(),
                nn.Linear(dim * 2, dim)
            )
        else:
            self.condition_mlp = None

        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, time_emb: torch.Tensor,
                condition: Optional[torch.Tensor] = None) -> torch.Tensor:
        # First convolution
        h = self.norm1(x)
        h = F.gelu(h)
        h = self.conv1(h)

        # Add time embedding
        time_emb = self.time_mlp(time_emb)
        h = h + time_emb[:, :, None, None]

        # Add conditioning if available
        if condition is not None and self.condition_mlp is not None:
            cond_emb = self.condition_mlp(condition)
            h = h + cond_emb[:, :, None, None]

        # Second convolution
        h = self.norm2(h)
        h = F.gelu(h)
        h = self.conv2(h)
        h = self.dropout(h)

        # Residual connection
        return x + h


class AttentionBlock(nn.Module):
    """Self-attention block for U-Net"""
    def __init__(self, dim: int, heads: int = 4, dim_head: int = 32, dropout: float = 0.1):
        super().__init__()
        self.heads = heads
        hidden_dim = dim_head * heads

        self.norm = nn.GroupNorm(8, dim)
        self.to_qkv = nn.Conv2d(dim, hidden_dim * 3, 1, bias=False)
        self.to_out = nn.Conv2d(hidden_dim, dim, 1)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, c, h, w = x.shape
        x = self.norm(x)

        # Compute Q, K, V
        qkv = self.to_qkv(x).chunk(3, dim=1)
        q, k, v = map(lambda t: rearrange(t, 'b (h d) x y -> b h (x y) d', h=self.heads), qkv)

        # Compute attention
        dots = torch.matmul(q, k.transpose(-1, -2)) * (q.shape[-1] ** -0.5)
        attn = F.softmax(dots, dim=-1)
        attn = self.dropout(attn)

        # Apply attention
        out = torch.matmul(attn, v)
        out = rearrange(out, 'b h (x y) d -> b (h d) x y', x=h, y=w)
        return self.to_out(out)


class UNet(nn.Module):
    """U-Net architecture for image diffusion"""
    def __init__(self, config: DiffusionConfig):
        super().__init__()
        self.config = config
        dim = config.model_dim
        dim_mults = config.unet_dim_mults
        channels = config.channels

        # Time embedding
        self.time_dim = dim * 4
        self.time_mlp = nn.Sequential(
            SinusoidalPositionEmbeddings(dim),
            nn.Linear(dim, self.time_dim),
            nn.GELU(),
            nn.Linear(self.time_dim, self.time_dim)
        )

        # Conditioning embedding
        if config.use_conditional:
            self.condition_proj = nn.Linear(config.condition_dim, self.time_dim)
        else:
            self.condition_proj = None

        # Initial projection
        self.init_conv = nn.Conv2d(channels, dim, 7, padding=3)

        # Downsampling
        self.downs = nn.ModuleList()
        for i, mult in enumerate(dim_mults):
            out_dim = dim * mult
            for _ in range(config.num_layers):
                self.downs.append(
                    ResidualBlock(out_dim, self.time_dim, self.time_dim if config.use_conditional else None)
                )
                self.downs.append(AttentionBlock(out_dim, config.num_heads))

            if i != len(dim_mults) - 1:
                self.downs.append(nn.Conv2d(out_dim, out_dim * 2, 4, 2, 1))

        # Middle
        self.mid_block1 = ResidualBlock(dim * dim_mults[-1], self.time_dim)
        self.mid_attn = AttentionBlock(dim * dim_mults[-1], config.num_heads)
        self.mid_block2 = ResidualBlock(dim * dim_mults[-1], self.time_dim)

        # Upsampling
        self.ups = nn.ModuleList()
        for i, mult in reversed(list(enumerate(dim_mults))):
            out_dim = dim * mult
            for _ in range(config.num_layers):
                self.ups.append(
                    ResidualBlock(out_dim * 2, self.time_dim)
                )
                self.ups.append(AttentionBlock(out_dim, config.num_heads))

            if i != 0:
                self.ups.append(nn.ConvTranspose2d(out_dim * 2, out_dim, 4, 2, 1))

        # Output
        self.final_conv = nn.Conv2d(dim, channels, 1)

    def forward(self, x: torch.Tensor, time: torch.Tensor,
                condition: Optional[torch.Tensor] = None) -> torch.Tensor:
        # Time embedding
        time_emb = self.time_mlp(time)

        # Add conditioning
        if condition is not None and self.condition_proj is not None:
            cond_emb = self.condition_proj(condition)
            time_emb = time_emb + cond_emb

        # Initial projection
        h = self.init_conv(x)

        # Downsampling
        skip_connections = []
        for layer in self.downs:
            if isinstance(layer, ResidualBlock):
                h = layer(h, time_emb)
            elif isinstance(layer, AttentionBlock):
                h = layer(h)
            else:  # Convolution
                skip_connections.append(h)
                h = layer(h)

        # Middle
        h = self.mid_block1(h, time_emb)
        h = self.mid_attn(h)
        h = self.mid_block2(h, time_emb)

        # Upsampling
        for layer in self.ups:
            if isinstance(layer, ResidualBlock):
                h = layer(h, time_emb)
            elif isinstance(layer, AttentionBlock):
                h = layer(h)
            else:  # Transposed convolution
                h = torch.cat((h, skip_connections.pop()), dim=1)
                h = layer(h)

        # Output
        return self.final_conv(h)


class TextDiffusionModel(nn.Module):
    """Diffusion model for text generation"""
    def __init__(self, config: DiffusionConfig):
        super().__init__()
        self.config = config

        # Token embedding
        self.token_embedding = nn.Embedding(config.vocab_size, config.text_dim)

        # Positional embedding
        self.pos_embedding = nn.Embedding(config.max_seq_len, config.text_dim)

        # Time embedding
        self.time_dim = config.text_dim * 4
        self.time_mlp = nn.Sequential(
            SinusoidalPositionEmbeddings(config.text_dim),
            nn.Linear(config.text_dim, self.time_dim),
            nn.GELU(),
            nn.Linear(self.time_dim, self.time_dim)
        )

        # Transformer layers
        self.transformer_layers = nn.ModuleList([
            nn.TransformerEncoderLayer(
                d_model=config.text_dim,
                nhead=config.num_heads,
                dim_feedforward=config.text_dim * 4,
                dropout=config.dropout,
                activation='gelu',
                batch_first=True
            )
            for _ in range(config.num_layers)
        ])

        # Output projection
        self.output_proj = nn.Linear(config.text_dim, config.vocab_size)

    def forward(self, x: torch.Tensor, time: torch.Tensor) -> torch.Tensor:
        batch_size, seq_len = x.shape
        device = x.device

        # Embeddings
        token_emb = self.token_embedding(x)
        pos_emb = self.pos_embedding(torch.arange(seq_len, device=device))
        h = token_emb + pos_emb

        # Time embedding
        time_emb = self.time_mlp(time)
        h = h + time_emb.unsqueeze(1)

        # Transformer layers
        for layer in self.transformer_layers:
            h = layer(h)

        # Output
        return self.output_proj(h)


class AudioDiffusionModel(nn.Module):
    """Diffusion model for audio generation"""
    def __init__(self, config: DiffusionConfig):
        super().__init__()
        self.config = config

        # Compute mel spectrogram dimensions
        self.n_mels = config.mel_channels
        self.hop_length = 256
        self.audio_length = int(config.sample_rate * config.audio_length)
        self.spec_length = self.audio_length // self.hop_length

        # Initial projection
        self.init_conv = nn.Conv2d(1, config.model_dim, 3, padding=1)

        # Time embedding
        self.time_dim = config.model_dim * 4
        self.time_mlp = nn.Sequential(
            SinusoidalPositionEmbeddings(config.model_dim),
            nn.Linear(config.model_dim, self.time_dim),
            nn.GELU(),
            nn.Linear(self.time_dim, self.time_dim)
        )

        # Residual blocks
        self.blocks = nn.ModuleList([
            ResidualBlock(config.model_dim, self.time_dim, dropout=config.dropout)
            for _ in range(config.num_layers)
        ])

        # Output projection
        self.final_conv = nn.Conv2d(config.model_dim, 1, 3, padding=1)

    def forward(self, x: torch.Tensor, time: torch.Tensor) -> torch.Tensor:
        # Initial projection
        h = self.init_conv(x)

        # Time embedding
        time_emb = self.time_mlp(time)

        # Residual blocks
        for block in self.blocks:
            h = block(h, time_emb)

        # Output
        return self.final_conv(h)


class MultimodalDiffusion(nn.Module):
    """Multimodal diffusion model combining text, image, and audio"""
    def __init__(self, config: DiffusionConfig):
        super().__init__()
        self.config = config

        # Individual diffusion models
        self.image_diffusion = UNet(config)
        self.text_diffusion = TextDiffusionModel(config)
        self.audio_diffusion = AudioDiffusionModel(config)

        # Cross-modal attention
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=config.model_dim,
            num_heads=config.num_heads,
            dropout=config.dropout,
            batch_first=True
        )

        # Fusion layers
        self.fusion_layers = nn.ModuleList([
            nn.TransformerEncoderLayer(
                d_model=config.model_dim,
                nhead=config.num_heads,
                dim_feedforward=config.model_dim * 4,
                dropout=config.dropout,
                activation='gelu',
                batch_first=True
            )
            for _ in range(3)
        ])

        # Modality projections
        self.image_proj = nn.Linear(config.model_dim, config.model_dim)
        self.text_proj = nn.Linear(config.text_dim, config.model_dim)
        self.audio_proj = nn.Linear(config.model_dim, config.model_dim)

    def forward(self, image: Optional[torch.Tensor] = None,
                text: Optional[torch.Tensor] = None,
                audio: Optional[torch.Tensor] = None,
                time: torch.Tensor = None) -> Dict[str, torch.Tensor]:

        outputs = {}
        modalities = []

        # Process each modality
        if image is not None:
            img_output = self.image_diffusion(image, time)
            outputs['image'] = img_output
            # Flatten and project
            img_flat = img_output.view(img_output.size(0), -1, img_output.size(1))
            img_proj = self.image_proj(img_flat)
            modalities.append(img_proj)

        if text is not None:
            text_output = self.text_diffusion(text, time)
            outputs['text'] = text_output
            text_proj = self.text_proj(text_output)
            modalities.append(text_proj)

        if audio is not None:
            audio_output = self.audio_diffusion(audio, time)
            outputs['audio'] = audio_output
            # Flatten and project
            audio_flat = audio_output.view(audio_output.size(0), -1, audio_output.size(1))
            audio_proj = self.audio_proj(audio_flat)
            modalities.append(audio_proj)

        # Cross-modal fusion if multiple modalities
        if len(modalities) > 1:
            # Stack modalities
            stacked = torch.stack(modalities, dim=1)  # [batch, modalities, seq, dim]

            # Apply fusion layers
            fused = stacked
            for layer in self.fusion_layers:
                fused = layer(fused)

            outputs['fused'] = fused

        return outputs


class DiffusionTrainer:
    """Trainer for diffusion models"""
    def __init__(self, model: nn.Module, scheduler: NoiseScheduler, config: DiffusionConfig):
        self.model = model
        self.scheduler = scheduler
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.model.to(self.device)

        # Optimizer
        self.optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay
        )

        # EMA model
        self.ema_model = self._create_ema_model(model)
        self.ema_decay = config.ema_decay

        # Loss function
        self.loss_fn = nn.MSELoss()

    def _create_ema_model(self, model: nn.Module) -> nn.Module:
        """Create EMA copy of model"""
        import copy
        ema_model = copy.deepcopy(model)
        for param in ema_model.parameters():
            param.requires_grad_(False)
        return ema_model

    def update_ema(self):
        """Update EMA model parameters"""
        with torch.no_grad():
            for ema_param, param in zip(self.ema_model.parameters(), self.model.parameters()):
                ema_param.data.mul_(self.ema_decay).add_(param.data, alpha=1 - self.ema_decay)

    def train_step(self, batch: Dict[str, torch.Tensor]) -> float:
        """Single training step"""
        self.model.train()
        self.optimizer.zero_grad()

        # Sample timesteps
        timesteps = self.scheduler.sample_timestep(batch['image'].size(0), self.device)

        # Add noise
        if 'image' in batch:
            noise = torch.randn_like(batch['image'])
            noisy_images = self.scheduler.add_noise(batch['image'], noise, timesteps)

            # Predict noise
            if 'condition' in batch:
                predicted_noise = self.model(noisy_images, timesteps, batch['condition'])
            else:
                predicted_noise = self.model(noisy_images, timesteps)

            # Compute loss
            loss = self.loss_fn(predicted_noise, noise)
        else:
            # Handle other modalities
            loss = 0.0

        # Backward pass
        loss.backward()

        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.gradient_clip)

        self.optimizer.step()
        self.update_ema()

        return loss.item()

    @torch.no_grad()
    def sample(self, shape: Tuple[int, ...], condition: Optional[torch.Tensor] = None,
               num_inference_steps: int = 50) -> torch.Tensor:
        """Generate samples from diffusion model"""
        self.ema_model.eval()

        # Start with random noise
        sample = torch.randn(shape, device=self.device)

        # Sampling timesteps
        timesteps = torch.linspace(self.config.num_timesteps - 1, 0, num_inference_steps, dtype=torch.long, device=self.device)

        for t in tqdm(timesteps, desc="Sampling"):
            # Predict noise
            if condition is not None:
                predicted_noise = self.ema_model(sample, t.unsqueeze(0), condition)
            else:
                predicted_noise = self.ema_model(sample, t.unsqueeze(0))

            # Compute previous sample
            sample = self.scheduler.step(predicted_noise, t.item(), sample)

        return sample


# Utility functions
def create_diffusion_config(model_size: str = "base") -> DiffusionConfig:
    """Create diffusion configuration"""
    if model_size == "base":
        return DiffusionConfig(
            model_dim=256,
            num_layers=6,
            num_heads=8,
            image_size=256,
            num_timesteps=1000
        )
    elif model_size == "large":
        return DiffusionConfig(
            model_dim=512,
            num_layers=8,
            num_heads=16,
            image_size=512,
            num_timesteps=1000
        )
    else:
        return DiffusionConfig()


def generate_image(model: nn.Module, scheduler: NoiseScheduler, prompt: Optional[str] = None,
                  num_inference_steps: int = 50, guidance_scale: float = 7.5) -> Image.Image:
    """Generate image from text prompt using classifier-free guidance"""
    device = next(model.parameters()).device

    # Create random noise
    shape = (1, 3, 256, 256)
    sample = torch.randn(shape, device=device)

    # Sampling timesteps
    timesteps = torch.linspace(scheduler.num_timesteps - 1, 0, num_inference_steps, dtype=torch.long, device=device)

    for t in tqdm(timesteps, desc="Generating image"):
        # Classifier-free guidance
        with torch.no_grad():
            # Unconditional prediction
            unconditional_pred = model(sample, t.unsqueeze(0), None)

            # Conditional prediction (if prompt provided)
            if prompt is not None:
                # Convert prompt to conditioning (placeholder)
                condition = torch.randn(1, 512, device=device)  # Replace with actual text encoding
                conditional_pred = model(sample, t.unsqueeze(0), condition)

                # Apply guidance
                predicted_noise = unconditional_pred + guidance_scale * (conditional_pred - unconditional_pred)
            else:
                predicted_noise = unconditional_pred

            # Compute previous sample
            sample = scheduler.step(predicted_noise, t.item(), sample)

    # Convert to image
    sample = sample.clamp(-1, 1)
    sample = (sample + 1) / 2
    sample = sample.permute(0, 2, 3, 1).cpu().numpy()
    sample = (sample * 255).astype(np.uint8)

    return Image.fromarray(sample[0])


def save_sample_images(samples: torch.Tensor, save_path: str, nrow: int = 4):
    """Save generated samples as a grid"""
    from torchvision.utils import save_image

    # Normalize samples
    samples = (samples + 1) / 2
    samples = samples.clamp(0, 1)

    # Save grid
    save_image(samples, save_path, nrow=nrow)


if __name__ == "__main__":
    print("Creating advanced diffusion models...")

    # Create configuration and models
    config = create_diffusion_config("base")
    scheduler = NoiseScheduler(config)
    model = UNet(config)
    multimodal_model = MultimodalDiffusion(config)

    print(f"U-Net parameters: {sum(p.numel() for p in model.parameters()):,}")
    print(f"Multimodal diffusion parameters: {sum(p.numel() for p in multimodal_model.parameters()):,}")

    # Create trainer
    trainer = DiffusionTrainer(model, scheduler, config)

    # Test forward pass
    batch_size = 4
    image = torch.randn(batch_size, 3, 256, 256)
    condition = torch.randn(batch_size, 512)
    timesteps = scheduler.sample_timestep(batch_size, "cpu")

    print("\nTesting diffusion models...")
    with torch.no_grad():
        # Test image diffusion
        noise_pred = model(image, timesteps, condition)
        print(f"Image noise prediction shape: {noise_pred.shape}")

        # Test multimodal diffusion
        text = torch.randint(0, 1000, (batch_size, 128))
        audio = torch.randn(batch_size, 1, 128, 128)

        multimodal_outputs = multimodal_model(
            image=image,
            text=text,
            audio=audio,
            time=timesteps
        )

        print(f"Multimodal outputs: {list(multimodal_outputs.keys())}")

    # Test sampling
    print("\nTesting image generation...")
    with torch.no_grad():
        generated = trainer.sample((1, 3, 256, 256), num_inference_steps=10)
        print(f"Generated image shape: {generated.shape}")

    print("\nDiffusion models initialized successfully!")