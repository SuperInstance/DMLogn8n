"""
AI Model Pools for Parallel Agent Processing
Fast, Medium, and Slow model pools for different decision complexities
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time
import json
from datetime import datetime
import hashlib
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelTier(Enum):
    FAST = "fast"          # <100ms responses, simple decisions
    MEDIUM = "medium"      # 1-3s responses, tactical decisions
    SLOW = "slow"          # 3-7s responses, strategic decisions
    CREATIVE = "creative"  # >7s responses, creative/complex decisions


@dataclass
class AIModelConfig:
    """Configuration for an AI model instance"""
    model_id: str
    tier: ModelTier
    endpoint: str
    api_key: str
    model_name: str
    max_concurrent: int = 10
    timeout: float = 10.0
    temperature: float = 0.7
    max_tokens: int = 2048


@dataclass
class AIRequest:
    """AI generation request"""
    request_id: str
    tier: ModelTier
    prompt: str
    context: Dict[str, Any] = field(default_factory=dict)
    character_id: str = ""
    priority: int = 5  # 1-10, 1 highest
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AIResponse:
    """AI generation response"""
    request_id: str
    content: str
    tier: ModelTier
    model_id: str
    processing_time: float
    token_usage: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelMetrics:
    """Performance metrics for a model"""
    model_id: str
    tier: ModelTier
    requests_processed: int = 0
    total_processing_time: float = 0.0
    average_response_time: float = 0.0
    success_rate: float = 1.0
    error_count: int = 0
    last_used: Optional[datetime] = None
    current_load: int = 0


class FastAIModelPool:
    """Fast AI model pool for simple, reflex decisions (<100ms)"""

    def __init__(self, configs: List[AIModelConfig]):
        self.models = configs
        self.semaphores = {cfg.model_id: asyncio.Semaphore(cfg.max_concurrent) for cfg in configs}
        self.metrics = {cfg.model_id: ModelMetrics(model_id=cfg.model_id, tier=ModelTier.FAST) for cfg in configs}
        self.session: Optional[aiohttp.ClientSession] = None
        self.round_robin_index = 0

    async def initialize(self):
        """Initialize HTTP session"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=20)
        timeout = aiohttp.ClientTimeout(total=0.2)  # 200ms timeout for fast models
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)

    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate response using fastest available model"""
        start_time = time.time()

        # Select model using round-robin with load checking
        selected_model = self._select_model()
        if not selected_model:
            raise Exception("No available fast models")

        async with self.semaphores[selected_model.model_id]:
            try:
                # Call fast AI model
                response = await self._call_model(selected_model, request)
                processing_time = time.time() - start_time

                # Update metrics
                metrics = self.metrics[selected_model.model_id]
                metrics.requests_processed += 1
                metrics.total_processing_time += processing_time
                metrics.average_response_time = metrics.total_processing_time / metrics.requests_processed
                metrics.last_used = datetime.now()

                return AIResponse(
                    request_id=request.request_id,
                    content=response,
                    tier=ModelTier.FAST,
                    model_id=selected_model.model_id,
                    processing_time=processing_time
                )

            except Exception as e:
                # Update error metrics
                self.metrics[selected_model.model_id].error_count += 1
                logger.error(f"Fast model error: {e}")
                raise

    def _select_model(self) -> Optional[AIModelConfig]:
        """Select model with lowest load"""
        available_models = [
            model for model in self.models
            if self.semaphores[model.model_id]._value > 0  # Has capacity
        ]

        if not available_models:
            return None

        # Round-robin through available models
        selected = available_models[self.round_robin_index % len(available_models)]
        self.round_robin_index += 1
        return selected

    async def _call_model(self, config: AIModelConfig, request: AIRequest) -> str:
        """Call the actual AI model API"""
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": config.model_name,
            "prompt": request.prompt,
            "temperature": config.temperature,
            "max_tokens": min(config.max_tokens, 500),  # Limit tokens for speed
            "stream": False
        }

        async with self.session.post(config.endpoint, json=payload, headers=headers) as resp:
            if resp.status != 200:
                raise Exception(f"Model API error: {resp.status}")
            data = await resp.json()
            return data.get("response", data.get("text", ""))

    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()


class MediumAIModelPool:
    """Medium AI model pool for tactical decisions (1-3s)"""

    def __init__(self, configs: List[AIModelConfig]):
        self.models = configs
        self.semaphores = {cfg.model_id: asyncio.Semaphore(cfg.max_concurrent) for cfg in configs}
        self.metrics = {cfg.model_id: ModelMetrics(model_id=cfg.model_id, tier=ModelTier.MEDIUM) for cfg in configs}
        self.session: Optional[aiohttp.ClientSession] = None
        self.load_balancer = {}  # Track current load per model

    async def initialize(self):
        """Initialize HTTP session"""
        connector = aiohttp.TCPConnector(limit=50, limit_per_host=10)
        timeout = aiohttp.ClientTimeout(total=5.0)  # 5s timeout for medium models
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)

    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate tactical response"""
        start_time = time.time()

        # Select model with lowest load
        selected_model = self._select_best_model()
        if not selected_model:
            raise Exception("No available medium models")

        async with self.semaphores[selected_model.model_id]:
            try:
                # Add tactical context
                enhanced_prompt = self._add_tactical_context(request)

                response = await self._call_model(selected_model, enhanced_prompt)
                processing_time = time.time() - start_time

                # Update metrics
                metrics = self.metrics[selected_model.model_id]
                metrics.requests_processed += 1
                metrics.total_processing_time += processing_time
                metrics.average_response_time = metrics.total_processing_time / metrics.requests_processed
                metrics.last_used = datetime.now()

                return AIResponse(
                    request_id=request.request_id,
                    content=response,
                    tier=ModelTier.MEDIUM,
                    model_id=selected_model.model_id,
                    processing_time=processing_time
                )

            except Exception as e:
                self.metrics[selected_model.model_id].error_count += 1
                logger.error(f"Medium model error: {e}")
                raise

    def _select_best_model(self) -> Optional[AIModelConfig]:
        """Select model based on load and performance"""
        best_model = None
        best_score = float('inf')

        for model in self.models:
            current_load = self.load_balancer.get(model.model_id, 0)
            if self.semaphores[model.model_id]._value > 0:  # Has capacity
                # Score based on load and average response time
                metrics = self.metrics[model.model_id]
                score = current_load + (metrics.average_response_time / 1000)
                if score < best_score:
                    best_score = score
                    best_model = model

        return best_model

    def _add_tactical_context(self, request: AIRequest) -> str:
        """Add tactical context to prompt"""
        tactical_prompt = f"""
Tactical Decision Context:
Character: {request.character_id}
Situation: {request.context.get('situation', 'Unknown')}
Available Actions: {request.context.get('actions', [])}
Objectives: {request.context.get('objectives', [])}

Request: {request.prompt}

Provide a tactical response considering:
1. Immediate consequences
2. Resource usage
3. Risk assessment
4. Tactical advantages
"""
        return tactical_prompt

    async def _call_model(self, config: AIModelConfig, prompt: str) -> str:
        """Call medium AI model"""
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": config.model_name,
            "prompt": prompt,
            "temperature": config.temperature,
            "max_tokens": min(config.max_tokens, 1000),
            "stream": False
        }

        async with self.session.post(config.endpoint, json=payload, headers=headers) as resp:
            if resp.status != 200:
                raise Exception(f"Model API error: {resp.status}")
            data = await resp.json()
            return data.get("response", data.get("text", ""))

    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()


class SlowAIModelPool:
    """Slow AI model pool for strategic/creative decisions (3-7s+)"""

    def __init__(self, configs: List[AIModelConfig]):
        self.models = configs
        self.semaphores = {cfg.model_id: asyncio.Semaphore(cfg.max_concurrent) for cfg in configs}
        self.metrics = {cfg.model_id: ModelMetrics(model_id=cfg.model_id, tier=ModelTier.SLOW) for cfg in configs}
        self.session: Optional[aiohttp.ClientSession] = None
        self.queue = asyncio.Queue()  # Priority queue for complex tasks
        self.processing = False

    async def initialize(self):
        """Initialize HTTP session and queue processor"""
        connector = aiohttp.TCPConnector(limit=20, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=15.0)  # 15s timeout for slow models
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)

        # Start queue processor
        asyncio.create_task(self._process_queue())

    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate strategic/creative response"""
        # Add to queue
        future = asyncio.Future()
        await self.queue.put((request.priority, request, future))

        # Wait for result
        return await future

    async def _process_queue(self):
        """Process queued requests by priority"""
        if self.processing:
            return

        self.processing = True

        while True:
            try:
                # Get highest priority request
                priority, request, future = await self.queue.get()

                # Select best model for this task
                selected_model = self._select_model_for_task(request)
                if not selected_model:
                    future.set_exception(Exception("No available slow models"))
                    continue

                # Process request
                try:
                    response = await self._process_complex_request(selected_model, request)
                    future.set_result(response)
                except Exception as e:
                    future.set_exception(e)

            except Exception as e:
                logger.error(f"Queue processing error: {e}")
                await asyncio.sleep(1)

    def _select_model_for_task(self, request: AIRequest) -> Optional[AIModelConfig]:
        """Select model based on task complexity"""
        # Check task type and select appropriate model
        task_type = request.context.get('task_type', 'general')

        available_models = [
            model for model in self.models
            if self.semaphores[model.model_id]._value > 0
        ]

        if not available_models:
            return None

        # Select model with best performance for this task type
        # For now, use round-robin
        return available_models[0]

    async def _process_complex_request(self, config: AIModelConfig, request: AIRequest) -> AIResponse:
        """Process complex strategic/creative request"""
        start_time = time.time()

        async with self.semaphores[config.model_id]:
            # Enhance prompt with strategic context
            enhanced_prompt = self._add_strategic_context(request)

            response = await self._call_model(config, enhanced_prompt)
            processing_time = time.time() - start_time

            # Update metrics
            metrics = self.metrics[config.model_id]
            metrics.requests_processed += 1
            metrics.total_processing_time += processing_time
            metrics.average_response_time = metrics.total_processing_time / metrics.requests_processed
            metrics.last_used = datetime.now()

            return AIResponse(
                request_id=request.request_id,
                content=response,
                tier=ModelTier.SLOW,
                model_id=config.model_id,
                processing_time=processing_time
            )

    def _add_strategic_context(self, request: AIRequest) -> str:
        """Add strategic context for complex decisions"""
        strategic_prompt = f"""
Strategic Decision Context:
Character: {request.character_id}
Long-term Goals: {request.context.get('long_term_goals', [])}
Current State: {request.context.get('current_state', {})}
Available Resources: {request.context.get('resources', {})}
Allies/Contacts: {request.context.get('allies', [])}
Risks/Threats: {request.context.get('threats', [])}
Past Decisions: {request.context.get('history', [])}

Request: {request.prompt}

Provide a comprehensive strategic response considering:
1. Long-term implications (months/years)
2. Multiple possible outcomes
3. Risk mitigation strategies
4. Resource allocation
5. Alliance building/maintenance
6. Creative solutions and innovations
7. Ethical considerations
8. Contingency plans
"""
        return strategic_prompt

    async def _call_model(self, config: AIModelConfig, prompt: str) -> str:
        """Call slow/strategic AI model"""
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": config.model_name,
            "prompt": prompt,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "stream": False
        }

        async with self.session.post(config.endpoint, json=payload, headers=headers) as resp:
            if resp.status != 200:
                raise Exception(f"Model API error: {resp.status}")
            data = await resp.json()
            return data.get("response", data.get("text", ""))

    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()


class ModelManager:
    """Manages all AI model pools and routes requests appropriately"""

    def __init__(self, fast_configs: List[AIModelConfig],
                 medium_configs: List[AIModelConfig],
                 slow_configs: List[AIModelConfig]):
        self.fast_pool = FastAIModelPool(fast_configs)
        self.medium_pool = MediumAIModelPool(medium_configs)
        self.slow_pool = SlowAIModelPool(slow_configs)
        self.initialized = False
        self.request_cache = {}  # Cache for common requests

    async def initialize(self):
        """Initialize all model pools"""
        await asyncio.gather(
            self.fast_pool.initialize(),
            self.medium_pool.initialize(),
            self.slow_pool.initialize()
        )
        self.initialized = True
        logger.info("All AI model pools initialized")

    async def generate(self, request: AIRequest) -> AIResponse:
        """Route request to appropriate model pool"""
        if not self.initialized:
            raise Exception("ModelManager not initialized")

        # Check cache for common requests
        cache_key = self._get_cache_key(request)
        if cache_key in self.request_cache:
            cached_response = self.request_cache[cache_key]
            logger.info(f"Cache hit for request {request.request_id}")
            return cached_response

        # Route to appropriate pool
        if request.tier == ModelTier.FAST:
            response = await self.fast_pool.generate(request)
        elif request.tier == ModelTier.MEDIUM:
            response = await self.medium_pool.generate(request)
        elif request.tier in [ModelTier.SLOW, ModelTier.CREATIVE]:
            response = await self.slow_pool.generate(request)
        else:
            raise ValueError(f"Unknown model tier: {request.tier}")

        # Cache response if appropriate
        if self._should_cache(request, response):
            self.request_cache[cache_key] = response

        return response

    def _get_cache_key(self, request: AIRequest) -> str:
        """Generate cache key for request"""
        content = f"{request.tier.value}:{request.prompt[:200]}"
        return hashlib.md5(content.encode()).hexdigest()

    def _should_cache(self, request: AIRequest, response: AIResponse) -> bool:
        """Determine if response should be cached"""
        # Only cache fast responses with common patterns
        if request.tier == ModelTier.FAST and response.processing_time < 0.05:
            return True
        return False

    async def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all models"""
        metrics = {
            "fast_pool": {},
            "medium_pool": {},
            "slow_pool": {},
            "cache_size": len(self.request_cache)
        }

        # Collect metrics from each pool
        for model_id, metric in self.fast_pool.metrics.items():
            metrics["fast_pool"][model_id] = {
                "requests_processed": metric.requests_processed,
                "average_response_time": metric.average_response_time,
                "success_rate": metric.success_rate,
                "current_load": metric.current_load
            }

        for model_id, metric in self.medium_pool.metrics.items():
            metrics["medium_pool"][model_id] = {
                "requests_processed": metric.requests_processed,
                "average_response_time": metric.average_response_time,
                "success_rate": metric.success_rate,
                "current_load": metric.current_load
            }

        for model_id, metric in self.slow_pool.metrics.items():
            metrics["slow_pool"][model_id] = {
                "requests_processed": metric.requests_processed,
                "average_response_time": metric.average_response_time,
                "success_rate": metric.success_rate,
                "current_load": metric.current_load
            }

        return metrics

    async def cleanup(self):
        """Clean up all resources"""
        await asyncio.gather(
            self.fast_pool.cleanup(),
            self.medium_pool.cleanup(),
            self.slow_pool.cleanup()
        )
        logger.info("All AI model pools cleaned up")


# Example usage and factory functions
def create_default_model_manager() -> ModelManager:
    """Create model manager with default configurations"""

    # Fast model configs (e.g., local small models, distilled models)
    fast_configs = [
        AIModelConfig(
            model_id="fast_1",
            tier=ModelTier.FAST,
            endpoint="http://localhost:11434/api/generate",
            api_key="local",  # No key needed for local models
            model_name="llama3.2:3b-instruct-q4_0",
            max_concurrent=20,
            timeout=0.2,
            temperature=0.1,
            max_tokens=150
        ),
        AIModelConfig(
            model_id="fast_2",
            tier=ModelTier.FAST,
            endpoint="http://localhost:11434/api/generate",
            api_key="local",
            model_name="phi3:mini-128k-instruct-q4_0",
            max_concurrent=20,
            timeout=0.2,
            temperature=0.1,
            max_tokens=150
        )
    ]

    # Medium model configs (e.g., GLM-4, Claude Haiku)
    medium_configs = [
        AIModelConfig(
            model_id="medium_1",
            tier=ModelTier.MEDIUM,
            endpoint="https://open.bigmodel.cn/api/paas/v4/chat/completions",
            api_key="${GLM4_API_KEY}",
            model_name="glm-4",
            max_concurrent=10,
            timeout=5.0,
            temperature=0.5,
            max_tokens=1000
        ),
        AIModelConfig(
            model_id="medium_2",
            tier=ModelTier.MEDIUM,
            endpoint="https://api.anthropic.com/v1/messages",
            api_key="${ANTHROPIC_API_KEY}",
            model_name="claude-3-haiku-20240307",
            max_concurrent=10,
            timeout=5.0,
            temperature=0.5,
            max_tokens=1000
        )
    ]

    # Slow model configs (e.g., GPT-4, Claude Opus)
    slow_configs = [
        AIModelConfig(
            model_id="slow_1",
            tier=ModelTier.SLOW,
            endpoint="https://api.openai.com/v1/chat/completions",
            api_key="${OPENAI_API_KEY}",
            model_name="gpt-4-turbo-preview",
            max_concurrent=5,
            timeout=15.0,
            temperature=0.7,
            max_tokens=4000
        ),
        AIModelConfig(
            model_id="slow_2",
            tier=ModelTier.SLOW,
            endpoint="https://api.anthropic.com/v1/messages",
            api_key="${ANTHROPIC_API_KEY}",
            model_name="claude-3-opus-20240229",
            max_concurrent=5,
            timeout=15.0,
            temperature=0.7,
            max_tokens=4000
        )
    ]

    return ModelManager(fast_configs, medium_configs, slow_configs)


# Test function
async def test_model_pools():
    """Test all model pools"""
    manager = create_default_model_manager()
    await manager.initialize()

    # Test fast model
    fast_request = AIRequest(
        request_id=str(uuid.uuid4()),
        tier=ModelTier.FAST,
        prompt="Should I attack or defend?",
        character_id="test_character"
    )

    fast_response = await manager.generate(fast_request)
    print(f"Fast response ({fast_response.processing_time:.3f}s): {fast_response.content[:100]}...")

    # Test medium model
    medium_request = AIRequest(
        request_id=str(uuid.uuid4()),
        tier=ModelTier.MEDIUM,
        prompt="Plan the next tactical move for the party",
        character_id="test_character",
        context={
            "situation": "In combat with goblins",
            "actions": ["attack", "defend", "retreat", "use spell"],
            "objectives": ["minimize casualties", "defeat enemies"]
        }
    )

    medium_response = await manager.generate(medium_request)
    print(f"Medium response ({medium_response.processing_time:.3f}s): {medium_response.content[:100]}...")

    # Test slow model
    slow_request = AIRequest(
        request_id=str(uuid.uuid4()),
        tier=ModelTier.CREATIVE,
        prompt="Develop a long-term strategy for the kingdom",
        character_id="test_character",
        context={
            "task_type": "strategic_planning",
            "long_term_goals": ["prosperity", "security", "expansion"],
            "current_state": {"resources": 1000, "army_size": 500},
            "resources": {"gold": 1000, "food": 500},
            "allies": ["neighboring_kingdom", "merchant_guild"],
            "threats": ["dragon", "rival_kingdom"]
        }
    )

    slow_response = await manager.generate(slow_request)
    print(f"Slow response ({slow_response.processing_time:.3f}s): {slow_response.content[:100]}...")

    # Get metrics
    metrics = await manager.get_metrics()
    print(f"\nMetrics: {json.dumps(metrics, indent=2, default=str)}")

    await manager.cleanup()


if __name__ == "__main__":
    asyncio.run(test_model_pools())