"""
Basic Character AI Example
Demonstrates core functionality of the Character AI System
"""

import sys
import os

# Add the character-ai-system to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from character_ai import CharacterAI, CharacterProfile, GameState


def create_fighter_character():
    """Create a sample fighter character"""
    return CharacterProfile(
        name="Thorin Ironforge",
        character_class="Fighter",
        race="Dwarf",
        level=5,
        background="Soldier",
        strength=16,
        dexterity=12,
        constitution=15,
        intelligence=10,
        wisdom=12,
        charisma=10,
        ideals="I will protect those who cannot protect themselves.",
        bonds="My honor is my life.",
        flaws="I can be reckless when my friends are in danger.",
        personality_traits="I'm always polite and respectful, but I speak my mind directly."
    )


def create_wizard_character():
    """Create a sample wizard character"""
    return CharacterProfile(
        name="Eldara Moonwhisper",
        character_class="Wizard",
        race="High Elf",
        level=5,
        background="Sage",
        strength=8,
        dexterity=14,
        constitution=12,
        intelligence=18,
        wisdom=14,
        charisma=12,
        ideals="Knowledge is the path to power and enlightenment.",
        bonds="I owe my life to my mentor who taught me the arcane arts.",
        flaws="I can be overconfident in my magical abilities.",
        personality_traits="I use polysyllabic words that convey my intelligence."
    )


def create_sample_combat_state():
    """Create a sample combat game state"""
    return GameState(
        environment={
            "terrain": "dungeon_corridor",
            "lighting": "dim",
            "cover_available": True,
            "enemies_grouped": False,
            "enemy_spellcaster": True,
            "difficult_terrain": False
        },
        allies=["Eldara Moonwhisper", "Brother Marcus"],
        enemies=["Goblin Shaman", "Two Goblin Warriors", "Hobgoblin Captain"],
        current_objective="Defeat the goblin warband",
        combat_status=True,
        resources={
            "health_ratio": 0.8,
            "party_health": {
                "Eldara Moonwhisper": 0.6,
                "Brother Marcus": 0.9,
                "Thorin Ironforge": 0.8
            },
            "party_morale": 0.7,
            "roles_filled": ["tank", "damage_dealer", "support"]
        },
        time_info={
            "turn": 3,
            "round": 1,
            "time_of_day": "afternoon"
        }
    )


def create_sample_social_state():
    """Create a sample social game state"""
    return GameState(
        environment={
            "location": "tavern",
            "crowded": True,
            "npc_present": True,
            "social_gathering": True
        },
        allies=["Eldara Moonwhisper"],
        enemies=[],
        current_objective="Gather information about the missing villagers",
        combat_status=False,
        resources={
            "health_ratio": 1.0,
            "gold": 50
        },
        time_info={
            "time_of_day": "evening"
        }
    )


def demonstrate_personality_engine(character_ai):
    """Demonstrate personality engine functionality"""
    print("\n=== PERSONALITY ENGINE DEMONSTRATION ===")

    personality = character_ai.personality_engine
    current_traits = personality.current_personality

    print(f"Character: {character_ai.profile.name}")
    print(f"Big Five Personality Traits:")
    print(f"  Openness: {current_traits.openness:.1f}")
    print(f"  Conscientiousness: {current_traits.conscientiousness:.1f}")
    print(f"  Extraversion: {current_traits.extraversion:.1f}")
    print(f"  Agreeableness: {current_traits.agreeableness:.1f}")
    print(f"  Neuroticism: {current_traits.neuroticism:.1f}")

    primary_traits = current_traits.get_primary_traits()
    print(f"Primary Traits: {[f'{trait.value} ({score:.1f})' for trait, score in primary_traits]}")

    decision_bias = personality.get_decision_bias()
    print(f"Decision Bias: {decision_bias}")

    speech_style = personality.get_speech_style()
    print(f"Speech Style: {speech_style}")


def demonstrate_decision_making(character_ai, game_state):
    """Demonstrate strategic decision making"""
    print(f"\n=== DECISION MAKING DEMONSTRATION ===")
    print(f"Situation: {'Combat' if game_state.combat_status else 'Social'}")
    print(f"Allies: {game_state.allies}")
    print(f"Enemies: {game_state.enemies}")

    # Get class-specific recommendations
    class_recommendations = character_ai.class_ai.get_action_recommendations(game_state)
    print(f"Class Recommendations: {class_recommendations}")

    # Make a strategic decision
    context = {
        "urgency": "high" if game_state.combat_status else "low",
        "party_health": game_state.resources.get("party_health", {}),
        "enemy_threat": len(game_state.enemies) > len(game_state.allies)
    }

    decision = character_ai.make_decision(context)
    print(f"\nStrategic Decision:")
    print(f"  Action: {decision['action']}")
    print(f"  Confidence: {decision['confidence']:.2f}")
    print(f"  Reasoning: {decision['reasoning']}")
    print(f"  Risk Assessment: {decision['risk_assessment']:.2f}")
    print(f"  Strategic Value: {decision['strategic_value']:.2f}")


def demonstrate_dialogue_generation(character_ai, game_state):
    """Demonstrate dialogue generation"""
    print(f"\n=== DIALOGUE GENERATION DEMONSTRATION ===")

    # Generate different types of dialogue
    contexts = [
        {"type": "greeting", "other_character": "Barkeep"},
        {"type": "combat", "enemies": game_state.enemies, "combat_status": True},
        {"type": "social", "topic": "missing villagers", "social_situation": True},
        {"type": "strategic", "plan": "investigate the dark forest"}
    ]

    for i, context in enumerate(contexts, 1):
        dialogue_type = context.get("type", "general")
        dialogue = character_ai.generate_dialogue(
            context=context,
            dialogue_type=dialogue_type
        )
        print(f"\nDialogue {i} ({dialogue_type}): {dialogue}")


def demonstrate_memory_system(character_ai):
    """Demonstrate memory system functionality"""
    print(f"\n=== MEMORY SYSTEM DEMONSTRATION ===")

    memory_system = character_ai.memory_system

    # Add some memories
    memory_system.add_memory(
        memory_type=memory_system.MemoryType.COMBAT,
        content={
            "action": "fought_goblins",
            "location": "dark_forest",
            "outcome": "victory",
            "allies_present": ["Eldara", "Marcus"]
        },
        importance=memory_system.MemoryImportance.SIGNIFICANT,
        emotional_impact=0.7
    )

    memory_system.add_memory(
        memory_type=memory_system.MemoryType.SOCIAL,
        content={
            "person": "Barkeep",
            "location": "tavern",
            "conversation": "missing_villagers",
            "information_gained": "strange_lights_in_forest"
        },
        importance=memory_system.MemoryImportance.MODERATE,
        emotional_impact=0.4
    )

    # Update relationships
    memory_system.update_relationship("Eldara Moonwhisper", {
        "type": "combat_support",
        "outcome": "positive",
        "emotional_impact": 0.8
    })

    memory_system.update_relationship("Barkeep", {
        "type": "information_exchange",
        "outcome": "positive",
        "emotional_impact": 0.5
    })

    # Show memory summary
    memory_summary = memory_system.get_memory_summary()
    print(f"Memory Summary: {memory_summary}")

    # Show relationships
    for character_name, relationship in memory_system.relationships.items():
        print(f"Relationship with {character_name}:")
        print(f"  Score: {relationship.relationship_score:.2f}")
        print(f"  Trust Level: {relationship.trust_level:.2f}")
        print(f"  Type: {relationship.relationship_type}")


def demonstrate_learning(character_ai):
    """Demonstrate learning from outcomes"""
    print(f"\n=== LEARNING DEMONSTRATION ===")

    # Simulate some action outcomes
    outcomes = [
        {
            "action": "aggressive_attack",
            "success": True,
            "effectiveness": 0.8,
            "damage_dealt": 15,
            "damage_taken": 5,
            "combat": True,
            "enemy_type": "goblin"
        },
        {
            "action": "defensive_stance",
            "success": True,
            "effectiveness": 0.9,
            "damage_dealt": 3,
            "damage_taken": 2,
            "combat": True,
            "enemy_type": "hobgoblin"
        },
        {
            "action": "diplomatic_approach",
            "success": False,
            "effectiveness": 0.3,
            "combat": False,
            "social": True,
            "emotional_impact": -0.2
        }
    ]

    for outcome in outcomes:
        action = outcome["action"]
        character_ai.learn_from_outcome(action, outcome)
        print(f"Learned from '{action}': Success={outcome['success']}, Effectiveness={outcome['effectiveness']:.2f}")

    # Show decision patterns
    decision_patterns = character_ai.decision_maker.get_decision_patterns()
    print(f"\nDecision Patterns: {decision_patterns}")


def main():
    """Main demonstration function"""
    print("Character AI System - Basic Demonstration")
    print("=" * 50)

    # Create characters
    fighter = create_fighter_character()
    fighter_ai = CharacterAI(fighter)

    wizard = create_wizard_character()
    wizard_ai = CharacterAI(wizard)

    # Create game states
    combat_state = create_sample_combat_state()
    social_state = create_sample_social_state()

    # Demonstrate with fighter
    print("\n" + "=" * 20 + " FIGHTER DEMO " + "=" * 20)

    # Update fighter with combat state
    fighter_ai.update_state(combat_state)

    demonstrate_personality_engine(fighter_ai)
    demonstrate_decision_making(fighter_ai, combat_state)
    demonstrate_dialogue_generation(fighter_ai, combat_state)
    demonstrate_memory_system(fighter_ai)
    demonstrate_learning(fighter_ai)

    # Demonstrate with wizard in social situation
    print("\n" + "=" * 20 + " WIZARD DEMO " + "=" * 20)

    # Update wizard with social state
    wizard_ai.update_state(social_state)

    print(f"\nWizard Character: {wizard_ai.profile.name}")
    demonstrate_personality_engine(wizard_ai)
    demonstrate_dialogue_generation(wizard_ai, social_state)

    print(f"\n" + "=" * 50)
    print("Character AI System demonstration complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()