"""
AI model configuration schemas for DMLogn8n multi-agent platform.
"""

from typing import Dict, List, Optional, Union, Any, Literal
from pydantic import BaseModel, Field, validator, RootModel
from enum import Enum
import secrets


class ModelProvider(str, Enum):
    """Supported AI model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"
    AZURE_OPENAI = "azure_openai"
    GOOGLE_AI = "google_ai"
    COHERE = "cohere"
    MISTRAL = "mistral"
    CUSTOM = "custom"


class ModelType(str, Enum):
    """Types of AI models."""
    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"
    AUDIO_TRANSCRIPTION = "audio_transcription"
    AUDIO_GENERATION = "audio_generation"
    CLASSIFICATION = "classification"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"


class ModelCapability(str, Enum):
    """Model capabilities."""
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    REASONING = "reasoning"
    MULTIMODAL = "multimodal"
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"
    VISION = "vision"
    AUDIO = "audio"
    TOOL_USE = "tool_use"


class ModelCredentials(BaseModel):
    """Model provider credentials."""
    api_key: Optional[str] = Field(default=None, description="API key for the model provider")
    api_base: Optional[str] = Field(default=None, description="API base URL")
    organization_id: Optional[str] = Field(default=None, description="Organization ID")
    project_id: Optional[str] = Field(default=None, description="Project ID")
    region: Optional[str] = Field(default=None, description="Provider region")
    additional_headers: Dict[str, str] = Field(default_factory=dict, description="Additional headers")
    auth_token: Optional[str] = Field(default=None, description="Authentication token")
    client_id: Optional[str] = Field(default=None, description="Client ID")
    client_secret: Optional[str] = Field(default=None, description="Client secret")

    @validator('api_key')
    def validate_api_key(cls, v):
        """Validate API key format."""
        if v and len(v) < 10:
            raise ValueError("API key must be at least 10 characters long")
        return v


class ModelParameters(BaseModel):
    """Model generation parameters."""
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(default=None, ge=1, description="Maximum tokens to generate")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    top_k: Optional[int] = Field(default=None, ge=1, description="Top-k sampling parameter")
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Presence penalty")
    stop_sequences: List[str] = Field(default_factory=list, description="Stop sequences")
    seed: Optional[int] = Field(default=None, ge=0, description="Random seed")
    logprobs: Optional[int] = Field(default=None, ge=0, description="Number of log probabilities to return")
    echo: bool = Field(default=False, description="Echo the prompt in the response")
    stream: bool = Field(default=False, description="Enable streaming response")
    tools: List[Dict[str, Any]] = Field(default_factory=list, description="Available tools")
    tool_choice: Optional[Union[str, Dict[str, Any]]] = Field(default=None, description="Tool choice strategy")

    # Vision-specific parameters
    image_quality: Optional[str] = Field(default="standard", description="Image quality for vision models")
    image_size: Optional[str] = Field(default="1024x1024", description="Image size for generation models")

    # Audio-specific parameters
    audio_format: Optional[str] = Field(default="mp3", description="Audio format")
    audio_language: Optional[str] = Field(default="en", description="Audio language code")


class RateLimiting(BaseModel):
    """Rate limiting configuration for models."""
    requests_per_minute: Optional[int] = Field(default=None, ge=1, description="Requests per minute limit")
    requests_per_hour: Optional[int] = Field(default=None, ge=1, description="Requests per hour limit")
    requests_per_day: Optional[int] = Field(default=None, ge=1, description="Requests per day limit")
    tokens_per_minute: Optional[int] = Field(default=None, ge=1, description="Tokens per minute limit")
    concurrent_requests: int = Field(default=5, ge=1, description="Maximum concurrent requests")
    retry_after_quota: bool = Field(default=True, description="Retry after quota exceeded")

    @validator('requests_per_minute', 'requests_per_hour', 'requests_per_day')
    def validate_rate_limits(cls, v, field):
        """Validate rate limit values."""
        if v is not None and v <= 0:
            raise ValueError(f"{field.name} must be greater than 0")
        return v


class CachingConfig(BaseModel):
    """Model response caching configuration."""
    enabled: bool = Field(default=True, description="Enable response caching")
    ttl_seconds: int = Field(default=3600, ge=1, description="Cache TTL in seconds")
    max_cache_size: int = Field(default=1000, ge=1, description="Maximum cache size in entries")
    cache_key_prefix: str = Field(default="model_cache", description="Cache key prefix")
    cache_similar_inputs: bool = Field(default=False, description="Cache semantically similar inputs")
    similarity_threshold: float = Field(default=0.95, ge=0.0, le=1.0, description="Similarity threshold for caching")


class ModelConfig(BaseModel):
    """Individual AI model configuration."""
    name: str = Field(..., description="Model configuration name")
    provider: ModelProvider = Field(..., description="Model provider")
    model_id: str = Field(..., description="Model identifier")
    model_type: ModelType = Field(..., description="Model type")
    capabilities: List[ModelCapability] = Field(default_factory=list, description="Model capabilities")
    credentials: ModelCredentials = Field(default_factory=ModelCredentials, description="Model credentials")
    parameters: ModelParameters = Field(default_factory=ModelParameters, description="Default generation parameters")
    rate_limiting: RateLimiting = Field(default_factory=RateLimiting, description="Rate limiting configuration")
    caching: CachingConfig = Field(default_factory=CachingConfig, description="Caching configuration")

    # Metadata
    description: Optional[str] = Field(default=None, description="Model description")
    version: str = Field(default="1.0.0", description="Model version")
    tags: List[str] = Field(default_factory=list, description="Model tags")

    # Configuration flags
    enabled: bool = Field(default=True, description="Whether this model is enabled")
    fallback_models: List[str] = Field(default_factory=list, description="Fallback model names")
    priority: int = Field(default=0, description="Model priority for selection")

    # Provider-specific settings
    provider_settings: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific settings")

    # Cost tracking
    cost_per_input_token: Optional[float] = Field(default=None, ge=0, description="Cost per 1M input tokens")
    cost_per_output_token: Optional[float] = Field(default=None, ge=0, description="Cost per 1M output tokens")

    # Quality metrics
    quality_score: Optional[float] = Field(default=None, ge=0.0, le=10.0, description="Quality score")
    latency_target_ms: Optional[int] = Field(default=None, ge=1, description="Target latency in milliseconds")

    @validator('name')
    def validate_name(cls, v):
        """Validate model name."""
        if not v or not v.strip():
            raise ValueError("Model name cannot be empty")
        if not v.replace('-', '_').replace('_', '').isalnum():
            raise ValueError("Model name must contain only alphanumeric characters, hyphens, and underscores")
        return v.strip()

    @validator('fallback_models')
    def validate_fallbacks(cls, v, values):
        """Validate fallback models don't include self."""
        if 'name' in values and values['name'] in v:
            raise ValueError("Model cannot list itself as a fallback")
        return v

    @validator('priority')
    def validate_priority_range(cls, v):
        """Validate priority range."""
        if not -100 <= v <= 100:
            raise ValueError("Priority must be between -100 and 100")
        return v


class ModelPool(BaseModel):
    """Model pool for load balancing and failover."""
    name: str = Field(..., description="Pool name")
    models: List[str] = Field(..., description="Model names in the pool")
    strategy: Literal["round_robin", "least_cost", "fastest", "best_quality", "random"] = Field(
        default="round_robin", description="Model selection strategy"
    )
    health_check_interval: int = Field(default=60, ge=1, description="Health check interval in seconds")
    failure_threshold: int = Field(default=3, ge=1, description="Failure threshold for model removal")
    recovery_threshold: int = Field(default=2, ge=1, description="Success threshold for model recovery")

    @validator('models')
    def validate_pool_models(cls, v):
        """Validate pool has models."""
        if len(v) == 0:
            raise ValueError("Model pool must contain at least one model")
        if len(v) > 20:
            raise ValueError("Model pool cannot contain more than 20 models")
        return v


class MultiModelConfig(RootModel):
    """Multi-model configuration root model."""
    models: Dict[str, ModelConfig] = Field(default_factory=dict, description="Model configurations")
    pools: Dict[str, ModelPool] = Field(default_factory=dict, description="Model pools")
    default_models: Dict[ModelType, str] = Field(default_factory=dict, description="Default models by type")
    global_settings: Dict[str, Any] = Field(default_factory=dict, description="Global model settings")

    @validator('default_models')
    def validate_defaults_exist(cls, v, values):
        """Validate default models exist."""
        if 'models' in values:
            for model_type, model_name in v.items():
                if model_name not in values['models']:
                    raise ValueError(f"Default {model_type} model '{model_name}' not found")
        return v

    def get_model(self, name: str) -> ModelConfig:
        """Get model configuration by name."""
        if name not in self.models:
            raise ValueError(f"Model '{name}' not found")
        return self.models[name]

    def get_default_model(self, model_type: ModelType) -> ModelConfig:
        """Get default model for a type."""
        if model_type not in self.default_models:
            raise ValueError(f"No default model configured for type {model_type}")
        return self.get_model(self.default_models[model_type])

    def get_pool(self, name: str) -> ModelPool:
        """Get model pool by name."""
        if name not in self.pools:
            raise ValueError(f"Model pool '{name}' not found")
        return self.pools[name]


# Predefined model configurations
class ModelPresets:
    """Predefined model configurations."""

    @staticmethod
    def gpt4_turbo() -> ModelConfig:
        """GPT-4 Turbo configuration."""
        return ModelConfig(
            name="gpt4_turbo",
            provider=ModelProvider.OPENAI,
            model_id="gpt-4-turbo-preview",
            model_type=ModelType.CHAT,
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CODE_GENERATION,
                ModelCapability.REASONING,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.VISION
            ],
            credentials=ModelCredentials(
                api_key="${OPENAI_API_KEY}",
                organization_id="${OPENAI_ORG_ID}"
            ),
            parameters=ModelParameters(
                temperature=0.7,
                max_tokens=4096,
                top_p=1.0
            ),
            rate_limiting=RateLimiting(
                requests_per_minute=500,
                tokens_per_minute=150000
            ),
            cost_per_input_token=0.01,
            cost_per_output_token=0.03,
            quality_score=9.0,
            latency_target_ms=2000
        )

    @staticmethod
    def claude3_opus() -> ModelConfig:
        """Claude 3 Opus configuration."""
        return ModelConfig(
            name="claude3_opus",
            provider=ModelProvider.ANTHROPIC,
            model_id="claude-3-opus-20240229",
            model_type=ModelType.CHAT,
            capabilities=[
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CODE_GENERATION,
                ModelCapability.REASONING,
                ModelCapability.MULTIMODAL,
                ModelCapability.VISION
            ],
            credentials=ModelCredentials(
                api_key="${ANTHROPIC_API_KEY}"
            ),
            parameters=ModelParameters(
                temperature=0.7,
                max_tokens=4096,
                top_p=1.0
            ),
            rate_limiting=RateLimiting(
                requests_per_minute=1000,
                tokens_per_minute=200000
            ),
            cost_per_input_token=0.015,
            cost_per_output_token=0.075,
            quality_score=9.5,
            latency_target_ms=3000
        )

    @staticmethod
    def text_embedding_ada() -> ModelConfig:
        """Text embedding Ada configuration."""
        return ModelConfig(
            name="text_embedding_ada",
            provider=ModelProvider.OPENAI,
            model_id="text-embedding-ada-002",
            model_type=ModelType.EMBEDDING,
            capabilities=[ModelCapability.TEXT_GENERATION],
            credentials=ModelCredentials(
                api_key="${OPENAI_API_KEY}"
            ),
            parameters=ModelParameters(),
            rate_limiting=RateLimiting(
                requests_per_minute=3000
            ),
            cost_per_input_token=0.0001,
            quality_score=8.5,
            latency_target_ms=500
        )

    @staticmethod
    def dall_e_3() -> ModelConfig:
        """DALL-E 3 configuration."""
        return ModelConfig(
            name="dall_e_3",
            provider=ModelProvider.OPENAI,
            model_id="dall-e-3",
            model_type=ModelType.IMAGE_GENERATION,
            capabilities=[ModelCapability.IMAGE_GENERATION],
            credentials=ModelCredentials(
                api_key="${OPENAI_API_KEY}"
            ),
            parameters=ModelParameters(
                image_quality="standard",
                image_size="1024x1024"
            ),
            rate_limiting=RateLimiting(
                requests_per_minute=5
            ),
            cost_per_output_token=0.04,  # Per image
            quality_score=9.0,
            latency_target_ms=10000
        )