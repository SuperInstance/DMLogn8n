#!/usr/bin/env python3
"""
Hierarchical Memory Architecture Demo
====================================

Demonstration of the memory system capabilities.
"""

import sys
import os
import tempfile
import shutil
from datetime import datetime, timedelta

# Add the memory architecture to path
sys.path.insert(0, os.path.dirname(__file__))

from integration.character_ai_integration import CharacterAIIntegration
from core.memory_base import MemoryType


def main():
    """Run a comprehensive demo of the memory system"""
    print("🧠 Hierarchical Memory Architecture Demo")
    print("=" * 50)

    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    print(f"📁 Using temporary directory: {temp_dir}")

    try:
        # Initialize memory system for a character
        print("\n1. Initializing Memory System")
        print("-" * 30)

        character_id = "demo_character"
        character_level = 5

        memory_system = CharacterAIIntegration(
            character_id=character_id,
            character_level=character_level,
            data_directory=temp_dir,
            enable_vector_store=False,  # Disable for demo simplicity
            enable_dashboard=False
        )

        print(f"✅ Initialized memory system for '{character_id}' at level {character_level}")

        # Show initial capacity
        capacity = memory_system.memory_manager.capacity_config
        print(f"📊 Memory Capacity: {capacity.total_memories} total memories")
        print(f"   Working Memory: {capacity.working_memory_capacity} items")
        print(f"   Consolidation Threshold: {capacity.consolidation_threshold}")

        # Process some experiences
        print("\n2. Processing Character Experiences")
        print("-" * 40)

        experiences = [
            {
                "description": "I fought a fierce dragon in the mountains and barely escaped with my life!",
                "emotional_valence": -0.3,
                "importance": 8.5,
                "location": "Dragon Peak Mountains",
                "participants": ["Red Dragon", "Wizard Companion"]
            },
            {
                "description": "Visited the local village and bought healing potions from the alchemist.",
                "emotional_valence": 0.2,
                "importance": 5.0,
                "location": "Village of Havenwood",
                "participants": ["Alchemist", "Village Elder"]
            },
            {
                "description": "Explored an ancient dungeon and discovered a treasure chest filled with gold coins!",
                "emotional_valence": 0.8,
                "importance": 9.0,
                "location": "Forgotten Dungeon",
                "participants": ["Party Members"]
            },
            {
                "description": "Learned that dragons are vulnerable to ice magic from an old tome.",
                "emotional_valence": 0.1,
                "importance": 7.0,
                "location": "Library",
                "participants": ["Scholar"]
            }
        ]

        for i, exp in enumerate(experiences, 1):
            result = memory_system.process_character_experience(**exp)
            print(f"   {i}. {exp['description'][:50]}...")
            print(f"      Memory ID: {result['memory_id']}")
            print(f"      Importance: {result['importance']}")

        # Process some dialogue
        print("\n3. Processing Character Dialogue")
        print("-" * 35)

        dialogues = [
            {
                "dialogue": "Beware the dragon in the northern peaks, young adventurer!",
                "speaker": "Village Elder",
                "emotional_tone": "warning",
                "importance": 7.0
            },
            {
                "dialogue": "Ice magic is particularly effective against fire-breathing creatures.",
                "speaker": "Wizard Companion",
                "emotional_tone": "informative",
                "importance": 6.5
            }
        ]

        for i, dialogue in enumerate(dialogues, 1):
            result = memory_system.process_character_dialogue(**dialogue)
            print(f"   {i}. {dialogue['speaker']}: \"{dialogue['dialogue']}\"")
            print(f"      Memory ID: {result['memory_id']}")

        # Retrieve relevant memories
        print("\n4. Memory Retrieval")
        print("-" * 20)

        queries = [
            "dragon combat",
            "village interactions",
            "dungeon exploration",
            "magic knowledge"
        ]

        for query in queries:
            results = memory_system.retrieve_relevant_memories(query, max_results=3)
            print(f"\n🔍 Query: '{query}'")
            if results:
                for i, result in enumerate(results[:2], 1):
                    print(f"   {i}. {result['content'][:60]}...")
                    print(f"      Relevance: {result['relevance']:.2f} | Importance: {result['importance']}")
            else:
                print("   No relevant memories found")

        # Get character context
        print("\n5. Character Context")
        print("-" * 18)

        context = memory_system.get_character_context()
        print(f"📝 Context Summary: {context['summary']}")

        print(f"\n🧠 Working Memory ({len(context['memories']['working'])} items):")
        for memory in context['memories']['working'][:2]:
            print(f"   - {memory['content'][:50]}...")

        print(f"\n📚 Episodic Memory ({len(context['memories']['episodic'])} recent):")
        for memory in context['memories']['episodic'][:2]:
            print(f"   - {memory['content'][:50]}...")

        print(f"\n🎯 Semantic Memory ({len(context['memories']['semantic'])} concepts):")
        for memory in context['memories']['semantic']:
            print(f"   - {memory['content'][:50]}...")

        # Trigger character reflection
        print("\n6. Character Reflection")
        print("-" * 22)

        reflection_results = memory_system.trigger_character_reflection()
        print(f"✅ Reflection completed")
        print(f"   Insights generated: {reflection_results['insights_generated']}")
        print(f"   Importance updates: {reflection_results.get('importance_updates', 0)}")

        if reflection_results.get('insights'):
            print("\n💡 Character Insights:")
            for insight in reflection_results['insights'][:2]:
                print(f"   - {insight['description']}")

        # Level up the character
        print("\n7. Character Level Up")
        print("-" * 21)

        old_level = character_level
        new_level = 8

        level_result = memory_system.update_character_level(new_level)
        print(f"⬆️  Leveled up from {old_level} to {new_level}")
        print(f"📊 New memory capacity: {level_result['new_capacity']} total memories")
        print(f"🧠 New working memory capacity: {memory_system.memory_manager.working_memory.capacity} items")

        # Show system statistics
        print("\n8. System Statistics")
        print("-" * 20)

        stats = memory_system.get_memory_system_status()
        memory_stats = stats['memory_stats']

        print(f"📈 Total memories created: {memory_stats['system_info']['total_memories_created']}")
        print(f"💾 Current memory counts:")
        for mem_type, count in memory_stats['memory_counts'].items():
            print(f"   - {mem_type}: {count}")

        print(f"🔄 Consolidation stats:")
        consolidation_stats = memory_stats['consolidation_stats']
        print(f"   - Total consolidations: {consolidation_stats['total_consolidations']}")
        print(f"   - Success rate: {consolidation_stats['success_rate']:.1%}")

        # Manual consolidation
        print("\n9. Manual Consolidation")
        print("-" * 23)

        consolidation_results = memory_system.memory_manager.run_consolidation_cycle()
        print(f"🔄 Consolidation cycle completed")
        print(f"   Memories consolidated: {consolidation_results['total_consolidated']}")
        print(f"   Success: {consolidation_results['success']}")

        # Test forgetting mechanism
        print("\n10. Forgetting Mechanism")
        print("-" * 25)

        forgetting_results = memory_system.memory_manager.run_forgetting_cycle()
        print(f"🗑️  Forgetting cycle completed")
        print(f"   Memories forgotten: {len(forgetting_results.get('forgotten_memories', []))}")
        print(f"   Protected memories: {len(forgetting_results.get('protection_applied', []))}")

        print("\n✨ Demo completed successfully!")
        print(f"🧠 The character '{character_id}' now has a rich, hierarchical memory system")
        print(f"   that learns from experiences and grows with level advancement.")

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"\n🧹 Cleaned up temporary directory: {temp_dir}")


if __name__ == "__main__":
    main()