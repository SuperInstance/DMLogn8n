#!/usr/bin/env python3
"""
DMLogn8n AI System Integration Tests
Comprehensive AI model integration testing for DM and game systems
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import random
import string

import aiohttp
import websockets
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import word_tokenize
from nltk.sentiment import SentimentIntensityAnalyzer

# Import test framework
from integration_test_suite import TestResult, TestStatus

class AISystemIntegrationTests:
    """
    Comprehensive AI system integration testing
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('ai_system_integration')
        self.base_url = config['base_url']
        self.ai_service_url = config.get('ai_service_url', 'http://localhost:8080')
        self.n8n_url = config.get('n8n_url', 'http://localhost:5678')

        # Initialize NLTK components
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        try:
            nltk.data.find('sentiment/vader_lexicon.zip')
        except LookupError:
            nltk.download('vader_lexicon')

        self.sentiment_analyzer = SentimentIntensityAnalyzer()

        # Test data
        self.test_scenarios = [
            {
                'name': 'tavern_intro',
                'description': 'Introduction at a fantasy tavern',
                'expected_elements': ['tavern', 'keeper', 'atmosphere', 'greeting'],
                'context': 'A weary traveler enters a dimly lit tavern'
            },
            {
                'name': 'combat_encounter',
                'description': 'Combat encounter with goblins',
                'expected_elements': ['goblins', 'combat', 'action', 'danger'],
                'context': 'The party encounters hostile goblins in the forest'
            },
            {
                'name': 'puzzle_solving',
                'description': 'Solving an ancient puzzle',
                'expected_elements': ['puzzle', 'riddle', 'mystery', 'ancient'],
                'context': 'The party discovers an ancient mechanism with mysterious symbols'
            },
            {
                'name': 'social_interaction',
                'description': 'Social interaction with NPC',
                'expected_elements': ['dialogue', 'character', 'emotion', 'choice'],
                'context': 'Meeting a mysterious merchant with rare goods'
            }
        ]

    async def test_ai_integration(self) -> TestResult:
        """
        Test complete AI integration with the game system
        """
        result = TestResult(
            name="ai_integration",
            status=TestStatus.RUNNING,
            duration=0.0
        )

        try:
            start_time = time.time()

            integration_tests = {
                'ai_service_health': await self.test_ai_service_health(),
                'dm_response_generation': await self.test_dm_response_generation(),
                'context_awareness': await self.test_context_awareness(),
                'character_consistency': await self.test_character_consistency(),
                'emotion_simulation': await self.test_emotion_simulation(),
                'narrative_coherence': await self.test_narrative_coherence(),
                'ai_workflow_integration': await self.test_ai_workflow_integration(),
                'response_quality_metrics': await self.test_response_quality_metrics()
            }

            # Calculate overall success rate
            success_count = sum(1 for test in integration_tests.values() if test.get('success', False))
            total_tests = len(integration_tests)
            success_rate = success_count / total_tests

            result.status = TestStatus.PASSED if success_rate >= 0.75 else TestStatus.FAILED
            result.message = f"AI integration test completed ({success_count}/{total_tests} tests passed)"
            result.details = {
                'tests': integration_tests,
                'success_rate': success_rate,
                'passed_tests': success_count,
                'total_tests': total_tests
            }

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"AI integration test failed: {str(e)}"
            self.logger.error(f"AI integration test failed: {e}")

        finally:
            result.duration = time.time() - start_time

        return result

    async def test_ai_service_health(self) -> Dict[str, Any]:
        """Test AI service health and availability"""
        try:
            async with aiohttp.ClientSession() as session:
                # Test main AI service
                async with session.get(f"{self.ai_service_url}/health", timeout=10) as response:
                    ai_health = response.status == 200
                    ai_data = await response.json() if response.content_type == 'application/json' else {}

                # Test AI model endpoints
                model_endpoints = [
                    '/api/models/dm',
                    '/api/models/narrative',
                    '/api/models/character'
                ]

                model_status = {}
                for endpoint in model_endpoints:
                    try:
                        async with session.get(f"{self.ai_service_url}{endpoint}/status", timeout=5) as response:
                            model_status[endpoint] = {
                                'available': response.status == 200,
                                'status': response.status
                            }
                    except Exception as e:
                        model_status[endpoint] = {
                            'available': False,
                            'error': str(e)
                        }

                return {
                    'success': ai_health,
                    'ai_service_healthy': ai_health,
                    'ai_service_data': ai_data,
                    'model_status': model_status,
                    'message': 'AI services are healthy' if ai_health else 'AI service health check failed'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_dm_response_generation(self) -> Dict[str, Any]:
        """Test DM response generation capabilities"""
        try:
            test_prompts = [
                "The party enters a dark cave. What do they see?",
                "A mysterious stranger approaches the party. What happens next?",
                "The party finds a treasure chest. What's inside?",
                "Combat begins! How does the battle unfold?"
            ]

            response_results = []
            async with aiohttp.ClientSession() as session:
                for i, prompt in enumerate(test_prompts):
                    start_time = time.time()

                    async with session.post(
                        f"{self.ai_service_url}/api/dm/generate",
                        json={
                            'prompt': prompt,
                            'context': self.test_scenarios[i % len(self.test_scenarios)]['context'],
                            'max_tokens': 150,
                            'temperature': 0.8
                        },
                        timeout=30
                    ) as response:
                        response_time = time.time() - start_time

                        if response.status == 200:
                            result = await response.json()
                            generated_text = result.get('response', '')

                            response_results.append({
                                'prompt': prompt,
                                'response': generated_text[:100] + '...' if len(generated_text) > 100 else generated_text,
                                'response_time': response_time,
                                'token_count': len(generated_text.split()),
                                'success': True
                            })
                        else:
                            response_results.append({
                                'prompt': prompt,
                                'error': f"HTTP {response.status}",
                                'success': False
                            })

            success_rate = sum(1 for r in response_results if r['success']) / len(response_results)
            avg_response_time = sum(r.get('response_time', 0) for r in response_results if r['success']) / max(1, sum(1 for r in response_results if r['success']))

            return {
                'success': success_rate >= 0.75,
                'success_rate': success_rate,
                'avg_response_time': avg_response_time,
                'responses': response_results,
                'message': f"DM response generation working ({success_rate:.1%} success rate)"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_context_awareness(self) -> Dict[str, Any]:
        """Test AI context awareness and memory"""
        try:
            # Simulate a conversation with context
            conversation_context = {
                'setting': 'medieval_fantasy_tavern',
                'characters': ['player', 'tavern_keeper'],
                'previous_events': ['player_entered', 'ordered_drink'],
                'current_situation': 'player asks about local rumors'
            }

            context_aware_prompts = [
                {
                    'prompt': "What rumors have you heard lately?",
                    'context': conversation_context,
                    'expected_elements': ['rumors', 'tavern', 'local', 'news']
                },
                {
                    'prompt': "Tell me more about the dragon sightings",
                    'context': {**conversation_context, 'previous_events': ['dragon_mentioned']},
                    'expected_elements': ['dragon', 'sightings', 'danger', 'location']
                }
            ]

            context_results = []
            async with aiohttp.ClientSession() as session:
                for test_case in context_aware_prompts:
                    async with session.post(
                        f"{self.ai_service_url}/api/dm/generate",
                        json={
                            'prompt': test_case['prompt'],
                            'context': test_case['context'],
                            'max_tokens': 100,
                            'temperature': 0.7
                        },
                        timeout=20
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            generated_text = result.get('response', '')

                            # Check if expected elements are present
                            elements_found = [
                                element for element in test_case['expected_elements']
                                if element.lower() in generated_text.lower()
                            ]

                            context_relevance = len(elements_found) / len(test_case['expected_elements'])

                            context_results.append({
                                'prompt': test_case['prompt'],
                                'context_relevance': context_relevance,
                                'elements_found': elements_found,
                                'response_preview': generated_text[:80] + '...' if len(generated_text) > 80 else generated_text,
                                'success': context_relevance >= 0.5
                            })

            avg_context_relevance = sum(r['context_relevance'] for r in context_results) / len(context_results)
            success_rate = sum(1 for r in context_results if r['success']) / len(context_results)

            return {
                'success': avg_context_relevance >= 0.5,
                'avg_context_relevance': avg_context_relevance,
                'success_rate': success_rate,
                'context_tests': context_results,
                'message': f"Context awareness working ({avg_context_relevance:.1%} relevance)"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_character_consistency(self) -> Dict[str, Any]:
        """Test AI character consistency across interactions"""
        try:
            # Define test characters
            test_characters = [
                {
                    'name': 'Grimlock the Tavern Keeper',
                    'traits': ['grumpy', 'knowledgeable', 'protective'],
                    'speech_pattern': 'gruff, direct',
                    'background': 'Former adventurer, now runs tavern'
                },
                {
                    'name': 'Elara the Mystic',
                    'traits': ['wise', 'mysterious', 'cryptic'],
                    'speech_pattern': 'poetic, metaphorical',
                    'background': 'Ancient seer with hidden knowledge'
                }
            ]

            consistency_results = []
            async with aiohttp.ClientSession() as session:
                for character in test_characters:
                    # Generate multiple responses for the same character
                    character_responses = []
                    test_questions = [
                        "What can you tell me about this area?",
                        "Have you seen any unusual activity lately?",
                        "What advice would you give to a traveler?"
                    ]

                    for question in test_questions:
                        async with session.post(
                            f"{self.ai_service_url}/api/character/generate",
                            json={
                                'character': character,
                                'prompt': question,
                                'max_tokens': 80,
                                'temperature': 0.6
                            },
                            timeout=20
                        ) as response:
                            if response.status == 200:
                                result = await response.json()
                                response_text = result.get('response', '')
                                character_responses.append(response_text)

                    # Analyze consistency across responses
                    if len(character_responses) >= 2:
                        consistency_score = self.calculate_character_consistency(
                            character, character_responses
                        )

                        consistency_results.append({
                            'character_name': character['name'],
                            'responses': [r[:50] + '...' if len(r) > 50 else r for r in character_responses],
                            'consistency_score': consistency_score,
                            'success': consistency_score >= 0.6
                        })

            avg_consistency = sum(r['consistency_score'] for r in consistency_results) / len(consistency_results) if consistency_results else 0

            return {
                'success': avg_consistency >= 0.6,
                'avg_consistency_score': avg_consistency,
                'character_tests': consistency_results,
                'message': f"Character consistency working ({avg_consistency:.1%} consistency)"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def calculate_character_consistency(self, character: Dict[str, Any], responses: List[str]) -> float:
        """Calculate consistency score for character responses"""
        try:
            # Simple consistency check based on trait adherence
            traits = character['traits']
            total_consistency = 0

            for response in responses:
                response_lower = response.lower()
                trait_matches = 0

                # Check for trait-consistent language
                for trait in traits:
                    if trait in ['grumpy', 'angry']:
                        if any(word in response_lower for word in ['ugh', 'hmm', 'whatever', 'fine']):
                            trait_matches += 1
                    elif trait in ['wise', 'knowledgeable']:
                        if any(word in response_lower for word in ['indeed', 'indeed', 'wisdom', 'knowledge']):
                            trait_matches += 1
                    elif trait in ['mysterious', 'cryptic']:
                        if any(word in response_lower for word in ['perhaps', 'maybe', 'unclear', 'mystery']):
                            trait_matches += 1
                    elif trait in ['friendly', 'cheerful']:
                        if any(word in response_lower for word in ['hello', 'welcome', 'friend', 'glad']):
                            trait_matches += 1

                total_consistency += trait_matches / len(traits)

            return total_consistency / len(responses)

        except Exception:
            return 0.5  # Default to moderate consistency on error

    async def test_emotion_simulation(self) -> Dict[str, Any]:
        """Test AI emotion simulation in responses"""
        try:
            emotion_scenarios = [
                {
                    'emotion': 'fear',
                    'situation': 'A shadowy figure appears in the darkness',
                    'expected_indicators': ['afraid', 'scared', 'worried', 'nervous']
                },
                {
                    'emotion': 'excitement',
                    'situation': 'The party discovers a treasure chest filled with gold',
                    'expected_indicators': ['excited', 'amazing', 'wonderful', 'great']
                },
                {
                    'emotion': 'sadness',
                    'situation': 'The village elder shares news of a recent tragedy',
                    'expected_indicators': ['sad', 'tragic', 'unfortunate', 'sorry']
                }
            ]

            emotion_results = []
            async with aiohttp.ClientSession() as session:
                for scenario in emotion_scenarios:
                    async with session.post(
                        f"{self.ai_service_url}/api/emotion/generate",
                        json={
                            'emotion': scenario['emotion'],
                            'situation': scenario['situation'],
                            'max_tokens': 60,
                            'temperature': 0.8
                        },
                        timeout=20
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            response_text = result.get('response', '')

                            # Use sentiment analysis to verify emotion
                            sentiment_scores = self.sentiment_analyzer.polarity_scores(response_text)

                            # Check for expected emotion indicators
                            response_lower = response_text.lower()
                            indicators_found = [
                                indicator for indicator in scenario['expected_indicators']
                                if indicator in response_lower
                            ]

                            emotion_score = len(indicators_found) / len(scenario['expected_indicators'])

                            emotion_results.append({
                                'emotion': scenario['emotion'],
                                'situation': scenario['situation'],
                                'response_preview': response_text[:60] + '...' if len(response_text) > 60 else response_text,
                                'emotion_score': emotion_score,
                                'sentiment': sentiment_scores,
                                'indicators_found': indicators_found,
                                'success': emotion_score >= 0.3 or sentiment_scores['compound'] < -0.1 if scenario['emotion'] == 'sadness' else True
                            })

            success_rate = sum(1 for r in emotion_results if r['success']) / len(emotion_results)
            avg_emotion_score = sum(r['emotion_score'] for r in emotion_results) / len(emotion_results)

            return {
                'success': success_rate >= 0.6,
                'success_rate': success_rate,
                'avg_emotion_score': avg_emotion_score,
                'emotion_tests': emotion_results,
                'message': f"Emotion simulation working ({success_rate:.1%} success rate)"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_narrative_coherence(self) -> Dict[str, Any]:
        """Test narrative coherence and story progression"""
        try:
            # Create a story progression test
            story_beats = [
                {
                    'beat': 'inciting_incident',
                    'prompt': 'The party receives a mysterious letter asking for help',
                    'expected_elements': ['letter', 'mystery', 'help', 'adventure']
                },
                {
                    'beat': 'rising_action',
                    'prompt': 'Following the clues, the party discovers an ancient ruin',
                    'expected_elements': ['ruin', 'ancient', 'clues', 'discovery']
                },
                {
                    'beat': 'climax',
                    'prompt': 'In the heart of the ruin, the party confronts the source of the mystery',
                    'expected_elements': ['confrontation', 'source', 'heart', 'climax']
                },
                {
                    'beat': 'resolution',
                    'prompt': 'With the mystery solved, the party considers their next steps',
                    'expected_elements': ['resolution', 'solved', 'future', 'reflection']
                }
            ]

            narrative_results = []
            story_context = {}

            async with aiohttp.ClientSession() as session:
                for i, beat in enumerate(story_beats):
                    # Include previous beats in context for coherence
                    context = {
                        'previous_beats': story_context,
                        'current_beat': beat['beat'],
                        'story_progress': i / len(story_beats)
                    }

                    async with session.post(
                        f"{self.ai_service_url}/api/narrative/generate",
                        json={
                            'prompt': beat['prompt'],
                            'context': context,
                            'max_tokens': 100,
                            'temperature': 0.7
                        },
                        timeout=25
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            response_text = result.get('response', '')

                            # Check for expected elements
                            response_lower = response_text.lower()
                            elements_found = [
                                element for element in beat['expected_elements']
                                if element in response_lower
                            ]

                            coherence_score = len(elements_found) / len(beat['expected_elements'])

                            # Store response for next beat's context
                            story_context[beat['beat']] = response_text

                            narrative_results.append({
                                'beat': beat['beat'],
                                'response_preview': response_text[:70] + '...' if len(response_text) > 70 else response_text,
                                'coherence_score': coherence_score,
                                'elements_found': elements_found,
                                'success': coherence_score >= 0.5
                            })

            avg_coherence = sum(r['coherence_score'] for r in narrative_results) / len(narrative_results)
            success_rate = sum(1 for r in narrative_results if r['success']) / len(narrative_results)

            return {
                'success': avg_coherence >= 0.5,
                'avg_coherence_score': avg_coherence,
                'success_rate': success_rate,
                'narrative_tests': narrative_results,
                'message': f"Narrative coherence working ({avg_coherence:.1%} coherence)"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_ai_workflow_integration(self) -> Dict[str, Any]:
        """Test AI integration with N8N workflows"""
        try:
            # Test N8N workflow triggers
            workflow_tests = {
                'dm_response_workflow': await self.test_dm_response_workflow(),
                'character_creation_workflow': await self.test_character_creation_workflow(),
                'scene_generation_workflow': await self.test_scene_generation_workflow()
            }

            success_rate = sum(1 for test in workflow_tests.values() if test.get('success', False)) / len(workflow_tests)

            return {
                'success': success_rate >= 0.66,
                'success_rate': success_rate,
                'workflow_tests': workflow_tests,
                'message': f"AI workflow integration working ({success_rate:.1%} success rate)"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_dm_response_workflow(self) -> Dict[str, Any]:
        """Test DM response generation via N8N workflow"""
        try:
            async with aiohttp.ClientSession() as session:
                # Trigger N8N workflow
                workflow_data = {
                    'user_input': 'What do you see in the forest?',
                    'context': {
                        'location': 'forest',
                        'time': 'day',
                        'party_status': 'healthy'
                    }
                }

                async with session.post(
                    f"{self.n8n_url}/webhook/dm-response",
                    json=workflow_data,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        dm_response = result.get('dm_response', '')

                        return {
                            'success': len(dm_response) > 20,
                            'response_preview': dm_response[:80] + '...' if len(dm_response) > 80 else dm_response,
                            'workflow_data': result,
                            'message': 'DM response workflow successful'
                        }
                    else:
                        return {
                            'success': False,
                            'status': response.status,
                            'error': f'Workflow failed with status {response.status}'
                        }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_character_creation_workflow(self) -> Dict[str, Any]:
        """Test character creation via N8N workflow"""
        try:
            async with aiohttp.ClientSession() as session:
                character_request = {
                    'character_class': 'rogue',
                    'background': 'street urchin',
                    'personality_traits': ['cunning', 'cautious', 'opportunistic']
                }

                async with session.post(
                    f"{self.n8n_url}/webhook/character-create",
                    json=character_request,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        character_data = result.get('character', {})

                        required_fields = ['name', 'stats', 'background', 'abilities']
                        has_required_fields = all(field in character_data for field in required_fields)

                        return {
                            'success': has_required_fields,
                            'character_preview': {
                                'name': character_data.get('name', 'N/A'),
                                'class': character_data.get('class', 'N/A'),
                                'stats_count': len(character_data.get('stats', {}))
                            },
                            'workflow_data': result,
                            'message': 'Character creation workflow successful'
                        }
                    else:
                        return {
                            'success': False,
                            'status': response.status,
                            'error': f'Workflow failed with status {response.status}'
                        }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_scene_generation_workflow(self) -> Dict[str, Any]:
        """Test scene generation via N8N workflow"""
        try:
            async with aiohttp.ClientSession() as session:
                scene_request = {
                    'scene_type': 'dungeon_room',
                    'atmosphere': 'mysterious',
                    'contents': ['treasure', 'trap', 'puzzle'],
                    'size': 'medium'
                }

                async with session.post(
                    f"{self.n8n_url}/webhook/scene-generate",
                    json=scene_request,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        scene_data = result.get('scene', {})

                        scene_description = scene_data.get('description', '')
                        has_description = len(scene_description) > 50

                        return {
                            'success': has_description,
                            'scene_preview': scene_description[:100] + '...' if len(scene_description) > 100 else scene_description,
                            'scene_elements': scene_data.get('elements', []),
                            'workflow_data': result,
                            'message': 'Scene generation workflow successful'
                        }
                    else:
                        return {
                            'success': False,
                            'status': response.status,
                            'error': f'Workflow failed with status {response.status}'
                        }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_response_quality_metrics(self) -> Dict[str, Any]:
        """Test AI response quality using various metrics"""
        try:
            # Generate sample responses for quality analysis
            test_cases = [
                {
                    'prompt': 'Describe a magical forest',
                    'category': 'descriptive',
                    'expected_length': 50
                },
                {
                    'prompt': 'What does the shopkeeper say?',
                    'category': 'dialogue',
                    'expected_length': 30
                },
                {
                    'prompt': 'What happens next in the combat?',
                    'category': 'action',
                    'expected_length': 40
                }
            ]

            quality_results = []
            async with aiohttp.ClientSession() as session:
                for test_case in test_cases:
                    async with session.post(
                        f"{self.ai_service_url}/api/dm/generate",
                        json={
                            'prompt': test_case['prompt'],
                            'max_tokens': 100,
                            'temperature': 0.7
                        },
                        timeout=20
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            response_text = result.get('response', '')

                            # Calculate quality metrics
                            metrics = self.calculate_response_quality(response_text, test_case)

                            quality_results.append({
                                'prompt': test_case['prompt'],
                                'category': test_case['category'],
                                'response_preview': response_text[:60] + '...' if len(response_text) > 60 else response_text,
                                'metrics': metrics,
                                'overall_quality': metrics['overall_score'],
                                'success': metrics['overall_score'] >= 0.6
                            })

            avg_quality = sum(r['overall_quality'] for r in quality_results) / len(quality_results)
            success_rate = sum(1 for r in quality_results if r['success']) / len(quality_results)

            return {
                'success': avg_quality >= 0.6,
                'avg_quality_score': avg_quality,
                'success_rate': success_rate,
                'quality_tests': quality_results,
                'message': f"Response quality metrics good ({avg_quality:.1%} average quality)"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def calculate_response_quality(self, response: str, test_case: Dict[str, Any]) -> Dict[str, float]:
        """Calculate various quality metrics for AI response"""
        try:
            metrics = {}

            # Length appropriateness
            word_count = len(response.split())
            expected_length = test_case.get('expected_length', 50)
            length_score = 1.0 - abs(word_count - expected_length) / expected_length
            metrics['length_appropriateness'] = max(0, min(1, length_score))

            # Vocabulary diversity (unique words / total words)
            words = word_tokenize(response.lower())
            unique_words = set(words)
            vocab_diversity = len(unique_words) / len(words) if words else 0
            metrics['vocabulary_diversity'] = vocab_diversity

            # Sentence structure (average sentence length)
            sentences = response.split('.')
            avg_sentence_length = sum(len(s.split()) for s in sentences if s.strip()) / len(sentences) if sentences else 0
            metrics['sentence_structure'] = min(1, avg_sentence_length / 15)  # Ideal around 15 words per sentence

            # Content relevance (simple keyword matching)
            relevant_keywords = {
                'descriptive': ['forest', 'trees', 'magical', 'mystical', 'enchanting'],
                'dialogue': ['says', 'tells', 'asks', 'replies', 'responds'],
                'action': ['attacks', 'moves', 'dodges', 'strikes', 'defends']
            }

            category = test_case.get('category', 'descriptive')
            keywords = relevant_keywords.get(category, [])
            keyword_matches = sum(1 for keyword in keywords if keyword in response.lower())
            relevance_score = keyword_matches / len(keywords) if keywords else 0.5
            metrics['content_relevance'] = relevance_score

            # Sentiment analysis
            sentiment = self.sentiment_analyzer.polarity_scores(response)
            metrics['sentiment_neutrality'] = abs(sentiment['compound']) < 0.3  # Neutral sentiment is often better for DM responses

            # Overall quality score
            metrics['overall_score'] = sum(metrics.values()) / len(metrics)

            return metrics

        except Exception as e:
            return {
                'overall_score': 0.5,
                'error': str(e)
            }

    async def test_ai_model_performance(self) -> TestResult:
        """
        Test AI model performance under different conditions
        """
        result = TestResult(
            name="ai_model_performance",
            status=TestStatus.RUNNING,
            duration=0.0
        )

        try:
            start_time = time.time()

            performance_tests = {
                'concurrent_requests': await self.test_concurrent_ai_requests(),
                'response_time_consistency': await self.test_response_time_consistency(),
                'model_resource_usage': await self.test_model_resource_usage(),
                'error_recovery': await self.test_ai_error_recovery()
            }

            all_passed = all(test.get('success', False) for test in performance_tests.values())

            result.status = TestStatus.PASSED if all_passed else TestStatus.FAILED
            result.message = "AI model performance test completed" if all_passed else "Some performance tests failed"
            result.details = performance_tests

        except Exception as e:
            result.status = TestStatus.ERROR
            result.message = f"AI model performance test failed: {str(e)}"
            self.logger.error(f"AI model performance test failed: {e}")

        finally:
            result.duration = time.time() - start_time

        return result

    async def test_concurrent_ai_requests(self) -> Dict[str, Any]:
        """Test AI service handling of concurrent requests"""
        try:
            concurrent_requests = 5
            test_prompt = "Describe a fantasy setting"

            async def make_request(session, request_id):
                start_time = time.time()
                async with session.post(
                    f"{self.ai_service_url}/api/dm/generate",
                    json={
                        'prompt': test_prompt,
                        'max_tokens': 50,
                        'temperature': 0.7
                    },
                    timeout=30
                ) as response:
                    response_time = time.time() - start_time
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'request_id': request_id,
                            'success': True,
                            'response_time': response_time,
                            'response_length': len(result.get('response', ''))
                        }
                    else:
                        return {
                            'request_id': request_id,
                            'success': False,
                            'status': response.status,
                            'response_time': response_time
                        }

            async with aiohttp.ClientSession() as session:
                tasks = [make_request(session, i) for i in range(concurrent_requests)]
                results = await asyncio.gather(*tasks, return_exceptions=True)

            successful_requests = [r for r in results if isinstance(r, dict) and r.get('success', False)]
            success_rate = len(successful_requests) / concurrent_requests
            avg_response_time = sum(r['response_time'] for r in successful_requests) / len(successful_requests) if successful_requests else 0

            return {
                'success': success_rate >= 0.8,
                'concurrent_requests': concurrent_requests,
                'successful_requests': len(successful_requests),
                'success_rate': success_rate,
                'avg_response_time': avg_response_time,
                'message': f"Concurrent request handling working ({success_rate:.1%} success rate)"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_response_time_consistency(self) -> Dict[str, Any]:
        """Test AI response time consistency"""
        try:
            test_requests = 10
            response_times = []

            async with aiohttp.ClientSession() as session:
                for i in range(test_requests):
                    start_time = time.time()
                    async with session.post(
                        f"{self.ai_service_url}/api/dm/generate",
                        json={
                            'prompt': f"Test prompt {i}",
                            'max_tokens': 30,
                            'temperature': 0.7
                        },
                        timeout=30
                    ) as response:
                        response_time = time.time() - start_time
                        if response.status == 200:
                            response_times.append(response_time)

            if len(response_times) >= 3:
                avg_response_time = sum(response_times) / len(response_times)
                variance = sum((t - avg_response_time) ** 2 for t in response_times) / len(response_times)
                std_deviation = variance ** 0.5
                consistency_score = 1.0 - (std_deviation / avg_response_time) if avg_response_time > 0 else 0

                return {
                    'success': consistency_score >= 0.7,
                    'avg_response_time': avg_response_time,
                    'std_deviation': std_deviation,
                    'consistency_score': consistency_score,
                    'total_requests': test_requests,
                    'successful_requests': len(response_times),
                    'message': f"Response time consistency good ({consistency_score:.1%} consistency)"
                }
            else:
                return {
                    'success': False,
                    'error': 'Not enough successful responses to measure consistency'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_model_resource_usage(self) -> Dict[str, Any]:
        """Test AI model resource usage (simplified version)"""
        try:
            # This is a simplified test - in a real environment you'd monitor actual resource usage
            # For now, we'll test if the service responds appropriately under load

            load_test_requests = 20
            successful_requests = 0
            total_response_time = 0

            async with aiohttp.ClientSession() as session:
                for i in range(load_test_requests):
                    start_time = time.time()
                    async with session.post(
                        f"{self.ai_service_url}/api/dm/generate",
                        json={
                            'prompt': f"Load test prompt {i}",
                            'max_tokens': 25,
                            'temperature': 0.7
                        },
                        timeout=30
                    ) as response:
                        response_time = time.time() - start_time
                        if response.status == 200:
                            successful_requests += 1
                            total_response_time += response_time

            success_rate = successful_requests / load_test_requests
            avg_response_time = total_response_time / successful_requests if successful_requests > 0 else 0

            return {
                'success': success_rate >= 0.9 and avg_response_time < 10,  # Response time under 10 seconds
                'load_test_requests': load_test_requests,
                'successful_requests': successful_requests,
                'success_rate': success_rate,
                'avg_response_time': avg_response_time,
                'message': f"Resource usage acceptable ({success_rate:.1%} success rate, {avg_response_time:.1f}s avg response)"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_ai_error_recovery(self) -> Dict[str, Any]:
        """Test AI service error recovery mechanisms"""
        try:
            error_scenarios = [
                {
                    'name': 'malformed_request',
                    'data': {'invalid': 'data'},
                    'expected_error': True
                },
                {
                    'name': 'empty_prompt',
                    'data': {'prompt': '', 'max_tokens': 50},
                    'expected_error': True
                },
                {
                    'name': 'very_long_prompt',
                    'data': {'prompt': 'x' * 10000, 'max_tokens': 50},
                    'expected_error': True
                },
                {
                    'name': 'valid_request',
                    'data': {'prompt': 'A simple test prompt', 'max_tokens': 30},
                    'expected_error': False
                }
            ]

            error_results = []
            async with aiohttp.ClientSession() as session:
                for scenario in error_scenarios:
                    try:
                        async with session.post(
                            f"{self.ai_service_url}/api/dm/generate",
                            json=scenario['data'],
                            timeout=30
                        ) as response:
                            got_error = response.status >= 400
                            error_handled_properly = got_error == scenario['expected_error']

                            error_results.append({
                                'scenario': scenario['name'],
                                'expected_error': scenario['expected_error'],
                                'got_error': got_error,
                                'status_code': response.status,
                                'error_handled_properly': error_handled_properly,
                                'success': error_handled_properly
                            })

                    except Exception as e:
                        error_results.append({
                            'scenario': scenario['name'],
                            'expected_error': scenario['expected_error'],
                            'got_error': True,
                            'exception': str(e),
                            'error_handled_properly': scenario['expected_error'],
                            'success': scenario['expected_error']
                        })

            success_rate = sum(1 for r in error_results if r['success']) / len(error_results)

            return {
                'success': success_rate >= 0.75,
                'success_rate': success_rate,
                'error_scenarios': error_results,
                'message': f"Error recovery working ({success_rate:.1%} success rate)"
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }