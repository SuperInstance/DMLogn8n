# Character AI System

A comprehensive Character AI System based on AgentDnDengine research that creates intelligent, personality-driven characters for D&D campaigns and role-playing games.

## Features

### 🧠 **Personality Engine**
- **Big Five personality traits model** (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism)
- **Character background traits** (ideals, bonds, flaws, personality traits)
- **Class-specific behavior patterns**
- **Racial cultural influences**
- **Dynamic personality evolution** based on experiences

### 🎯 **Strategic Decision Making**
- **Situation assessment engine**
- **Goal-oriented planning system**
- **Risk evaluation and decision matrix**
- **Learning from success/failure patterns**
- **Adaptation to party dynamics**

### ⚔️ **Class-Specific AI Modules**
- **Fighter**: Tactical positioning, protection instincts
- **Rogue**: Opportunity seeking, stealth optimization
- **Wizard**: Spell management, tactical casting
- **Cleric**: Healing prioritization, divine guidance
- **Barbarian**: Rage-fueled combat, primal instincts
- **Bard**: Musical inspiration, social manipulation
- **Druid**: Nature magic, wild shaping
- **Monk**: Martial arts mastery, ki manipulation
- **Paladin**: Divine combat, righteous smiting
- **Ranger**: Wilderness expertise, tracking
- **Sorcerer**: Innate magic, metamagic
- **Warlock**: Pact magic, patron powers

### 🧠 **Memory & Learning System**
- **Short-term memory** of current session
- **Long-term memory** of past experiences
- **Relationship tracking** with other characters
- **Environmental knowledge base**
- **Pattern recognition** for strategies

### 💬 **Dialogue Generation**
- **Character-appropriate speech patterns**
- **Context-aware responses**
- **Emotional expression in dialogue**
- **Strategic conversation** (intimidation, persuasion)
- **Party communication and coordination**

### 🔗 **Portal Integration**
- **Real-time synchronization** with DM Portal
- **WebSocket communication** for live updates
- **Event-driven architecture**
- **Multi-character support**

## Installation

```bash
cd /home/activeloguser/DMlogn8n/character-ai-system
pip install -r requirements.txt  # If requirements.txt exists
```

## Quick Start

### Basic Character AI

```python
from character_ai import CharacterAI, CharacterProfile, GameState

# Create a character
profile = CharacterProfile(
    name="Thorin Ironforge",
    character_class="Fighter",
    race="Dwarf",
    level=5,
    strength=16,
    constitution=15,
    ideals="I protect those who cannot protect themselves."
)

# Initialize AI
character_ai = CharacterAI(profile)

# Create game state
game_state = GameState(
    combat_status=True,
    allies=["Eldara", "Marcus"],
    enemies=["Goblin Shaman", "Hobgoblin"],
    resources={"health_ratio": 0.8}
)

# Update AI with current situation
character_ai.update_state(game_state)

# Make strategic decision
decision = character_ai.make_decision({"urgency": "high"})
print(f"Decision: {decision['action']}")

# Generate dialogue
dialogue = character_ai.generate_dialogue(
    context={"type": "combat", "enemies": ["Goblin"]},
    dialogue_type="combat"
)
print(f"Dialogue: {dialogue}")
```

### Portal Integration

```python
from character_ai.portal_integration import PortalIntegrationManager

# Create integration manager
integration_manager = PortalIntegrationManager()

# Add characters
for character_ai in character_ai_list:
    integration_manager.add_character_integration(character_ai)

# Connect to portal
await integration_manager.connect_all()

# Simulate portal events
await simulate_portal_events(integration_manager)
```

## Architecture

### Core Components

1. **CharacterAI**: Main orchestrator that coordinates all subsystems
2. **PersonalityEngine**: Manages personality traits and behavioral patterns
3. **StrategicDecisionMaker**: Handles situation assessment and decision logic
4. **MemorySystem**: Manages short-term and long-term memory
5. **DialogueGenerator**: Creates character-appropriate dialogue
6. **ClassAIFactory**: Creates class-specific AI modules

### Data Flow

```
Game State → CharacterAI → Personality Engine → Decision Context
                ↓                ↓                    ↓
          Memory System ← Dialogue Generator ← Class AI Module
                ↓                ↓                    ↓
           Learning ← Response Generation ← Action Execution
```

## Examples

### Running Examples

```bash
# Basic character AI demonstration
python examples/basic_character_ai_example.py

# Portal integration demonstration
python examples/portal_integration_example.py
```

### Running Tests

```bash
# Run all tests
python tests/test_character_ai.py

# Or use unittest
python -m unittest tests.test_character_ai -v
```

## Character Classes

All standard D&D 5th Edition classes are supported:

- **Martial Classes**: Fighter, Rogue, Barbarian, Monk, Ranger, Paladin
- **Spellcasting Classes**: Wizard, Cleric, Druid, Bard, Sorcerer, Warlock

Each class has unique behavioral patterns, tactical preferences, and special abilities.

## Personality System

The system uses the Big Five personality model:

1. **Openness**: Creative vs. Conventional
2. **Conscientiousness**: Organized vs. Disorganized
3. **Extraversion**: Outgoing vs. Reserved
4. **Agreeableness**: Cooperative vs. Competitive
5. **Neuroticism**: Sensitive vs. Confident

Personality traits influence:
- Decision-making patterns
- Dialogue style
- Risk tolerance
- Social behavior
- Learning preferences

## Memory Types

The system supports multiple memory types:

- **Combat**: Battle experiences and tactics
- **Social**: Interactions and relationships
- **Exploration**: Locations and discoveries
- **Items**: Equipment and artifacts
- **Skills**: Abilities and their effectiveness
- **Trauma**: Negative experiences
- **Success**: Positive achievements

## Portal Events

The system responds to various portal events:

- `state_update`: Game state changes
- `combat_start`: Combat initiation
- `combat_end`: Combat conclusion
- `dialogue_request`: Request for character dialogue
- `decision_request`: Request for strategic decisions
- `social_interaction`: Character interactions

## Configuration

### Personality Configuration

```python
# Adjust personality bias
personality_engine.current_personality.openness = 75
personality_engine.current_personality.conscientiousness = 60
```

### Class AI Configuration

```python
# Modify class preferences
fighter_ai.combat_preferences["protection_instinct"] = 0.9
wizard_ai.resource_management["spell_slot_efficiency"] = 0.8
```

### Memory Configuration

```python
# Adjust memory parameters
memory_system.memory_capacity = 1500
memory_system.decay_factor = 0.15
memory_system.consolidation_threshold = 0.8
```

## Advanced Features

### Pattern Recognition
The system learns from repeated situations and develops tactical patterns.

### Relationship Evolution
Character relationships evolve based on interactions and experiences.

### Personality Growth
Personality traits can change based on significant experiences.

### Strategic Learning
Characters learn which tactics work best in different situations.

## Performance Considerations

- Memory consolidation runs periodically to manage memory usage
- Pattern recognition is optimized for common D&D scenarios
- Dialogue generation uses templates for efficient response times
- Portal integration uses async/await for non-blocking operations

## Extensibility

### Adding New Classes

```python
from character_ai.class_modules.base_class_ai import BaseClassAI

class CustomClassAI(BaseClassAI):
    def _initialize_class_data(self):
        # Initialize class-specific data
        pass

    def get_action_recommendations(self, state):
        # Return class-specific recommendations
        pass

# Register the new class
ClassAIFactory.register_class_ai("CustomClass", CustomClassAI)
```

### Custom Dialogue Templates

```python
# Add custom dialogue templates
custom_template = DialogueTemplate(
    template_id="custom_greeting",
    dialogue_type=DialogueType.SOCIAL,
    emotional_tone=EmotionalTone.HAPPY,
    patterns=["Hello {name}, it's a fine day for adventure!"],
    contexts=["greeting", "outdoor"],
    personality_requirements={"extraversion": 0.6}
)

dialogue_generator.dialogue_templates.append(custom_template)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is part of the DMlogn8n system and follows the same licensing terms.

## Support

For issues, questions, or contributions, please refer to the main DMlogn8n project documentation.