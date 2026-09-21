# Hierarchical Memory Architecture for DMlogn8n

A sophisticated, multi-tier memory system designed for AI characters in the DMlogn8n D&D agent arena. This system implements a neuroscience-inspired hierarchical memory architecture with intelligent consolidation, capacity management, and vector-based retrieval.

## Overview

The memory system is based on research from AgentDnDengine3.txt and implements:

- **Level-based capacity scaling** - Memory capacity grows with character level
- **Three-tier memory architecture** - Working, Episodic, and Semantic memory
- **Intelligent consolidation** - Automatic pattern extraction and knowledge transfer
- **Forgetting mechanisms** - Smart capacity management with protection rules
- **Vector-based retrieval** - ChromaDB integration for semantic similarity search
- **Real-time dashboard** - Visual monitoring and management interface

## Architecture

### Memory Tiers

#### Working Memory (Level 1-4: 5 items, Level 5-10: 10 items, Level 11-16: 15 items, Level 17-20: 25 items)
- Fast access, limited capacity
- Activation-based retention with decay
- Current thoughts and immediate context
- Volatile, requires constant refresh

#### Episodic Memory (Level 1-4: 50 total, Level 5-10: 200 total, Level 11-16: 500 total, Level 17-20: 1000 total)
- Specific events and experiences
- Rich temporal and spatial context
- "What, where, when" information
- Source material for consolidation

#### Semantic Memory (30% of total capacity)
- General knowledge and concepts
- Patterns and rules extracted from experiences
- Persistent, high-confidence knowledge
- Foundation for decision making

### Level Specifications

| Level Range | Total Capacity | Working Memory | Consolidation Threshold |
|-------------|----------------|----------------|------------------------|
| 1-4         | 50 memories     | 5 items        | 100                    |
| 5-10        | 200 memories    | 10 items       | 200                    |
| 11-16       | 500 memories    | 15 items       | 400                    |
| 17-20       | 1000 memories   | 25 items       | 800                    |

## Components

### Core Components

- **MemoryManager** - Central orchestration and unified interface
- **MemoryBase** - Abstract base classes and data structures
- **ForgettingMechanism** - Intelligent capacity management

### Memory Types

- **WorkingMemory** - Fast, volatile current thoughts
- **EpisodicMemory** - Rich event-based memories
- **SemanticMemory** - Consolidated knowledge and patterns

### Processing Systems

- **ConsolidationEngine** - Pattern extraction and memory transfer
- **VectorStore** - ChromaDB-based semantic retrieval
- **MemoryDashboard** - Real-time visualization and monitoring

### Integration Layer

- **CharacterAIIntegration** - Bridge to existing character AI system
- Legacy system compatibility and migration tools

## Quick Start

### Basic Usage

```python
from memory_architecture.integration.character_ai_integration import CharacterAIIntegration

# Initialize memory system for a character
memory_system = CharacterAIIntegration(
    character_id="dragon_slayer_01",
    character_level=5
)

# Process an experience
result = memory_system.process_character_experience(
    experience_description="I fought a mighty dragon in the mountains and barely escaped with my life!",
    emotional_valence=-0.3,  # Slightly negative (dangerous)
    importance=8.5,
    location="Dragon Peak Mountains",
    participants=["Red Dragon", "Wizard Companion"]
)

# Get character context for decision making
context = memory_system.get_character_context()
print(f"Current context: {context['summary']}")

# Retrieve relevant memories
relevant_memories = memory_system.retrieve_relevant_memories(
    query="dragon combat strategies",
    max_results=5
)

# Trigger character reflection
insights = memory_system.trigger_character_reflection()
print(f"Generated {insights['insights_generated']} insights")
```

### Advanced Usage

```python
# Level up character
memory_system.update_character_level(new_level=8)

# Process dialogue
memory_system.process_character_dialogue(
    dialogue="Beware the dragon in the northern peaks!",
    speaker="Village Elder",
    emotional_tone="warning",
    importance=7.0
)

# Access memory dashboard
dashboard_html = memory_system.get_character_memory_dashboard()

# Get system statistics
status = memory_system.get_memory_system_status()
print(f"Memory system status: {status}")
```

## Memory Management

### Adding Memories

```python
# Episodic memory (default)
memory = memory_system.memory_manager.add_memory(
    content="Explored an ancient dungeon",
    memory_type=MemoryType.EPISODIC,
    importance=7.0,
    location="Forgotten Dungeon",
    participants=["Party Members"]
)

# Semantic memory
semantic_memory = memory_system.memory_manager.add_memory(
    content="Dungeons often contain traps and treasures",
    memory_type=MemoryType.SEMANTIC,
    importance=8.0,
    confidence=0.9
)
```

### Memory Retrieval

```python
# General search
results = memory_system.memory_manager.retrieve_memories(
    query="dungeon exploration",
    max_results=10,
    memory_types=[MemoryType.EPISODIC, MemoryType.SEMANTIC]
)

# Context retrieval
context = memory_system.memory_manager.get_context_memories(
    max_working=5,
    max_episodic=10,
    max_semantic=5
)
```

### Consolidation

```python
# Manual consolidation cycle
results = memory_system.memory_manager.run_consolidation_cycle()

# Character reflection
insights = memory_system.memory_manager.reflect_on_experiences()
```

## Configuration

### Environment Setup

```bash
# Install dependencies
pip install chromadb sentence-transformers numpy

# Set up data directory
mkdir -p ./data/memory_system
```

### Character Configuration

```python
# Initialize with custom settings
memory_system = CharacterAIIntegration(
    character_id="unique_character_id",
    character_level=1,
    data_directory="./custom_data_path",
    enable_vector_store=True,
    enable_dashboard=True
)

# Configure forgetting strategy
from memory_architecture.core.forgetting_mechanism import ImportanceBasedForgetting
memory_system.memory_manager.forgetting_mechanism.set_strategy(
    ImportanceBasedForgetting()
)
```

## Integration with Existing Systems

### Legacy System Migration

The system includes automatic migration from the existing DMlogn8n memory system:

```python
# Enable migration during initialization
memory_system = CharacterAIIntegration(
    character_id="existing_character",
    enable_migration=True
)

# Check migration status
status = memory_system.get_memory_system_status()
migration_status = status["migration_status"]
print(f"Migrated {migration_status['stats']['migrated_memories']} memories")
```

### API Integration

```python
# Example Flask endpoint
from flask import Flask, request, jsonify

app = Flask(__name__)
memory_system = CharacterAIIntegration("demo_character")

@app.route('/api/experience', methods=['POST'])
def add_experience():
    data = request.json
    result = memory_system.process_character_experience(
        experience_description=data['description'],
        emotional_valence=data.get('emotional_valence', 0.0),
        importance=data.get('importance', 5.0),
        location=data.get('location', ''),
        participants=data.get('participants', [])
    )
    return jsonify(result)

@app.route('/api/context', methods=['GET'])
def get_context():
    context = memory_system.get_character_context()
    return jsonify(context)
```

## Dashboard

Access the memory dashboard through:

```python
# Generate HTML dashboard
dashboard_html = memory_system.get_character_memory_dashboard()

# Save to file or serve via web server
with open("memory_dashboard.html", "w") as f:
    f.write(dashboard_html)
```

The dashboard provides:
- Real-time memory usage statistics
- Consolidation and forgetting activity
- Memory performance metrics
- Recent activity logs
- System insights and recommendations

## Testing

Run comprehensive tests:

```bash
cd memory_architecture
python -m pytest tests/ -v
```

Test coverage includes:
- Memory creation and management
- Working memory capacity and activation
- Episodic memory similarity and consolidation
- Semantic memory validation and application
- Consolidation engine functionality
- Forgetting mechanism strategies
- Character AI integration
- Performance and reliability

## Performance Considerations

### Vector Store Configuration

```python
# Optimize for production
memory_system = CharacterAIIntegration(
    character_id="production_character",
    enable_vector_store=True
)

# Configure vector store for performance
memory_system.memory_manager.vector_store.optimize_index()
```

### Memory Management

```python
# Configure forgetting for performance
from memory_architecture.core.forgetting_mechanism import AdaptiveForgetting
memory_system.memory_manager.forgetting_mechanism.set_strategy(
    AdaptiveForgetting()
)

# Enable auto-processes
memory_system.memory_manager.auto_consolidation = True
memory_system.memory_manager.auto_forgetting = True
```

## Research Basis

This implementation is based on research from AgentDnDengine3.txt, incorporating:

- **Neuroscience principles** - Hippocampal-neocortical memory transfer
- **Cognitive psychology** - Working memory limitations and chunking
- **Machine learning** - Vector embeddings and similarity search
- **Game design** - Progressive difficulty and character development

## Contributing

1. Follow the existing code structure and patterns
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure backward compatibility with existing integrations

## License

This memory architecture system is part of the DMlogn8n project and follows the same licensing terms.

## Support

For questions, issues, or contributions:
- Check the test files for usage examples
- Review the documentation in each module
- Examine the integration layer for compatibility patterns