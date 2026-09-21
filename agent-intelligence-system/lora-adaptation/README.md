# LoRA-based Strategic Adaptation System for D&D Agents

A sophisticated system that enables D&D agents to learn and adapt through personalized LoRA fine-tuning, strategic pattern analysis, and continuous improvement from gameplay experiences.

## Overview

The LoRA-based Strategic Adaptation System implements advanced machine learning techniques to create truly intelligent D&D agents that evolve and improve over time. Agents develop unique personalities, learn from their experiences, and make increasingly sophisticated strategic decisions.

## Key Features

### 🧠 Adaptive Intelligence
- **Personalized LoRA Models**: Each agent has their own fine-tuned model that evolves based on experiences
- **Strategic Pattern Recognition**: Automatically identifies successful strategies from gameplay data
- **Continuous Learning**: Agents improve with every session through experience collection and analysis

### 🎯 Character Personalization
- **Class-Specific Adaptation**: Models adapt based on character class (Wizard, Fighter, Rogue, etc.)
- **Personality Development**: Agents develop unique personalities based on their traits and experiences
- **Playstyle Evolution**: Agents refine their playstyle (aggressive, defensive, strategic, social) over time

### ⚡ Performance Optimization
- **Efficient Resource Management**: Optimizes memory usage, GPU utilization, and model caching
- **Batch Processing**: Handles multiple operations efficiently
- **Smart Caching**: LRU cache for models with automatic eviction

### 📊 Analytics & Monitoring
- **Comprehensive Logging**: Detailed error handling and performance tracking
- **Health Monitoring**: Real-time system health checks and resource monitoring
- **Performance Analytics**: Detailed metrics on response generation and training effectiveness

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                LoRA Adaptation System                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐    │
│  │   LoRA      │  │  Strategic   │  │  Personalized   │    │
│  │  Trainer    │  │  Pattern     │  │   Model         │    │
│  │             │  │  Analyzer    │  │   Manager       │    │
│  └─────────────┘  └──────────────┘  └─────────────────┘    │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐    │
│  │ Adaptive    │  │  Error       │  │ Performance     │    │
│  │ Response    │  │  Handling    │  │   Optimizer     │    │
│  │ Generator   │  │  System      │  │                 │    │
│  └─────────────┘  └──────────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. LoRA Trainer (`agent_dnd-lora-trainer.py`)
- **Purpose**: Manages LoRA fine-tuning for individual agents
- **Key Features**:
  - Character-specific LoRA configurations
  - Experience collection and formatting
  - Efficient training with limited resources
  - Model caching and optimization

### 2. Strategic Pattern Analyzer (`strategic_pattern_analyzer.py`)
- **Purpose**: Extracts and analyzes strategic patterns from gameplay
- **Key Features**:
  - Success/failure pattern identification
  - Strategic recommendations generation
  - Learning opportunity detection
  - Pattern confidence scoring

### 3. Personalized Model Manager (`personalized_model_manager.py`)
- **Purpose**: Manages agent lifecycles and model coordination
- **Key Features**:
  - Agent registration and profiling
  - Experience tracking and learning
  - Resource management and cleanup
  - Performance monitoring

### 4. Adaptive Response Generator (`adaptive_response_generator.py`)
- **Purpose**: Generates contextual, in-character responses
- **Key Features**:
  - Style-adaptive responses (aggressive, defensive, strategic, social)
  - Context-aware prompt enhancement
  - Strategic consideration integration
  - Response quality metrics

### 5. Error Handling System (`error_handling.py`)
- **Purpose**: Comprehensive error handling and recovery
- **Key Features**:
  - Structured error logging and categorization
  - Automatic recovery mechanisms
  - Resource monitoring and health checks
  - Performance tracking

### 6. Performance Optimizer (`performance_optimizer.py`)
- **Purpose**: Optimizes system performance and resource usage
- **Key Features**:
  - Memory and GPU optimization
  - Intelligent model caching
  - Batch processing
  - Resource usage monitoring

## Installation

### Prerequisites
- Python 3.8+
- PyTorch with CUDA support (recommended)
- Sufficient RAM (8GB+ recommended)
- GPU with 6GB+ VRAM (optional but recommended)

### Setup

1. **Clone the repository**:
```bash
cd /home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/
```

2. **Install dependencies**:
```bash
pip install torch transformers peft datasets scikit-learn pandas psutil numpy
```

3. **Create necessary directories**:
```bash
mkdir -p data/agents models/adapters models/cache logs backups
```

## Quick Start

### Basic Usage

```python
import asyncio
from personalized_model_manager import PersonalizedModelManager
from adaptive_response_generator import AdaptiveResponseGenerator, ResponseContext

async def main():
    # Initialize the system
    model_manager = PersonalizedModelManager()
    response_generator = AdaptiveResponseGenerator(model_manager)

    # Register an agent
    character_info = {
        "name": "Aria Swiftblade",
        "class": "Rogue",
        "level": 8,
        "skills": ["stealth", "perception", "deception"],
        "traits": ["cunning", "agile", "cautious"]
    }

    agent_id = "rogue_001"
    await model_manager.register_agent(agent_id, character_info)

    # Create a context for response generation
    context = ResponseContext(
        agent_id=agent_id,
        current_situation="You discover a trapped treasure chest in an ancient dungeon",
        game_state={"health": 85, "position": "dungeon_chamber"},
        available_actions=["disarm_trap", "force_open", "search_for_mechanism", "leave_it"],
        nearby_characters=["Gandalf the Wizard", "Thorin the Fighter"],
        environment={"lighting": "dim", "terrain": "stone", "traps": "detected"},
        urgency_level=3,
        stakes="medium"
    )

    # Generate a response
    response = await response_generator.generate_response(context)
    print(f"Agent Response: {response.response_text}")
    print(f"Response Style: {response.response_style.value}")
    print(f"Confidence: {response.confidence:.2f}")

asyncio.run(main())
```

### Training and Learning

```python
from agent_dnd_lora_trainer import CharacterExperience

# Add experiences for learning
experience = CharacterExperience(
    agent_id=agent_id,
    session_id="dungeon_crawl_001",
    timestamp=datetime.now(),
    situation="Encountered a group of goblins guarding treasure",
    action="Used stealth to bypass them and disarm the trap on the treasure chest",
    outcome="Successfully acquired treasure without combat",
    success_score=0.95,
    reward=150.0,
    context={"location": "dungeon", "trap_type": "poison_dart"},
    skills_used=["stealth", "perception", "dexterity"],
    character_class="Rogue",
    level=8,
    emotional_valence=0.8,
    strategic_importance=0.9
)

await model_manager.add_experience(experience)

# Trigger training when enough data is collected
await model_manager.train_agent_model(agent_id)
```

## Configuration

### Resource Limits

```python
from performance_optimizer import ResourceLimits

limits = ResourceLimits(
    max_memory_mb=4096,      # Maximum memory usage
    max_gpu_memory_mb=6144,  # Maximum GPU memory
    max_cpu_percent=80,      # Maximum CPU usage
    max_disk_usage_percent=90,  # Maximum disk usage
    max_concurrent_operations=5   # Maximum concurrent operations
)

resource_manager = ResourceManager(limits)
```

### LoRA Configuration

```python
from peft import LoraConfig

lora_config = LoraConfig(
    task_type="CAUSAL_LM",
    inference_mode=False,
    r=8,                    # Rank (higher = more parameters)
    lora_alpha=32,         # Scaling factor
    lora_dropout=0.1,      # Dropout rate
    target_modules=["q_proj", "v_proj", "k_proj"],  # Target modules
    bias="none"
)
```

## Performance Optimization

### Memory Optimization

```python
# Enable automatic memory optimization
await resource_manager.optimize_system()

# Manual memory cleanup
await resource_manager._optimize_memory_usage()
await resource_manager._optimize_gpu_memory()
```

### Caching

```python
# Configure model cache
from performance_optimizer import ModelCache

cache = ModelCache(
    max_size=5,              # Maximum number of cached models
    max_memory_mb=2048       # Maximum memory for cache
)

# Use cached models
model = await get_cached_model(
    model_key="agent_001_adapter",
    load_function=load_model_function,
    size_estimate_mb=500
)
```

## Monitoring and Analytics

### Performance Metrics

```python
# Get performance analysis
analysis = resource_manager.get_performance_analysis(
    operation_name="response_generation",
    hours=24
)

print(f"Average duration: {analysis['duration_stats']['avg_ms']:.2f}ms")
print(f"Success rate: {analysis.get('success_rate', 0):.1%}")
```

### System Health

```python
from error_handling import HealthChecker

health_checker = HealthChecker()
health_status = await health_checker.get_system_health()

print(f"Overall status: {health_status['overall_status']}")
print(f"Component health: {health_status['components']}")
```

### Error Analysis

```python
from error_handling import global_logger

error_summary = global_logger.get_error_summary(hours=24)
print(f"Total errors: {error_summary['total_errors']}")
print(f"Error categories: {error_summary['error_categories']}")
```

## Testing

Run the comprehensive integration test suite:

```bash
python integration_tests.py
```

This will test all components and generate a detailed report in `test_results.json`.

## Best Practices

### 1. Resource Management
- Monitor memory usage regularly
- Use appropriate batch sizes for training
- Clear cache when not needed
- Set realistic resource limits

### 2. Model Training
- Collect diverse experiences for better learning
- Train periodically rather than continuously
- Monitor training loss and performance metrics
- Use appropriate LoRA rank for your use case

### 3. Response Generation
- Provide rich context for better responses
- Use appropriate response styles for situations
- Monitor response quality and provide feedback
- Cache frequently used models

### 4. Error Handling
- Use the safe_execute decorator for critical operations
- Monitor error logs regularly
- Implement appropriate fallback mechanisms
- Set up alerts for critical errors

## Troubleshooting

### Common Issues

**Memory Issues**:
```
Error: CUDA out of memory
Solution: Reduce batch size, clear GPU cache, use smaller models
```

**Training Issues**:
```
Error: Insufficient training data
Solution: Collect more experiences before training
```

**Model Loading Issues**:
```
Error: Model not found
Solution: Check model paths, re-initialize adapters
```

### Performance Issues

**Slow Response Generation**:
- Check GPU utilization
- Optimize model caching
- Reduce model complexity
- Enable performance optimization

**High Memory Usage**:
- Clear model cache
- Reduce batch sizes
- Enable memory optimization
- Monitor resource usage

## API Reference

### PersonalizedModelManager

```python
class PersonalizedModelManager:
    async def register_agent(agent_id: str, character_info: Dict) -> bool
    async def add_experience(experience: CharacterExperience) -> bool
    async def generate_response(agent_id: str, prompt: str) -> str
    async def train_agent_model(agent_id: str, force: bool = False) -> bool
    async def cleanup_agent(agent_id: str, backup: bool = True) -> bool
    def get_agent_summary(agent_id: str) -> Dict[str, Any]
    def get_system_status() -> Dict[str, Any]
```

### AdaptiveResponseGenerator

```python
class AdaptiveResponseGenerator:
    async def generate_response(context: ResponseContext,
                             force_style: Optional[ResponseStyle] = None,
                             max_length: int = 150) -> GeneratedResponse
    async def provide_feedback(response_id: str, agent_id: str,
                             success_score: float, feedback_text: str) -> bool
    def get_response_analytics(agent_id: str, days: int = 7) -> Dict[str, Any]
```

### ResourceManager

```python
class ResourceManager:
    async def monitor_resources() -> Dict[str, Any]
    async def optimize_system() -> Dict[str, Any]
    def get_performance_analysis(operation_name: str = None,
                               hours: int = 24) -> Dict[str, Any]
    def get_resource_efficiency_report() -> Dict[str, Any]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Run the integration test suite
5. Submit a pull request

## License

This project is part of the DMlogn8n system. See the main project license for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the error logs
3. Run the integration tests
4. Check system health monitoring

## Changelog

### Version 1.0.0
- Initial implementation of LoRA-based adaptation system
- Personalized model fine-tuning
- Strategic pattern analysis
- Adaptive response generation
- Comprehensive error handling
- Performance optimization
- Resource management
- Integration testing suite