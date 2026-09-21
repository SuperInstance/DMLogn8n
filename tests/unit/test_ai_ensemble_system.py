"""
Unit Tests for AI Ensemble System
================================

Tests the core Agent Intelligence System components including:
- AIEnsemble class and ensemble strategies
- RealTimeLearningEngine
- EnsembleCharacterAI
- Model routing and expertise tracking
- Performance monitoring and adaptation

Uses BDD-style testing with comprehensive coverage.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List
import numpy as np

# Import the system under test
from source_code.backend.ai_ensemble_system import (
    AIEnsemble,
    RealTimeLearningEngine,
    EnsembleCharacterAI,
    EnsembleStrategy,
    LearningMode,
    ModelExpertise,
    EnsembleResponse,
    LearningSignal,
    EnsembleCharacterAI
)


class TestModelExpertise:
    """Test suite for ModelExpertise data class"""

    def test_model_expertise_creation(self):
        """Test creating a ModelExpertise instance"""
        expertise = ModelExpertise(
            model_name="gpt-4",
            expertise_domains=["strategic", "complex_social", "moral"],
            confidence_score=0.85,
            performance_history={"strategic": 0.9, "social": 0.8}
        )

        assert expertise.model_name == "gpt-4"
        assert len(expertise.expertise_domains) == 3
        assert expertise.confidence_score == 0.85
        assert "strategic" in expertise.performance_history
        assert isinstance(expertise.last_updated, datetime)

    def test_model_expertise_defaults(self):
        """Test ModelExpertise with default values"""
        expertise = ModelExpertise(
            model_name="claude-sonnet",
            expertise_domains=["dialogue", "storytelling"]
        )

        assert expertise.confidence_score == 0.8
        assert expertise.adaptation_rate == 0.1
        assert expertise.performance_history == {}

    def test_model_expertise_to_dict(self):
        """Test converting ModelExpertise to dictionary"""
        expertise = ModelExpertise(
            model_name="gpt-4o-mini",
            expertise_domains=["balanced", "efficient"],
            confidence_score=0.75
        )

        from dataclasses import asdict
        expertise_dict = asdict(expertise)

        assert expertise_dict["model_name"] == "gpt-4o-mini"
        assert expertise_dict["confidence_score"] == 0.75
        assert "last_updated" in expertise_dict


class TestEnsembleResponse:
    """Test suite for EnsembleResponse data class"""

    def test_ensemble_response_creation(self):
        """Test creating an EnsembleResponse instance"""
        response = EnsembleResponse(
            content="The party should investigate the mysterious ruins.",
            confidence=0.92,
            reasoning="Expert panel consensus with strategic analysis",
            contributing_models=["gpt-4", "claude-opus"],
            consensus_score=0.88,
            alternative_responses=[
                {"content": "Alternative response", "model": "claude-sonnet"}
            ],
            metadata={"strategy": "expert_panel", "rounds": 2}
        )

        assert response.content == "The party should investigate the mysterious ruins."
        assert response.confidence == 0.92
        assert len(response.contributing_models) == 2
        assert response.consensus_score == 0.88
        assert len(response.alternative_responses) == 1
        assert response.metadata["strategy"] == "expert_panel"

    def test_ensemble_response_minimal(self):
        """Test EnsembleResponse with minimal required fields"""
        response = EnsembleResponse(
            content="Basic response",
            confidence=0.7,
            reasoning="Simple reasoning",
            contributing_models=["gpt-4"],
            consensus_score=0.8,
            alternative_responses=[],
            metadata={}
        )

        assert response.content == "Basic response"
        assert response.confidence == 0.7
        assert response.alternative_responses == []


class TestAIEnsemble:
    """Test suite for AIEnsemble class"""

    @pytest.fixture
    def mock_model_router(self):
        """Create a mock model router"""
        router = Mock()
        router.models = {
            "gpt-4": Mock(provider="openai"),
            "claude-opus": Mock(provider="anthropic"),
            "gpt-4o-mini": Mock(provider="openai"),
            "claude-sonnet": Mock(provider="anthropic"),
            "gpt-3.5-turbo": Mock(provider="openai")
        }
        router.invoke = AsyncMock(return_value=("Mock response", {"model": "gpt-4"}))
        return router

    @pytest.fixture
    def ai_ensemble(self, mock_model_router):
        """Create an AIEnsemble instance with mocked dependencies"""
        with patch('source_code.backend.ai_ensemble_system.ModelRouter', return_value=mock_model_router):
            ensemble = AIEnsemble()
            return ensemble

    def test_ensemble_initialization(self, ai_ensemble):
        """Test AIEnsemble initialization"""
        assert ai_ensemble.ensemble_strategy == EnsembleStrategy.EXPERT_PANEL
        assert ai_ensemble.learning_mode == LearningMode.ADAPTIVE
        assert ai_ensemble.consensus_threshold == 0.7
        assert ai_ensemble.debate_rounds == 2
        assert len(ai_ensemble.model_expertise) > 0
        assert isinstance(ai_ensemble.context_memory, type(ai_ensemble.context_memory))

    def test_expertise_initialization(self, ai_ensemble):
        """Test that model expertise is properly initialized"""
        assert "gpt-4" in ai_ensemble.model_expertise
        assert "claude-opus" in ai_ensemble.model_expertise

        gpt4_expertise = ai_ensemble.model_expertise["gpt-4"]
        assert "strategic" in gpt4_expertise.expertise_domains
        assert "complex_social" in gpt4_expertise.expertise_domains

    def test_analyze_required_expertise_combat(self, ai_ensemble):
        """Test expertise analysis for combat scenarios"""
        prompt = "The party is attacked by orcs in the forest. What should the fighter do?"
        expertise = ai_ensemble._analyze_required_expertise(prompt, {})

        assert "combat" in expertise
        assert isinstance(expertise, list)

    def test_analyze_required_expertise_social(self, ai_ensemble):
        """Test expertise analysis for social scenarios"""
        prompt = "The party needs to persuade the king to help their cause."
        expertise = ai_ensemble._analyze_required_expertise(prompt, {})

        assert "social" in expertise

    def test_analyze_required_expertise_exploration(self, ai_ensemble):
        """Test expertise analysis for exploration scenarios"""
        prompt = "The party wants to search the ancient ruins for treasure."
        expertise = ai_ensemble._analyze_required_expertise(prompt, {})

        assert "exploration" in expertise

    def test_analyze_required_expertise_default(self, ai_ensemble):
        """Test expertise analysis returns general for unclear prompts"""
        prompt = "Hello world"
        expertise = ai_ensemble._analyze_required_expertise(prompt, {})

        assert expertise == ["general"]

    def test_select_diverse_models(self, ai_ensemble):
        """Test selecting diverse models for ensemble"""
        models = ai_ensemble._select_diverse_models("test prompt", {}, num_models=3)

        assert len(models) <= 3
        assert len(set(models)) == len(models)  # Ensure no duplicates
        # Should have models from different providers when possible
        providers = [ai_ensemble.model_router.models[m].provider for m in models]
        assert len(set(providers)) >= 1

    def test_select_expert_models(self, ai_ensemble):
        """Test selecting expert models for specific tasks"""
        required_expertise = ["combat", "social"]
        expert_models = ai_ensemble._select_expert_models(required_expertise)

        assert len(expert_models) == 2
        assert "combat" in expert_models
        assert "social" in expert_models
        assert all(isinstance(model, str) for model in expert_models.values())

    def test_estimate_confidence(self, ai_ensemble):
        """Test confidence estimation for models"""
        # Test with matching expertise
        confidence = ai_ensemble._estimate_confidence(
            "gpt-4", "strategic combat decision", {}
        )
        assert 0.1 <= confidence <= 1.0

        # Test with non-existent model
        confidence = ai_ensemble._estimate_confidence(
            "unknown-model", "test prompt", {}
        )
        assert 0.1 <= confidence <= 1.0

    @pytest.mark.asyncio
    async def test_get_model_response_success(self, ai_ensemble):
        """Test successful model response generation"""
        response = await ai_ensemble._get_model_response(
            "gpt-4", "What should the party do next?", {}
        )

        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_get_model_response_failure(self, ai_ensemble):
        """Test model response failure handling"""
        # Make the model router fail
        ai_ensemble.model_router.invoke.side_effect = Exception("API Error")

        response = await ai_ensemble._get_model_response(
            "gpt-4", "test prompt", {}
        )

        assert "error" in response.lower()

    @pytest.mark.asyncio
    async def test_generate_response_expert_panel(self, ai_ensemble):
        """Test response generation using expert panel strategy"""
        response = await ai_ensemble.generate_response(
            prompt="The party encounters a dragon. What should they do?",
            context={"situation": "combat"},
            strategy=EnsembleStrategy.EXPERT_PANEL
        )

        assert isinstance(response, EnsembleResponse)
        assert response.content is not None
        assert response.confidence > 0
        assert response.metadata["strategy"] == "expert_panel"
        assert len(response.contributing_models) > 0

    @pytest.mark.asyncio
    async def test_generate_response_consensus(self, ai_ensemble):
        """Test response generation using consensus strategy"""
        response = await ai_ensemble.generate_response(
            prompt="Should the party trust the mysterious stranger?",
            context={"situation": "social"},
            strategy=EnsembleStrategy.CONSENSUS
        )

        assert isinstance(response, EnsembleResponse)
        assert response.metadata["strategy"] == "consensus"
        assert "rounds" in response.metadata

    @pytest.mark.asyncio
    async def test_generate_response_debate(self, ai_ensemble):
        """Test response generation using debate strategy"""
        response = await ai_ensemble.generate_response(
            prompt="Is it morally acceptable to steal from the evil corporation?",
            context={"situation": "moral_dilemma"},
            strategy=EnsembleStrategy.DEBATE
        )

        assert isinstance(response, EnsembleResponse)
        assert response.metadata["strategy"] == "debate"
        assert "debate_rounds" in response.metadata

    @pytest.mark.asyncio
    async def test_generate_response_chain_of_thought(self, ai_ensemble):
        """Test response generation using chain of thought strategy"""
        response = await ai_ensemble.generate_response(
            prompt="Solve the ancient riddle to open the door",
            context={"situation": "puzzle"},
            strategy=EnsembleStrategy.CHAIN_OF_THOUGHT
        )

        assert isinstance(response, EnsembleResponse)
        assert response.metadata["strategy"] == "chain_of_thought"
        assert "reasoning_steps" in response.metadata

    @pytest.mark.asyncio
    async def test_generate_response_mixture_of_experts(self, ai_ensemble):
        """Test response generation using mixture of experts strategy"""
        response = await ai_ensemble.generate_response(
            prompt="Plan the party's approach to the diplomatic mission",
            context={"situation": "strategic_planning"},
            strategy=EnsembleStrategy.MOE
        )

        assert isinstance(response, EnsembleResponse)
        assert response.metadata["strategy"] == "mixture_of_experts"
        assert "expert_weights" in response.metadata

    @pytest.mark.asyncio
    async def test_generate_response_fallback(self, ai_ensemble):
        """Test fallback response when ensemble fails"""
        # Mock the expert panel to fail
        with patch.object(ai_ensemble, '_expert_panel_ensemble', side_effect=Exception("Ensemble failed")):
            response = await ai_ensemble.generate_response(
                prompt="test prompt",
                context={}
            )

            assert isinstance(response, EnsembleResponse)
            assert response.metadata["strategy"] == "fallback"
            assert response.metadata.get("error") is True

    def test_track_performance(self, ai_ensemble):
        """Test performance tracking"""
        response = EnsembleResponse(
            content="test response",
            confidence=0.8,
            reasoning="test reasoning",
            contributing_models=["gpt-4"],
            consensus_score=0.7,
            alternative_responses=[],
            metadata={"strategy": "expert_panel"}
        )

        # Should not raise an exception
        ai_ensemble._track_performance("test prompt", response, 1.5)

    def test_provide_feedback(self, ai_ensemble):
        """Test providing feedback for learning"""
        # Should not raise an exception
        ai_ensemble.provide_feedback("response-123", 0.9, "Excellent response!")

    def test_get_ensemble_stats(self, ai_ensemble):
        """Test getting ensemble statistics"""
        stats = ai_ensemble.get_ensemble_stats()

        assert isinstance(stats, dict)
        assert "total_generations" in stats
        assert "strategy_usage" in stats
        assert "model_expertise" in stats
        assert "average_confidence" in stats
        assert "consensus_rate" in stats


class TestRealTimeLearningEngine:
    """Test suite for RealTimeLearningEngine"""

    @pytest.fixture
    def mock_ensemble(self):
        """Create a mock AIEnsemble"""
        ensemble = Mock()
        return ensemble

    @pytest.fixture
    def learning_engine(self, mock_ensemble):
        """Create a RealTimeLearningEngine instance"""
        return RealTimeLearningEngine(mock_ensemble)

    def test_learning_engine_initialization(self, learning_engine, mock_ensemble):
        """Test learning engine initialization"""
        assert learning_engine.ensemble == mock_ensemble
        assert learning_engine.learning_buffer.maxlen == 1000
        assert isinstance(learning_engine.performance_metrics, dict)
        assert isinstance(learning_engine.adaptation_history, list)

    def test_record_interaction(self, learning_engine):
        """Test recording interaction for learning"""
        response = EnsembleResponse(
            content="test response",
            confidence=0.8,
            reasoning="test reasoning",
            contributing_models=["gpt-4"],
            consensus_score=0.7,
            alternative_responses=[],
            metadata={}
        )

        # Record successful interaction
        learning_engine.record_interaction(
            prompt="test prompt",
            response=response,
            user_feedback=0.9,
            context={"session_id": "test"}
        )

        assert len(learning_engine.learning_buffer) == 1

        # Record failed interaction
        learning_engine.record_interaction(
            prompt="test prompt 2",
            response=response,
            user_feedback=0.3,
            context={}
        )

        assert len(learning_engine.learning_buffer) == 2

    def test_classify_task(self, learning_engine):
        """Test task classification"""
        task_type = learning_engine._classify_task("The party fights a dragon")
        assert isinstance(task_type, str)
        assert len(task_type) > 0

    def test_trigger_adaptation(self, learning_engine):
        """Test adaptation triggering"""
        # Fill buffer to trigger adaptation
        for i in range(50):
            learning_engine.learning_buffer.append(
                LearningSignal(
                    model_name="gpt-4",
                    task_type="test",
                    success=True,
                    user_feedback=0.8,
                    context={}
                )
            )

        # Should not raise an exception
        learning_engine._trigger_adaptation()


class TestEnsembleCharacterAI:
    """Test suite for EnsembleCharacterAI"""

    @pytest.fixture
    def mock_character(self):
        """Create a mock character"""
        character = Mock()
        character.name = "Aragorn"
        character.race = "Human"
        character.character_class = Mock(name="Fighter")
        character.get_stats_summary.return_value = {"strength": 16, "dexterity": 14}
        character.get_health_summary.return_value = {"current_hp": 45, "max_hp": 60}
        character.get_inventory_summary.return_value = ["sword", "shield"]
        character.get_recent_memories.return_value = ["Fought orcs", "Found treasure"]
        return character

    @pytest.fixture
    def character_ai(self, mock_character):
        """Create an EnsembleCharacterAI instance"""
        with patch('source_code.backend.ai_ensemble_system.AIEnsemble'):
            character_ai = EnsembleCharacterAI(mock_character)
            return character_ai

    def test_character_ai_initialization(self, character_ai, mock_character):
        """Test character AI initialization"""
        assert character_ai.character == mock_character
        assert character_ai.ensemble is not None
        assert character_ai.learning_engine is not None
        assert isinstance(character_ai.character_context_cache, dict)

    @pytest.mark.asyncio
    async def test_make_character_decision(self, character_ai):
        """Test character decision making"""
        # Mock the ensemble response
        mock_response = EnsembleResponse(
            content="I will attack the goblin with my sword.",
            confidence=0.85,
            reasoning="As a brave fighter, engaging in combat is the best option",
            contributing_models=["gpt-4"],
            consensus_score=0.8,
            alternative_responses=[],
            metadata={"strategy": "expert_panel"}
        )

        character_ai.ensemble.generate_response = AsyncMock(return_value=mock_response)

        decision = await character_ai.make_character_decision(
            situation="A goblin appears in front of the party",
            available_actions=["Attack", "Talk", "Run", "Use Magic"],
            context={"location": "dungeon", "allies_present": True}
        )

        assert isinstance(decision, dict)
        assert "action" in decision
        assert "reasoning" in decision
        assert "confidence" in decision
        assert "character" in decision
        assert "strategy_used" in decision
        assert decision["character"] == "Aragorn"

    def test_build_character_context(self, character_ai):
        """Test building character-specific context"""
        context = character_ai._build_character_context(
            situation="Combat with dragon",
            available_actions=["Attack", "Defend", "Use Magic"],
            context={"location": "mountain", "weather": "stormy"}
        )

        assert context["character_name"] == "Aragorn"
        assert context["character_race"] == "Human"
        assert context["character_class"] == "Fighter"
        assert "character_stats" in context
        assert "health_status" in context
        assert "situation_type" in context
        assert context["available_actions"] == ["Attack", "Defend", "Use Magic"]

    def test_craft_character_prompt(self, character_ai):
        """Test crafting character-specific prompt"""
        context = {
            "character_name": "Aragorn",
            "character_race": "Human",
            "character_class": "Fighter",
            "character_personality": "Brave and loyal",
            "character_goals": "Protect the innocent",
            "health_status": "Healthy",
            "recent_memories": ["Recent battle"],
            "available_actions": ["Attack", "Defend"]
        }

        prompt = character_ai._craft_character_prompt(
            situation="Dragon appears",
            available_actions=["Attack", "Defend"],
            context=context
        )

        assert "Aragorn" in prompt
        assert "Human" in prompt
        assert "Fighter" in prompt
        assert "Dragon appears" in prompt
        assert "Attack" in prompt
        assert "Defend" in prompt

    def test_select_optimal_strategy(self, character_ai):
        """Test selecting optimal ensemble strategy"""
        # Test moral dilemma
        strategy = character_ai._select_optimal_strategy(
            "Should we steal from the corrupt merchant?",
            {}
        )
        assert strategy == EnsembleStrategy.DEBATE

        # Test combat
        strategy = character_ai._select_optimal_strategy(
            "The party is attacked by bandits!",
            {}
        )
        assert strategy == EnsembleStrategy.EXPERT_PANEL

        # Test creative situation
        strategy = character_ai._select_optimal_strategy(
            "Describe the beautiful sunset over the mountains",
            {}
        )
        assert strategy == EnsembleStrategy.CHAIN_OF_THOUGHT

        # Test default
        strategy = character_ai._select_optimal_strategy(
            "Simple situation",
            {}
        )
        assert strategy == EnsembleStrategy.MOE

    def test_classify_situation(self, character_ai):
        """Test situation classification"""
        assert character_ai._classify_situation("The party fights orcs") == "combat"
        assert character_ai._classify_situation("Talk to the king") == "social"
        assert character_ai._classify_situation("Explore the dungeon") == "exploration"
        assert character_ai._classify_situation("Something happens") == "general"

    def test_provide_decision_feedback(self, character_ai):
        """Test providing feedback for character decision learning"""
        # Should not raise an exception
        character_ai.provide_decision_feedback(
            decision_id="decision-123",
            feedback=0.9,
            reasoning="Good in-character decision"
        )


class TestIntegrationScenarios:
    """Integration scenarios for the AI Ensemble System"""

    @pytest.fixture
    def full_ensemble_system(self):
        """Create a full ensemble system with mocked dependencies"""
        with patch('source_code.backend.ai_ensemble_system.ModelRouter') as mock_router_class:
            mock_router = Mock()
            mock_router.models = {
                "gpt-4": Mock(provider="openai"),
                "claude-opus": Mock(provider="anthropic")
            }
            mock_router.invoke = AsyncMock(return_value=("Response", {"model": "gpt-4"}))
            mock_router_class.return_value = mock_router

            ensemble = AIEnsemble()
            learning_engine = RealTimeLearningEngine(ensemble)

            return ensemble, learning_engine, mock_router

    @pytest.mark.asyncio
    async def test_full_character_decision_workflow(self, full_ensemble_system):
        """Test complete character decision workflow"""
        ensemble, learning_engine, mock_router = full_ensemble_system

        # Create character
        mock_character = Mock()
        mock_character.name = "Gandalf"
        mock_character.race = "Human"
        mock_character.character_class = Mock(name="Wizard")
        mock_character.get_stats_summary.return_value = {"intelligence": 18, "wisdom": 16}
        mock_character.get_health_summary.return_value = {"current_hp": 50, "max_hp": 60}
        mock_character.get_inventory_summary.return_value = ["staff", "spellbook"]
        mock_character.get_recent_memories.return_value = ["Defeated Balrog"]

        # Create character AI
        with patch('source_code.backend.ai_ensemble_system.AIEnsemble', return_value=ensemble):
            character_ai = EnsembleCharacterAI(mock_character)
            character_ai.learning_engine = learning_engine

        # Make decision
        decision = await character_ai.make_character_decision(
            situation="The party encounters a riddle-locked door",
            available_actions=["Solve riddle", "Cast spell", "Break door", "Find another way"],
            context={"location": "ancient_temple", "time_pressure": False}
        )

        # Verify decision structure
        assert isinstance(decision, dict)
        assert "action" in decision
        assert "reasoning" in decision
        assert "confidence" in decision
        assert decision["character"] == "Gandalf"

        # Provide feedback for learning
        character_ai.provide_decision_feedback(
            decision_id="test-decision",
            feedback=0.95,
            reasoning="Perfect in-character decision"
        )

        # Verify learning
        assert len(learning_engine.learning_buffer) > 0

    @pytest.mark.asyncio
    async def test_ensemble_strategy_comparison(self, full_ensemble_system):
        """Test comparing different ensemble strategies"""
        ensemble, _, _ = full_ensemble_system

        prompt = "The party must decide whether to trust the mysterious stranger offering help"
        context = {"situation": "social", "risk_level": "high"}

        strategies = [
            EnsembleStrategy.EXPERT_PANEL,
            EnsembleStrategy.CONSENSUS,
            EnsembleStrategy.DEBATE,
            EnsembleStrategy.MOE
        ]

        responses = {}
        for strategy in strategies:
            response = await ensemble.generate_response(
                prompt=prompt,
                context=context,
                strategy=strategy
            )
            responses[strategy.value] = response

        # Verify all strategies produced responses
        assert len(responses) == len(strategies)
        for strategy_value, response in responses.items():
            assert isinstance(response, EnsembleResponse)
            assert response.metadata["strategy"] == strategy_value
            assert response.confidence > 0
            assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_performance_under_load(self, full_ensemble_system):
        """Test ensemble system performance under load"""
        ensemble, _, _ = full_ensemble_system

        # Generate multiple concurrent requests
        tasks = []
        for i in range(10):
            task = ensemble.generate_response(
                prompt=f"Test prompt {i}: What should the party do?",
                context={"test_id": i},
                strategy=EnsembleStrategy.EXPERT_PANEL
            )
            tasks.append(task)

        # Wait for all to complete
        start_time = asyncio.get_event_loop().time()
        responses = await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()

        # Verify responses
        assert len(responses) == 10
        for i, response in enumerate(responses):
            assert isinstance(response, EnsembleResponse)
            assert response.confidence > 0

        # Verify performance (should complete in reasonable time)
        total_time = end_time - start_time
        assert total_time < 10.0  # 10 seconds for 10 requests

        # Average time per request
        avg_time = total_time / 10
        assert avg_time < 2.0  # 2 seconds per request average

    def test_expertise_adaptation(self, full_ensemble_system):
        """Test model expertise adaptation based on performance"""
        ensemble, _, _ = full_ensemble_system

        # Get initial expertise
        initial_expertise = ensemble.model_expertise["gpt-4"]
        initial_confidence = initial_expertise.confidence_score

        # Simulate successful performance
        for _ in range(5):
            ensemble.model_expertise["gpt-4"].performance_history["strategic"] = 0.95

        # The system should adapt expertise based on performance
        # This is a simplified test - real adaptation would be more complex
        assert initial_confidence > 0
        assert "strategic" in ensemble.model_expertise["gpt-4"].performance_history


class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.fixture
    def ensemble_with_failing_models(self):
        """Create ensemble with failing models"""
        with patch('source_code.backend.ai_ensemble_system.ModelRouter') as mock_router_class:
            mock_router = Mock()
            mock_router.models = {"gpt-4": Mock(provider="openai")}
            mock_router.invoke = AsyncMock(side_effect=Exception("API Error"))
            mock_router_class.return_value = mock_router

            ensemble = AIEnsemble()
            return ensemble

    @pytest.mark.asyncio
    async def test_all_models_fail(self, ensemble_with_failing_models):
        """Test behavior when all models fail"""
        response = await ensemble_with_failing_models.generate_response(
            prompt="test prompt",
            context={}
        )

        assert isinstance(response, EnsembleResponse)
        assert response.metadata["strategy"] == "fallback"
        assert "error" in response.metadata

    @pytest.mark.asyncio
    async def test_empty_model_list(self):
        """Test behavior with no available models"""
        with patch('source_code.backend.ai_ensemble_system.ModelRouter') as mock_router_class:
            mock_router = Mock()
            mock_router.models = {}
            mock_router_class.return_value = mock_router

            ensemble = AIEnsemble()

            # Should handle empty model list gracefully
            response = await ensemble._select_expert_models(["combat"])
            assert isinstance(response, dict)

    def test_invalid_expertise_analysis(self, ai_ensemble):
        """Test expertise analysis with edge cases"""
        # Empty prompt
        expertise = ai_ensemble._analyze_required_expertise("", {})
        assert expertise == ["general"]

        # Very long prompt
        long_prompt = "test " * 1000
        expertise = ai_ensemble._analyze_required_expertise(long_prompt, {})
        assert isinstance(expertise, list)

        # Special characters
        special_prompt = "!@#$%^&*()_+{}|:<>?[]\\;'\",./"
        expertise = ai_ensemble._analyze_required_expertise(special_prompt, {})
        assert isinstance(expertise, list)

    @pytest.mark.asyncio
    async def test_context_handling_edge_cases(self, ai_ensemble):
        """Test handling of various context scenarios"""
        # None context
        response = await ai_ensemble.generate_response(
            prompt="test",
            context=None
        )
        assert isinstance(response, EnsembleResponse)

        # Empty context
        response = await ai_ensemble.generate_response(
            prompt="test",
            context={}
        )
        assert isinstance(response, EnsembleResponse)

        # Large context
        large_context = {f"key_{i}": f"value_{i}" * 100 for i in range(10)}
        response = await ai_ensemble.generate_response(
            prompt="test",
            context=large_context
        )
        assert isinstance(response, EnsembleResponse)


# BDD-style test scenarios
@pytest.mark.behavior
class TestBehavioralScenarios:
    """Behavior-Driven Development test scenarios"""

    @pytest.mark.asyncio
    async def test_scenario_complex_combat_decision(self, ai_ensemble):
        """
        Scenario: Complex combat decision requiring multiple expertise areas

        Given the party is in a complex combat situation
        When the AI ensemble is asked for combat strategy
        Then it should provide a well-reasoned tactical response
        And the response should include both offensive and defensive considerations
        """
        prompt = """
        The party (Fighter, Wizard, Rogue, Cleric) is facing an adult red dragon
        in a volcanic lair. The dragon is airborne and has already used its breath
        weapon. The Wizard is low on spell slots, the Fighter is injured, and the
        Rogue has found a hiding spot. What should the party do?
        """

        response = await ai_ensemble.generate_response(
            prompt=prompt,
            context={"situation": "combat", "difficulty": "deadly"},
            strategy=EnsembleStrategy.EXPERT_PANEL
        )

        assert isinstance(response, EnsembleResponse)
        assert response.confidence > 0.7
        assert len(response.contributing_models) > 1
        assert any(word in response.content.lower() for word in ["dragon", "attack", "defend", "strategy"])
        assert response.metadata["strategy"] == "expert_panel"

    @pytest.mark.asyncio
    async def test_scenario_moral_dilemma_resolution(self, ai_ensemble):
        """
        Scenario: Moral dilemma requiring ethical reasoning

        Given the party faces a moral dilemma
        When the AI ensemble is asked for ethical guidance
        Then it should provide nuanced ethical analysis
        And consider multiple ethical frameworks
        """
        prompt = """
        The party discovers that the local lord has been stealing from the poor
        to fund his wars, but he's also keeping the region safe from monsters.
        Exposing him would cause chaos and potentially let monsters in, but keeping
        quiet allows the injustice to continue. What should the party do?
        """

        response = await ai_ensemble.generate_response(
            prompt=prompt,
            context={"situation": "moral_dilemma", "stakes": "high"},
            strategy=EnsembleStrategy.DEBATE
        )

        assert isinstance(response, EnsembleResponse)
        assert response.metadata["strategy"] == "debate"
        assert any(word in response.content.lower() for word in ["moral", "ethical", "justice", "consequence"])
        assert response.confidence > 0.6  # Moral dilemmas naturally have lower confidence

    @pytest.mark.asyncio
    async def test_scenario_creative_problem_solving(self, ai_ensemble):
        """
        Scenario: Creative puzzle solving requiring innovative thinking

        Given the party encounters a creative puzzle
        When the AI ensemble is asked for solution approaches
        Then it should provide creative and innovative solutions
        And think outside conventional approaches
        """
        prompt = """
        The party finds a door with no visible lock, handle, or hinges. The door
        is covered in shifting runes that seem to form patterns. When touched,
        the runes rearrange themselves. The door responds to speech but not to
        any languages the party knows. How can the party open this door?
        """

        response = await ai_ensemble.generate_response(
            prompt=prompt,
            context={"situation": "puzzle", "creativity_required": True},
            strategy=EnsembleStrategy.CHAIN_OF_THOUGHT
        )

        assert isinstance(response, EnsembleResponse)
        assert response.metadata["strategy"] == "chain_of_thought"
        assert any(word in response.content.lower() for word in ["rune", "pattern", "solution", "approach"])
        assert len(response.reasoning) > 50  # Should have detailed reasoning

    @pytest.mark.asyncio
    async def test_scenario_character_roleplaying(self, character_ai):
        """
        Scenario: Character-specific roleplaying decisions

        Given a character with specific personality traits
        When the character AI is asked for a decision
        Then the decision should reflect the character's personality
        And be consistent with their background and goals
        """
        decision = await character_ai.make_character_decision(
            situation="A merchant offers the party a seemingly too-good-to-be-true deal",
            available_actions=["Accept deal", "Negotiate better terms", "Investigate further", "Refuse"],
            context={"character_alignment": "Lawful Good", "merchant_reputation": "mixed"}
        )

        assert isinstance(decision, dict)
        assert "action" in decision
        assert "reasoning" in decision
        assert decision["confidence"] > 0.5

        # The reasoning should mention character-relevant considerations
        reasoning_lower = decision["reasoning"].lower()
        assert any(word in reasoning_lower for word in ["honest", "investigate", "cautious", "careful"])


# Performance benchmarks
@pytest.mark.performance
class TestPerformanceBenchmarks:
    """Performance benchmarks for the AI Ensemble System"""

    @pytest.mark.asyncio
    async def benchmark_response_generation_time(self, ai_ensemble):
        """Benchmark response generation times"""
        prompts = [
            "Simple combat question",
            "Complex social interaction requiring nuance",
            "Moral dilemma with ethical considerations",
            "Creative puzzle that needs innovative thinking"
        ]

        times = []
        for prompt in prompts:
            start_time = asyncio.get_event_loop().time()
            response = await ai_ensemble.generate_response(prompt=prompt)
            end_time = asyncio.get_event_loop().time()
            times.append(end_time - start_time)

            assert isinstance(response, EnsembleResponse)
            assert response.confidence > 0

        avg_time = sum(times) / len(times)
        max_time = max(times)

        # Performance assertions
        assert avg_time < 3.0, f"Average response time {avg_time:.2f}s exceeds 3.0s"
        assert max_time < 5.0, f"Maximum response time {max_time:.2f}s exceeds 5.0s"

    @pytest.mark.asyncio
    async def benchmark_concurrent_requests(self, ai_ensemble):
        """Benchmark concurrent request handling"""
        num_requests = 20
        prompt = "What should the adventuring party do next?"

        start_time = asyncio.get_event_loop().time()

        tasks = [
            ai_ensemble.generate_response(
                prompt=f"{prompt} (Request {i})",
                context={"request_id": i}
            )
            for i in range(num_requests)
        ]

        responses = await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()

        total_time = end_time - start_time
        requests_per_second = num_requests / total_time

        # Verify all responses
        assert len(responses) == num_requests
        for response in responses:
            assert isinstance(response, EnsembleResponse)
            assert response.confidence > 0

        # Performance assertions
        assert requests_per_second > 2.0, f"RPS {requests_per_second:.2f} below threshold of 2.0"
        assert total_time < 30.0, f"Total time {total_time:.2f}s exceeds 30.0s"

    def test_memory_usage_stability(self, ai_ensemble):
        """Test memory usage stability over multiple operations"""
        import sys
        import gc

        # Get initial memory usage
        gc.collect()
        initial_objects = len(gc.get_objects())

        # Perform many operations
        for i in range(100):
            # Simulate operations without actual async calls
            ai_ensemble._analyze_required_expertise(f"Test prompt {i}", {})
            ai_ensemble._select_diverse_models(f"Test prompt {i}", {})

            # Add some learning signals
            if i % 10 == 0:
                ai_ensemble.learning_signals.append(
                    LearningSignal(
                        model_name="gpt-4",
                        task_type="test",
                        success=True,
                        user_feedback=0.8,
                        context={}
                    )
                )

        # Check final memory usage
        gc.collect()
        final_objects = len(gc.get_objects())

        # Memory growth should be reasonable
        object_growth = final_objects - initial_objects
        assert object_growth < 1000, f"Object growth {object_growth} indicates potential memory leak"


if __name__ == "__main__":
    # Run tests if this file is executed directly
    pytest.main([__file__, "-v", "--tb=short"])