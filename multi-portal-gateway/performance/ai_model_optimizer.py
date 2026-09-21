#!/usr/bin/env python3
"""
Advanced AI Model Optimizer for DMLogn8n Platform
AI model inference optimization, quantization, batching, and hardware acceleration
"""

import asyncio
import json
import logging
import time
import threading
import weakref
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import hashlib
import numpy as np

# AI/ML libraries
try:
    import torch
    import torch.nn as nn
    import torch.quantization
    import torchvision.transforms as transforms
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import onnx
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

try:
    import tensorflow as tf
    from tensorflow import lite as tflite
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False

try:
    import transformers
    from transformers import AutoModel, AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """AI model types"""
    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"
    ONNX = "onnx"
    TFLITE = "tflite"
    TRANSFORMERS = "transformers"
    OPENAI_API = "openai_api"
    CUSTOM = "custom"

class QuantizationType(Enum):
    """Model quantization types"""
    DYNAMIC = "dynamic"
    STATIC = "static"
    QAT = "quantization_aware_training"
    INT8 = "int8"
    FP16 = "fp16"
    BF16 = "bf16"

class OptimizationStrategy(Enum):
    """Model optimization strategies"""
    LATENCY = "latency"          # Prioritize inference speed
    THROUGHPUT = "throughput"    # Prioritize batch processing
    MEMORY = "memory"           # Prioritize memory efficiency
    ACCURACY = "accuracy"       # Prioritize model accuracy
    BALANCED = "balanced"       # Balance all factors

class HardwareType(Enum):
    """Hardware acceleration types"""
    CPU = "cpu"
    GPU = "gpu"
    TPU = "tpu"
    NEURAL_COMPUTE = "neural_compute"
    CUSTOM_ACCELERATOR = "custom_accelerator"

@dataclass
class ModelMetrics:
    """Model performance metrics"""
    model_id: str
    timestamp: datetime
    inference_time_ms: float
    preprocessing_time_ms: float
    postprocessing_time_ms: float
    memory_usage_mb: float
    gpu_memory_usage_mb: float
    batch_size: int
    input_size: Tuple[int, ...]
    output_size: Tuple[int, ...]
    accuracy: Optional[float] = None
    throughput_per_sec: float = 0.0
    hardware_type: HardwareType = HardwareType.CPU
    quantization_type: Optional[QuantizationType] = None

@dataclass
class ModelConfig:
    """Model configuration"""
    model_id: str
    model_type: ModelType
    model_path: str
    optimization_strategy: OptimizationStrategy
    quantization_type: Optional[QuantizationType] = None
    hardware_type: HardwareType = HardwareType.CPU
    batch_size: int = 1
    max_batch_size: int = 32
    enable_dynamic_batching: bool = True
    cache_enabled: bool = True
    warmup_iterations: int = 3
    timeout_ms: float = 5000.0

@dataclass
class BatchRequest:
    """Batch inference request"""
    requests: List[Any]
    timestamps: List[datetime]
    max_wait_time_ms: float = 50.0
    priority: int = 0

class ModelBackend(ABC):
    """Abstract model backend interface"""

    @abstractmethod
    async def load_model(self, config: ModelConfig) -> bool:
        """Load model"""
        pass

    @abstractmethod
    async def predict(self, inputs: Any, batch_size: int = 1) -> Any:
        """Run inference"""
        pass

    @abstractmethod
    async def benchmark(self, sample_input: Any, iterations: int = 100) -> Dict[str, float]:
        """Benchmark model performance"""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        pass

    @abstractmethod
    async def optimize(self, optimization_type: str) -> bool:
        """Optimize model"""
        pass

class PyTorchBackend(ModelBackend):
    """PyTorch model backend"""

    def __init__(self):
        self.model = None
        self.device = None
        self.tokenizer = None
        self.config = None

    async def load_model(self, config: ModelConfig) -> bool:
        """Load PyTorch model"""
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch not available")

        self.config = config

        try:
            # Set device
            if config.hardware_type == HardwareType.GPU and torch.cuda.is_available():
                self.device = torch.device("cuda")
                torch.cuda.empty_cache()
            else:
                self.device = torch.device("cpu")

            # Load model based on type
            if config.model_type == ModelType.TRANSFORMERS and TRANSFORMERS_AVAILABLE:
                self.model = AutoModel.from_pretrained(config.model_path)
                self.tokenizer = AutoTokenizer.from_pretrained(config.model_path)
                self.model.to(self.device)
            else:
                self.model = torch.load(config.model_path, map_location=self.device)

            # Apply optimizations
            self.model.eval()

            if config.quantization_type:
                await self._apply_quantization(config.quantization_type)

            # Warmup
            await self._warmup(config.warmup_iterations)

            logger.info(f"PyTorch model loaded: {config.model_id} on {self.device}")
            return True

        except Exception as e:
            logger.error(f"Failed to load PyTorch model: {e}")
            return False

    async def predict(self, inputs: Any, batch_size: int = 1) -> Any:
        """Run PyTorch inference"""
        if self.model is None:
            raise RuntimeError("Model not loaded")

        try:
            preprocessing_start = time.time()

            # Preprocess inputs
            if self.tokenizer:
                # Handle text inputs with tokenizer
                if isinstance(inputs, str):
                    inputs = [inputs]
                processed = self.tokenizer(
                    inputs,
                    padding=True,
                    truncation=True,
                    return_tensors="pt"
                ).to(self.device)
            else:
                # Handle tensor inputs
                if isinstance(inputs, np.ndarray):
                    inputs = torch.from_numpy(inputs)
                if not isinstance(inputs, torch.Tensor):
                    inputs = torch.tensor(inputs)

                if len(inputs.shape) == 1:
                    inputs = inputs.unsqueeze(0)

                processed = inputs.to(self.device)

            preprocessing_time = (time.time() - preprocessing_start) * 1000

            # Run inference
            inference_start = time.time()
            with torch.no_grad():
                if self.tokenizer:
                    outputs = self.model(**processed)
                else:
                    outputs = self.model(processed)

            inference_time = (time.time() - inference_start) * 1000

            # Postprocess outputs
            postprocessing_start = time.time()
            if hasattr(outputs, 'last_hidden_state'):
                result = outputs.last_hidden_state.cpu().numpy()
            elif hasattr(outputs, 'logits'):
                result = outputs.logits.cpu().numpy()
            else:
                result = outputs.cpu().numpy() if isinstance(outputs, torch.Tensor) else outputs

            postprocessing_time = (time.time() - postprocessing_start) * 1000

            return {
                'outputs': result,
                'metrics': {
                    'preprocessing_time_ms': preprocessing_time,
                    'inference_time_ms': inference_time,
                    'postprocessing_time_ms': postprocessing_time,
                    'total_time_ms': preprocessing_time + inference_time + postprocessing_time
                }
            }

        except Exception as e:
            logger.error(f"PyTorch inference failed: {e}")
            raise

    async def benchmark(self, sample_input: Any, iterations: int = 100) -> Dict[str, float]:
        """Benchmark PyTorch model"""
        if self.model is None:
            raise RuntimeError("Model not loaded")

        times = []
        memory_usage = []

        for i in range(iterations):
            # Measure memory before
            if self.device.type == 'cuda':
                torch.cuda.reset_peak_memory_stats()
                memory_before = torch.cuda.memory_allocated()

            start_time = time.time()
            result = await self.predict(sample_input)
            end_time = time.time()

            times.append((end_time - start_time) * 1000)

            if self.device.type == 'cuda':
                memory_after = torch.cuda.max_memory_allocated()
                memory_usage.append((memory_after - memory_before) / 1024 / 1024)  # MB

        return {
            'avg_inference_time_ms': np.mean(times),
            'min_inference_time_ms': np.min(times),
            'max_inference_time_ms': np.max(times),
            'std_inference_time_ms': np.std(times),
            'throughput_per_sec': 1.0 / (np.mean(times) / 1000),
            'avg_memory_usage_mb': np.mean(memory_usage) if memory_usage else 0,
            'device': str(self.device)
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Get PyTorch model information"""
        if self.model is None:
            return {}

        info = {
            'model_type': 'pytorch',
            'device': str(self.device),
            'parameters': sum(p.numel() for p in self.model.parameters()),
            'trainable_parameters': sum(p.numel() for p in self.model.parameters() if p.requires_grad),
        }

        if self.device.type == 'cuda':
            info.update({
                'gpu_name': torch.cuda.get_device_name(),
                'gpu_memory_allocated_mb': torch.cuda.memory_allocated() / 1024 / 1024,
                'gpu_memory_reserved_mb': torch.cuda.memory_reserved() / 1024 / 1024
            })

        return info

    async def optimize(self, optimization_type: str) -> bool:
        """Optimize PyTorch model"""
        try:
            if optimization_type == 'torch_script':
                # Convert to TorchScript
                if self.model:
                    dummy_input = torch.randn(1, 3, 224, 224).to(self.device)
                    traced_model = torch.jit.trace(self.model, dummy_input)
                    traced_model.eval()
                    # Use traced model for inference
                    return True

            elif optimization_type == 'compile':
                # Use torch.compile for PyTorch 2.0+
                if hasattr(torch, 'compile'):
                    self.model = torch.compile(self.model)
                    return True

            return False

        except Exception as e:
            logger.error(f"Model optimization failed: {e}")
            return False

    async def _apply_quantization(self, quantization_type: QuantizationType):
        """Apply model quantization"""
        try:
            if quantization_type == QuantizationType.DYNAMIC:
                self.model = torch.quantization.quantize_dynamic(
                    self.model, {nn.Linear}, dtype=torch.qint8
                )
            elif quantization_type == QuantizationType.FP16 and self.device.type == 'cuda':
                self.model = self.model.half()
            elif quantization_type == QuantizationType.INT8:
                self.model = torch.quantization.quantize(
                    self.model, dtype=torch.qint8
                )

        except Exception as e:
            logger.warning(f"Quantization failed: {e}")

    async def _warmup(self, iterations: int):
        """Warmup model"""
        try:
            dummy_input = torch.randn(1, 3, 224, 224).to(self.device)
            with torch.no_grad():
                for _ in range(iterations):
                    _ = self.model(dummy_input)
        except:
            pass  # Warmup is optional

class ONNXBackend(ModelBackend):
    """ONNX model backend"""

    def __init__(self):
        self.session = None
        self.input_name = None
        self.output_name = None
        self.config = None

    async def load_model(self, config: ModelConfig) -> bool:
        """Load ONNX model"""
        if not ONNX_AVAILABLE:
            raise RuntimeError("ONNX not available")

        self.config = config

        try:
            # Configure session options
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

            # Configure providers based on hardware
            providers = ['CPUExecutionProvider']
            if config.hardware_type == HardwareType.GPU:
                providers.insert(0, 'CUDAExecutionProvider')

            # Create inference session
            self.session = ort.InferenceSession(
                config.model_path,
                sess_options=sess_options,
                providers=providers
            )

            # Get input/output names
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name

            logger.info(f"ONNX model loaded: {config.model_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to load ONNX model: {e}")
            return False

    async def predict(self, inputs: Any, batch_size: int = 1) -> Any:
        """Run ONNX inference"""
        if self.session is None:
            raise RuntimeError("Model not loaded")

        try:
            preprocessing_start = time.time()

            # Preprocess inputs
            if isinstance(inputs, np.ndarray):
                processed = inputs
            else:
                processed = np.array(inputs)

            if len(processed.shape) == 1:
                processed = np.expand_dims(processed, axis=0)

            preprocessing_time = (time.time() - preprocessing_start) * 1000

            # Run inference
            inference_start = time.time()
            outputs = self.session.run(None, {self.input_name: processed})
            inference_time = (time.time() - inference_start) * 1000

            # Postprocess outputs
            postprocessing_start = time.time()
            result = outputs[0]  # Take first output
            postprocessing_time = (time.time() - postprocessing_start) * 1000

            return {
                'outputs': result,
                'metrics': {
                    'preprocessing_time_ms': preprocessing_time,
                    'inference_time_ms': inference_time,
                    'postprocessing_time_ms': postprocessing_time,
                    'total_time_ms': preprocessing_time + inference_time + postprocessing_time
                }
            }

        except Exception as e:
            logger.error(f"ONNX inference failed: {e}")
            raise

    async def benchmark(self, sample_input: Any, iterations: int = 100) -> Dict[str, float]:
        """Benchmark ONNX model"""
        if self.session is None:
            raise RuntimeError("Model not loaded")

        times = []

        for i in range(iterations):
            start_time = time.time()
            result = await self.predict(sample_input)
            end_time = time.time()
            times.append((end_time - start_time) * 1000)

        return {
            'avg_inference_time_ms': np.mean(times),
            'min_inference_time_ms': np.min(times),
            'max_inference_time_ms': np.max(times),
            'std_inference_time_ms': np.std(times),
            'throughput_per_sec': 1.0 / (np.mean(times) / 1000),
            'providers': self.session.get_providers()
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Get ONNX model information"""
        if self.session is None:
            return {}

        return {
            'model_type': 'onnx',
            'inputs': [{'name': input.name, 'shape': input.shape, 'type': input.type}
                      for input in self.session.get_inputs()],
            'outputs': [{'name': output.name, 'shape': output.shape, 'type': output.type}
                       for output in self.session.get_outputs()],
            'providers': self.session.get_providers()
        }

    async def optimize(self, optimization_type: str) -> bool:
        """ONNX optimization is handled during session creation"""
        return True

class AIModelOptimizer:
    """Advanced AI model optimization and management system"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self.models = {}
        self.backends = {}
        self.metrics_history = deque(maxlen=self.config.get('history_size', 10000))
        self.batch_queues = defaultdict(asyncio.Queue)
        self.active_requests = {}

        # Optimization settings
        self.auto_quantization = self.config.get('auto_quantization', False)
        self.dynamic_batching = self.config.get('dynamic_batching', True)
        self.model_caching = self.config.get('model_caching', True)
        self.auto_scaling = self.config.get('auto_scaling', False)

        # Performance thresholds
        self.latency_threshold = self.config.get('latency_threshold', 100.0)  # ms
        self.memory_threshold = self.config.get('memory_threshold', 1024.0)  # MB
        self.throughput_threshold = self.config.get('throughput_threshold', 10.0)  # requests/sec

        # Initialize backends
        self._initialize_backends()

        # Background tasks
        self.background_running = False
        self.background_tasks = set()

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'history_size': 10000,
            'latency_threshold': 100.0,
            'memory_threshold': 1024.0,
            'throughput_threshold': 10.0,
            'auto_quantization': False,
            'dynamic_batching': True,
            'model_caching': True,
            'auto_scaling': False,
            'monitoring_interval': 60.0,
            'optimization_interval': 300.0,
            'max_batch_wait_time_ms': 50.0,
            'default_batch_size': 1,
            'max_batch_size': 32,
            'warmup_iterations': 3,
            'model_cache_size': 5
        }

    def _initialize_backends(self):
        """Initialize model backends"""
        self.backends[ModelType.PYTORCH] = PyTorchBackend()
        self.backends[ModelType.TRANSFORMERS] = PyTorchBackend()
        self.backends[ModelType.ONNX] = ONNXBackend()

    async def load_model(self, config: ModelConfig) -> bool:
        """Load and optimize AI model"""
        if config.model_id in self.models:
            logger.warning(f"Model {config.model_id} already loaded")
            return True

        try:
            # Get appropriate backend
            backend = self.backends.get(config.model_type)
            if not backend:
                raise ValueError(f"Unsupported model type: {config.model_type}")

            # Load model
            success = await backend.load_model(config)
            if not success:
                return False

            # Store model
            self.models[config.model_id] = {
                'config': config,
                'backend': backend,
                'loaded_at': datetime.now(),
                'request_count': 0,
                'total_inference_time': 0.0,
                'cache_hits': 0
            }

            # Start batch processing if enabled
            if self.dynamic_batching and config.enable_dynamic_batching:
                await self._start_batch_processing(config.model_id)

            logger.info(f"Model loaded successfully: {config.model_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to load model {config.model_id}: {e}")
            return False

    async def predict(self, model_id: str, inputs: Any,
                     priority: int = 0) -> Dict[str, Any]:
        """Run model inference"""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not loaded")

        model_info = self.models[model_id]
        config = model_info['config']
        backend = model_info['backend']

        start_time = time.time()
        request_id = hashlib.md5(f"{model_id}_{time.time()}_{inputs}".encode()).hexdigest()

        try:
            # Dynamic batching
            if self.dynamic_batching and config.enable_dynamic_batching:
                result = await self._process_with_batching(model_id, inputs, priority)
            else:
                # Direct inference
                result = await backend.predict(inputs, config.batch_size)

            # Update metrics
            inference_time = (time.time() - start_time) * 1000
            model_info['request_count'] += 1
            model_info['total_inference_time'] += inference_time

            # Create metrics record
            metrics = ModelMetrics(
                model_id=model_id,
                timestamp=datetime.now(),
                inference_time_ms=inference_time,
                preprocessing_time_ms=result['metrics']['preprocessing_time_ms'],
                postprocessing_time_ms=result['metrics']['postprocessing_time_ms'],
                memory_usage_mb=0,  # Would need memory monitoring
                gpu_memory_usage_mb=0,  # Would need GPU memory monitoring
                batch_size=result.get('batch_size', 1),
                input_size=tuple(inputs.shape if hasattr(inputs, 'shape') else ()),
                output_size=tuple(result['outputs'].shape if hasattr(result['outputs'], 'shape') else ()),
                hardware_type=config.hardware_type,
                quantization_type=config.quantization_type
            )

            self.metrics_history.append(metrics)

            # Check performance thresholds
            self._check_performance_thresholds(metrics)

            return result

        except Exception as e:
            logger.error(f"Model inference failed for {model_id}: {e}")
            raise

    async def _process_with_batching(self, model_id: str, inputs: Any, priority: int) -> Dict[str, Any]:
        """Process request with dynamic batching"""
        batch_queue = self.batch_queues[model_id]
        request = {
            'inputs': inputs,
            'priority': priority,
            'timestamp': time.time(),
            'future': asyncio.Future()
        }

        # Add to batch queue
        await batch_queue.put(request)

        # Wait for result
        return await request['future']

    async def _start_batch_processing(self, model_id: str):
        """Start batch processing task"""
        async def batch_processor():
            model_info = self.models[model_id]
            config = model_info['config']
            backend = model_info['backend']
            batch_queue = self.batch_queues[model_id]

            while self.background_running:
                try:
                    # Collect batch
                    batch = []
                    batch_start_time = time.time()

                    # Wait for first request
                    request = await asyncio.wait_for(
                        batch_queue.get(),
                        timeout=1.0
                    )
                    batch.append(request)

                    # Collect more requests within time window
                    remaining_time = self.config.get('max_batch_wait_time_ms', 50.0) / 1000.0
                    while (len(batch) < config.max_batch_size and
                           (time.time() - batch_start_time) < remaining_time):
                        try:
                            request = await asyncio.wait_for(
                                batch_queue.get(),
                                timeout=remaining_time - (time.time() - batch_start_time)
                            )
                            batch.append(request)
                        except asyncio.TimeoutError:
                            break

                    # Process batch
                    if batch:
                        try:
                            # Prepare batch inputs
                            batch_inputs = [req['inputs'] for req in batch]

                            # Run inference
                            result = await backend.predict(batch_inputs, len(batch))

                            # Distribute results
                            for i, request in enumerate(batch):
                                if len(result['outputs']) > i:
                                    request['future'].set_result({
                                        'outputs': result['outputs'][i],
                                        'metrics': result['metrics'],
                                        'batch_size': len(batch)
                                    })
                                else:
                                    request['future'].set_exception(
                                        RuntimeError("Batch result size mismatch")
                                    )

                        except Exception as e:
                            # Set exception for all requests in batch
                            for request in batch:
                                request['future'].set_exception(e)

                except Exception as e:
                    logger.error(f"Batch processing error for {model_id}: {e}")
                    await asyncio.sleep(0.1)

        # Start batch processor task
        task = asyncio.create_task(batch_processor())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

    async def benchmark_model(self, model_id: str, sample_input: Any,
                            iterations: int = 100) -> Dict[str, Any]:
        """Benchmark model performance"""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not loaded")

        model_info = self.models[model_id]
        backend = model_info['backend']

        logger.info(f"Benchmarking model {model_id} with {iterations} iterations")
        return await backend.benchmark(sample_input, iterations)

    async def optimize_model(self, model_id: str, optimization_type: str) -> bool:
        """Optimize loaded model"""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not loaded")

        model_info = self.models[model_id]
        backend = model_info['backend']

        return await backend.optimize(optimization_type)

    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get model information"""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not loaded")

        model_info = self.models[model_id]
        backend = model_info['backend']
        config = model_info['config']

        info = {
            'model_id': model_id,
            'config': {
                'model_type': config.model_type.value,
                'optimization_strategy': config.optimization_strategy.value,
                'hardware_type': config.hardware_type.value,
                'batch_size': config.batch_size,
                'quantization_type': config.quantization_type.value if config.quantization_type else None
            },
            'backend_info': backend.get_model_info(),
            'statistics': {
                'loaded_at': model_info['loaded_at'].isoformat(),
                'request_count': model_info['request_count'],
                'total_inference_time': model_info['total_inference_time'],
                'avg_inference_time': (model_info['total_inference_time'] /
                                     max(model_info['request_count'], 1)),
                'cache_hits': model_info['cache_hits']
            }
        }

        return info

    def _check_performance_thresholds(self, metrics: ModelMetrics):
        """Check if performance thresholds are exceeded"""
        if metrics.inference_time_ms > self.latency_threshold:
            logger.warning(f"High inference latency detected: {metrics.inference_time_ms:.2f}ms for {metrics.model_id}")

        if metrics.memory_usage_mb > self.memory_threshold:
            logger.warning(f"High memory usage detected: {metrics.memory_usage_mb:.2f}MB for {metrics.model_id}")

        # Calculate throughput from recent metrics
        recent_metrics = [m for m in self.metrics_history[-100:]
                         if m.model_id == metrics.model_id]
        if len(recent_metrics) >= 10:
            time_span = (recent_metrics[-1].timestamp - recent_metrics[0].timestamp).total_seconds()
            if time_span > 0:
                throughput = len(recent_metrics) / time_span
                if throughput < self.throughput_threshold:
                    logger.warning(f"Low throughput detected: {throughput:.2f} req/s for {metrics.model_id}")

    def start_background_tasks(self):
        """Start background optimization tasks"""
        if self.background_running:
            return

        self.background_running = True

        # Performance monitoring task
        monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.background_tasks.add(monitoring_task)

        # Auto-optimization task
        optimization_task = asyncio.create_task(self._optimization_loop())
        self.background_tasks.add(optimization_task)

        logger.info("Background model optimization tasks started")

    def stop_background_tasks(self):
        """Stop background tasks"""
        self.background_running = False

        for task in self.background_tasks:
            task.cancel()

        if self.background_tasks:
            asyncio.gather(*self.background_tasks, return_exceptions=True)

        self.background_tasks.clear()
        logger.info("Background model optimization tasks stopped")

    async def _monitoring_loop(self):
        """Background model performance monitoring loop"""
        while self.background_running:
            try:
                # Analyze model performance
                await self._analyze_model_performance()

                await asyncio.sleep(self.config.get('monitoring_interval', 60.0))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in model monitoring loop: {e}")
                await asyncio.sleep(30)

    async def _optimization_loop(self):
        """Background model optimization loop"""
        while self.background_running:
            try:
                # Auto-optimize models if enabled
                if self.auto_quantization:
                    await self._auto_optimize_models()

                await asyncio.sleep(self.config.get('optimization_interval', 300.0))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in model optimization loop: {e}")
                await asyncio.sleep(60)

    async def _analyze_model_performance(self):
        """Analyze model performance patterns"""
        recent_metrics = list(self.metrics_history)[-100:]

        if not recent_metrics:
            return

        # Group by model
        model_performance = defaultdict(list)
        for metric in recent_metrics:
            model_performance[metric.model_id].append(metric)

        # Analyze each model
        for model_id, metrics in model_performance.items():
            if len(metrics) < 10:
                continue

            latencies = [m.inference_time_ms for m in metrics]
            avg_latency = np.mean(latencies)

            if avg_latency > self.latency_threshold:
                logger.warning(f"Model {model_id} has high average latency: {avg_latency:.2f}ms")
                # Suggest optimizations
                await self._suggest_optimizations(model_id, metrics)

    async def _suggest_optimizations(self, model_id: str, metrics: List[ModelMetrics]):
        """Suggest optimizations for underperforming model"""
        if model_id not in self.models:
            return

        model_info = self.models[model_id]
        config = model_info['config']

        suggestions = []

        # Latency optimizations
        avg_latency = np.mean([m.inference_time_ms for m in metrics])
        if avg_latency > self.latency_threshold:
            if config.quantization_type is None:
                suggestions.append("Consider model quantization to reduce latency")
            if config.batch_size == 1:
                suggestions.append("Consider enabling dynamic batching")
            if config.hardware_type == HardwareType.CPU:
                suggestions.append("Consider GPU acceleration if available")

        # Memory optimizations
        avg_memory = np.mean([m.memory_usage_mb for m in metrics])
        if avg_memory > self.memory_threshold:
            suggestions.append("Consider model quantization or pruning to reduce memory usage")

        # Throughput optimizations
        time_span = (metrics[-1].timestamp - metrics[0].timestamp).total_seconds()
        if time_span > 0:
            throughput = len(metrics) / time_span
            if throughput < self.throughput_threshold:
                suggestions.append("Consider increasing batch size or model parallelization")

        if suggestions:
            logger.info(f"Optimization suggestions for {model_id}: {', '.join(suggestions)}")

    async def _auto_optimize_models(self):
        """Automatically optimize underperforming models"""
        for model_id, model_info in self.models.items():
            try:
                # Get recent metrics
                recent_metrics = [m for m in self.metrics_history[-50:]
                                if m.model_id == model_id]

                if len(recent_metrics) < 20:
                    continue

                avg_latency = np.mean([m.inference_time_ms for m in recent_metrics])

                # Auto-quantize if latency is high
                if avg_latency > self.latency_threshold * 1.5:
                    if model_info['config'].quantization_type is None:
                        logger.info(f"Auto-quantizing model {model_id}")
                        # This would implement automatic quantization
                        # await self.optimize_model(model_id, 'quantize')

            except Exception as e:
                logger.error(f"Error in auto-optimization for {model_id}: {e}")

    def get_performance_report(self, time_window: timedelta = None) -> Dict[str, Any]:
        """Generate comprehensive model performance report"""
        if time_window is None:
            time_window = timedelta(hours=24)

        cutoff_time = datetime.now() - time_window
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]

        if not recent_metrics:
            return {"error": "No model data available for specified time window"}

        # Calculate statistics
        latencies = [m.inference_time_ms for m in recent_metrics]
        memory_usage = [m.memory_usage_mb for m in recent_metrics]

        # Model statistics
        model_stats = {}
        for model_id in self.models.keys():
            model_metrics = [m for m in recent_metrics if m.model_id == model_id]
            if model_metrics:
                model_latencies = [m.inference_time_ms for m in model_metrics]
                model_memory = [m.memory_usage_mb for m in model_metrics]

                model_stats[model_id] = {
                    'request_count': len(model_metrics),
                    'avg_latency_ms': np.mean(model_latencies),
                    'max_latency_ms': np.max(model_latencies),
                    'min_latency_ms': np.min(model_latencies),
                    'avg_memory_mb': np.mean(model_memory) if model_memory else 0,
                    'throughput_per_sec': len(model_metrics) / time_window.total_seconds()
                }

        report = {
            'time_window': str(time_window),
            'total_requests': len(recent_metrics),
            'loaded_models': list(self.models.keys()),
            'overall_performance': {
                'avg_latency_ms': np.mean(latencies),
                'max_latency_ms': np.max(latencies),
                'min_latency_ms': np.min(latencies),
                'std_latency_ms': np.std(latencies),
                'avg_memory_mb': np.mean(memory_usage) if memory_usage else 0
            },
            'model_performance': model_stats,
            'hardware_distribution': {
                hw.value: len([m for m in recent_metrics if m.hardware_type == hw])
                for hw in HardwareType
            },
            'quantization_distribution': {
                q.value: len([m for m in recent_metrics if m.quantization_type == q])
                for q in QuantizationType
            }
        }

        return report

    async def unload_model(self, model_id: str) -> bool:
        """Unload model from memory"""
        if model_id not in self.models:
            logger.warning(f"Model {model_id} not loaded")
            return False

        try:
            # Stop batch processing
            if model_id in self.batch_queues:
                # Cancel pending requests
                while not self.batch_queues[model_id].empty():
                    try:
                        request = self.batch_queues[model_id].get_nowait()
                        request['future'].cancel()
                    except asyncio.QueueEmpty:
                        break

                del self.batch_queues[model_id]

            # Remove model
            del self.models[model_id]

            logger.info(f"Model unloaded: {model_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to unload model {model_id}: {e}")
            return False

    async def cleanup(self):
        """Cleanup all models and resources"""
        # Unload all models
        for model_id in list(self.models.keys()):
            await self.unload_model(model_id)

        # Stop background tasks
        self.stop_background_tasks()

        logger.info("AI model optimizer cleanup completed")

# Model inference decorator
def optimize_inference(optimizer: AIModelOptimizer, model_id: str, priority: int = 0):
    """Decorator for optimized model inference"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # This decorator would need to be integrated with specific model functions
            # For now, it's a placeholder for the concept
            result = await func(*args, **kwargs)
            return result

        return async_wrapper

    return decorator

# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize AI model optimizer
        optimizer = AIModelOptimizer({
            'dynamic_batching': True,
            'auto_quantization': False,
            'latency_threshold': 100.0
        })

        # Start background tasks
        optimizer.start_background_tasks()

        try:
            # Example model configuration
            config = ModelConfig(
                model_id="example_model",
                model_type=ModelType.PYTORCH,
                model_path="path/to/model.pth",
                optimization_strategy=OptimizationStrategy.LATENCY,
                hardware_type=HardwareType.CPU,
                batch_size=4,
                enable_dynamic_batching=True
            )

            # Note: This would require an actual model file
            # success = await optimizer.load_model(config)
            # if success:
            #     # Example inference
            #     sample_input = torch.randn(1, 3, 224, 224)
            #     result = await optimizer.predict("example_model", sample_input)
            #     print(f"Inference result shape: {result['outputs'].shape}")
            #
            #     # Benchmark model
            #     benchmark = await optimizer.benchmark_model("example_model", sample_input, iterations=10)
            #     print(f"Benchmark results: {benchmark}")

            # Get model info (would work with loaded model)
            try:
                info = optimizer.get_model_info("example_model")
                print(f"Model info: {json.dumps(info, indent=2, default=str)}")
            except:
                print("Model not loaded - this is expected without actual model file")

            # Get performance report
            report = optimizer.get_performance_report()
            print(f"Performance report: {json.dumps(report, indent=2, default=str)}")

            await asyncio.sleep(5)

        except Exception as e:
            print(f"Error: {e}")

        finally:
            # Cleanup
            await optimizer.cleanup()

    # Run example
    asyncio.run(main())