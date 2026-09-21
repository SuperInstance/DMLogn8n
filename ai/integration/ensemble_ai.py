#!/usr/bin/env python3
"""
Advanced AI Ensemble System - Combines multiple AI models for superior results
Provides intelligent model fusion, consensus building, and quality enhancement
"""

import asyncio
import time
import json
import logging
import numpy as np
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import hashlib
from collections import defaultdict
import difflib
import re

logger = logging.getLogger(__name__)

class EnsembleMethod(Enum):
    """Ensemble combination methods"""
    MAJORITY_VOTE = "majority_vote"
    WEIGHTED_AVERAGE = "weighted_average"
    CONSENSUS_BUILDING = "consensus_building"
    BEST_OF_N = "best_of_n"
    RANKED_CHOICE = "ranked_choice"
    CONFIDENCE_WEIGHTED = "confidence_weighted"
    EXPERT_WEIGHTED = "expert_weighted"
    DIVERSITY_ENHANCED = "diversity_enhanced"

class TaskType(Enum):
    """Task types for ensemble selection"""
    TEXT_GENERATION = "text_generation"
    QUESTION_ANSWERING = "question_answering"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    CODE_GENERATION = "code_generation"
    ANALYSIS = "analysis"
    CREATIVE_WRITING = "creative_writing"
    FACTUAL_RETRIEVAL = "factual_retrieval"

@dataclass
class ModelConfig:
    """Configuration for ensemble member model"""
    name: str
    weight: float = 1.0
    specialty_tasks: List[TaskType] = None
    confidence_threshold: float = 0.5
    max_tokens: int = 2048
    temperature: float = 0.7
    cost_factor: float = 1.0
    reliability_score: float = 0.8
    speed_factor: float = 1.0
    quality_factor: float = 1.0

@dataclass
class EnsembleRequest:
    """Request to ensemble system"""
    prompt: str
    task_type: TaskType
    method: EnsembleMethod = EnsembleMethod.WEIGHTED_AVERAGE
    max_responses: int = 3
    timeout: float = 30.0
    context: Optional[Dict[str, Any]] = None
    quality_threshold: float = 0.7
    diversity_requirement: bool = False

@dataclass
class ModelResponse:
    """Individual model response"""
    model_name: str
    content: str
    confidence: float
    response_time: float
    token_usage: int
    cost: float
    quality_score: float
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class EnsembleResponse:
    """Combined ensemble response"""
    content: str
    confidence: float
    method: EnsembleMethod
    contributing_models: List[str]
    individual_responses: List[ModelResponse]
    consensus_score: float
    diversity_score: float
    processing_time: float
    cost: float
    metadata: Dict[str, Any]

class AIEnsemble:
    """Advanced AI ensemble system for superior results"""

    def __init__(self, model_configs: Optional[List[ModelConfig]] = None):
        self.model_configs = model_configs or self._get_default_configs()
        self.model_scores: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.response_cache: Dict[str, EnsembleResponse] = {}

        # Performance metrics
        self.ensemble_stats = {
            "total_requests": 0,
            "average_response_time": 0.0,
            "average_confidence": 0.0,
            "consensus_rate": 0.0,
            "diversity_rate": 0.0,
            "cost_savings": 0.0
        }

        # Initialize model performance tracking
        self._initialize_performance_tracking()

        logger.info(f"AIEnsemble initialized with {len(self.model_configs)} models")

    def _get_default_configs(self) -> List[ModelConfig]:
        """Get default model configurations"""
        return [
            ModelConfig(
                name="gpt-4-turbo",
                weight=1.2,
                specialty_tasks=[TaskType.ANALYSIS, TaskType.CODE_GENERATION, TaskType.QUESTION_ANSWERING],
                reliability_score=0.9,
                quality_factor=1.1,
                cost_factor=1.5
            ),
            ModelConfig(
                name="claude-3-sonnet",
                weight=1.1,
                specialty_tasks=[TaskType.CREATIVE_WRITING, TaskType.ANALYSIS, TaskType.SUMMARIZATION],
                reliability_score=0.85,
                quality_factor=1.05,
                cost_factor=1.2
            ),
            ModelConfig(
                name="gpt-3.5-turbo",
                weight=0.8,
                specialty_tasks=[TaskType.TEXT_GENERATION, TaskType.TRANSLATION],
                reliability_score=0.75,
                speed_factor=1.5,
                cost_factor=0.5
            ),
            ModelConfig(
                name="claude-instant",
                weight=0.7,
                specialty_tasks=[TaskType.TEXT_GENERATION, TaskType.CREATIVE_WRITING],
                reliability_score=0.7,
                speed_factor=2.0,
                cost_factor=0.3
            )
        ]

    def _initialize_performance_tracking(self):
        """Initialize performance tracking for models"""
        for config in self.model_configs:
            self.model_scores[config.name] = {
                "accuracy": 0.8,
                "speed": 1.0,
                "cost_efficiency": 1.0,
                "reliability": config.reliability_score,
                "quality": config.quality_factor,
                "total_requests": 0,
                "success_count": 0
            }

    async def process_request(self, request: EnsembleRequest) -> EnsembleResponse:
        """Process ensemble request"""
        start_time = time.time()
        self.ensemble_stats["total_requests"] += 1

        try:
            # Check cache first
            cache_key = self._generate_cache_key(request)
            if cache_key in self.response_cache:
                cached_response = self.response_cache[cache_key]
                logger.debug("Ensemble cache hit")
                return cached_response

            # Select best models for this task
            selected_models = await self._select_models(request)

            # Get responses from selected models
            individual_responses = await self._get_model_responses(request, selected_models)

            # Combine responses using specified method
            ensemble_result = await self._combine_responses(
                individual_responses, request.method, request
            )

            # Calculate ensemble metrics
            consensus_score = self._calculate_consensus(individual_responses)
            diversity_score = self._calculate_diversity(individual_responses)

            # Create ensemble response
            ensemble_response = EnsembleResponse(
                content=ensemble_result["content"],
                confidence=ensemble_result["confidence"],
                method=request.method,
                contributing_models=[resp.model_name for resp in individual_responses],
                individual_responses=individual_responses,
                consensus_score=consensus_score,
                diversity_score=diversity_score,
                processing_time=time.time() - start_time,
                cost=sum(resp.cost for resp in individual_responses),
                metadata={
                    "selected_models": selected_models,
                    "method_details": ensemble_result.get("details", {}),
                    "quality_factors": [resp.quality_score for resp in individual_responses]
                }
            )

            # Update performance metrics
            self._update_performance_metrics(ensemble_response)

            # Cache response
            self.response_cache[cache_key] = ensemble_response

            logger.info(f"Ensemble processed in {ensemble_response.processing_time:.3f}s "
                       f"using {len(individual_responses)} models")
            return ensemble_response

        except Exception as e:
            logger.error(f"Ensemble processing failed: {e}")
            raise

    async def _select_models(self, request: EnsembleRequest) -> List[str]:
        """Select best models for the given task"""
        model_scores = {}

        for config in self.model_configs:
            score = 0.0

            # Task specialization score
            if request.task_type in config.specialty_tasks:
                score += 2.0
            else:
                score += 0.5

            # Historical performance score
            perf_score = (
                self.model_scores[config.name]["accuracy"] * 0.4 +
                self.model_scores[config.name]["quality"] * 0.3 +
                self.model_scores[config.name]["reliability"] * 0.3
            )
            score += perf_score

            # Speed consideration
            speed_bonus = 1.0 / config.speed_factor
            score += speed_bonus * 0.2

            # Cost consideration
            cost_penalty = config.cost_factor * 0.1
            score -= cost_penalty

            # Weight adjustment
            score *= config.weight

            model_scores[config.name] = score

        # Sort by score and select top models
        sorted_models = sorted(model_scores.items(), key=lambda x: x[1], reverse=True)
        selected = [model for model, _ in sorted_models[:request.max_responses]]

        logger.debug(f"Selected models for {request.task_type}: {selected}")
        return selected

    async def _get_model_responses(self, request: EnsembleRequest, model_names: List[str]) -> List[ModelResponse]:
        """Get responses from multiple models concurrently"""
        tasks = [
            self._get_single_model_response(request, model_name)
            for model_name in model_names
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out failed responses
        valid_responses = []
        for response in responses:
            if isinstance(response, ModelResponse):
                valid_responses.append(response)
            elif isinstance(response, Exception):
                logger.warning(f"Model response failed: {response}")

        return valid_responses

    async def _get_single_model_response(self, request: EnsembleRequest, model_name: str) -> ModelResponse:
        """Get response from a single model"""
        config = next((c for c in self.model_configs if c.name == model_name), None)
        if not config:
            raise ValueError(f"Model config not found: {model_name}")

        start_time = time.time()

        try:
            # Simulate model API call
            # In a real implementation, this would call the actual model APIs
            await asyncio.sleep(0.1 / config.speed_factor)  # Simulate different speeds

            # Generate mock response based on model characteristics
            content = await self._generate_mock_response(request, model_name, config)

            # Calculate confidence and quality based on task and model
            confidence = self._calculate_confidence(request, model_name, config)
            quality_score = self._calculate_quality_score(content, request, config)

            response_time = time.time() - start_time
            token_usage = len(content.split())
            cost = (token_usage / 1000) * 0.01 * config.cost_factor

            response = ModelResponse(
                model_name=model_name,
                content=content,
                confidence=confidence,
                response_time=response_time,
                token_usage=token_usage,
                cost=cost,
                quality_score=quality_score,
                metadata={
                    "temperature": config.temperature,
                    "max_tokens": config.max_tokens,
                    "specialty": config.specialty_tasks
                }
            )

            # Update model performance
            self._update_model_performance(model_name, response, request)

            return response

        except Exception as e:
            logger.error(f"Model {model_name} failed: {e}")
            raise

    async def _generate_mock_response(self, request: EnsembleRequest, model_name: str, config: ModelConfig) -> str:
        """Generate mock response based on model characteristics"""
        base_responses = {
            TaskType.TEXT_GENERATION: [
                f"This is a {model_name} generated text response to: {request.prompt[:50]}...",
                f"Based on the prompt, {model_name} creates this well-structured response.",
                f"Here's {model_name}'s thoughtful response to your query."
            ],
            TaskType.QUESTION_ANSWERING: [
                f"According to {model_name}'s analysis, the answer is comprehensive and well-researched.",
                f"{model_name} provides this detailed answer to your question.",
                f"Based on {model_name}'s knowledge base, here's the response."
            ],
            TaskType.SUMMARIZATION: [
                f"Summary by {model_name}: The key points from the text are concisely presented here.",
                f"{model_name} extracts the main ideas and presents them in a clear summary.",
                f"Key insights summarized by {model_name} in a structured manner."
            ],
            TaskType.CREATIVE_WRITING: [
                f"{model_name} crafts a creative and engaging response: 'Once upon a time...'",
                f"With creative flair, {model_name} weaves an imaginative narrative.",
                f"{model_name}'s creative interpretation brings fresh perspective to the prompt."
            ],
            TaskType.CODE_GENERATION: [
                f"# Generated by {model_name}\ndef optimized_function():\n    # Efficient implementation\n    pass",
                f"// {model_name} code solution\nfunction solve() {\n    // Optimized approach\n}",
                f"/* {model_name} implementation */\nclass Solution {{\n    // Clean, efficient code\n}}"
            ]
        }

        # Select response based on task type and model specialty
        if request.task_type in config.specialty_tasks:
            responses = base_responses.get(request.task_type, [f"Response from {model_name}"])
            # Specialty models get better responses
            response = responses[0] if responses else f"Specialized response from {model_name}"
        else:
            responses = base_responses.get(request.task_type, [f"Response from {model_name}"])
            response = np.random.choice(responses)

        # Add model-specific characteristics
        if "gpt-4" in model_name.lower():
            response = f"[Detailed and analytical] {response}"
        elif "claude" in model_name.lower():
            response = f"[Thoughtful and nuanced] {response}"
        elif "instant" in model_name.lower() or "3.5" in model_name.lower():
            response = f"[Quick and efficient] {response}"

        return response

    def _calculate_confidence(self, request: EnsembleRequest, model_name: str, config: ModelConfig) -> float:
        """Calculate model confidence for the response"""
        base_confidence = 0.7

        # Task specialization bonus
        if request.task_type in config.specialty_tasks:
            base_confidence += 0.2

        # Historical performance
        historical_confidence = self.model_scores[model_name]["accuracy"]
        base_confidence = (base_confidence + historical_confidence) / 2

        # Reliability factor
        base_confidence *= config.reliability_score

        return min(1.0, base_confidence)

    def _calculate_quality_score(self, content: str, request: EnsembleRequest, config: ModelConfig) -> float:
        """Calculate quality score for the response"""
        score = 0.5  # Base score

        # Length appropriateness
        word_count = len(content.split())
        if 50 <= word_count <= 500:
            score += 0.2
        elif word_count > 500:
            score += 0.1

        # Content diversity (unique words)
        unique_words = len(set(content.lower().split()))
        if word_count > 0:
            diversity = unique_words / word_count
            score += diversity * 0.2

        # Structure indicators
        if any(indicator in content for indicator in [".", "?", "!", "\n"]):
            score += 0.1

        # Model quality factor
        score *= config.quality_factor

        return min(1.0, score)

    async def _combine_responses(self, responses: List[ModelResponse], method: EnsembleMethod, request: EnsembleRequest) -> Dict[str, Any]:
        """Combine multiple model responses using specified method"""
        if not responses:
            return {"content": "", "confidence": 0.0}

        if method == EnsembleMethod.MAJORITY_VOTE:
            return await self._majority_vote_combination(responses)
        elif method == EnsembleMethod.WEIGHTED_AVERAGE:
            return await self._weighted_average_combination(responses)
        elif method == EnsembleMethod.CONSENSUS_BUILDING:
            return await self._consensus_building_combination(responses, request)
        elif method == EnsembleMethod.BEST_OF_N:
            return await self._best_of_n_combination(responses)
        elif method == EnsembleMethod.RANKED_CHOICE:
            return await self._ranked_choice_combination(responses)
        elif method == EnsembleMethod.CONFIDENCE_WEIGHTED:
            return await self._confidence_weighted_combination(responses)
        elif method == EnsembleMethod.EXPERT_WEIGHTED:
            return await self._expert_weighted_combination(responses, request)
        elif method == EnsembleMethod.DIVERSITY_ENHANCED:
            return await self._diversity_enhanced_combination(responses, request)
        else:
            # Default to weighted average
            return await self._weighted_average_combination(responses)

    async def _majority_vote_combination(self, responses: List[ModelResponse]) -> Dict[str, Any]:
        """Combine responses using majority voting"""
        if len(responses) <= 2:
            # With 2 or fewer responses, use the highest confidence
            best_response = max(responses, key=lambda r: r.confidence)
            return {"content": best_response.content, "confidence": best_response.confidence}

        # For demonstration, select the response with highest quality score
        best_response = max(responses, key=lambda r: r.quality_score)
        return {
            "content": best_response.content,
            "confidence": np.mean([r.confidence for r in responses]),
            "details": {"method": "majority_vote", "selected_model": best_response.model_name}
        }

    async def _weighted_average_combination(self, responses: List[ModelResponse]) -> Dict[str, Any]:
        """Combine responses using weighted averaging"""
        total_weight = sum(r.confidence * r.quality_score for r in responses)

        if total_weight == 0:
            # Fallback to simple average
            combined_content = responses[0].content if responses else ""
            combined_confidence = np.mean([r.confidence for r in responses]) if responses else 0.0
        else:
            # For text responses, select the highest weighted response
            # In a more sophisticated implementation, this could merge content
            weighted_responses = [(r, r.confidence * r.quality_score) for r in responses]
            weighted_responses.sort(key=lambda x: x[1], reverse=True)
            best_response = weighted_responses[0][0]

            combined_content = best_response.content
            combined_confidence = sum(r.confidence * w for r, w in weighted_responses) / total_weight

        return {
            "content": combined_content,
            "confidence": combined_confidence,
            "details": {"method": "weighted_average", "total_responses": len(responses)}
        }

    async def _consensus_building_combination(self, responses: List[ModelResponse], request: EnsembleRequest) -> Dict[str, Any]:
        """Build consensus among model responses"""
        if len(responses) <= 1:
            return {
                "content": responses[0].content if responses else "",
                "confidence": responses[0].confidence if responses else 0.0
            }

        # Find common themes and key points
        all_content = [r.content for r in responses]
        consensus_content = await self._build_consensus_text(all_content, request)

        # Consensus confidence based on agreement level
        agreement_score = self._calculate_agreement_score(responses)
        consensus_confidence = np.mean([r.confidence for r in responses]) * agreement_score

        return {
            "content": consensus_content,
            "confidence": consensus_confidence,
            "details": {
                "method": "consensus_building",
                "agreement_score": agreement_score,
                "participants": len(responses)
            }
        }

    async def _best_of_n_combination(self, responses: List[ModelResponse]) -> Dict[str, Any]:
        """Select the best single response"""
        if not responses:
            return {"content": "", "confidence": 0.0}

        # Score responses based on multiple factors
        def score_response(response):
            return (
                response.confidence * 0.4 +
                response.quality_score * 0.4 +
                (1.0 / (response.response_time + 0.1)) * 0.1 +
                (1.0 / (response.cost + 0.01)) * 0.1
            )

        best_response = max(responses, key=score_response)

        return {
            "content": best_response.content,
            "confidence": best_response.confidence,
            "details": {
                "method": "best_of_n",
                "selected_model": best_response.model_name,
                "score": score_response(best_response)
            }
        }

    async def _ranked_choice_combination(self, responses: List[ModelResponse]) -> Dict[str, Any]:
        """Combine using ranked choice voting"""
        if len(responses) <= 1:
            return {
                "content": responses[0].content if responses else "",
                "confidence": responses[0].confidence if responses else 0.0
            }

        # Rank responses by combined score
        def combined_score(response):
            return response.confidence * response.quality_score

        ranked_responses = sorted(responses, key=combined_score, reverse=True)

        # Use top-ranked response
        best_response = ranked_responses[0]

        # Calculate confidence based on ranking consensus
        if len(ranked_responses) > 1:
            second_best_score = combined_score(ranked_responses[1])
            best_score = combined_score(ranked_responses[0])
            consensus_factor = 1.0 - (second_best_score / best_score) if best_score > 0 else 1.0
        else:
            consensus_factor = 1.0

        final_confidence = best_response.confidence * consensus_factor

        return {
            "content": best_response.content,
            "confidence": final_confidence,
            "details": {
                "method": "ranked_choice",
                "rankings": [r.model_name for r in ranked_responses],
                "consensus_factor": consensus_factor
            }
        }

    async def _confidence_weighted_combination(self, responses: List[ModelResponse]) -> Dict[str, Any]:
        """Weight responses by confidence scores"""
        if not responses:
            return {"content": "", "confidence": 0.0}

        total_confidence = sum(r.confidence for r in responses)
        if total_confidence == 0:
            # Equal weights if no confidence
            weights = [1.0] * len(responses)
        else:
            weights = [r.confidence / total_confidence for r in responses]

        # Select response with highest weight
        best_idx = np.argmax(weights)
        best_response = responses[best_idx]

        # Adjust confidence based on weight distribution
        max_weight = max(weights)
        weight_entropy = -sum(w * np.log(w + 1e-10) for w in weights if w > 0)
        confidence_adjustment = 1.0 - (weight_entropy / np.log(len(responses))) if len(responses) > 1 else 1.0

        final_confidence = best_response.confidence * confidence_adjustment

        return {
            "content": best_response.content,
            "confidence": final_confidence,
            "details": {
                "method": "confidence_weighted",
                "weights": weights,
                "weight_entropy": weight_entropy
            }
        }

    async def _expert_weighted_combination(self, responses: List[ModelResponse], request: EnsembleRequest) -> Dict[str, Any]:
        """Weight responses by model expertise in the task"""
        if not responses:
            return {"content": "", "confidence": 0.0}

        # Calculate expertise weights
        expertise_weights = []
        for response in responses:
            config = next((c for c in self.model_configs if c.name == response.model_name), None)
            if config and request.task_type in config.specialty_tasks:
                weight = 2.0  # Expert models get double weight
            else:
                weight = 1.0  # Non-expert models get normal weight
            expertise_weights.append(weight)

        # Normalize weights
        total_weight = sum(expertise_weights)
        if total_weight > 0:
            expertise_weights = [w / total_weight for w in expertise_weights]

        # Combine with confidence scores
        combined_scores = [
            expertise_weights[i] * responses[i].confidence
            for i in range(len(responses))
        ]

        best_idx = np.argmax(combined_scores)
        best_response = responses[best_idx]

        # Enhanced confidence for expert responses
        expertise_bonus = expertise_weights[best_idx]
        final_confidence = best_response.confidence * expertise_bonus

        return {
            "content": best_response.content,
            "confidence": final_confidence,
            "details": {
                "method": "expert_weighted",
                "expertise_weights": expertise_weights,
                "selected_expert": request.task_type in (next((c.specialty_tasks for c in self.model_configs if c.name == best_response.model_name), []))
            }
        }

    async def _diversity_enhanced_combination(self, responses: List[ModelResponse], request: EnsembleRequest) -> Dict[str, Any]:
        """Enhance diversity in responses while maintaining quality"""
        if not responses:
            return {"content": "", "confidence": 0.0}

        if not request.diversity_requirement or len(responses) <= 1:
            # No diversity requirement, use standard weighted average
            return await self._weighted_average_combination(responses)

        # Calculate pairwise similarities
        similarities = []
        for i in range(len(responses)):
            for j in range(i + 1, len(responses)):
                similarity = self._calculate_text_similarity(responses[i].content, responses[j].content)
                similarities.append(similarity)

        avg_similarity = np.mean(similarities) if similarities else 0.0

        # Adjust weights to favor diverse responses
        diversity_weights = []
        for i, response in enumerate(responses):
            # Calculate average similarity of this response to others
            response_similarities = [
                self._calculate_text_similarity(response.content, other_response.content)
                for j, other_response in enumerate(responses) if i != j
            ]
            avg_response_similarity = np.mean(response_similarities) if response_similarities else 0.0

            # Lower similarity = higher diversity weight
            diversity_weight = 1.0 - avg_response_similarity
            diversity_weights.append(diversity_weight)

        # Combine diversity weights with confidence scores
        combined_scores = [
            diversity_weights[i] * responses[i].confidence * responses[i].quality_score
            for i in range(len(responses))
        ]

        best_idx = np.argmax(combined_scores)
        best_response = responses[best_idx]

        # Adjust confidence based on diversity level
        diversity_bonus = diversity_weights[best_idx]
        final_confidence = best_response.confidence * (1.0 + diversity_bonus * 0.5)

        return {
            "content": best_response.content,
            "confidence": final_confidence,
            "details": {
                "method": "diversity_enhanced",
                "diversity_weights": diversity_weights,
                "avg_similarity": avg_similarity,
                "diversity_bonus": diversity_bonus
            }
        }

    async def _build_consensus_text(self, contents: List[str], request: EnsembleRequest) -> str:
        """Build consensus text from multiple responses"""
        if not contents:
            return ""

        if len(contents) == 1:
            return contents[0]

        # Extract common themes and key points
        all_words = []
        for content in contents:
            words = content.lower().split()
            all_words.extend(words)

        # Find most common words (themes)
        word_counts = defaultdict(int)
        for word in all_words:
            if len(word) > 3:  # Ignore short words
                word_counts[word] += 1

        common_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # Create consensus by selecting the highest quality response and enhancing it
        best_content = max(contents, key=lambda c: len(c.split()))  # Simple quality metric

        # Add consensus note
        consensus_prefix = f"[Ensemble consensus from {len(contents)} models] "
        return consensus_prefix + best_content

    def _calculate_agreement_score(self, responses: List[ModelResponse]) -> float:
        """Calculate agreement score among responses"""
        if len(responses) <= 1:
            return 1.0

        # Calculate pairwise similarities
        similarities = []
        for i in range(len(responses)):
            for j in range(i + 1, len(responses)):
                similarity = self._calculate_text_similarity(responses[i].content, responses[j].content)
                similarities.append(similarity)

        return np.mean(similarities) if similarities else 0.0

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        # Simple similarity using sequence matching
        return difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def _calculate_consensus(self, responses: List[ModelResponse]) -> float:
        """Calculate consensus score among responses"""
        if len(responses) <= 1:
            return 1.0

        # Consensus based on confidence alignment and content similarity
        confidences = [r.confidence for r in responses]
        confidence_std = np.std(confidences)
        confidence_consensus = 1.0 - min(confidence_std, 1.0)

        content_consensus = self._calculate_agreement_score(responses)

        return (confidence_consensus + content_consensus) / 2

    def _calculate_diversity(self, responses: List[ModelResponse]) -> float:
        """Calculate diversity score among responses"""
        if len(responses) <= 1:
            return 0.0

        # Diversity is inversely proportional to similarity
        similarity = self._calculate_agreement_score(responses)
        return 1.0 - similarity

    def _update_model_performance(self, model_name: str, response: ModelResponse, request: EnsembleRequest):
        """Update model performance metrics"""
        perf = self.model_scores[model_name]
        perf["total_requests"] += 1

        # Update accuracy based on confidence
        perf["accuracy"] = (perf["accuracy"] * 0.9 + response.confidence * 0.1)

        # Update speed metric
        speed_score = 1.0 / (response.response_time + 0.1)
        perf["speed"] = (perf["speed"] * 0.9 + speed_score * 0.1)

        # Update cost efficiency
        cost_efficiency = 1.0 / (response.cost + 0.01)
        perf["cost_efficiency"] = (perf["cost_efficiency"] * 0.9 + cost_efficiency * 0.1)

        # Update quality
        perf["quality"] = (perf["quality"] * 0.9 + response.quality_score * 0.1)

    def _update_performance_metrics(self, response: EnsembleResponse):
        """Update ensemble performance metrics"""
        # Update average response time
        current_avg = self.ensemble_stats["average_response_time"]
        new_avg = (current_avg * (self.ensemble_stats["total_requests"] - 1) + response.processing_time) / self.ensemble_stats["total_requests"]
        self.ensemble_stats["average_response_time"] = new_avg

        # Update average confidence
        current_conf = self.ensemble_stats["average_confidence"]
        new_conf = (current_conf * (self.ensemble_stats["total_requests"] - 1) + response.confidence) / self.ensemble_stats["total_requests"]
        self.ensemble_stats["average_confidence"] = new_conf

        # Update consensus rate
        if response.consensus_score > 0.7:
            self.ensemble_stats["consensus_rate"] = (
                self.ensemble_stats["consensus_rate"] * 0.9 + 0.1
            )

        # Update diversity rate
        if response.diversity_score > 0.5:
            self.ensemble_stats["diversity_rate"] = (
                self.ensemble_stats["diversity_rate"] * 0.9 + 0.1
            )

    def _generate_cache_key(self, request: EnsembleRequest) -> str:
        """Generate cache key for request"""
        key_data = {
            "prompt": request.prompt,
            "task_type": request.task_type.value,
            "method": request.method.value,
            "max_responses": request.max_responses
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get_ensemble_stats(self) -> Dict[str, Any]:
        """Get ensemble performance statistics"""
        return self.ensemble_stats.copy()

    def get_model_performance(self) -> Dict[str, Dict[str, float]]:
        """Get individual model performance metrics"""
        return {model: scores.copy() for model, scores in self.model_scores.items()}

    async def benchmark_ensemble(self, test_requests: List[EnsembleRequest]) -> Dict[str, Any]:
        """Benchmark ensemble performance"""
        start_time = time.time()
        results = []

        for request in test_requests:
            result = await self.process_request(request)
            results.append(result)

        total_time = time.time() - start_time

        # Calculate benchmark metrics
        avg_response_time = np.mean([r.processing_time for r in results])
        avg_confidence = np.mean([r.confidence for r in results])
        avg_consensus = np.mean([r.consensus_score for r in results])
        avg_diversity = np.mean([r.diversity_score for r in results])
        total_cost = sum([r.cost for r in results])

        return {
            "total_requests": len(test_requests),
            "total_time": total_time,
            "average_response_time": avg_response_time,
            "average_confidence": avg_confidence,
            "average_consensus": avg_consensus,
            "average_diversity": avg_diversity,
            "total_cost": total_cost,
            "requests_per_second": len(test_requests) / total_time,
            "cost_per_request": total_cost / len(test_requests)
        }

# Example usage
async def demonstrate_ensemble():
    """Demonstrate ensemble functionality"""
    ensemble = AIEnsemble()

    # Create test request
    request = EnsembleRequest(
        prompt="Explain the concept of artificial intelligence",
        task_type=TaskType.QUESTION_ANSWERING,
        method=EnsembleMethod.WEIGHTED_AVERAGE,
        max_responses=3
    )

    # Process request
    response = await ensemble.process_request(request)

    print(f"Ensemble Response: {response.content[:100]}...")
    print(f"Confidence: {response.confidence:.2f}")
    print(f"Contributing Models: {response.contributing_models}")
    print(f"Consensus Score: {response.consensus_score:.2f}")
    print(f"Diversity Score: {response.diversity_score:.2f}")
    print(f"Processing Time: {response.processing_time:.3f}s")

    # Get stats
    stats = ensemble.get_ensemble_stats()
    print(f"Ensemble Stats: {stats}")

if __name__ == "__main__":
    asyncio.run(demonstrate_ensemble())