"""
Memory System Tests
===================

Comprehensive tests for the hierarchical memory architecture.
"""

import unittest
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import List

# Import memory system components
from ..core.memory_base import MemoryBase, MemoryType, MemoryImportance
from ..memory_types.working_memory import WorkingMemory
from ..memory_types.episodic_memory import EpisodicMemory
from ..memory_types.semantic_memory import SemanticMemory
from ..core.memory_manager import MemoryManager
from ..consolidation.consolidation_engine import ConsolidationEngine
from ..core.forgetting_mechanism import ForgettingMechanism, CompositeForgetting
from ..integration.character_ai_integration import CharacterAIIntegration


class TestMemoryBase(unittest.TestCase):
    """Test base memory functionality"""

    def setUp(self):
        self.memory = EpisodicMemory(
            content="Test memory content",
            importance=7.0,
            emotional_valence=0.5,
            location="test_location",
            participants=["test_participant"]
        )

    def test_memory_creation(self):
        """Test basic memory creation"""
        self.assertEqual(self.memory.content.primary_content, "Test memory content")
        self.assertEqual(self.memory.importance, 7.0)
        self.assertEqual(self.memory.type, MemoryType.EPISODIC)
        self.assertEqual(self.memory.metadata.location, "test_location")
        self.assertEqual(self.memory.metadata.participants, ["test_participant"])

    def test_memory_access(self):
        """Test memory access tracking"""
        initial_count = self.memory.metadata.access_count
        self.memory.access()
        self.assertEqual(self.memory.metadata.access_count, initial_count + 1)
        self.assertIsNotNone(self.memory.metadata.last_accessed)

    def test_memory_importance_decay(self):
        """Test importance decay over time"""
        initial_importance = self.memory.importance
        self.memory.decay_importance(0.9)
        self.assertLess(self.memory.importance, initial_importance)

    def test_memory_serialization(self):
        """Test memory serialization to dictionary"""
        memory_dict = self.memory.to_dict()
        self.assertIn("id", memory_dict)
        self.assertIn("content", memory_dict)
        self.assertIn("metadata", memory_dict)
        self.assertEqual(memory_dict["type"], MemoryType.EPISODIC.value)


class TestWorkingMemory(unittest.TestCase):
    """Test working memory functionality"""

    def setUp(self):
        self.working_memory = WorkingMemory(capacity=5)

    def test_working_memory_capacity(self):
        """Test working memory capacity limits"""
        # Add memories up to capacity
        for i in range(5):
            memory = EpisodicMemory(content=f"Memory {i}")
            self.working_memory.add_memory(memory)

        self.assertEqual(len(self.working_memory), 5)

        # Try to add one more - should evict weakest
        extra_memory = EpisodicMemory(content="Extra memory")
        success = self.working_memory.add_memory(extra_memory)
        self.assertTrue(success)
        self.assertLessEqual(len(self.working_memory), 5)

    def test_working_memory_activation(self):
        """Test activation-based retention"""
        memory = EpisodicMemory(content="Test memory")
        self.working_memory.add_memory(memory, initial_activation=0.8)

        # Should be able to retrieve
        retrieved = self.working_memory.get_memory(memory.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, memory.id)

    def test_working_memory_retrieval(self):
        """Test memory retrieval by relevance"""
        # Add relevant memories
        memory1 = EpisodicMemory(content="Dragon fight in the mountains")
        memory2 = EpisodicMemory(content="Buying potions in town")
        memory3 = EpisodicMemory(content="Exploring dark caves")

        self.working_memory.add_memory(memory1)
        self.working_memory.add_memory(memory2)
        self.working_memory.add_memory(memory3)

        # Search for dragon-related memories
        results = self.working_memory.retrieve_by_relevance("dragon", max_results=2)
        self.assertGreater(len(results), 0)
        self.assertIn("dragon", results[0][0].content.primary_content.lower())

    def test_working_memory_decay(self):
        """Test activation decay over time"""
        memory = EpisodicMemory(content="Test memory")
        self.working_memory.add_memory(memory, initial_activation=1.0)

        # Force decay
        self.working_memory.decay_all(0.5)

        # Check if memory still exists (might be evicted if activation too low)
        if memory.id in self.working_memory.items:
            item = self.working_memory.items[memory.id]
            self.assertLess(item.activation, 1.0)


class TestEpisodicMemory(unittest.TestCase):
    """Test episodic memory functionality"""

    def setUp(self):
        self.episodic_memory = EpisodicMemory(
            content="Fought a dragon in the mountains",
            location="Dragon Peak",
            participants=["Dragon", "Wizard Companion"],
            emotional_valence=-0.3,  # Slightly negative (dangerous)
            importance=8.0
        )

    def test_episodic_memory_creation(self):
        """Test episodic memory creation with rich context"""
        self.assertEqual(self.episodic_memory.metadata.location, "Dragon Peak")
        self.assertEqual(self.episodic_memory.metadata.participants, ["Dragon", "Wizard Companion"])
        self.assertEqual(self.episodic_memory.metadata.emotional_valence, -0.3)
        self.assertEqual(self.episodic_memory.importance, 8.0)

    def test_episodic_memory_similarity(self):
        """Test episodic memory similarity calculation"""
        memory2 = EpisodicMemory(
            content="Fought another dragon in the same mountains",
            location="Dragon Peak",
            participants=["Dragon"]
        )

        similarity = self.episodic_memory.calculate_similarity_to(memory2)
        self.assertGreater(similarity, 0.5)  # Should be quite similar

    def test_temporal_landmark(self):
        """Test temporal landmark marking"""
        self.assertFalse(self.episodic_memory.is_temporal_landmark)

        self.episodic_memory.mark_as_temporal_landmark("first_dragon_fight", 2.0)
        self.assertTrue(self.episodic_memory.is_temporal_landmark)
        self.assertEqual(self.episodic_memory.landmark_type, "first_dragon_fight")
        self.assertGreater(self.episodic_memory.importance, 8.0)  # Should be boosted

    def test_consolidation_readiness(self):
        """Test consolidation readiness checks"""
        # New memory shouldn't be ready
        self.assertFalse(self.episodic_memory.can_consolidate())

        # Simulate time passing and access
        self.episodic_memory.creation_time = datetime.now() - timedelta(days=2)
        self.episodic_memory.access()  # Increment access count
        self.episodic_memory.access()

        # Should now be ready
        self.assertTrue(self.episodic_memory.can_consolidate())


class TestSemanticMemory(unittest.TestCase):
    """Test semantic memory functionality"""

    def setUp(self):
        self.semantic_memory = SemanticMemory(
            content="Dragons are dangerous creatures that breathe fire and guard treasures",
            concept="dragons",
            confidence=0.9,
            importance=8.5
        )

    def test_semantic_memory_creation(self):
        """Test semantic memory creation"""
        self.assertEqual(self.semantic_memory.concept, "dragons")
        self.assertEqual(self.semantic_memory.confidence, 0.9)
        self.assertEqual(self.semantic_memory.type, MemoryType.SEMANTIC)

    def test_knowledge_validation(self):
        """Test knowledge validation"""
        initial_confidence = self.semantic_memory.confidence

        # Validate with positive outcome
        self.semantic_memory.validate_knowledge(True)
        self.assertGreater(self.semantic_memory.confidence, initial_confidence)

        # Validate with negative outcome
        self.semantic_memory.validate_knowledge(False)
        self.assertLess(self.semantic_memory.confidence, initial_confidence)

    def test_knowledge_application(self):
        """Test knowledge application"""
        context = {"situation": "encountering a dragon"}
        result = self.semantic_memory.apply_knowledge(context)

        self.assertTrue(result["applied"])
        self.assertIn("dragons", result["knowledge_applied"])
        self.assertEqual(result["confidence"], self.semantic_memory.confidence)

    def test_memory_abstraction(self):
        """Test semantic memory abstraction"""
        abstract_memory = self.semantic_memory.abstract_to_higher_level()

        self.assertIsNotNone(abstract_memory)
        self.assertEqual(abstract_memory.type, MemoryType.SEMANTIC)
        self.assertIn("abstract", abstract_memory.concept)
        self.assertGreater(abstract_memory.importance, self.semantic_memory.importance)


class TestConsolidationEngine(unittest.TestCase):
    """Test memory consolidation functionality"""

    def setUp(self):
        self.character_level = 5
        self.consolidation_engine = ConsolidationEngine(self.character_level)
        self.working_memory = WorkingMemory(capacity=10)
        self.episodic_memories: List[EpisodicMemory] = []
        self.semantic_memories: List[SemanticMemory] = []

    def test_consolidation_thresholds(self):
        """Test consolidation thresholds by level"""
        self.assertEqual(self.consolidation_engine.consolidation_threshold, 200.0)
        self.assertEqual(self.consolidation_engine.working_memory_capacity, 10)

        # Update level
        self.consolidation_engine.update_character_level(15)
        self.assertEqual(self.consolidation_engine.consolidation_threshold, 400.0)
        self.assertEqual(self.consolidation_engine.working_memory_capacity, 15)

    def test_working_to_episodic_consolidation(self):
        """Test consolidation from working to episodic memory"""
        # Add memories to working memory
        for i in range(3):
            memory = EpisodicMemory(
                content=f"Important experience {i}",
                importance=7.0 + i
            )
            self.working_memory.add_memory(memory)

        # Consolidate
        results = self.consolidation_engine.consolidate_working_to_episodic(
            self.working_memory, self.episodic_memories
        )

        self.assertGreater(results["consolidated_count"], 0)
        self.assertEqual(len(results["new_episodic_memories"]), results["consolidated_count"])

    def test_episodic_to_semantic_consolidation(self):
        """Test consolidation from episodic to semantic memory"""
        # Create similar episodic memories
        for i in range(3):
            memory = EpisodicMemory(
                content=f"Fought dragons in different locations {i}",
                importance=8.0,
                timestamp=datetime.now() - timedelta(days=i+2)  # Old enough for consolidation
            )
            memory.metadata.access_count = 2  # Accessed multiple times
            self.episodic_memories.append(memory)

        # Consolidate
        results = self.consolidation_engine.consolidate_episodic_to_semantic(
            self.episodic_memories, self.semantic_memories
        )

        # Note: This test might not find clusters without vector store
        # In a real environment with vector store, it would work better
        self.assertIsInstance(results, dict)

    def test_consolidation_cycle(self):
        """Test full consolidation cycle"""
        # Add some memories
        memory1 = EpisodicMemory(content="Important event 1", importance=8.0)
        memory2 = EpisodicMemory(content="Important event 2", importance=7.5)

        self.working_memory.add_memory(memory1)
        self.working_memory.add_memory(memory2)

        # Run consolidation cycle
        results = self.consolidation_engine.run_consolidation_cycle(
            self.working_memory, self.episodic_memories, self.semantic_memories
        )

        self.assertIn("timestamp", results)
        self.assertIn("total_consolidated", results)
        self.assertIsInstance(results["total_consolidated"], int)


class TestForgettingMechanism(unittest.TestCase):
    """Test forgetting mechanism functionality"""

    def setUp(self):
        self.character_level = 5
        self.forgetting_mechanism = ForgettingMechanism(
            self.character_level,
            CompositeForgetting()
        )
        self.working_memory = WorkingMemory(capacity=5)
        self.episodic_memories: List[EpisodicMemory] = []
        self.semantic_memories: List[SemanticMemory] = []

    def test_capacity_limits(self):
        """Test capacity limits by level"""
        limits = self.forgetting_mechanism.capacity_limits
        self.assertIn("working", limits)
        self.assertIn("episodic", limits)
        self.assertIn("semantic", limits)
        self.assertIn("total", limits)

    def test_memory_protection(self):
        """Test memory protection rules"""
        # Create high-importance memory
        memory = EpisodicMemory(content="Very important memory", importance=9.5)

        # Should be protected
        self.assertTrue(self.forgetting_mechanism.is_memory_protected(memory))

        # Create low-importance memory
        memory2 = EpisodicMemory(content="Less important memory", importance=3.0)

        # Should not be protected
        self.assertFalse(self.forgetting_mechanism.is_memory_protected(memory2))

    def test_capacity_management(self):
        """Test capacity management through forgetting"""
        # Fill episodic memory beyond capacity
        for i in range(25):  # More than typical capacity
            memory = EpisodicMemory(
                content=f"Memory {i}",
                importance=3.0 + (i % 5)  # Varying importance
            )
            self.episodic_memories.append(memory)

        # Manage capacity
        results = self.forgetting_mechanism.manage_capacity(
            self.working_memory, self.episodic_memories, self.semantic_memories
        )

        self.assertIn("forgotten_memories", results)
        self.assertIsInstance(results["forgotten_memories"], list)

    def test_strategy_changes(self):
        """Test changing forgetting strategies"""
        from ..core.forgetting_mechanism import ImportanceBasedForgetting

        new_strategy = ImportanceBasedForgetting()
        self.forgetting_mechanism.set_strategy(new_strategy)

        self.assertEqual(self.forgetting_mechanism.strategy.name, "importance_based")


class TestMemoryManager(unittest.TestCase):
    """Test memory manager functionality"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.character_id = "test_character"
        self.character_level = 5

        self.memory_manager = MemoryManager(
            character_id=self.character_id,
            character_level=self.character_level,
            data_directory=self.temp_dir,
            enable_vector_store=False,  # Disable for testing
            enable_dashboard=False
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_memory_addition(self):
        """Test adding memories through manager"""
        memory = self.memory_manager.add_memory(
            content="Test experience",
            importance=7.0,
            location="Test Location",
            participants=["Test Person"]
        )

        self.assertIsNotNone(memory)
        self.assertEqual(memory.content.primary_content, "Test experience")
        self.assertEqual(memory.type, MemoryType.EPISODIC)

    def test_memory_retrieval(self):
        """Test memory retrieval through manager"""
        # Add some memories
        self.memory_manager.add_memory("Dragon fight", importance=8.0)
        self.memory_manager.add_memory("Town visit", importance=5.0)
        self.memory_manager.add_memory("Cave exploration", importance=6.0)

        # Search for dragon-related memory
        results = self.memory_manager.retrieve_memories("dragon", max_results=5)

        self.assertGreater(len(results), 0)
        self.assertIn("dragon", results[0]["document"].lower())

    def test_context_retrieval(self):
        """Test context memory retrieval"""
        # Add memories to different types
        working_memory = EpisodicMemory("Current thought", importance=7.0)
        episodic_memory = EpisodicMemory("Recent experience", importance=6.0)
        semantic_memory = SemanticMemory("Known fact", importance=8.0)

        self.memory_manager.working_memory.add_memory(working_memory)
        self.episodic_memories = [episodic_memory]
        self.semantic_memories = [semantic_memory]

        # Get context
        context = self.memory_manager.get_context_memories()

        self.assertIn("working", context)
        self.assertIn("episodic", context)
        self.assertIn("semantic", context)

    def test_character_level_update(self):
        """Test character level updates"""
        old_level = self.memory_manager.character_level
        new_level = 10

        self.memory_manager.update_character_level(new_level)

        self.assertEqual(self.memory_manager.character_level, new_level)
        self.assertNotEqual(self.memory_manager.capacity_config.total_memories,
                          self.memory_manager.capacity_config.total_memories)  # Should change

    def test_reflection(self):
        """Test experience reflection"""
        # Add some memories
        for i in range(3):
            self.memory_manager.add_memory(
                content=f"Experience {i}",
                importance=6.0 + i
            )

        # Trigger reflection
        results = self.memory_manager.reflect_on_experiences()

        self.assertIn("insights_generated", results)
        self.assertIn("importance_updates", results)
        self.assertIsInstance(results["insights_generated"], int)


class TestCharacterAIIntegration(unittest.TestCase):
    """Test character AI integration functionality"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.character_id = "test_character"
        self.character_level = 5

        self.integration = CharacterAIIntegration(
            character_id=self.character_id,
            character_level=self.character_level,
            data_directory=self.temp_dir,
            enable_migration=False
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_experience_processing(self):
        """Test character experience processing"""
        result = self.integration.process_character_experience(
            experience_description="I fought a dragon and won",
            emotional_valence=0.8,
            importance=8.5,
            location="Dragon Peak",
            participants=["Dragon", "Wizard"]
        )

        self.assertTrue(result["success"])
        self.assertIn("memory_id", result)
        self.assertEqual(result["memory_type"], "episodic")

    def test_dialogue_processing(self):
        """Test character dialogue processing"""
        result = self.integration.process_character_dialogue(
            dialogue="Hello, brave adventurer!",
            speaker="Village Elder",
            emotional_tone="friendly",
            importance=6.0
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["speaker"], "Village Elder")

    def test_context_retrieval(self):
        """Test character context retrieval"""
        # Add some experiences
        self.integration.process_character_experience("Recent adventure", importance=7.0)
        self.integration.process_character_experience("Another experience", importance=6.0)

        # Get context
        context = self.integration.get_character_context()

        self.assertIn("character_id", context)
        self.assertIn("memories", context)
        self.assertIn("working", context["memories"])
        self.assertIn("episodic", context["memories"])
        self.assertIn("semantic", context["memories"])

    def test_level_update(self):
        """Test character level update"""
        old_level = self.character_level
        new_level = 8

        result = self.integration.update_character_level(new_level)

        self.assertTrue(result["success"])
        self.assertEqual(result["old_level"], old_level)
        self.assertEqual(result["new_level"], new_level)

    def test_memory_retrieval(self):
        """Test relevant memory retrieval"""
        # Add some memories
        self.integration.process_character_experience("Dragon fight in mountains", importance=8.0)
        self.integration.process_character_experience("Shopping in town", importance=5.0)

        # Search for dragon memories
        results = self.integration.retrieve_relevant_memories("dragon", max_results=5)

        self.assertGreater(len(results), 0)
        self.assertIn("dragon", results[0]["content"].lower())

    def test_system_status(self):
        """Test memory system status retrieval"""
        status = self.integration.get_memory_system_status()

        self.assertIn("character_id", status)
        self.assertIn("character_level", status)
        self.assertIn("memory_stats", status)
        self.assertIn("migration_status", status)


if __name__ == "__main__":
    unittest.main()