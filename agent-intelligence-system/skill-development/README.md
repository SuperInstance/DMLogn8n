# Progressive Skill Development System for DMlogn8n

A comprehensive skill development framework where AI agents develop expertise through experience, featuring skill trees, experience tracking, performance analytics, and seamless D&D 5e integration.

## 🎯 Overview

This system implements a sophisticated skill progression mechanism that transforms static D&D mechanics into dynamic, evolving character capabilities. AI agents develop mastery through practice, learn from failures, and unlock new abilities as they gain experience.

## ✨ Key Features

### 🌟 Core Features
- **Skill Specialization Framework**: 75+ skills across 5 categories
- **Progressive Mastery System**: 5 mastery levels with unique abilities
- **Dynamic Experience Calculation**: Multipliers based on success, difficulty, streaks, and context
- **Performance Analytics**: Comprehensive effectiveness tracking and recommendations
- **Skill Tree Visualization**: Multiple formats (HTML, SVG, Mermaid, ASCII)
- **D&D 5e Integration**: Seamless conversion between progression and traditional mechanics

### 📊 Skill Categories
- **Combat Skills** (15 skills): Weapon mastery, targeting, positioning, timing
- **Social Skills** (15 skills): Persuasion, deception, intimidation, empathy
- **Exploration Skills** (15 skills): Perception, investigation, survival, stealth
- **Magic Skills** (15 skills): Spell selection, mana management, combos, crafting
- **Strategic Skills** (15 skills): Planning, tactics, resource management, leadership

## 🏗️ Architecture

```
skill-development/
├── core/                    # Core skill system
│   ├── skill.py            # Main Skill class with progression
│   └── skill_progression.py # Multi-skill coordination
├── calculators/            # Experience calculations
│   └── experience_calculator.py # Advanced XP system
├── systems/               # Unlock and progression systems
│   └── skill_unlock_system.py # Skill trees and prerequisites
├── analyzers/             # Performance analysis
│   └── performance_analyzer.py # Effectiveness tracking
├── visualization/         # Tree visualization
│   └── skill_tree_visualizer.py # Multiple viz formats
├── categories/           # Skill implementations
│   ├── combat_skills.py  # Combat skill definitions
│   ├── social_skills.py  # Social skill definitions
│   ├── exploration_skills.py # Exploration skill definitions
│   ├── magic_skills.py   # Magic skill definitions
│   └── strategic_skills.py # Strategic skill definitions
├── integration/          # D&D 5e integration
│   └── dnd5e_integration.py # Rule system conversion
├── examples/             # Usage examples
│   ├── basic_usage.py    # Fundamental usage
│   ├── advanced_features.py # Complex scenarios
│   └── integration_examples.py # D&D integration
└── tests/               # Unit tests
    └── test_skill_system.py # Core system tests
```

## 🚀 Quick Start

### Basic Usage

```python
from skill_development import (
    Skill, SkillProgression, ExperienceCalculator,
    PerformanceAnalyzer, DND5EIntegration
)
from categories.combat_skills import CombatSkills

# Create progression system for an agent
progression = SkillProgression("agent_001")

# Add a combat skill
weapon_mastery = CombatSkills.create_weapon_mastery()
progression.add_skill(weapon_mastery)

# Record skill usage
result = progression.record_skill_usage(
    skill_name="Weapon Mastery",
    success=True,
    difficulty=0.7,
    context="Combat with goblin",
    xp_gained=25
)

print(f"Gained {result['total_xp']} XP!")
print(f"Skill level: {weapon_mastery.current_level.name}")
```

### D&D 5e Integration

```python
from integration.dnd5e_integration import DND5EIntegration, DND5ECharacter, DND5EAbility

# Create D&D character from progression
character = DND5EIntegration.create_character_from_progression(
    progression=progression,
    name="Aldric",
    level=5,
    character_class="Fighter",
    ability_scores={DND5EAbility.STRENGTH: 16, ...}
)

# Perform skill check
result = DND5EIntegration.roll_skill_check(
    skill=weapon_mastery,
    character=character,
    advantage=True
)

print(f"Roll: {result['total']} vs DC {result['dc']}")
print(f"Success: {result['total'] >= result['dc']}")
```

### Performance Analysis

```python
from analyzers.performance_analyzer import PerformanceAnalyzer

analyzer = PerformanceAnalyzer()
metrics = analyzer.analyze_skill_performance(weapon_mastery, progression)

print(f"Success Rate: {metrics.success_rate:.1f}%")
print(f"Effectiveness Score: {metrics.effectiveness_score:.1f}/100")
print(f"Performance Tier: {metrics.performance_tier.name}")

# Get improvement recommendations
effectiveness = analyzer.analyze_skill_effectiveness(weapon_mastery, progression)
print(f"Recommendations: {effectiveness.recommended_focus}")
```

### Skill Tree Visualization

```python
from visualization.skill_tree_visualizer import SkillTreeVisualizer, VisualizationFormat

# Create skill tree
tree = SkillTree("Combat Mastery", "Combat skill development tree")
# ... add nodes and connections ...

# Generate visualization
visualizer = SkillTreeVisualizer()
viz_data = visualizer.visualize_tree(tree, progression)

# Export to file
visualizer.export_visualization(viz_data, "skill_tree.html")
```

## 📈 Skill Progression System

### Mastery Levels
1. **Novice** (0-25 XP): Basic understanding
   - Base abilities only
   - Standard success rates

2. **Apprentice** (25-100 XP): Reliable usage
   - 1.1x XP multiplier
   - Unlock basic special abilities

3. **Journeyman** (100-400 XP): Skilled practitioner
   - 1.25x XP multiplier
   - 1 bonus die
   - Advanced abilities unlocked

4. **Expert** (400-1600 XP): Master level
   - 1.5x XP multiplier
   - 2 bonus dice
   - Expert abilities unlocked

5. **Master** (1600+ XP): True mastery
   - 2.0x XP multiplier
   - 3 bonus dice
   - Master abilities unlocked

### Experience Calculation

The system uses a sophisticated XP calculation with multiple modifiers:

```python
# Base XP = 10-50 (based on difficulty)
# Success bonus = +50%
# Critical success = +100%
# Mastery multiplier = 1.0x - 2.0x
# Streak bonuses = +20% to +100%
# Time bonuses = +10% (early/late)
# Category bonuses = +20% to +30%
# Synergy bonuses = Variable
```

### Performance Metrics

- **Success Rate**: Percentage of successful skill uses
- **Effectiveness Score**: 0-100 overall performance rating
- **Usage Frequency**: Uses per day
- **Trend Analysis**: Improving, stable, or declining
- **Contextual Performance**: Performance in different situations

## 🎮 D&D 5e Integration Features

### Character Creation
- Convert skill progression to D&D character sheets
- Automatic proficiency assignment based on mastery
- Ability score integration
- Class and background compatibility

### Skill Checks
- Progressive bonuses added to traditional rolls
- Advantage/disadvantage support
- Critical success/failure handling
- Difficulty calculation based on skill level

### Combat Integration
- Attack bonuses from combat skills
- Damage bonuses from weapon mastery
- AC bonuses from defensive skills
- Special ability integration

### Encounter Balancing
- Party skill assessment
- Encounter difficulty calculation
- Recommended adjustments based on party capabilities

## 🎯 Skill Examples

### Combat Skills
```python
# Weapon Mastery - General weapon proficiency
weapon_mastery.add_experience(200)  # Journeyman level
print(weapon_mastery.current_level.bonus_dice)  # 1 bonus die

# Critical Strike - Landing critical hits
critical_strike.calculate_success_chance(0.8)  # Higher chance with mastery
```

### Social Skills
```python
# Persuasion - Convincing others
persuasion.record_usage(True, 0.6, "Negotiated with merchant", 30)
print(persuasion.success_rate)  # Track improvement

# Deception - Lying and misdirection
deception.calculate_success_chance(0.7, {"Performance": performance_skill})
```

### Magic Skills
```python
# Spell Selection - Choosing optimal spells
spell_selection.add_experience(150)  # Better spell choices

# Mana Management - Resource efficiency
mana_efficiency = mana_management.current_level.multiplier  # 1.5x at Expert
```

## 🧪 Testing

Run the test suite to verify functionality:

```bash
cd tests/
python -m unittest test_skill_system.py
```

Run examples to see the system in action:

```bash
# Basic usage examples
cd examples/
python basic_usage.py

# Advanced features
python advanced_features.py

# D&D integration
python integration_examples.py
```

## 🔧 Configuration

### Custom Skill Creation

```python
from core.skill import Skill, SkillCategory, SynergyBonus, SpecialAbility

custom_skill = Skill(
    name="Custom Skill",
    category=SkillCategory.COMBAT,
    description="A custom skill for specific use case",
    base_difficulty=0.6,
    synergies=[
        SynergyBonus(
            skill_name="Related Skill",
            bonus_type="success_chance",
            bonus_value=0.15,
            description="Synergy description"
        )
    ],
    special_abilities=[
        SpecialAbility(
            name="Special Ability",
            description="Ability description",
            required_level=MasteryLevel.EXPERT,
            effect_type="active",
            effect_value="Effect details"
        )
    ]
)
```

### Experience Calculator Customization

```python
from calculators.experience_calculator import ExperienceCalculator, XPModifier

calculator = ExperienceCalculator()

# Add custom modifier
calculator.add_modifier(XPModifier(
    name="Custom Bonus",
    type=XPModifierType.SUCCESS_BONUS,
    value=1.3,
    description="30% bonus for special condition",
    condition="special_condition == True"
))
```

## 📊 Analytics and Reporting

### Development Statistics
```python
stats = progression.get_development_stats()
print(f"Total skills: {stats.total_skills_learned}")
print(f"Master skills: {stats.master_level_skills}")
print(f"Development rate: {stats.development_rate:.1f} XP/day")
```

### Performance Trends
```python
trends = analyzer.get_performance_trends(skill, days=30)
print(f"Success rate trend: {trends['success_rate_trend']}")
print(f"XP gain trend: {trends['xp_gain_trend']}")
```

### Skill Comparison
```python
comparison = analyzer.compare_skills(skill1, skill2)
print(f"Winner: {comparison.winner}")
print(f"Analysis: {comparison.analysis_summary}")
```

## 🔮 Advanced Features

### Skill Trees and Unlocking
- Complex prerequisite systems
- Multiple unlock conditions
- Visual tree representations
- Progress tracking

### Synergy System
- Cross-skill bonuses
- Dynamic bonus calculation
- Context-dependent effects

### Performance Analysis
- Trend detection
- Improvement recommendations
- Weakness identification
- Strength highlighting

### Visualization
- Interactive HTML trees
- Static SVG diagrams
- Mermaid flowcharts
- ASCII text trees

## 🎯 Use Cases

### AI Agent Development
- Character progression simulation
- Dynamic difficulty adjustment
- Personalized learning paths
- Performance-based adaptation

### D&D Campaign Management
- Character development tracking
- Encounter balancing
- Party composition analysis
- Skill progression planning

### Game Design
- Skill system prototyping
- Balance testing
- Progression curve analysis
- Player engagement metrics

## 📚 API Reference

### Core Classes
- `Skill`: Individual skill with progression tracking
- `SkillProgression`: Multi-skill coordination
- `ExperienceCalculator`: Advanced XP calculation
- `PerformanceAnalyzer`: Effectiveness analysis
- `SkillTreeVisualizer`: Tree visualization
- `DND5EIntegration`: D&D 5e conversion layer

### Key Methods
- `skill.add_experience(xp)`: Add XP and check for level ups
- `skill.record_usage(...)`: Record skill usage with XP
- `skill.calculate_success_chance(...)`: Calculate success probability
- `progression.record_skill_usage(...)`: Record usage with context
- `analyzer.analyze_skill_performance(...)`: Analyze effectiveness
- `visualizer.visualize_tree(...)`: Generate visualization

## 🤝 Contributing

This system is designed to be extensible and modular. Key areas for enhancement:

- Additional skill categories
- New visualization formats
- Enhanced D&D integration
- Performance optimization
- Analytics expansion

## 📄 License

This system is part of the DMlogn8n project and follows the same licensing terms.

---

**The Progressive Skill Development System transforms static D&D mechanics into dynamic, evolving character capabilities, creating engaging and measurable progression for AI agents and players alike.** 🚀