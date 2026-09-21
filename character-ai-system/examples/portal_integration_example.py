"""
Portal Integration Example
Demonstrates integration between Character AI and DM Portal
"""

import asyncio
import sys
import os

# Add the character-ai-system to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from character_ai import CharacterAI, CharacterProfile, GameState
from character_ai.portal_integration import PortalIntegrationManager


def create_sample_characters():
    """Create sample characters for demonstration"""
    characters = []

    # Fighter
    fighter_profile = CharacterProfile(
        name="Marcus Valerius",
        character_class="Fighter",
        race="Human",
        level=3,
        background="Soldier",
        strength=16,
        dexterity=12,
        constitution=14,
        intelligence=10,
        wisdom=12,
        charisma=10
    )
    characters.append(CharacterAI(fighter_profile))

    # Cleric
    cleric_profile = CharacterProfile(
        name="Sister Elara",
        character_class="Cleric",
        race="Human",
        level=3,
        background="Acolyte",
        strength=12,
        dexterity=10,
        constitution=14,
        intelligence=12,
        wisdom=16,
        charisma=14
    )
    characters.append(CharacterAI(cleric_profile))

    # Rogue
    rogue_profile = CharacterProfile(
        name="Shadow Swift",
        character_class="Rogue",
        race="Half-Elf",
        level=3,
        background="Criminal",
        strength=10,
        dexterity=18,
        constitution=12,
        intelligence=12,
        wisdom=14,
        charisma=12
    )
    characters.append(CharacterAI(rogue_profile))

    return characters


async def simulate_portal_events(integration_manager):
    """Simulate portal events to demonstrate integration"""
    print("\n=== Simulating Portal Events ===")

    # Simulate combat start
    print("1. Combat Start Event")
    combat_data = {
        "enemies": ["Goblin Shaman", "Two Goblin Warriors"],
        "environment": {
            "terrain": "forest_clearing",
            "lighting": "dim",
            "cover_available": True
        }
    }

    for integration in integration_manager.integrations.values():
        await integration._handle_combat_start(
            type('Event', (), {
                "event_type": "combat_start",
                "data": combat_data,
                "character_id": integration.character_ai.character_id
            })()
        )

    await asyncio.sleep(0.1)

    # Simulate state updates
    print("2. State Update Events")
    for integration in integration_manager.integrations.values():
        state_data = {
            "combat_status": True,
            "enemies": combat_data["enemies"],
            "allies": [ai.profile.name for ai in integration_manager.integrations.values()
                      if ai.character_id != integration.character_ai.character_id],
            "environment": combat_data["environment"],
            "resources": {
                "health_ratio": 0.8,
                "party_health": {
                    "Marcus Valerius": 0.9,
                    "Sister Elara": 0.7,
                    "Shadow Swift": 0.8
                }
            },
            "request_ai_action": True
        }

        await integration._handle_state_update(
            type('Event', (), {
                "event_type": "state_update",
                "data": state_data,
                "character_id": integration.character_ai.character_id
            })()
        )

    await asyncio.sleep(0.2)

    # Simulate dialogue requests
    print("3. Dialogue Request Events")
    dialogue_requests = [
        {"context": {"type": "greeting", "other_character": "Barkeep"}, "dialogue_type": "social"},
        {"context": {"type": "tactical", "situation": "enemies_approaching"}, "dialogue_type": "combat"},
        {"context": {"type": "planning", "objective": "defeat_goblins"}, "dialogue_type": "strategic"}
    ]

    for i, integration in enumerate(integration_manager.integrations.values()):
        if i < len(dialogue_requests):
            request = dialogue_requests[i]
            await integration._handle_dialogue_request(
                type('Event', (), {
                    "event_type": "dialogue_request",
                    "data": request,
                    "character_id": integration.character_ai.character_id
                })()
            )

    await asyncio.sleep(0.2)

    # Simulate decision requests
    print("4. Decision Request Events")
    for integration in integration_manager.integrations.values():
        decision_context = {
            "urgency": "high",
            "situation": "combat",
            "allies_in_danger": True,
            "enemies_weakened": False
        }

        await integration._handle_decision_request(
            type('Event', (), {
                "event_type": "decision_request",
                "data": {"context": decision_context},
                "character_id": integration.character_ai.character_id
            })()
        )

    await asyncio.sleep(0.2)

    # Simulate combat end
    print("5. Combat End Event")
    combat_outcomes = {
        "outcomes": {
            "Marcus Valerius": {"action": "melee_attack", "success": True, "damage_dealt": 12},
            "Sister Elara": {"action": "healing_spell", "success": True, "health_restored": 15},
            "Shadow Swift": {"action": "sneak_attack", "success": True, "damage_dealt": 18}
        }
    }

    for integration in integration_manager.integrations.values():
        await integration._handle_combat_end(
            type('Event', (), {
                "event_type": "combat_end",
                "data": combat_outcomes,
                "character_id": integration.character_ai.character_id
            })()
        )


async def demonstrate_character_synchronization(integration_manager):
    """Demonstrate character state synchronization"""
    print("\n=== Character State Synchronization ===")

    for character_id, integration in integration_manager.integrations.items():
        print(f"\nSynchronizing {integration.character_ai.profile.name}...")

        # Get character status
        status = integration.character_ai.get_character_status()
        print(f"  Current Mood: {status['current_mood']}")
        print(f"  Current Goals: {status['current_goals']}")
        print(f"  Personality Traits: {status['personality_traits']}")
        print(f"  Memory Summary: {status['memory_summary']}")

        # Sync with portal
        await integration.sync_character_state()
        print(f"  Synchronized with portal at {integration.last_sync_time}")


async def demonstrate_memory_integration(integration_manager):
    """Demonstrate memory system integration with portal"""
    print("\n=== Memory System Integration ===")

    for integration in integration_manager.integrations.values():
        # Add combat memory
        await integration.send_memory_update("combat", {
            "action": "fought_goblins",
            "location": "dark_forest",
            "outcome": "victory",
            "allies": [ai.profile.name for ai in integration_manager.integrations.values()
                      if ai.character_id != integration.character_ai.character_id]
        })

        # Add social memory
        await integration.send_memory_update("social", {
            "person": "Barkeep",
            "location": "tavern",
            "conversation": "goblin_attacks",
            "information": "goblins_seeing_dark_fortress"
        })

        # Add learning update
        await integration.send_learning_update({
            "pattern_recognized": "goblin_shaman_combat",
            "success_rate": 0.8,
            "recommended_action": "target_spellcaster_first"
        })

        print(f"  Sent memory and learning updates for {integration.character_ai.profile.name}")


async def demonstrate_social_interaction_integration(integration_manager):
    """Demonstrate social interaction through portal"""
    print("\n=== Social Interaction Integration ===")

    # Simulate character-to-character interaction
    characters = list(integration_manager.integrations.values())

    if len(characters) >= 2:
        # Marcus talks to Sister Elara
        marcus_integration = characters[0]
        elara_integration = characters[1]

        interaction_data = {
            "interaction_id": "marcus_to_elara_001",
            "other_character": "Sister Elara",
            "type": "conversation",
            "topic": "battle_strategy",
            "tone": "respectful",
            "outcome": "positive"
        }

        await marcus_integration._handle_social_interaction(
            type('Event', (), {
                "event_type": "social_interaction",
                "data": interaction_data,
                "character_id": marcus_integration.character_ai.character_id
            })()
        )

        print(f"  Marcus Valerius interacted with Sister Elara")
        print(f"  Response: {marcus_integration.character_ai.generate_dialogue(interaction_data, 'social')}")

        # Check relationship changes
        marcus_to_elara = marcus_integration.character_ai.memory_system.get_relationship_change("Sister Elara")
        if marcus_to_elara != {"status": "no_relationship"}:
            print(f"  Relationship change: Score={marcus_to_elara['relationship_score']:.2f}, Type={marcus_to_elara['relationship_type']}")


async def main():
    """Main demonstration function"""
    print("Portal Integration Demonstration")
    print("=" * 50)

    # Create integration manager
    integration_manager = PortalIntegrationManager()

    # Create and add characters
    characters = create_sample_characters()
    for character_ai in characters:
        integration = integration_manager.add_character_integration(character_ai)
        print(f"Added {character_ai.profile.name} to integration manager")

    print(f"\nTotal characters integrated: {len(integration_manager.integrations)}")

    try:
        # Connect all integrations (simulated)
        print("\n=== Connecting to Portal ===")
        connection_results = await integration_manager.connect_all()
        for character_id, success in connection_results.items():
            character_name = integration_manager.integrations[character_id].character_ai.profile.name
            status = "Connected" if success else "Failed"
            print(f"  {character_name}: {status}")

        # Demonstrate various integration features
        await simulate_portal_events(integration_manager)
        await demonstrate_character_synchronization(integration_manager)
        await demonstrate_memory_integration(integration_manager)
        await demonstrate_social_interaction_integration(integration_manager)

        print("\n=== Integration Demonstration Complete ===")

    except Exception as e:
        print(f"Error during demonstration: {e}")

    finally:
        # Clean up
        await integration_manager.disconnect_all()
        print("\nDisconnected all integrations")


if __name__ == "__main__":
    asyncio.run(main())