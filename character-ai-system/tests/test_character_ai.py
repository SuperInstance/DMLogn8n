"""
Test suite for Character AI System
"""

import unittest
import sys
import os

# Add the character-ai-system to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from character_ai import CharacterAI, CharacterProfile, GameState
from character_ai.personality_engine import PersonalityEngine, BigFivePersonality
from character_ai.decision_maker import StrategicDecisionMaker, DecisionType
from character_ai.memory_system import MemorySystem, MemoryType, MemoryImportance
from character_ai.dialogue_generator import DialogueGenerator, DialogueType
from character_ai.class_modules import ClassAIFactory


class TestCharacterProfile(unittest.TestCase):
    """Test CharacterProfile creation and validation"""

    def setUp(self):
        self.profile = CharacterProfile(
            name="Test Character",
            character_class="Fighter",
            race="Human",
            level=1,
            strength=14,
            dexterity=12,
            constitution=13,
            intelligence=10,
            wisdom=12,
            charisma=8
        )

    def test_profile_creation(self):
        """Test basic profile creation"""
        self.assertEqual(self.profile.name, "Test Character")
        self.assertEqual(self.profile.character_class, "Fighter")
        self.assertEqual(self.profile.race, "Human")
        self.assertEqual(self.profile.level, 1)

    def test_ability_scores(self):
        """Test ability score assignment"""
        self.assertEqual(self.profile.strength, 14)
        self.assertEqual(self.profile.intelligence, 10)


class TestPersonalityEngine(unittest.TestCase):
    """Test PersonalityEngine functionality"""

    def setUp(self):
        self.profile = CharacterProfile(
            name="Test Fighter",
            character_class="Fighter",
            race="Human",
            level=5
        )
        self.personality_engine = PersonalityEngine(self.profile)

    def test_personality_generation(self):
        """Test Big Five personality generation"""
        personality = self.personality_engine.current_personality
        self.assertIsInstance(personality, BigFivePersonality)
        self.assertGreaterEqual(personality.openness, 0)
        self.assertLessEqual(personality.openness, 100)

    def test_decision_bias(self):
        """Test decision bias calculation"""
        bias = self.personality_engine.get_decision_bias()
        self.assertIn("approach", bias)
        self.assertIn("planning", bias)
        self.assertIn("social", bias)
        self.assertIn("conflict", bias)
        self.assertIn("risk", bias)

    def test_speech_style(self):
        """Test speech style generation"""
        style = self.personality_engine.get_speech_style()
        self.assertIn("vocabulary", style)
        self.assertIn("pace", style)
        self.assertIn("tone", style)
        self.assertIn("structure", style)
        self.assertIn("emotional_level", style)

    def test_mood_changes(self):
        """Test mood changes based on situation"""
        combat_mood = self.personality_engine.get_combat_mood()
        peace_mood = self.personality_engine.get_peacetime_mood()
        self.assertIsInstance(combat_mood, str)
        self.assertIsInstance(peace_mood, str)


class TestStrategicDecisionMaker(unittest.TestCase):
    """Test StrategicDecisionMaker functionality"""

    def setUp(self):
        self.profile = CharacterProfile(
            name="Test Rogue",
            character_class="Rogue",
            race="Half-Elf",
            level=3
        )
        self.decision_maker = StrategicDecisionMaker(self.profile)

    def test_risk_tolerance_calculation(self):
        """Test risk tolerance calculation"""
        risk_tolerance = self.decision_maker.risk_tolerance
        self.assertGreaterEqual(risk_tolerance, 0.1)
        self.assertLessEqual(risk_tolerance, 0.9)

    def test_situation_assessment(self):
        """Test situation assessment"""
        game_state = GameState(
            combat_status=True,
            allies=["Ally1"],
            enemies=["Enemy1", "Enemy2"],
            resources={"health_ratio": 0.7}
        )
        self.decision_maker.update_state(game_state)
        assessment = self.decision_maker.current_assessment
        self.assertGreater(assessment.threat_level, 0)
        self.assertGreaterEqual(assessment.threat_level, 0)
        self.assertLessEqual(assessment.threat_level, 1)

    def test_decision_making(self):
        """Test decision making process"""
        game_state = GameState(
            combat_status=True,
            allies=["Ally1"],
            enemies=["Enemy1"],
            resources={"health_ratio": 0.8}
        )
        self.decision_maker.update_state(game_state)

        context = {
            "personality_bias": {"approach": "creative_experimental"},
            "class_recommendations": ["stealth_attack"],
            "current_state": game_state
        }

        decision = self.decision_maker.make_decision(context)
        self.assertIn("action", decision)
        self.assertIn("confidence", decision)
        self.assertIn("reasoning", decision)


class TestMemorySystem(unittest.TestCase):
    """Test MemorySystem functionality"""

    def setUp(self):
        self.profile = CharacterProfile(
            name="Test Wizard",
            character_class="Wizard",
            race="High Elf",
            level=4
        )
        self.memory_system = MemorySystem(self.profile)

    def test_memory_addition(self):
        """Test adding memories"""
        memory_id = self.memory_system.add_memory(
            memory_type=MemoryType.COMBAT,
            content={"action": "cast_fireball", "damage": 25},
            importance=MemoryImportance.SIGNIFICANT,
            emotional_impact=0.8
        )
        self.assertIsNotNone(memory_id)
        self.assertGreater(len(self.memory_system.long_term_memory), 0)

    def test_memory_retrieval(self):
        """Test memory retrieval"""
        # Add a memory
        self.memory_system.add_memory(
            memory_type=MemoryType.SOCIAL,
            content={"person": "Barkeep", "location": "tavern"},
            importance=MemoryImportance.MODERATE
        )

        # Retrieve relevant memories
        context = {
            "type": "social",
            "entities": ["Barkeep"],
            "location": "tavern"
        }
        relevant_memories = self.memory_system.get_relevant_memories(context)
        self.assertGreater(len(relevant_memories), 0)

    def test_relationship_tracking(self):
        """Test relationship tracking"""
        # Add relationship
        self.memory_system.update_relationship("Test Ally", {
            "type": "conversation",
            "outcome": "positive",
            "emotional_impact": 0.7
        })

        # Check relationship
        relationship_change = self.memory_system.get_relationship_change("Test Ally")
        self.assertNotEqual(relationship_change["status"], "no_relationship")
        self.assertGreater(relationship_change["relationship_score"], 0)

    def test_outcome_recording(self):
        """Test recording action outcomes"""
        self.memory_system.record_outcome("cast_fireball", {
            "success": True,
            "effectiveness": 0.9,
            "damage": 28,
            "enemies_affected": 3
        })

        # Check that memory was added
        combat_memories = [m for m in self.memory_system.long_term_memory if m.type == MemoryType.SUCCESS]
        self.assertGreater(len(combat_memories), 0)


class TestDialogueGenerator(unittest.TestCase):
    """Test DialogueGenerator functionality"""

    def setUp(self):
        self.profile = CharacterProfile(
            name="Test Bard",
            character_class="Bard",
            race="Half-Elf",
            level=3,
            charisma=16
        )
        self.dialogue_generator = DialogueGenerator(self.profile)

    def test_dialogue_generation(self):
        """Test basic dialogue generation"""
        context = {
            "type": "greeting",
            "other_character": "Stranger"
        }
        dialogue = self.dialogue_generator.generate_dialogue(
            context=context,
            speech_style={"tone": "friendly"},
            mood="happy",
            memory_context=[],
            dialogue_type="social"
        )
        self.assertIsInstance(dialogue, str)
        self.assertGreater(len(dialogue), 0)

    def test_combat_dialogue(self):
        """Test combat dialogue generation"""
        context = {
            "combat_status": True,
            "enemies": ["Goblin"],
            "target": "Goblin"
        }
        dialogue = self.dialogue_generator.generate_dialogue(
            context=context,
            speech_style={},
            mood="confident",
            memory_context=[],
            dialogue_type="combat"
        )
        self.assertIsInstance(dialogue, str)
        self.assertGreater(len(dialogue), 0)

    def test_response_generation(self):
        """Test response generation"""
        input_dialogue = "Hello there, traveler!"
        context = {"social_situation": True}
        response = self.dialogue_generator.generate_response(input_dialogue, context)
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)


class TestClassModules(unittest.TestCase):
    """Test class-specific AI modules"""

    def test_class_ai_factory(self):
        """Test ClassAIFactory functionality"""
        supported_classes = ClassAIFactory.get_supported_classes()
        self.assertIn("Fighter", supported_classes)
        self.assertIn("Wizard", supported_classes)
        self.assertIn("Rogue", supported_classes)
        self.assertIn("Cleric", supported_classes)

    def test_fighter_ai(self):
        """Test Fighter AI module"""
        profile = CharacterProfile(
            name="Test Fighter",
            character_class="Fighter",
            race="Human",
            level=3
        )
        fighter_ai = ClassAIFactory.create_class_ai("Fighter", profile)

        # Test recommendations
        state = GameState(
            combat_status=True,
            enemies=["Goblin"],
            resources={"health_ratio": 0.8}
        )
        recommendations = fighter_ai.get_action_recommendations(state)
        self.assertIsInstance(recommendations, list)

    def test_wizard_ai(self):
        """Test Wizard AI module"""
        profile = CharacterProfile(
            name="Test Wizard",
            character_class="Wizard",
            race="High Elf",
            level=3
        )
        wizard_ai = ClassAIFactory.create_class_ai("Wizard", profile)

        # Test situation evaluation
        state = GameState(
            combat_status=True,
            enemies=["Orc"],
            resources={"health_ratio": 0.6}
        )
        evaluation = wizard_ai.evaluate_situation(state)
        self.assertIn("spell_optimization", evaluation)
        self.assertIn("area_effect_opportunity", evaluation)


class TestCharacterAI(unittest.TestCase):
    """Test main CharacterAI class"""

    def setUp(self):
        self.profile = CharacterProfile(
            name="Test Character",
            character_class="Fighter",
            race="Human",
            level=3
        )
        self.character_ai = CharacterAI(self.profile)

    def test_character_ai_creation(self):
        """Test CharacterAI initialization"""
        self.assertIsNotNone(self.character_ai.personality_engine)
        self.assertIsNotNone(self.character_ai.decision_maker)
        self.assertIsNotNone(self.character_ai.memory_system)
        self.assertIsNotNone(self.character_ai.dialogue_generator)
        self.assertIsNotNone(self.character_ai.class_ai)

    def test_state_updates(self):
        """Test game state updates"""
        game_state = GameState(
            combat_status=True,
            allies=["Ally1"],
            enemies=["Enemy1"],
            resources={"health_ratio": 0.7}
        )
        self.character_ai.update_state(game_state)
        self.assertEqual(self.character_ai.current_state.combat_status, True)

    def test_decision_making_integration(self):
        """Test integrated decision making"""
        game_state = GameState(
            combat_status=True,
            enemies=["Goblin"],
            resources={"health_ratio": 0.8}
        )
        self.character_ai.update_state(game_state)

        decision = self.character_ai.make_decision({
            "urgency": "moderate",
            "combat": True
        })
        self.assertIn("action", decision)
        self.assertIn("confidence", decision)

    def test_dialogue_integration(self):
        """Test integrated dialogue generation"""
        dialogue = self.character_ai.generate_dialogue(
            context={"type": "greeting"},
            dialogue_type="social"
        )
        self.assertIsInstance(dialogue, str)
        self.assertGreater(len(dialogue), 0)

    def test_learning_integration(self):
        """Test integrated learning system"""
        outcome = {
            "success": True,
            "effectiveness": 0.8,
            "damage_dealt": 15
        }
        self.character_ai.learn_from_outcome("melee_attack", outcome)

        # Check that learning occurred
        memory_summary = self.character_ai.memory_system.get_memory_summary()
        self.assertGreater(memory_summary["long_term_count"], 0)

    def test_social_interaction(self):
        """Test social interaction handling"""
        interaction = {
            "other_character": "Test NPC",
            "type": "conversation",
            "outcome": "positive"
        }
        response = self.character_ai.handle_social_interaction(interaction)
        self.assertIn("dialogue", response)
        self.assertIn("personality_response", response)


def run_tests():
    """Run all tests"""
    # Create test suite
    test_classes = [
        TestCharacterProfile,
        TestPersonalityEngine,
        TestStrategicDecisionMaker,
        TestMemorySystem,
        TestDialogueGenerator,
        TestClassModules,
        TestCharacterAI
    ]

    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return success status
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Character AI System Test Suite")
    print("=" * 50)
    success = run_tests()
    print("=" * 50)
    if success:
        print("All tests passed!")
    else:
        print("Some tests failed.")
    sys.exit(0 if success else 1)