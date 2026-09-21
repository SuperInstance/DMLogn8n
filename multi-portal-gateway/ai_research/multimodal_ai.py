"""
Multimodal AI System for DMLogn8n
Advanced vision, language, and audio integration models
Based on latest research in multimodal learning and cross-modal understanding
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from einops import rearrange, repeat, einsum
from transformers import CLIPVisionModel, CLIPTextModel, Wav2Vec2Model
import torchvision.models as models
from PIL import Image
import librosa
import torchaudio
from scipy import signal


@dataclass
class MultimodalConfig:
    """Configuration for multimodal AI models"""
    # Vision config
    vision_encoder: str = "clip"  # clip, vit, resnet
    image_size: int = 224
    vision_dim: int = 768
    vision_layers: int = 12
    vision_heads: int = 12

    # Language config
    text_encoder: str = "clip"  # clip, bert, gpt
    vocab_size: int = 50432
    text_dim: int = 768
    text_layers: int = 12
    text_heads: int = 12
    max_seq_len: int = 512

    # Audio config
    audio_encoder: str = "wav2vec"  # wav2vec, spectrogram
    audio_dim: int = 768
    audio_layers: int = 12
    sample_rate: int = 16000
    max_audio_length: float = 30.0  # seconds

    # Fusion config
    fusion_dim: int = 1024
    fusion_method: str = "cross_attention"  # concat, cross_attention, transformer
    num_fusion_layers: int = 4

    # Training config
    temperature: float = 0.07
    dropout: float = 0.1
    use_contrastive_learning: bool = True
    use_mlm: bool = True
    use_image_captioning: bool = True
    use_audio_classification: bool = True


class VisionEncoder(nn.Module):
    """Advanced vision encoder with multiple architecture options"""
    def __init__(self, config: MultimodalConfig):
        super().__init__()
        self.config = config

        if config.vision_encoder == "clip":
            self.encoder = CLIPVisionModel.from_pretrained("openai/clip-vit-base-patch32")
            self.dim = self.encoder.config.hidden_size
        elif config.vision_encoder == "vit":
            from transformers import ViTModel
            self.encoder = ViTModel.from_pretrained("google/vit-base-patch16-224")
            self.dim = self.encoder.config.hidden_size
        elif config.vision_encoder == "resnet":
            self.encoder = models.resnet50(pretrained=True)
            self.encoder.fc = nn.Identity()
            self.dim = 2048
        else:
            raise ValueError(f"Unknown vision encoder: {config.vision_encoder}")

        # Projection to common dimension
        self.projection = nn.Linear(self.dim, config.vision_dim)

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        if self.config.vision_encoder in ["clip", "vit"]:
            outputs = self.encoder(pixel_values=images)
            features = outputs.pooler_output
        else:  # ResNet
            features = self.encoder(images)

        return self.projection(features)


class TextEncoder(nn.Module):
    """Advanced text encoder with multiple architecture options"""
    def __init__(self, config: MultimodalConfig):
        super().__init__()
        self.config = config

        if config.text_encoder == "clip":
            self.encoder = CLIPTextModel.from_pretrained("openai/clip-vit-base-patch32")
            self.dim = self.encoder.config.hidden_size
        elif config.text_encoder == "bert":
            from transformers import BertModel
            self.encoder = BertModel.from_pretrained("bert-base-uncased")
            self.dim = self.encoder.config.hidden_size
        else:
            raise ValueError(f"Unknown text encoder: {config.text_encoder}")

        # Projection to common dimension
        self.projection = nn.Linear(self.dim, config.text_dim)

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        features = outputs.pooler_output
        return self.projection(features)


class AudioEncoder(nn.Module):
    """Advanced audio encoder with multiple architecture options"""
    def __init__(self, config: MultimodalConfig):
        super().__init__()
        self.config = config
        self.sample_rate = config.sample_rate

        if config.audio_encoder == "wav2vec":
            from transformers import Wav2Vec2Model
            self.encoder = Wav2Vec2Model.from_pretrained("facebook/wav2vec2-base")
            self.dim = self.encoder.config.hidden_size
        elif config.audio_encoder == "spectrogram":
            self.encoder = AudioSpectrogramEncoder(config)
            self.dim = 512
        else:
            raise ValueError(f"Unknown audio encoder: {config.audio_encoder}")

        # Projection to common dimension
        self.projection = nn.Linear(self.dim, config.audio_dim)

    def forward(self, audio: torch.Tensor) -> torch.Tensor:
        if self.config.audio_encoder == "wav2vec":
            outputs = self.encoder(audio)
            features = outputs.last_hidden_state.mean(dim=1)  # Average pooling
        else:
            features = self.encoder(audio)

        return self.projection(features)


class AudioSpectrogramEncoder(nn.Module):
    """Custom spectrogram-based audio encoder"""
    def __init__(self, config: MultimodalConfig):
        super().__init__()
        self.config = config

        # Spectrogram transformation
        self.mel_spectrogram = torchaudio.transforms.MelSpectrogram(
            sample_rate=config.sample_rate,
            n_fft=1024,
            hop_length=512,
            n_mels=128
        )

        # CNN backbone for spectrogram
        self.conv_layers = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1))
        )

        self.dim = 256

    def forward(self, audio: torch.Tensor) -> torch.Tensor:
        # Convert to spectrogram
        spectrogram = self.mel_spectrogram(audio)
        spectrogram = spectrogram.unsqueeze(1)  # Add channel dimension

        # Process through CNN
        features = self.conv_layers(spectrogram)
        features = features.view(features.size(0), -1)  # Flatten

        return features


class CrossModalAttention(nn.Module):
    """Cross-modal attention mechanism for multimodal fusion"""
    def __init__(self, dim: int, num_heads: int = 8):
        super().__init__()
        self.dim = dim
        self.num_heads = num_heads
        self.head_dim = dim // num_heads

        self.query = nn.Linear(dim, dim)
        self.key = nn.Linear(dim, dim)
        self.value = nn.Linear(dim, dim)

        self.output = nn.Linear(dim, dim)
        self.dropout = nn.Dropout(0.1)

    def forward(self, query: torch.Tensor, key: torch.Tensor, value: torch.Tensor,
                attention_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        batch_size = query.size(0)

        # Project to Q, K, V
        q = self.query(query).view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.key(key).view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        v = self.value(value).view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)

        # Compute attention
        scores = torch.matmul(q, k.transpose(-2, -1)) / (self.head_dim ** 0.5)

        if attention_mask is not None:
            scores = scores.masked_fill(attention_mask == 0, float('-inf'))

        attention_weights = F.softmax(scores, dim=-1)
        attention_weights = self.dropout(attention_weights)

        # Apply attention
        attended = torch.matmul(attention_weights, v)
        attended = attended.transpose(1, 2).contiguous().view(batch_size, -1, self.dim)

        return self.output(attended)


class MultimodalFusion(nn.Module):
    """Advanced multimodal fusion with multiple strategies"""
    def __init__(self, config: MultimodalConfig):
        super().__init__()
        self.config = config
        self.fusion_method = config.fusion_method

        if config.fusion_method == "concat":
            total_dim = config.vision_dim + config.text_dim + config.audio_dim
            self.fusion = nn.Sequential(
                nn.Linear(total_dim, config.fusion_dim),
                nn.ReLU(),
                nn.Dropout(config.dropout),
                nn.Linear(config.fusion_dim, config.fusion_dim)
            )

        elif config.fusion_method == "cross_attention":
            self.vision_attention = CrossModalAttention(config.vision_dim)
            self.text_attention = CrossModalAttention(config.text_dim)
            self.audio_attention = CrossModalAttention(config.audio_dim)

            self.fusion = nn.Sequential(
                nn.Linear(config.vision_dim + config.text_dim + config.audio_dim, config.fusion_dim),
                nn.ReLU(),
                nn.Dropout(config.dropout),
                nn.Linear(config.fusion_dim, config.fusion_dim)
            )

        elif config.fusion_method == "transformer":
            self.fusion_transformer = nn.TransformerEncoder(
                nn.TransformerEncoderLayer(
                    d_model=config.fusion_dim,
                    nhead=8,
                    dim_feedforward=config.fusion_dim * 4,
                    dropout=config.dropout,
                    activation='gelu'
                ),
                num_layers=config.num_fusion_layers
            )

            # Project modalities to fusion dimension
            self.vision_proj = nn.Linear(config.vision_dim, config.fusion_dim)
            self.text_proj = nn.Linear(config.text_dim, config.fusion_dim)
            self.audio_proj = nn.Linear(config.audio_dim, config.fusion_dim)

    def forward(self, vision_features: torch.Tensor,
                text_features: torch.Tensor,
                audio_features: torch.Tensor) -> torch.Tensor:

        if self.fusion_method == "concat":
            # Simple concatenation
            fused = torch.cat([vision_features, text_features, audio_features], dim=-1)
            return self.fusion(fused)

        elif self.fusion_method == "cross_attention":
            # Cross-modal attention
            attended_vision = self.vision_attention(vision_features, text_features, audio_features)
            attended_text = self.text_attention(text_features, vision_features, audio_features)
            attended_audio = self.audio_attention(audio_features, vision_features, text_features)

            fused = torch.cat([attended_vision, attended_text, attended_audio], dim=-1)
            return self.fusion(fused)

        elif self.fusion_method == "transformer":
            # Project to common dimension
            vision_proj = self.vision_proj(vision_features).unsqueeze(1)
            text_proj = self.text_proj(text_features).unsqueeze(1)
            audio_proj = self.audio_proj(audio_features).unsqueeze(1)

            # Stack modalities
            modalities = torch.cat([vision_proj, text_proj, audio_proj], dim=1)
            modalities = modalities.transpose(0, 1)  # (seq_len, batch, dim)

            # Apply transformer fusion
            fused = self.fusion_transformer(modalities)
            fused = fused.mean(dim=0)  # Average over modalities

            return fused


class ContrastiveLearning(nn.Module):
    """Contrastive learning for multimodal alignment"""
    def __init__(self, dim: int, temperature: float = 0.07):
        super().__init__()
        self.temperature = temperature

    def forward(self, features1: torch.Tensor, features2: torch.Tensor) -> torch.Tensor:
        """Compute contrastive loss between two feature sets"""
        # Normalize features
        features1 = F.normalize(features1, dim=-1)
        features2 = F.normalize(features2, dim=-1)

        # Compute similarity matrix
        similarity = torch.matmul(features1, features2.T) / self.temperature

        # Labels are diagonal (positive pairs)
        labels = torch.arange(features1.size(0), device=features1.device)

        # Compute symmetric loss
        loss_fct = nn.CrossEntropyLoss()
        loss1 = loss_fct(similarity, labels)
        loss2 = loss_fct(similarity.T, labels)

        return (loss1 + loss2) / 2


class MultimodalAI(nn.Module):
    """Complete multimodal AI system for DMLogn8n"""
    def __init__(self, config: MultimodalConfig):
        super().__init__()
        self.config = config

        # Encoders for each modality
        self.vision_encoder = VisionEncoder(config)
        self.text_encoder = TextEncoder(config)
        self.audio_encoder = AudioEncoder(config)

        # Fusion module
        self.fusion = MultimodalFusion(config)

        # Contrastive learning
        if config.use_contrastive_learning:
            self.contrastive_vt = ContrastiveLearning(config.vision_dim, config.temperature)
            self.contrastive_va = ContrastiveLearning(config.vision_dim, config.temperature)
            self.contrastive_ta = ContrastiveLearning(config.text_dim, config.temperature)

        # Task-specific heads
        self.classification_head = nn.Sequential(
            nn.Linear(config.fusion_dim, config.fusion_dim // 2),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.fusion_dim // 2, 10)  # Number of classes
        )

        self.regression_head = nn.Sequential(
            nn.Linear(config.fusion_dim, config.fusion_dim // 2),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.fusion_dim // 2, 1)
        )

        # Gaming-specific outputs
        self.emotion_head = nn.Sequential(
            nn.Linear(config.fusion_dim, config.fusion_dim // 2),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.fusion_dim // 2, 8)  # Basic emotions
        )

        self.action_head = nn.Sequential(
            nn.Linear(config.fusion_dim, config.fusion_dim // 2),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.fusion_dim // 2, 100)  # Possible actions
        )

    def encode_vision(self, images: torch.Tensor) -> torch.Tensor:
        """Encode visual input"""
        return self.vision_encoder(images)

    def encode_text(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        """Encode textual input"""
        return self.text_encoder(input_ids, attention_mask)

    def encode_audio(self, audio: torch.Tensor) -> torch.Tensor:
        """Encode audio input"""
        return self.audio_encoder(audio)

    def forward(self,
                images: Optional[torch.Tensor] = None,
                input_ids: Optional[torch.Tensor] = None,
                attention_mask: Optional[torch.Tensor] = None,
                audio: Optional[torch.Tensor] = None,
                task: str = "fusion") -> Dict[str, torch.Tensor]:

        # Encode available modalities
        vision_features = None
        text_features = None
        audio_features = None

        if images is not None:
            vision_features = self.encode_vision(images)

        if input_ids is not None and attention_mask is not None:
            text_features = self.encode_text(input_ids, attention_mask)

        if audio is not None:
            audio_features = self.encode_audio(audio)

        # Compute contrastive losses if all modalities are present
        contrastive_loss = 0
        if self.config.use_contrastive_learning:
            if vision_features is not None and text_features is not None:
                contrastive_loss += self.contrastive_vt(vision_features, text_features)
            if vision_features is not None and audio_features is not None:
                contrastive_loss += self.contrastive_va(vision_features, audio_features)
            if text_features is not None and audio_features is not None:
                contrastive_loss += self.contrastive_ta(text_features, audio_features)

        # Fuse modalities
        available_features = [f for f in [vision_features, text_features, audio_features] if f is not None]
        if len(available_features) == 0:
            raise ValueError("At least one modality must be provided")

        # If only one modality, use it directly
        if len(available_features) == 1:
            fused_features = available_features[0]
        else:
            # Pad missing modalities with zeros
            if vision_features is None:
                vision_features = torch.zeros_like(available_features[0])
            if text_features is None:
                text_features = torch.zeros_like(available_features[0])
            if audio_features is None:
                audio_features = torch.zeros_like(available_features[0])

            fused_features = self.fusion(vision_features, text_features, audio_features)

        outputs = {
            "fused_features": fused_features,
            "vision_features": vision_features,
            "text_features": text_features,
            "audio_features": audio_features,
            "contrastive_loss": contrastive_loss
        }

        # Task-specific outputs
        if task == "classification":
            outputs["classification_logits"] = self.classification_head(fused_features)
        elif task == "regression":
            outputs["regression_output"] = self.regression_head(fused_features)
        elif task == "gaming":
            outputs["emotion_logits"] = self.emotion_head(fused_features)
            outputs["action_logits"] = self.action_head(fused_features)
        elif task == "fusion":
            outputs["classification_logits"] = self.classification_head(fused_features)
            outputs["emotion_logits"] = self.emotion_head(fused_features)
            outputs["action_logits"] = self.action_head(fused_features)

        return outputs


class GamingMultimodalAI(MultimodalAI):
    """Specialized multimodal AI for gaming applications"""
    def __init__(self, config: MultimodalConfig):
        super().__init__(config)

        # Gaming-specific encoders
        self.game_state_encoder = nn.Sequential(
            nn.Linear(100, 256),  # Game state representation
            nn.ReLU(),
            nn.Linear(256, config.fusion_dim)
        )

        self.character_embedding = nn.Embedding(1000, config.fusion_dim)

        # Enhanced gaming outputs
        self.dialogue_generator = nn.Sequential(
            nn.Linear(config.fusion_dim, config.fusion_dim),
            nn.ReLU(),
            nn.Linear(config.fusion_dim, config.vocab_size)
        )

        self.narrative_coherence = nn.Sequential(
            nn.Linear(config.fusion_dim, config.fusion_dim // 2),
            nn.ReLU(),
            nn.Linear(config.fusion_dim // 2, 1),
            nn.Sigmoid()
        )

        self.player_engagement = nn.Sequential(
            nn.Linear(config.fusion_dim, config.fusion_dim // 2),
            nn.ReLU(),
            nn.Linear(config.fusion_dim // 2, 1),
            nn.Sigmoid()
        )

    def forward(self,
                images: Optional[torch.Tensor] = None,
                input_ids: Optional[torch.Tensor] = None,
                attention_mask: Optional[torch.Tensor] = None,
                audio: Optional[torch.Tensor] = None,
                game_states: Optional[torch.Tensor] = None,
                character_ids: Optional[torch.Tensor] = None,
                task: str = "gaming") -> Dict[str, torch.Tensor]:

        # Standard multimodal processing
        outputs = super().forward(images, input_ids, attention_mask, audio, task)
        fused_features = outputs["fused_features"]

        # Add gaming-specific information
        if game_states is not None:
            game_features = self.game_state_encoder(game_states)
            fused_features = fused_features + game_features

        if character_ids is not None:
            char_features = self.character_embedding(character_ids)
            fused_features = fused_features + char_features

        # Gaming-specific outputs
        outputs["dialogue_logits"] = self.dialogue_generator(fused_features)
        outputs["narrative_coherence"] = self.narrative_coherence(fused_features)
        outputs["player_engagement"] = self.player_engagement(fused_features)

        return outputs


# Utility functions
def load_image(image_path: str, size: int = 224) -> torch.Tensor:
    """Load and preprocess image"""
    from torchvision import transforms
    image = Image.open(image_path).convert('RGB')
    transform = transforms.Compose([
        transforms.Resize((size, size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    return transform(image).unsqueeze(0)


def load_audio(audio_path: str, sample_rate: int = 16000, max_length: float = 30.0) -> torch.Tensor:
    """Load and preprocess audio"""
    waveform, sr = torchaudio.load(audio_path)

    # Resample if necessary
    if sr != sample_rate:
        resampler = torchaudio.transforms.Resample(sr, sample_rate)
        waveform = resampler(waveform)

    # Trim or pad to max length
    max_samples = int(sample_rate * max_length)
    if waveform.size(1) > max_samples:
        waveform = waveform[:, :max_samples]
    elif waveform.size(1) < max_samples:
        padding = max_samples - waveform.size(1)
        waveform = F.pad(waveform, (0, padding))

    return waveform


def create_multimodal_config(model_size: str = "base") -> MultimodalConfig:
    """Create multimodal configuration"""
    if model_size == "base":
        return MultimodalConfig(
            vision_dim=768,
            text_dim=768,
            audio_dim=768,
            fusion_dim=1024,
            fusion_method="cross_attention"
        )
    elif model_size == "large":
        return MultimodalConfig(
            vision_dim=1024,
            text_dim=1024,
            audio_dim=1024,
            fusion_dim=1536,
            fusion_method="transformer",
            num_fusion_layers=6
        )
    else:
        return MultimodalConfig()


if __name__ == "__main__":
    print("Creating multimodal AI system...")

    # Create configuration and model
    config = create_multimodal_config("base")
    model = GamingMultimodalAI(config)

    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    # Example usage
    batch_size = 2

    # Dummy inputs
    images = torch.randn(batch_size, 3, 224, 224)
    input_ids = torch.randint(0, 1000, (batch_size, 128))
    attention_mask = torch.ones(batch_size, 128)
    audio = torch.randn(batch_size, 1, 16000)  # 1 second of audio
    game_states = torch.randn(batch_size, 100)
    character_ids = torch.randint(0, 1000, (batch_size,))

    print("\nTesting multimodal forward pass...")
    with torch.no_grad():
        outputs = model(
            images=images,
            input_ids=input_ids,
            attention_mask=attention_mask,
            audio=audio,
            game_states=game_states,
            character_ids=character_ids,
            task="gaming"
        )

        print(f"Fused features shape: {outputs['fused_features'].shape}")
        print(f"Emotion logits shape: {outputs['emotion_logits'].shape}")
        print(f"Action logits shape: {outputs['action_logits'].shape}")
        print(f"Dialogue logits shape: {outputs['dialogue_logits'].shape}")
        print(f"Narrative coherence shape: {outputs['narrative_coherence'].shape}")

    print("\nMultimodal AI system initialized successfully!")