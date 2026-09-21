"""
Character AI System Demonstration
Shows all major features of the Character AI System
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from character_profile import CharacterProfile
from character_ai import CharacterAI
from game_state import GameState
from memory_system import MemoryType, MemoryImportance

def create_sample_party():
    """Create a sample D&D party"""
    party = []

    # Fighter - Tank/Leader
    fighter_profile = CharacterProfile(
        name="Marcus Valerius",
        character_class="Fighter",
        race="Human",
        level=5,
        background="Soldier",
        strength=18,
        dexterity=14,
        constitution=16,
        intelligence=12,
        wisdom=13,
        charisma=14,
        ideals="Honor and duty above all else.",
        bonds="My legion is my family.",
        flaws="I'm haunted by memories of war."
    )
    party.append(CharacterAI(fighter_profile))

    # Wizard - Arcane Expert
    wizard_profile = CharacterProfile(
        name="Elara Moonwhisper",
        character_class="Wizard",
        race="High Elf",
        level=5,
        background="Sage",
        strength=8,
        dexterity=14,
        constitution=12,
        intelligence=20,
        wisdom=16,
        charisma=12,
        ideals="Knowledge is the path to enlightenment.",
        bonds="My library contains secrets that could change the world.",
        flaws="I'm easily distracted by magical mysteries."
    )
    party.append(CharacterAI(wizard_profile))

    # Cleric - Healer/Support
    cleric_profile = CharacterProfile(
        name="Brother Theron",
        character_class="Cleric",
        race="Human",
        level=5,
        background="Acolyte",
        strength=14,
        dexterity=10,
        constitution=15,
        intelligence=12,
        wisdom=18,
        charisma=16,
        ideals="I must protect the innocent and punish evil.",
        bonds="I owe my life to the temple that raised me.",
        flaws="I judge others harshly based on their alignment."
    )
    party.append(CharacterAI(cleric_profile))

    # Rogue - Scout/Utility
    rogue_profile = CharacterProfile(
        name="Shadow Swift",
        character_class="Rogue",
        race="Half-Elf",
        level=5,
        background="Criminal",
        strength=12,
        dexterity=20,
        constitution=14,
        intelligence=14,
        wisdom=12,
        charisma=15,
        ideals="Freedom is the ultimate treasure.",
        bonds="I stole something of great value and must hide it.",
        flaws="I can't resist a risky gamble."
    )
    party.append(CharacterAI(rogue_profile))

    return party

def demonstrate_combat_scenario(party):
    """Demonstrate combat scenario"""
    print("\n" + "="*60)
    print("COMBAT SCENARIO: Goblin Ambush")
    print("="*60)

    # Create combat state
    combat_state = GameState(
        environment={
            "terrain": "forest_path",
            "lighting": "dim",
            "cover_available": True,
            "enemies_grouped": False,
            "difficult_terrain": True
        },
        allies=[ai.profile.name for ai in party],
        enemies=["Goblin Shaman", "4 Goblin Warriors", "Hobgoblin Captain"],
        current_objective="Defeat the goblin ambush",
        combat_status=True,
        resources={
            "health_ratio": 0.85,
            "party_health": {
                "Marcus Valerius": 0.9,
                "Elara Moonwhisper": 0.7,
                "Brother Theron": 0.8,
                "Shadow Swift": 0.85
            },
            "party_morale": 0.8
        }
    )

    # Update all characters with combat state
    for character_ai in party:
        character_ai.update_state(combat_state)

    # Show initial reactions
    print("\nInitial Combat Reactions:")
    print("-" * 40)
    for character_ai in party:
        dialogue = character_ai.generate_dialogue(
            context={"combat_start": True, "enemies": combat_state.enemies},
            dialogue_type="combat"
        )
        print(f"{character_ai.profile.name}: {dialogue}")

    # Show tactical decisions
    print("\nTactical Decisions:")
    print("-" * 40)
    for character_ai in party:
        decision = character_ai.make_decision({
            "urgency": "high",
            "combat": True,
            "party_health": combat_state.resources["party_health"],
            "enemies_weakened": False
        })
        print(f"{character_ai.profile.name}: {decision['action']} (Confidence: {decision['confidence']:.2f})")

    # Show class-specific thinking
    print("\nClass-Specific Analysis:")
    print("-" * 40)
    for character_ai in party:
        evaluation = character_ai.class_ai.evaluate_situation(combat_state)
        print(f"{character_ai.profile.name} ({character_ai.profile.character_class}):")
        for key, value in evaluation.items():
            print(f"  {key}: {value:.2f}")
        print()

def demonstrate_social_scenario(party):
    """Demonstrate social scenario"""
    print("\n" + "="*60)
    print("SOCIAL SCENARIO: Meeting at the Tavern")
    print("="*60)

    # Create social state
    social_state = GameState(
        environment={
            "location": "tavern",
            "crowded": True,
            "npc_present": True,
            "social_gathering": True
        },
        allies=[ai.profile.name for ai in party],
        enemies=[],
        current_objective="Gather information about missing villagers",
        combat_status=False,
        resources={
            "health_ratio": 1.0,
            "gold": 50
        }
    )

    # Update all characters with social state
    for character_ai in party:
        character_ai.update_state(social_state)

    # Social interactions with tavern keeper
    print("\nInteracting with Tavern Keeper:")
    print("-" * 40)
    for character_ai in party:
        if character_ai.profile.charisma > 14:  # Most charismatic characters lead
            dialogue = character_ai.generate_dialogue(
                context={
                    "type": "information_gathering",
                    "topic": "missing_villagers",
                    "npc": "tavern_keeper"
                },
                dialogue_type="social"
            )
            print(f"{character_ai.profile.name}: {dialogue}")
            break

    # Show party planning
    print("\nParty Planning:")
    print("-" * 40)
    for character_ai in party:
        if character_ai.profile.intelligence > 14:  # Smart characters contribute to planning
            dialogue = character_ai.generate_dialogue(
                context={
                    "type": "planning",
                    "objective": "investigate_missing_villagers",
                    "situation": "mysterious_disappearances"
                },
                dialogue_type="strategic"
            )
            print(f"{character_ai.profile.name}: {dialogue}")

def demonstrate_memory_and_learning(party):
    """Demonstrate memory and learning systems"""
    print("\n" + "="*60)
    print("MEMORY AND LEARNING DEMONSTRATION")
    print("="*60)

    fighter_ai = party[0]  # Marcus

    # Add combat memories
    fighter_ai.memory_system.add_memory(
        memory_type=MemoryType.COMBAT,
        content={
            "action": "fought_goblins",
            "location": "dark_forest",
            "outcome": "victory",
            "allies_present": ["Elara", "Theron", "Shadow"],
            "enemies_defeated": 6
        },
        importance=MemoryImportance.SIGNIFICANT,
        emotional_impact=0.8
    )

    fighter_ai.memory_system.add_memory(
        memory_type=MemoryType.SOCIAL,
        content={
            "person": "Tavern Keeper",
            "location": "Rusty Flagon Tavern",
            "conversation": "missing_villagers",
            "information_gained": "strange_lights_in_forest"
        },
        importance=MemoryImportance.MODERATE,
        emotional_impact=0.5
    )

    # Update relationships
    fighter_ai.memory_system.update_relationship("Elara Moonwhisper", {
        "type": "combat_support",
        "outcome": "positive",
        "emotional_impact": 0.8
    })

    fighter_ai.memory_system.update_relationship("Tavern Keeper", {
        "type": "information_exchange",
        "outcome": "positive",
        "emotional_impact": 0.6
    })

    # Show memory summary
    memory_summary = fighter_ai.memory_system.get_memory_summary()
    print(f"Memory Summary: {memory_summary}")

    # Show relationships
    print("\nRelationships:")
    print("-" * 40)
    for character_name, relationship in fighter_ai.memory_system.relationships.items():
        print(f"{character_name}:")
        print(f"  Relationship Score: {relationship.relationship_score:.2f}")
        print(f"  Trust Level: {relationship.trust_level:.2f}")
        print(f"  Type: {relationship.relationship_type}")

    # Learning from outcomes
    fighter_ai.learn_from_outcome("shield_bash", {
        "success": True,
        "effectiveness": 0.8,
        "damage_dealt": 12,
        "damage_taken": 3,
        "combat": True,
        "enemy_type": "goblin_warrior"
    })

    # Show decision patterns
    decision_patterns = fighter_ai.decision_maker.get_decision_patterns()
    print(f"\nDecision Patterns: {decision_patterns}")

def demonstrate_personalities(party):
    """Demonstrate personality differences"""
    print("\n" + "="*60)
    print("PERSONALITY PROFILES")
    print("="*60)

    for character_ai in party:
        personality = character_ai.personality_engine.current_personality
        primary_traits = personality.get_primary_traits()
        decision_bias = character_ai.personality_engine.get_decision_bias()
        speech_style = character_ai.personality_engine.get_speech_style()

        print(f"\n{character_ai.profile.name} ({character_ai.profile.character_class}):")
        print(f"  Big Five Traits: O:{personality.openness:.0f} C:{personality.conscientiousness:.0f} E:{personality.extraversion:.0f} A:{personality.agreeableness:.0f} N:{personality.neuroticism:.0f}")
        print(f"  Primary Traits: {[f'{trait.value} ({score:.0f})' for trait, score in primary_traits]}")
        print(f"  Decision Bias: {decision_bias['approach']} / {decision_bias['planning']}")
        print(f"  Speech Style: {speech_style['vocabulary']} vocabulary, {speech_style['tone']} tone")

def main():
    """Main demonstration"""
    print("Character AI System - Complete Demonstration")
    print("Based on AgentDnDengine research")
    print("="*60)

    # Create party
    party = create_sample_party()
    print(f"Created party of {len(party)} adventurers")

    # Show personalities
    demonstrate_personalities(party)

    # Combat scenario
    demonstrate_combat_scenario(party)

    # Social scenario
    demonstrate_social_scenario(party)

    # Memory and learning
    demonstrate_memory_and_learning(party)

    # Final status
    print("\n" + "="*60)
    print("SYSTEM STATUS")
    print("="*60)

    for character_ai in party:
        status = character_ai.get_character_status()
        print(f"\n{character_ai.profile.name}:")
        print(f"  Current Mood: {status['current_mood']}")
        print(f"  Active Traits: {status['personality_traits']}")
        print(f"  Memory Count: {status['memory_summary']['long_term_count']}")
        print(f"  Class Status: {list(status['class_ai_status'].keys())}")

    print("\n" + "="*60)
    print("✅ Character AI System demonstration complete!")
    print("All systems operational and integrated.")
    print("="*60)

if __name__ == "__main__":
    main()