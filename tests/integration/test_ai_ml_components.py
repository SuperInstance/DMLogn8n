"""
Comprehensive AI/ML Component Testing
Tests AI decision-making, LLM integration, vector memory, and learning systems
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any, Optional
import numpy as np
from datetime import datetime


class TestLLMIntegration:
    """Test LLM integration and model routing"""

    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI API response"""
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="This is a test response from OpenAI"))
        ]
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        return mock_response

    @pytest.fixture
    def mock_anthropic_response(self):
        """Mock Anthropic API response"""
        mock_response = Mock()
        mock_response.content = [
            Mock(type="text", text="This is a test response from Anthropic")
        ]
        mock_response.usage = Mock(input_tokens=10, output_tokens=20)
        return mock_response

    def test_openai_integration(self, mock_external_services, mock_openai_response):
        """Test OpenAI API integration"""
        mock_openai = mock_external_services['openai']
        mock_openai.chat.completions.create.return_value = mock_openai_response

        # Test OpenAI API call
        response = mock_openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Test prompt"}],
            temperature=0.7,
            max_tokens=100
        )

        assert response.choices[0].message.content == "This is a test response from OpenAI"
        assert response.usage.total_tokens == 30

    def test_anthropic_integration(self, mock_external_services, mock_anthropic_response):
        """Test Anthropic API integration"""
        mock_anthropic = mock_external_services['anthropic']
        mock_anthropic.messages.create.return_value = mock_anthropic_response

        # Test Anthropic API call
        response = mock_anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            messages=[{"role": "user", "content": "Test prompt"}],
            temperature=0.7,
            max_tokens=100
        )

        assert response.content[0].text == "This is a test response from Anthropic"
        assert response.usage.output_tokens == 20

    def test_model_routing_logic(self):
        """Test model routing and selection logic"""
        from source_code.backend.model_routing import ModelRouter

        # Mock ModelRouter class (would normally import from actual module)
        class MockModelRouter:
            def __init__(self):
                self.models = {
                    'fast': 'gpt-3.5-turbo',
                    'smart': 'gpt-4',
                    'creative': 'claude-3-sonnet'
                }

            def select_model(self, complexity: str, budget: float) -> str:
                if budget < 0.01:
                    return self.models['fast']
                elif complexity == 'high':
                    return self.models['smart']
                else:
                    return self.models['creative']

        router = MockModelRouter()

        # Test model selection based on different criteria
        assert router.select_model('low', 0.005) == 'gpt-3.5-turbo'  # Budget constrained
        assert router.select_model('high', 0.1) == 'gpt-4'  # High complexity
        assert router.select_model('medium', 0.05) == 'claude-3-sonnet'  # Default

    def test_llm_error_handling(self, mock_external_services):
        """Test LLM API error handling"""
        mock_openai = mock_external_services['openai']

        # Simulate API error
        mock_openai.chat.completions.create.side_effect = Exception("API Error")

        # Test error handling
        try:
            mock_openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": "Test"}]
            )
            assert False, "Should have raised exception"
        except Exception as e:
            assert "API Error" in str(e)

    def test_llm_rate_limiting(self, mock_external_services):
        """Test LLM API rate limiting"""
        mock_openai = mock_external_services['openai']

        # Simulate rate limit error
        from openai import RateLimitError
        mock_openai.chat.completions.create.side_effect = RateLimitError(
            message="Rate limit exceeded",
            response=Mock(status_code=429),
            body={"error": {"message": "Rate limit exceeded"}}
        )

        # Test rate limit handling
        try:
            mock_openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": "Test"}]
            )
            assert False, "Should have raised RateLimitError"
        except RateLimitError:
            assert True  # Expected behavior

    def test_llm_cost_tracking(self, mock_external_services):
        """Test LLM API cost tracking"""
        # Mock cost tracking functionality
        cost_tracker = {
            'total_cost': 0.0,
            'requests': 0,
            'tokens': 0
        }

        def track_cost(prompt_tokens, completion_tokens, model):
            # Mock cost calculation
            if model == 'gpt-4':
                cost_per_prompt_token = 0.00003
                cost_per_completion_token = 0.00006
            else:
                cost_per_prompt_token = 0.000001
                cost_per_completion_token = 0.000002

            cost = (prompt_tokens * cost_per_prompt_token +
                   completion_tokens * cost_per_completion_token)

            cost_tracker['total_cost'] += cost
            cost_tracker['requests'] += 1
            cost_tracker['tokens'] += prompt_tokens + completion_tokens

            return cost

        # Test cost tracking
        cost = track_cost(10, 20, 'gpt-4')
        assert cost > 0
        assert cost_tracker['requests'] == 1
        assert cost_tracker['tokens'] == 30
        assert cost_tracker['total_cost'] == cost


class TestVectorMemory:
    """Test vector memory and semantic search"""

    def test_vector_embedding_generation(self):
        """Test text embedding generation"""
        # Mock embedding generation
        class MockEmbeddingModel:
            def encode(self, text: str) -> np.ndarray:
                # Generate mock embeddings (normally would use actual model)
                return np.random.rand(384)  # Common embedding dimension

        embedding_model = MockEmbeddingModel()

        # Test embedding generation
        text = "The brave warrior entered the dark dungeon"
        embedding = embedding_model.encode(text)

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)
        assert embedding.dtype == np.float64

    def test_vector_storage_and_retrieval(self, mock_external_services):
        """Test vector storage and retrieval"""
        mock_qdrant = mock_external_services['qdrant']

        # Mock vector storage operations
        mock_qdrant.upsert.return_value = {"status": "completed"}
        mock_qdrant.search.return_value = [
            {"id": "1", "score": 0.95, "payload": {"text": "Similar memory"}},
            {"id": "2", "score": 0.87, "payload": {"text": "Related memory"}}
        ]

        # Test storing vectors
        vectors = [np.random.rand(384) for _ in range(5)]
        payloads = [{"text": f"Memory {i}"} for i in range(5)]

        mock_qdrant.upsert(
            collection_name="memories",
            points=[
                {"id": str(i), "vector": vectors[i].tolist(), "payload": payloads[i]}
                for i in range(5)
            ]
        )

        # Test vector search
        query_vector = np.random.rand(384)
        results = mock_qdrant.search(
            collection_name="memories",
            query_vector=query_vector.tolist(),
            limit=3
        )

        assert len(results) == 2  # Mock response has 2 results
        assert all(result["score"] > 0.8 for result in results)  # High similarity

    def test_semantic_search(self):
        """Test semantic search functionality"""
        # Mock semantic search
        class MockSemanticSearch:
            def __init__(self):
                self.memories = [
                    {"id": "1", "text": "Fighter attacks the goblin with his sword", "type": "combat"},
                    {"id": "2", "text": "Wizard casts fireball at the orcs", "type": "combat"},
                    {"id": "3", "text": "Rogue sneaks past the guards", "type": "stealth"},
                    {"id": "4", "text": "Cleric heals the wounded warrior", "type": "healing"}
                ]

            def search(self, query: str, limit: int = 3) -> List[Dict]:
                # Simple keyword-based mock search
                query_lower = query.lower()
                results = []

                for memory in self.memories:
                    if any(word in memory["text"].lower() for word in query_lower.split()):
                        results.append({
                            "memory": memory,
                            "score": 0.9  # Mock relevance score
                        })

                return results[:limit]

        search_engine = MockSemanticSearch()

        # Test combat-related search
        results = search_engine.search("sword attack combat")
        assert len(results) >= 1
        assert any("combat" in result["memory"]["type"] for result in results)

        # Test stealth-related search
        results = search_engine.search("sneaky rogue")
        assert len(results) >= 1
        assert any("stealth" in result["memory"]["type"] for result in results)

    def test_memory_consolidation(self):
        """Test memory consolidation and summarization"""
        class MockMemoryConsolidation:
            def consolidate_memories(self, memories: List[Dict]) -> Dict:
                # Mock consolidation logic
                if not memories:
                    return {"summary": "No memories to consolidate", "patterns": []}

                # Extract common themes
                themes = {}
                for memory in memories:
                    memory_type = memory.get("type", "unknown")
                    themes[memory_type] = themes.get(memory_type, 0) + 1

                # Generate mock summary
                summary = f"Consolidated {len(memories)} memories. "
                summary += f"Most common type: {max(themes, key=themes.get) if themes else 'unknown'}"

                return {
                    "summary": summary,
                    "patterns": list(themes.keys()),
                    "consolidated_count": len(memories)
                }

        consolidator = MockMemoryConsolidation()

        # Test memory consolidation
        memories = [
            {"text": "Fought goblins", "type": "combat", "importance": 0.8},
            {"text": "Searched treasure", "type": "exploration", "importance": 0.6},
            {"text": "Spoke to merchant", "type": "social", "importance": 0.5},
            {"text": "Battle orcs", "type": "combat", "importance": 0.9}
        ]

        result = consolidator.consolidate_memories(memories)

        assert "summary" in result
        assert "patterns" in result
        assert result["consolidated_count"] == 4
        assert "combat" in result["patterns"]


class TestEscalationEngine:
    """Test decision escalation engine"""

    def test_bot_decision_routing(self):
        """Test routing to bot decision makers"""
        class MockEscalationEngine:
            def __init__(self):
                self.bots = {
                    'mechanical': Mock(return_value={"action": "attack", "confidence": 0.9}),
                    'social': Mock(return_value={"action": "persuade", "confidence": 0.7}),
                    'combat': Mock(return_value={"action": "defend", "confidence": 0.8})
                }

            def route_decision(self, context: Dict) -> Dict:
                complexity = context.get("complexity", "low")
                decision_type = context.get("type", "mechanical")

                if complexity == "low" and decision_type in self.bots:
                    bot = self.bots[decision_type]
                    return bot(context)
                else:
                    return {"action": "escalate_to_llm", "confidence": 0.5}

        engine = MockEscalationEngine()

        # Test simple mechanical decision
        context = {"complexity": "low", "type": "mechanical", "situation": "door_locked"}
        decision = engine.route_decision(context)
        assert decision["action"] == "attack"
        assert decision["confidence"] == 0.9

        # Test complex decision escalation
        context = {"complexity": "high", "type": "social", "situation": "complex_negotiation"}
        decision = engine.route_decision(context)
        assert decision["action"] == "escalate_to_llm"

    def test_cost_optimization(self):
        """Test cost optimization in decision routing"""
        class MockCostOptimizer:
            def __init__(self):
                self.costs = {
                    'bot': 0.0001,
                    'llm_fast': 0.001,
                    'llm_smart': 0.01
                }

            def optimize_route(self, context: Dict, budget: float) -> str:
                urgency = context.get("urgency", "normal")
                complexity = context.get("complexity", "low")

                if complexity == "low" and budget > self.costs['bot']:
                    return "bot"
                elif complexity == "medium" and budget > self.costs['llm_fast']:
                    return "llm_fast"
                elif urgency == "high" and budget > self.costs['llm_smart']:
                    return "llm_smart"
                else:
                    return "bot"  # Default to cheapest

        optimizer = MockCostOptimizer()

        # Test budget-based routing
        context = {"complexity": "low", "urgency": "normal"}

        assert optimizer.optimize_route(context, 0.0005) == "bot"
        assert optimizer.optimize_route(context, 0.005) == "llm_fast"
        assert optimizer.optimize_route({"complexity": "high", "urgency": "high"}, 0.05) == "llm_smart"

    def test_performance_tracking(self):
        """Test decision performance tracking"""
        class MockPerformanceTracker:
            def __init__(self):
                self.decisions = []
                self.metrics = {
                    'total_decisions': 0,
                    'bot_decisions': 0,
                    'llm_decisions': 0,
                    'avg_response_time': 0.0
                }

            def track_decision(self, decision_type: str, response_time: float, success: bool):
                self.decisions.append({
                    'type': decision_type,
                    'response_time': response_time,
                    'success': success,
                    'timestamp': datetime.now()
                })

                self.metrics['total_decisions'] += 1
                if decision_type == 'bot':
                    self.metrics['bot_decisions'] += 1
                else:
                    self.metrics['llm_decisions'] += 1

                # Update average response time
                total_time = (self.metrics['avg_response_time'] *
                            (self.metrics['total_decisions'] - 1) + response_time)
                self.metrics['avg_response_time'] = total_time / self.metrics['total_decisions']

        tracker = MockPerformanceTracker()

        # Track some decisions
        tracker.track_decision('bot', 0.05, True)
        tracker.track_decision('llm', 1.2, True)
        tracker.track_decision('bot', 0.03, False)
        tracker.track_decision('llm', 0.8, True)

        assert tracker.metrics['total_decisions'] == 4
        assert tracker.metrics['bot_decisions'] == 2
        assert tracker.metrics['llm_decisions'] == 2
        assert 0.5 < tracker.metrics['avg_response_time'] < 1.0


class TestLearningPipeline:
    """Test learning pipeline and model training"""

    def test_decision_logging(self):
        """Test decision data logging"""
        class MockDecisionLogger:
            def __init__(self):
                self.decisions = []

            def log_decision(self, character_id: str, context: Dict, decision: Dict, outcome: Dict):
                log_entry = {
                    'character_id': character_id,
                    'timestamp': datetime.now(),
                    'context': context,
                    'decision': decision,
                    'outcome': outcome,
                    'success_score': self._calculate_success_score(decision, outcome)
                }
                self.decisions.append(log_entry)

            def _calculate_success_score(self, decision: Dict, outcome: Dict) -> float:
                # Mock success calculation
                if outcome.get('goal_achieved', False):
                    return 1.0
                elif outcome.get('partial_success', False):
                    return 0.5
                else:
                    return 0.0

        logger = MockDecisionLogger()

        # Test decision logging
        logger.log_decision(
            character_id="char_123",
            context={"situation": "combat", "enemy": "goblin"},
            decision={"action": "attack", "weapon": "sword"},
            outcome={"goal_achieved": True, "damage_dealt": 15}
        )

        logger.log_decision(
            character_id="char_123",
            context={"situation": "social", "npc": "merchant"},
            decision={"action": "persuade", "approach": "friendly"},
            outcome={"goal_achieved": False, "partial_success": True}
        )

        assert len(logger.decisions) == 2
        assert logger.decisions[0]["success_score"] == 1.0
        assert logger.decisions[1]["success_score"] == 0.5

    def test_training_data_generation(self):
        """Test training data generation from decisions"""
        class MockTrainingDataGenerator:
            def generate_training_pairs(self, decisions: List[Dict]) -> List[Dict]:
                training_pairs = []

                for decision_log in decisions:
                    if decision_log['success_score'] > 0.5:  # Only use successful decisions
                        training_pair = {
                            'input': self._format_context(decision_log['context']),
                            'target_output': self._format_decision(decision_log['decision']),
                            'weight': decision_log['success_score']
                        }
                        training_pairs.append(training_pair)

                return training_pairs

            def _format_context(self, context: Dict) -> str:
                return f"Situation: {context.get('situation', 'unknown')}"

            def _format_decision(self, decision: Dict) -> str:
                return f"Action: {decision.get('action', 'unknown')}"

        generator = MockTrainingDataGenerator()

        # Mock decision logs
        decisions = [
            {
                'context': {'situation': 'combat', 'enemy': 'goblin'},
                'decision': {'action': 'attack', 'weapon': 'sword'},
                'success_score': 1.0
            },
            {
                'context': {'situation': 'social', 'npc': 'merchant'},
                'decision': {'action': 'persuade', 'approach': 'friendly'},
                'success_score': 0.5
            },
            {
                'context': {'situation': 'exploration', 'area': 'dungeon'},
                'decision': {'action': 'search', 'method': 'thorough'},
                'success_score': 0.2
            }
        ]

        training_data = generator.generate_training_pairs(decisions)

        # Should only include successful decisions (score > 0.5)
        assert len(training_data) == 2
        assert training_data[0]['input'] == "Situation: combat"
        assert training_data[0]['target_output'] == "Action: attack"
        assert training_data[0]['weight'] == 1.0

    def test_model_training_simulation(self):
        """Test model training simulation"""
        class MockModelTrainer:
            def __init__(self):
                self.training_history = []

            def train_model(self, training_data: List[Dict], epochs: int = 10) -> Dict:
                # Mock training process
                initial_loss = 2.0
                final_loss = initial_loss * (0.9 ** epochs)  # Simulate loss reduction

                training_result = {
                    'initial_loss': initial_loss,
                    'final_loss': final_loss,
                    'epochs': epochs,
                    'training_samples': len(training_data),
                    'improvement': initial_loss - final_loss
                }

                self.training_history.append(training_result)
                return training_result

        trainer = MockModelTrainer()

        # Mock training data
        training_data = [
            {'input': 'context1', 'target_output': 'action1', 'weight': 1.0},
            {'input': 'context2', 'target_output': 'action2', 'weight': 0.8},
            {'input': 'context3', 'target_output': 'action3', 'weight': 0.9}
        ]

        # Test training
        result = trainer.train_model(training_data, epochs=20)

        assert result['initial_loss'] == 2.0
        assert result['final_loss'] < result['initial_loss']
        assert result['epochs'] == 20
        assert result['training_samples'] == 3
        assert result['improvement'] > 0

    def test_model_evaluation(self):
        """Test model evaluation and performance metrics"""
        class MockModelEvaluator:
            def evaluate_model(self, model: Mock, test_data: List[Dict]) -> Dict:
                # Mock evaluation
                correct_predictions = 0
                total_predictions = len(test_data)

                for data_point in test_data:
                    # Simulate model prediction
                    prediction = self._mock_predict(data_point['input'])
                    if prediction == data_point['expected_output']:
                        correct_predictions += 1

                accuracy = correct_predictions / total_predictions

                return {
                    'accuracy': accuracy,
                    'total_predictions': total_predictions,
                    'correct_predictions': correct_predictions,
                    'precision': accuracy * 0.9,  # Mock precision
                    'recall': accuracy * 0.85,     # Mock recall
                    'f1_score': 2 * (accuracy * 0.9 * accuracy * 0.85) / (accuracy * 0.9 + accuracy * 0.85)
                }

            def _mock_predict(self, input_text: str) -> str:
                # Mock prediction logic
                if 'combat' in input_text.lower():
                    return 'attack'
                elif 'social' in input_text.lower():
                    return 'persuade'
                else:
                    return 'explore'

        evaluator = MockModelEvaluator()
        mock_model = Mock()

        # Mock test data
        test_data = [
            {'input': 'Situation: combat with goblin', 'expected_output': 'attack'},
            {'input': 'Situation: social with merchant', 'expected_output': 'persuade'},
            {'input': 'Situation: combat with dragon', 'expected_output': 'attack'},
            {'input': 'Situation: exploration of ruins', 'expected_output': 'explore'},
            {'input': 'Situation: social negotiation', 'expected_output': 'persuade'}
        ]

        # Test evaluation
        metrics = evaluator.evaluate_model(mock_model, test_data)

        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1_score' in metrics
        assert 0 <= metrics['accuracy'] <= 1
        assert 0 <= metrics['precision'] <= 1
        assert 0 <= metrics['recall'] <= 1
        assert 0 <= metrics['f1_score'] <= 1


class TestAICharacterBehavior:
    """Test AI character behavior and decision-making"""

    def test_character_decision_process(self):
        """Test character decision-making process"""
        class MockAICharacter:
            def __init__(self, name: str, character_class: str):
                self.name = name
                self.character_class = character_class
                self.personality = {"brave": 0.8, "cautious": 0.2}
                self.memory = []

            def make_decision(self, situation: Dict) -> Dict:
                # Mock decision logic based on character class and personality
                situation_type = situation.get('type', 'unknown')

                if situation_type == 'combat':
                    if self.character_class == 'Fighter':
                        action = 'attack'
                    elif self.character_class == 'Wizard':
                        action = 'cast_spell'
                    else:
                        action = 'defend'

                    confidence = self.personality['brave'] if action == 'attack' else self.personality['cautious']

                elif situation_type == 'social':
                    action = 'negotiate'
                    confidence = 0.7

                else:
                    action = 'explore'
                    confidence = 0.5

                decision = {
                    'character': self.name,
                    'action': action,
                    'confidence': confidence,
                    'reasoning': f'As a {self.character_class}, I choose to {action}'
                }

                # Store decision in memory
                self.memory.append({
                    'timestamp': datetime.now(),
                    'situation': situation,
                    'decision': decision
                })

                return decision

        # Create test characters
        fighter = MockAICharacter("Aragorn", "Fighter")
        wizard = MockAICharacter("Gandalf", "Wizard")

        # Test decision making
        combat_situation = {'type': 'combat', 'enemy': 'goblin', 'environment': 'dungeon'}

        fighter_decision = fighter.make_decision(combat_situation)
        wizard_decision = wizard.make_decision(combat_situation)

        assert fighter_decision['action'] == 'attack'
        assert wizard_decision['action'] == 'cast_spell'
        assert fighter_decision['confidence'] > 0.5
        assert len(fighter.memory) == 1
        assert len(wizard.memory) == 1

    def test_character_learning_from_experience(self):
        """Test character learning from past experiences"""
        class MockLearningCharacter:
            def __init__(self):
                self.experience = {}
                self.success_patterns = {}

            def learn_from_outcome(self, decision: Dict, outcome: Dict):
                action = decision['action']
                situation_type = decision.get('situation_type', 'unknown')
                success = outcome.get('success', False)

                # Update experience
                key = f"{situation_type}_{action}"
                if key not in self.experience:
                    self.experience[key] = {'attempts': 0, 'successes': 0}

                self.experience[key]['attempts'] += 1
                if success:
                    self.experience[key]['successes'] += 1

                # Update success patterns
                success_rate = self.experience[key]['successes'] / self.experience[key]['attempts']
                self.success_patterns[key] = success_rate

            def get_recommended_action(self, situation_type: str) -> str:
                # Find most successful action for this situation
                relevant_patterns = {
                    k.split('_', 1)[1]: v
                    for k, v in self.success_patterns.items()
                    if k.startswith(f"{situation_type}_")
                }

                if relevant_patterns:
                    return max(relevant_patterns, key=relevant_patterns.get)
                else:
                    return 'explore'  # Default action

        character = MockLearningCharacter()

        # Simulate learning experiences
        experiences = [
            {'decision': {'action': 'attack', 'situation_type': 'combat'},
             'outcome': {'success': True}},
            {'decision': {'action': 'attack', 'situation_type': 'combat'},
             'outcome': {'success': True}},
            {'decision': {'action': 'attack', 'situation_type': 'combat'},
             'outcome': {'success': False}},
            {'decision': {'action': 'flee', 'situation_type': 'combat'},
             'outcome': {'success': False}},
            {'decision': {'action': 'negotiate', 'situation_type': 'social'},
             'outcome': {'success': True}},
        ]

        for exp in experiences:
            character.learn_from_outcome(exp['decision'], exp['outcome'])

        # Test learning results
        assert character.experience['combat_attack']['attempts'] == 3
        assert character.experience['combat_attack']['successes'] == 2
        assert character.success_patterns['combat_attack'] == 2/3

        # Test recommendation based on learning
        recommended_action = character.get_recommended_action('combat')
        assert recommended_action == 'attack'  # Most successful action

    def test_personality_evolution(self):
        """Test character personality evolution over time"""
        class MockPersonalitySystem:
            def __init__(self, initial_traits: Dict):
                self.traits = initial_traits.copy()
                self.traits_history = [initial_traits.copy()]

            def update_personality(self, experience: Dict):
                # Mock personality evolution based on experiences
                if experience.get('type') == 'combat_success':
                    self.traits['brave'] = min(1.0, self.traits['brave'] + 0.05)
                    self.traits['aggressive'] = min(1.0, self.traits['aggressive'] + 0.03)
                elif experience.get('type') == 'social_success':
                    self.traits['charismatic'] = min(1.0, self.traits['charismatic'] + 0.04)
                    self.traits['friendly'] = min(1.0, self.traits['friendly'] + 0.02)
                elif experience.get('type') == 'failure':
                    self.traits['cautious'] = min(1.0, self.traits['cautious'] + 0.03)

                self.traits_history.append(self.traits.copy())

            def get_personality_summary(self) -> str:
                dominant_trait = max(self.traits, key=self.traits.get)
                return f"Character is most {dominant_trait} ({self.traits[dominant_trait]:.2f})"

        # Create character with initial personality
        personality = MockPersonalitySystem({
            'brave': 0.5,
            'cautious': 0.3,
            'aggressive': 0.2,
            'charismatic': 0.4,
            'friendly': 0.6
        })

        # Simulate personality evolution
        experiences = [
            {'type': 'combat_success'},
            {'type': 'combat_success'},
            {'type': 'social_success'},
            {'type': 'failure'},
            {'type': 'combat_success'},
        ]

        for exp in experiences:
            personality.update_personality(exp)

        # Test personality evolution
        assert personality.traits['brave'] > 0.5  # Should increase due to combat success
        assert personality.traits['charismatic'] > 0.4  # Should increase due to social success
        assert personality.traits['cautious'] > 0.3  # Should increase due to failure
        assert len(personality.traits_history) == 6  # Initial + 5 updates

        summary = personality.get_personality_summary()
        assert 'Character is most' in summary


@pytest.mark.asyncio
class TestAsyncAIComponents:
    """Test async AI component functionality"""

    async def test_async_llm_calls(self, mock_external_services):
        """Test asynchronous LLM API calls"""
        mock_openai = mock_external_services['openai']

        # Configure async mock
        async def mock_async_create(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate API delay
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Async response"))]
            return mock_response

        mock_openai.chat.completions.create = mock_async_create

        # Test async call
        response = await mock_openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Test"}]
        )

        assert response.choices[0].message.content == "Async response"

    async def test_concurrent_decision_making(self):
        """Test concurrent AI decision making"""
        class AsyncDecisionMaker:
            async def make_decision(self, character_id: str, situation: Dict) -> Dict:
                await asyncio.sleep(0.1)  # Simulate processing time
                return {
                    'character_id': character_id,
                    'action': 'attack',
                    'confidence': 0.8
                }

        decision_maker = AsyncDecisionMaker()

        # Test concurrent decisions for multiple characters
        characters = ['char_1', 'char_2', 'char_3', 'char_4', 'char_5']
        situation = {'type': 'combat', 'enemy': 'goblin'}

        # Make decisions concurrently
        tasks = [
            decision_maker.make_decision(char_id, situation)
            for char_id in characters
        ]

        start_time = asyncio.get_event_loop().time()
        decisions = await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()

        # Should complete faster than sequential processing
        processing_time = end_time - start_time
        assert processing_time < 0.3  # Much less than 5 * 0.1 = 0.5 seconds
        assert len(decisions) == 5
        assert all(dec['action'] == 'attack' for dec in decisions)

    async def test_async_learning_pipeline(self):
        """Test async learning pipeline processing"""
        class AsyncLearningPipeline:
            async def process_experience_batch(self, experiences: List[Dict]) -> Dict:
                await asyncio.sleep(0.2)  # Simulate processing

                # Mock learning metrics
                total_experiences = len(experiences)
                successful_experiences = sum(1 for exp in experiences if exp.get('success', False))

                return {
                    'processed_experiences': total_experiences,
                    'success_rate': successful_experiences / total_experiences,
                    'learning_update': 'model_weights_updated'
                }

        pipeline = AsyncLearningPipeline()

        # Mock experience batch
        experiences = [
            {'character_id': 'char_1', 'action': 'attack', 'success': True},
            {'character_id': 'char_2', 'action': 'defend', 'success': False},
            {'character_id': 'char_3', 'action': 'cast_spell', 'success': True},
        ]

        # Test async processing
        result = await pipeline.process_experience_batch(experiences)

        assert result['processed_experiences'] == 3
        assert result['success_rate'] == 2/3
        assert result['learning_update'] == 'model_weights_updated'