"""
Simple test to verify Character AI System basic functionality
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_functionality():
    """Test basic functionality without complex imports"""
    try:
        # Test character profile creation
        from character_profile import CharacterProfile
        profile = CharacterProfile(
            name="Test Character",
            character_class="Fighter",
            race="Human",
            level=1
        )
        assert profile.name == "Test Character"
        assert profile.character_class == "Fighter"
        print("✅ CharacterProfile creation works")

        # Test personality engine
        from personality_engine import PersonalityEngine
        personality = PersonalityEngine(profile)
        assert personality.current_personality.openness >= 0
        assert personality.current_personality.openness <= 100
        print("✅ PersonalityEngine works")

        # Test decision maker
        from decision_maker import StrategicDecisionMaker
        decision_maker = StrategicDecisionMaker(profile)
        assert 0.1 <= decision_maker.risk_tolerance <= 0.9
        print("✅ StrategicDecisionMaker works")

        # Test memory system
        from memory_system import MemorySystem, MemoryType, MemoryImportance
        memory_system = MemorySystem(profile)
        memory_id = memory_system.add_memory(
            memory_type=MemoryType.COMBAT,
            content={"test": "data"},
            importance=MemoryImportance.MODERATE
        )
        assert memory_id is not None
        print("✅ MemorySystem works")

        # Test dialogue generator
        from dialogue_generator import DialogueGenerator
        dialogue_gen = DialogueGenerator(profile)
        dialogue = dialogue_gen.generate_dialogue(
            context={"type": "test"},
            speech_style={},
            mood="neutral",
            memory_context=[],
            dialogue_type="general"
        )
        assert isinstance(dialogue, str)
        assert len(dialogue) > 0
        print("✅ DialogueGenerator works")

        # Test class AI factory
        from class_modules import ClassAIFactory
        fighter_ai = ClassAIFactory.create_class_ai("Fighter", profile)
        assert fighter_ai is not None
        print("✅ ClassAIFactory works")

        # Test main CharacterAI class
        from character_ai import CharacterAI
        from game_state import GameState
        character_ai = CharacterAI(profile)

        game_state = GameState(
            combat_status=True,
            enemies=["Goblin"],
            resources={"health_ratio": 0.8}
        )

        character_ai.update_state(game_state)
        decision = character_ai.make_decision({"urgency": "moderate"})
        assert "action" in decision

        dialogue = character_ai.generate_dialogue(
            context={"type": "combat"},
            dialogue_type="combat"
        )
        assert isinstance(dialogue, str)
        assert len(dialogue) > 0

        print("✅ CharacterAI main class works")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run simple tests"""
    print("Character AI System - Simple Test")
    print("=" * 40)

    success = test_basic_functionality()

    print("=" * 40)
    if success:
        print("✅ All basic tests passed!")
        print("The Character AI System is working correctly.")
    else:
        print("❌ Some tests failed.")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)