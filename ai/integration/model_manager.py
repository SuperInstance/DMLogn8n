#!/usr/bin/env python3
"""
Advanced AI Model Manager - Central orchestration for multiple AI models
Provides sub-500ms response times with intelligent model selection and optimization
"""

import asyncio
import time
import json
import logging
import hashlib
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import numpy as np
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelType(Enum):
    """AI Model types supported by the system"""
    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    IMAGE_GENERATION = "image_generation"
    CODE_GENERATION = "code_generation"
    ANALYSIS = "analysis"
    TRANSLATION = "translation"

class ModelProvider(Enum):
    """Supported AI model providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"
    CUSTOM = "custom"

@dataclass
class ModelConfig:
    """Model configuration"""
    name: str
    provider: ModelProvider
    model_type: ModelType
    max_tokens: int
    temperature: float
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    timeout: float = 30.0
    retry_count: int = 3
    cost_per_1k_tokens: float = 0.0
    priority: int = 1
    warmup_enabled: bool = True
    streaming_enabled: bool = True
    context_window: int = 4096
    special_features: List[str] = None

@dataclass
class ModelMetrics:
    """Model performance metrics"""
    model_name: str
    response_times: List[float]
    success_rate: float
    error_count: int
    total_requests: int
    average_tokens_per_second: float
    cost_per_request: float
    last_used: datetime
    quality_score: float

@dataclass
class ModelRequest:
    """AI model request structure"""
    prompt: str
    model_type: ModelType
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    context: Optional[Dict[str, Any]] = None
    stream: bool = False
    priority: int = 1
    timeout: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ModelResponse:
    """AI model response structure"""
    content: str
    model_name: str
    provider: ModelProvider
    response_time: float
    token_usage: Dict[str, int]
    cost: float
    metadata: Dict[str, Any]
    quality_score: Optional[float] = None
    cached: bool = False

class ModelManager:
    """Advanced AI Model Manager with intelligent orchestration"""

    def __init__(self, config_file: Optional[str] = None):
        self.models: Dict[str, ModelConfig] = {}
        self.model_metrics: Dict[str, ModelMetrics] = {}
        self.model_connections: Dict[str, Any] = {}
        self.request_queue: asyncio.Queue = asyncio.Queue()
        self.response_cache: Dict[str, ModelResponse] = {}
        self.executor = ThreadPoolExecutor(max_workers=20)
        self.session: Optional[aiohttp.ClientSession] = None
        self.performance_threshold = 0.5  # 500ms target
        self.cost_optimizer_enabled = True
        self.quality_threshold = 0.8

        # Load configuration
        if config_file:
            self._load_config(config_file)
        else:
            self._load_default_models()

        # Initialize warmup tasks
        self.warmed_models = set()
        self.warmup_tasks = asyncio.create_task(self._warmup_models())

        logger.info(f"ModelManager initialized with {len(self.models)} models")

    def _load_default_models(self):
        """Load default model configurations"""
        default_models = [
            ModelConfig(
                name="gpt-4-turbo",
                provider=ModelProvider.OPENAI,
                model_type=ModelType.CHAT,
                max_tokens=4096,
                temperature=0.7,
                cost_per_1k_tokens=0.03,
                priority=1,
                context_window=128000,
                special_features=["function_calling", "vision", "code_analysis"]
            ),
            ModelConfig(
                name="claude-3-sonnet",
                provider=ModelProvider.ANTHROPIC,
                model_type=ModelType.CHAT,
                max_tokens=4096,
                temperature=0.7,
                cost_per_1k_tokens=0.015,
                priority=1,
                context_window=200000,
                special_features=["long_context", "analysis", "reasoning"]
            ),
            ModelConfig(
                name="text-embedding-3-large",
                provider=ModelProvider.OPENAI,
                model_type=ModelType.EMBEDDING,
                max_tokens=8192,
                temperature=0.0,
                cost_per_1k_tokens=0.00013,
                priority=2
            ),
            ModelConfig(
                name="gpt-3.5-turbo",
                provider=ModelProvider.OPENAI,
                model_type=ModelType.CHAT,
                max_tokens=4096,
                temperature=0.7,
                cost_per_1k_tokens=0.002,
                priority=3,
                context_window=16384
            ),
            ModelConfig(
                name="claude-instant",
                provider=ModelProvider.ANTHROPIC,
                model_type=ModelType.CHAT,
                max_tokens=4096,
                temperature=0.7,
                cost_per_1k_tokens=0.0008,
                priority=2,
                context_window=100000
            )
        ]

        for model in default_models:
            self.models[model.name] = model
            self.model_metrics[model.name] = ModelMetrics(
                model_name=model.name,
                response_times=[],
                success_rate=1.0,
                error_count=0,
                total_requests=0,
                average_tokens_per_second=0.0,
                cost_per_request=0.0,
                last_used=datetime.now(),
                quality_score=0.8
            )

    def _load_config(self, config_file: str):
        """Load model configurations from file"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)

            for model_data in config.get('models', []):
                model = ModelConfig(**model_data)
                self.models[model.name] = model
                self.model_metrics[model.name] = ModelMetrics(
                    model_name=model.name,
                    response_times=[],
                    success_rate=1.0,
                    error_count=0,
                    total_requests=0,
                    average_tokens_per_second=0.0,
                    cost_per_request=0.0,
                    last_used=datetime.now(),
                    quality_score=0.8
                )
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._load_default_models()

    async def initialize(self):
        """Initialize model connections and services"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30.0),
            connector=aiohttp.TCPConnector(limit=100)
        )

        logger.info("ModelManager initialized and ready")

    async def select_best_model(self, request: ModelRequest) -> str:
        """Intelligently select the best model for a given request"""
        suitable_models = [
            name for name, config in self.models.items()
            if config.model_type == request.model_type
        ]

        if not suitable_models:
            raise ValueError(f"No models available for type: {request.model_type}")

        # Score models based on multiple factors
        model_scores = {}
        for model_name in suitable_models:
            score = 0.0
            config = self.models[model_name]
            metrics = self.model_metrics[model_name]

            # Performance score (40% weight)
            avg_response_time = np.mean(metrics.response_times) if metrics.response_times else self.performance_threshold
            performance_score = min(1.0, self.performance_threshold / avg_response_time)
            score += performance_score * 0.4

            # Success rate score (20% weight)
            score += metrics.success_rate * 0.2

            # Cost optimization score (15% weight)
            if self.cost_optimizer_enabled:
                cost_score = 1.0 - min(1.0, config.cost_per_1k_tokens / 0.1)
                score += cost_score * 0.15

            # Quality score (15% weight)
            score += metrics.quality_score * 0.15

            # Priority score (10% weight)
            priority_score = 1.0 / config.priority
            score += priority_score * 0.1

            # Warmup bonus
            if model_name in self.warmed_models:
                score += 0.1

            model_scores[model_name] = score

        # Select highest scoring model
        best_model = max(model_scores, key=model_scores.get)
        logger.debug(f"Selected model: {best_model} (score: {model_scores[best_model]:.3f})")

        return best_model

    async def execute_request(self, request: ModelRequest) -> ModelResponse:
        """Execute AI model request with optimization"""
        start_time = time.time()

        try:
            # Select best model
            model_name = await self.select_best_model(request)
            config = self.models[model_name]

            # Check cache first
            cache_key = self._generate_cache_key(request, model_name)
            if cache_key in self.response_cache:
                cached_response = self.response_cache[cache_key]
                cached_response.cached = True
                logger.debug(f"Cache hit for model: {model_name}")
                return cached_response

            # Preprocess prompt
            optimized_prompt = self._optimize_prompt(request.prompt, config)

            # Execute request with timeout
            timeout = request.timeout or config.timeout
            response = await asyncio.wait_for(
                self._execute_model_request(model_name, optimized_prompt, request),
                timeout=timeout
            )

            # Calculate performance metrics
            response_time = time.time() - start_time
            response.response_time = response_time

            # Update metrics
            self._update_metrics(model_name, response_time, True, response)

            # Cache response
            self.response_cache[cache_key] = response

            # Validate quality
            if response.quality_score and response.quality_score < self.quality_threshold:
                logger.warning(f"Low quality response from {model_name}: {response.quality_score}")
                # Try fallback model
                if len(self.models) > 1:
                    return await self._execute_fallback(request, model_name)

            logger.info(f"Request completed in {response_time:.3f}s using {model_name}")
            return response

        except asyncio.TimeoutError:
            logger.error(f"Request timeout for {model_name}")
            self._update_metrics(model_name, time.time() - start_time, False)
            raise
        except Exception as e:
            logger.error(f"Request failed: {e}")
            self._update_metrics(model_name, time.time() - start_time, False)
            raise

    async def _execute_model_request(self, model_name: str, prompt: str, request: ModelRequest) -> ModelResponse:
        """Execute request to specific model"""
        config = self.models[model_name]

        if config.provider == ModelProvider.OPENAI:
            return await self._execute_openai_request(model_name, prompt, request)
        elif config.provider == ModelProvider.ANTHROPIC:
            return await self._execute_anthropic_request(model_name, prompt, request)
        elif config.provider == ModelProvider.LOCAL:
            return await self._execute_local_request(model_name, prompt, request)
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")

    async def _execute_openai_request(self, model_name: str, prompt: str, request: ModelRequest) -> ModelResponse:
        """Execute OpenAI API request"""
        import openai

        config = self.models[model_name]
        start_time = time.time()

        try:
            if config.model_type == ModelType.CHAT:
                response = await openai.AsyncOpenAI().chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=request.max_tokens or config.max_tokens,
                    temperature=request.temperature or config.temperature,
                    stream=request.stream
                )

                if request.stream:
                    content = ""
                    async for chunk in response:
                        if chunk.choices[0].delta.content:
                            content += chunk.choices[0].delta.content
                else:
                    content = response.choices[0].message.content
                    usage = response.usage

            else:
                # Handle other model types
                response = await openai.AsyncOpenAI().completions.create(
                    model=model_name,
                    prompt=prompt,
                    max_tokens=request.max_tokens or config.max_tokens,
                    temperature=request.temperature or config.temperature
                )
                content = response.choices[0].text
                usage = response.usage

            # Calculate cost
            cost = self._calculate_cost(model_name, usage)

            return ModelResponse(
                content=content,
                model_name=model_name,
                provider=config.provider,
                response_time=time.time() - start_time,
                token_usage={"prompt": usage.prompt_tokens, "completion": usage.completion_tokens, "total": usage.total_tokens},
                cost=cost,
                metadata={"model": model_name, "finish_reason": response.choices[0].finish_reason},
                quality_score=self._assess_response_quality(content)
            )

        except Exception as e:
            logger.error(f"OpenAI request failed: {e}")
            raise

    async def _execute_anthropic_request(self, model_name: str, prompt: str, request: ModelRequest) -> ModelResponse:
        """Execute Anthropic Claude API request"""
        import anthropic

        config = self.models[model_name]
        start_time = time.time()

        try:
            client = anthropic.AsyncAnthropic()

            response = await client.messages.create(
                model=model_name,
                max_tokens=request.max_tokens or config.max_tokens,
                temperature=request.temperature or config.temperature,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text if response.content else ""
            usage = response.usage

            # Calculate cost
            cost = self._calculate_cost(model_name, usage)

            return ModelResponse(
                content=content,
                model_name=model_name,
                provider=config.provider,
                response_time=time.time() - start_time,
                token_usage={"input": usage.input_tokens, "output": usage.output_tokens},
                cost=cost,
                metadata={"model": model_name, "stop_reason": response.stop_reason},
                quality_score=self._assess_response_quality(content)
            )

        except Exception as e:
            logger.error(f"Anthropic request failed: {e}")
            raise

    async def _execute_local_request(self, model_name: str, prompt: str, request: ModelRequest) -> ModelResponse:
        """Execute local model request"""
        # This would integrate with local models like Ollama, Llama, etc.
        # For now, return a mock response
        start_time = time.time()

        await asyncio.sleep(0.1)  # Simulate processing time

        return ModelResponse(
            content=f"Local model {model_name} response to: {prompt[:100]}...",
            model_name=model_name,
            provider=ModelProvider.LOCAL,
            response_time=time.time() - start_time,
            token_usage={"prompt": len(prompt.split()), "completion": 50, "total": len(prompt.split()) + 50},
            cost=0.0,
            metadata={"model": model_name, "type": "local"},
            quality_score=0.7
        )

    async def _execute_fallback(self, original_request: ModelRequest, failed_model: str) -> ModelResponse:
        """Execute fallback model request"""
        suitable_models = [
            name for name in self.models.keys()
            if name != failed_model and
            self.models[name].model_type == original_request.model_type
        ]

        if not suitable_models:
            raise ValueError("No fallback models available")

        fallback_model = suitable_models[0]
        logger.warning(f"Falling back to {fallback_model} after {failed_model} failure")

        return await self.execute_request(original_request)

    def _optimize_prompt(self, prompt: str, config: ModelConfig) -> str:
        """Optimize prompt for specific model"""
        # Add model-specific optimizations
        if "claude" in config.name.lower():
            # Claude prefers specific formatting
            if not prompt.startswith(("Human:", "Assistant:")):
                prompt = f"Human: {prompt}\n\nAssistant:"

        elif "gpt" in config.name.lower():
            # GPT optimizations
            if len(prompt) > config.context_window * 0.8:
                # Truncate if too long
                prompt = prompt[:int(config.context_window * 0.8)] + "..."

        return prompt

    def _generate_cache_key(self, request: ModelRequest, model_name: str) -> str:
        """Generate cache key for request"""
        content = f"{model_name}:{request.model_type}:{request.prompt}:{request.temperature}:{request.max_tokens}"
        return hashlib.md5(content.encode()).hexdigest()

    def _calculate_cost(self, model_name: str, usage) -> float:
        """Calculate request cost"""
        config = self.models[model_name]

        if hasattr(usage, 'total_tokens'):
            total_tokens = usage.total_tokens
        elif hasattr(usage, 'input_tokens') and hasattr(usage, 'output_tokens'):
            total_tokens = usage.input_tokens + usage.output_tokens
        else:
            total_tokens = 100  # Default estimate

        return (total_tokens / 1000) * config.cost_per_1k_tokens

    def _assess_response_quality(self, content: str) -> float:
        """Assess response quality"""
        if not content:
            return 0.0

        # Simple quality metrics
        length_score = min(1.0, len(content) / 100)  # Prefer adequate length
        diversity_score = len(set(content.split())) / max(len(content.split()), 1)  # Word diversity
        coherence_score = self._assess_coherence(content)  # Basic coherence check

        return (length_score + diversity_score + coherence_score) / 3

    def _assess_coherence(self, text: str) -> float:
        """Basic coherence assessment"""
        sentences = text.split('.')
        if len(sentences) < 2:
            return 0.5

        # Check for basic coherence indicators
        coherent_indicators = ['however', 'therefore', 'because', 'since', 'although', 'meanwhile']
        indicator_count = sum(1 for s in sentences if any(ind in s.lower() for ind in coherent_indicators))

        return min(1.0, indicator_count / len(sentences) * 2)

    def _update_metrics(self, model_name: str, response_time: float, success: bool, response: Optional[ModelResponse] = None):
        """Update model performance metrics"""
        metrics = self.model_metrics[model_name]
        metrics.total_requests += 1
        metrics.last_used = datetime.now()

        if success:
            metrics.response_times.append(response_time)
            # Keep only last 100 response times
            if len(metrics.response_times) > 100:
                metrics.response_times = metrics.response_times[-100:]

            if response:
                # Update tokens per second
                total_tokens = response.token_usage.get('total', 0)
                if total_tokens > 0 and response_time > 0:
                    tokens_per_second = total_tokens / response_time
                    metrics.average_tokens_per_second = (
                        metrics.average_tokens_per_second * 0.9 + tokens_per_second * 0.1
                    )

                # Update cost per request
                metrics.cost_per_request = (
                    metrics.cost_per_request * 0.9 + response.cost * 0.1
                )

                # Update quality score
                if response.quality_score:
                    metrics.quality_score = (
                        metrics.quality_score * 0.9 + response.quality_score * 0.1
                    )
        else:
            metrics.error_count += 1

        # Update success rate
        metrics.success_rate = (metrics.total_requests - metrics.error_count) / metrics.total_requests

    async def _warmup_models(self):
        """Warmup models for better performance"""
        logger.info("Starting model warmup...")

        warmup_tasks = []
        for model_name, config in self.models.items():
            if config.warmup_enabled:
                warmup_tasks.append(self._warmup_single_model(model_name))

        if warmup_tasks:
            await asyncio.gather(*warmup_tasks, return_exceptions=True)

        logger.info(f"Model warmup completed. Warmed {len(self.warmed_models)} models.")

    async def _warmup_single_model(self, model_name: str):
        """Warmup a single model"""
        try:
            # Send a simple warmup request
            warmup_request = ModelRequest(
                prompt="Hello, this is a warmup request.",
                model_type=self.models[model_name].model_type,
                max_tokens=10
            )

            await self._execute_model_request(model_name, warmup_request.prompt, warmup_request)
            self.warmed_models.add(model_name)
            logger.debug(f"Model {model_name} warmed up successfully")

        except Exception as e:
            logger.warning(f"Failed to warmup model {model_name}: {e}")

    async def batch_execute(self, requests: List[ModelRequest]) -> List[ModelResponse]:
        """Execute multiple requests in parallel"""
        tasks = [self.execute_request(req) for req in requests]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def get_model_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get comprehensive model statistics"""
        stats = {}

        for model_name, metrics in self.model_metrics.items():
            config = self.models[model_name]

            avg_response_time = np.mean(metrics.response_times) if metrics.response_times else 0

            stats[model_name] = {
                "provider": config.provider.value,
                "type": config.model_type.value,
                "total_requests": metrics.total_requests,
                "success_rate": metrics.success_rate,
                "average_response_time": avg_response_time,
                "tokens_per_second": metrics.average_tokens_per_second,
                "cost_per_request": metrics.cost_per_request,
                "quality_score": metrics.quality_score,
                "last_used": metrics.last_used.isoformat(),
                "is_warmed": model_name in self.warmed_models,
                "priority": config.priority,
                "cost_per_1k_tokens": config.cost_per_1k_tokens
            }

        return stats

    async def health_check(self) -> Dict[str, bool]:
        """Perform health check on all models"""
        health_status = {}

        for model_name in self.models:
            try:
                # Send a simple health check request
                health_request = ModelRequest(
                    prompt="Health check",
                    model_type=self.models[model_name].model_type,
                    max_tokens=5,
                    timeout=5.0
                )

                await self._execute_model_request(model_name, health_request.prompt, health_request)
                health_status[model_name] = True

            except Exception as e:
                logger.warning(f"Health check failed for {model_name}: {e}")
                health_status[model_name] = False

        return health_status

    async def shutdown(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()

        self.executor.shutdown(wait=True)
        logger.info("ModelManager shutdown complete")

# Fast API endpoints for integration
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="AI Model Manager", version="1.0.0")
model_manager = ModelManager()

class ChatRequest(BaseModel):
    prompt: str
    model_type: str = "chat"
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    stream: bool = False

class ChatResponse(BaseModel):
    content: str
    model_name: str
    response_time: float
    cost: float
    quality_score: float
    cached: bool

@app.on_event("startup")
async def startup():
    await model_manager.initialize()

@app.on_event("shutdown")
async def shutdown():
    await model_manager.shutdown()

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Execute chat request"""
    try:
        model_request = ModelRequest(
            prompt=request.prompt,
            model_type=ModelType(request.model_type),
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stream=request.stream
        )

        response = await model_manager.execute_request(model_request)

        return ChatResponse(
            content=response.content,
            model_name=response.model_name,
            response_time=response.response_time,
            cost=response.cost,
            quality_score=response.quality_score or 0.0,
            cached=response.cached
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/stats")
async def get_model_stats():
    """Get model statistics"""
    return model_manager.get_model_stats()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return await model_manager.health_check()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)