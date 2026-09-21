#!/usr/bin/env python3
"""
Advanced Prompt Optimizer - Intelligent prompt engineering and optimization
Provides automatic prompt enhancement, A/B testing, and performance analysis
"""

import asyncio
import time
import json
import logging
import numpy as np
import re
import hashlib
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from collections import defaultdict, deque
import random

logger = logging.getLogger(__name__)

class OptimizationStrategy(Enum):
    """Prompt optimization strategies"""
    CLARITY_ENHANCEMENT = "clarity_enhancement"
    CONTEXT_ADDITION = "context_addition"
    STRUCTURE_IMPROVEMENT = "structure_improvement"
    EXAMPLE_INCLUSION = "example_inclusion"
    CONSTRAINT_SPECIFICATION = "constraint_specification"
    TONE_ADJUSTMENT = "tone_adjustment"
    LENGTH_OPTIMIZATION = "length_optimization"
    TOKEN_EFFICIENCY = "token_efficiency"

class TaskType(Enum):
    """Types of tasks for optimization"""
    QUESTION_ANSWERING = "question_answering"
    TEXT_GENERATION = "text_generation"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    CODE_GENERATION = "code_generation"
    ANALYSIS = "analysis"
    CREATIVE_WRITING = "creative_writing"
    INSTRUCTION_FOLLOWING = "instruction_following"

@dataclass
class PromptTemplate:
    """Prompt template with variables"""
    template: str
    variables: List[str]
    description: str
    task_type: TaskType
    examples: Optional[List[str]] = None
    constraints: Optional[List[str]] = None

@dataclass
class PromptVariant:
    """Variant of a prompt for testing"""
    variant_id: str
    prompt_text: str
    strategy: OptimizationStrategy
    original_prompt: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class PromptTest:
    """A/B test for prompts"""
    test_id: str
    original_prompt: str
    variants: List[PromptVariant]
    task_type: TaskType
    status: str = "active"  # active, completed, paused
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None

@dataclass
class PromptMetrics:
    """Performance metrics for a prompt"""
    prompt_id: str
    average_response_time: float
    average_quality_score: float
    success_rate: float
    token_efficiency: float
    cost_per_request: float
    total_requests: int
    user_satisfaction: Optional[float] = None
    clarity_score: Optional[float] = None

@dataclass
class OptimizationConfig:
    """Configuration for prompt optimization"""
    enable_ab_testing: bool = True
    min_test_samples: int = 50
    significance_threshold: float = 0.05
    optimization_interval: int = 100  # requests
    max_variants_per_test: int = 5
    enable_auto_optimization: bool = True
    quality_threshold: float = 0.8
    cost_sensitivity: float = 0.5  # 0 = ignore cost, 1 = max cost sensitivity

class PromptOptimizer:
    """Advanced prompt optimization system"""

    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.config = config or OptimizationConfig()
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Storage
        self.prompt_templates: Dict[str, PromptTemplate] = {}
        self.active_tests: Dict[str, PromptTest] = {}
        self.prompt_metrics: Dict[str, PromptMetrics] = defaultdict(lambda: PromptMetrics(
            prompt_id="", average_response_time=0.0, average_quality_score=0.0,
            success_rate=0.0, token_efficiency=0.0, cost_per_request=0.0, total_requests=0
        ))

        # Performance tracking
        self.request_history: deque = deque(maxlen=10000)
        self.optimization_history: List[Dict[str, Any]] = []

        # Optimization strategies
        self.strategy_implementations = {
            OptimizationStrategy.CLARITY_ENHANCEMENT: self._enhance_clarity,
            OptimizationStrategy.CONTEXT_ADDITION: self._add_context,
            OptimizationStrategy.STRUCTURE_IMPROVEMENT: self._improve_structure,
            OptimizationStrategy.EXAMPLE_INCLUSION: self._include_examples,
            OptimizationStrategy.CONSTRAINT_SPECIFICATION: self._specify_constraints,
            OptimizationStrategy.TONE_ADJUSTMENT: self._adjust_tone,
            OptimizationStrategy.LENGTH_OPTIMIZATION: self._optimize_length,
            OptimizationStrategy.TOKEN_EFFICIENCY: self._improve_token_efficiency
        }

        logger.info("PromptOptimizer initialized")

    def register_template(self, template_id: str, template: PromptTemplate):
        """Register a prompt template"""
        self.prompt_templates[template_id] = template
        logger.info(f"Registered template: {template_id}")

    async def optimize_prompt(self, prompt: str, task_type: TaskType,
                            context: Optional[Dict[str, Any]] = None) -> str:
        """Optimize a prompt for better performance"""
        try:
            # Check if there's an active A/B test for this prompt
            test_id = self._find_active_test(prompt, task_type)
            if test_id and self.config.enable_ab_testing:
                return await self._get_test_variant(test_id)

            # Apply optimization strategies
            optimized_prompt = prompt

            # Determine which strategies to apply based on task type and prompt characteristics
            strategies = self._select_optimization_strategies(prompt, task_type)

            for strategy in strategies:
                try:
                    optimized_prompt = await self.strategy_implementations[strategy](
                        optimized_prompt, task_type, context
                    )
                except Exception as e:
                    logger.warning(f"Strategy {strategy.value} failed: {e}")
                    continue

            # If significantly different, create A/B test
            if self._should_create_test(prompt, optimized_prompt):
                await self._create_ab_test(prompt, optimized_prompt, task_type)

            return optimized_prompt

        except Exception as e:
            logger.error(f"Prompt optimization failed: {e}")
            return prompt  # Return original prompt on failure

    def _select_optimization_strategies(self, prompt: str, task_type: TaskType) -> List[OptimizationStrategy]:
        """Select appropriate optimization strategies"""
        strategies = []

        # Analyze prompt characteristics
        prompt_length = len(prompt.split())
        has_examples = "example" in prompt.lower() or "for instance" in prompt.lower()
        has_structure = any(indicator in prompt for indicator in ["###", "1.", "2.", "•", "-"])
        has_constraints = "must" in prompt.lower() or "should not" in prompt.lower()
        is_unclear = len(prompt.split(".")) < 2 or len(prompt) < 50

        # Select strategies based on analysis
        if is_unclear:
            strategies.append(OptimizationStrategy.CLARITY_ENHANCEMENT)

        if not has_structure and prompt_length > 50:
            strategies.append(OptimizationStrategy.STRUCTURE_IMPROVEMENT)

        if not has_examples and task_type in [TaskType.INSTRUCTION_FOLLOWING, TaskType.CODE_GENERATION]:
            strategies.append(OptimizationStrategy.EXAMPLE_INCLUSION)

        if not has_constraints and task_type in [TaskType.ANALYSIS, TaskType.GENERATION]:
            strategies.append(OptimizationStrategy.CONSTRAINT_SPECIFICATION)

        if prompt_length > 500:
            strategies.append(OptimizationStrategy.LENGTH_OPTIMIZATION)

        # Always consider token efficiency
        strategies.append(OptimizationStrategy.TOKEN_EFFICIENCY)

        # Randomly add one more strategy for diversity
        remaining_strategies = [s for s in OptimizationStrategy if s not in strategies]
        if remaining_strategies:
            strategies.append(random.choice(remaining_strategies))

        return strategies[:3]  # Limit to 3 strategies per optimization

    async def _enhance_clarity(self, prompt: str, task_type: TaskType, context: Optional[Dict] = None) -> str:
        """Enhance prompt clarity"""
        enhanced = prompt

        # Add clear instruction markers
        if not any(marker in enhanced for marker in ["###", "Task:", "Please"]):
            if task_type == TaskType.QUESTION_ANSWERING:
                enhanced = f"### Question\n{enhanced}\n\n### Please provide a clear and concise answer:"
            elif task_type == TaskType.SUMMARIZATION:
                enhanced = f"### Task: Summarize\n{enhanced}\n\n### Please provide a summary:"
            else:
                enhanced = f"### Task\n{enhanced}"

        # Improve sentence structure
        sentences = enhanced.split('.')
        improved_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 100:
                # Break down long sentences
                if ',' in sentence:
                    parts = sentence.split(',', 1)
                    improved_sentences.append(parts[0] + '.')
                    improved_sentences.append(parts[1].strip())
                else:
                    improved_sentences.append(sentence)
            elif sentence:
                improved_sentences.append(sentence)

        enhanced = '. '.join(improved_sentences)

        # Add clarification if too brief
        if len(enhanced.split()) < 20:
            enhanced += "\n\nPlease provide detailed and specific information."

        return enhanced

    async def _add_context(self, prompt: str, task_type: TaskType, context: Optional[Dict] = None) -> str:
        """Add relevant context to prompt"""
        if not context:
            return prompt

        contextual_prompt = prompt

        # Add role context
        if "role" in context:
            contextual_prompt = f"You are acting as a {context['role']}. \n\n{contextual_prompt}"

        # Add domain context
        if "domain" in context:
            contextual_prompt = f"Domain: {context['domain']}\n\n{contextual_prompt}"

        # Add audience context
        if "audience" in context:
            contextual_prompt = f"Target audience: {context['audience']}\n\n{contextual_prompt}"

        # Add format requirements
        if "format" in context:
            contextual_prompt += f"\n\nPlease format your response as: {context['format']}"

        return contextual_prompt

    async def _improve_structure(self, prompt: str, task_type: TaskType, context: Optional[Dict] = None) -> str:
        """Improve prompt structure with sections and formatting"""
        structured_prompt = prompt

        # Add section headers if not present
        if "###" not in structured_prompt and len(structured_prompt.split()) > 50:
            # Split into logical sections
            sentences = structured_prompt.split('. ')
            if len(sentences) > 3:
                structured_prompt = "### Background\n" + '. '.join(sentences[:2]) + ".\n\n"
                structured_prompt += "### Task\n" + '. '.join(sentences[2:]) + "."

        # Add bullet points for lists
        if "and" in structured_prompt and structured_prompt.count(",") > 2:
            # Convert comma-separated lists to bullet points
            structured_prompt = re.sub(
                r'([^,]+)(?:,\s*| and )([^,]+)(?:,\s*| and )([^,.]+)',
                r'• \1\n• \2\n• \3',
                structured_prompt
            )

        # Add numbering for steps
        if "step" in structured_prompt.lower() or "first" in structured_prompt.lower():
            structured_prompt = re.sub(r'(\b(first|second|third|then|next)\b)', r'### \1', structured_prompt, flags=re.IGNORECASE)

        return structured_prompt

    async def _include_examples(self, prompt: str, task_type: TaskType, context: Optional[Dict] = None) -> str:
        """Add relevant examples to prompt"""
        if "example" in prompt.lower():
            return prompt  # Already has examples

        examples = {
            TaskType.QUESTION_ANSWERING: [
                "Example:\nQ: What is photosynthesis?\nA: Photosynthesis is the process by which plants convert sunlight into energy.",
                "For example, when asked about a scientific concept, provide a clear definition followed by key details."
            ],
            TaskType.CODE_GENERATION: [
                "Example:\n```python\ndef hello_world():\n    print('Hello, World!')\nreturn hello_world\n```",
                "For instance, write clean, well-commented code that follows best practices."
            ],
            TaskType.SUMMARIZATION: [
                "Example:\nOriginal: 'The quick brown fox jumps over the lazy dog. The dog was sleeping in the sun.'\nSummary: 'A fox jumped over a sleeping dog.'",
                "For example, identify the main points and condense them into a brief, clear summary."
            ]
        }

        if task_type in examples:
            example_text = random.choice(examples[task_type])
            return f"{prompt}\n\n{example_text}"

        return prompt

    async def _specify_constraints(self, prompt: str, task_type: TaskType, context: Optional[Dict] = None) -> str:
        """Add specific constraints to guide the response"""
        if "must" in prompt.lower() or "should not" in prompt.lower():
            return prompt  # Already has constraints

        constraints = {
            TaskType.QUESTION_ANSWERING: [
                "The answer must be accurate and based on reliable sources.",
                "Do not include personal opinions unless specifically asked.",
                "Keep the response focused on the question asked."
            ],
            TaskType.TEXT_GENERATION: [
                "The text must be coherent and well-structured.",
                "Avoid repetition and maintain a consistent tone.",
                "Ensure proper grammar and spelling throughout."
            ],
            TaskType.SUMMARIZATION: [
                "The summary must capture all key points from the original text.",
                "Do not introduce new information not present in the source.",
                "Keep the summary concise and to the point."
            ],
            TaskType.CODE_GENERATION: [
                "The code must be syntactically correct and runnable.",
                "Include proper error handling where applicable.",
                "Follow coding best practices and conventions."
            ]
        }

        if task_type in constraints:
            constraint_text = "\n".join(constraints[task_type])
            return f"{prompt}\n\n### Constraints\n{constraint_text}"

        return prompt

    async def _adjust_tone(self, prompt: str, task_type: TaskType, context: Optional[Dict] = None) -> str:
        """Adjust tone based on context and requirements"""
        # Determine appropriate tone
        tone_indicators = {
            "formal": ["formal", "professional", "academic", "business"],
            "casual": ["casual", "informal", "friendly", "conversational"],
            "technical": ["technical", "detailed", "specific", "precise"],
            "creative": ["creative", "imaginative", "innovative", "artistic"]
        }

        detected_tone = "neutral"
        prompt_lower = prompt.lower()

        for tone, indicators in tone_indicators.items():
            if any(indicator in prompt_lower for indicator in indicators):
                detected_tone = tone
                break

        # Add tone adjustment if needed
        tone_prefixes = {
            "formal": "Please provide a formal, professional response.",
            "casual": "Please provide a friendly, conversational response.",
            "technical": "Please provide a detailed, technical response.",
            "creative": "Please provide a creative, imaginative response."
        }

        if detected_tone in tone_prefixes:
            return f"{tone_prefixes[detected_tone]}\n\n{prompt}"

        return prompt

    async def _optimize_length(self, prompt: str, task_type: TaskType, context: Optional[Dict] = None) -> str:
        """Optimize prompt length for efficiency"""
        current_length = len(prompt.split())

        # If too long, condense while preserving key information
        if current_length > 300:
            # Remove redundant phrases
            condensed = prompt.replace("please ", "").replace("kindly ", "")
            condensed = re.sub(r'\b(very|quite|rather|somewhat)\s+', '', condensed)

            # Remove duplicate sentences
            sentences = condensed.split('. ')
            unique_sentences = []
            seen = set()
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and sentence not in seen:
                    unique_sentences.append(sentence)
                    seen.add(sentence)

            condensed = '. '.join(unique_sentences)

            # If still too long, truncate intelligently
            if len(condensed.split()) > 250:
                words = condensed.split()
                condensed = ' '.join(words[:250]) + "..."

            return condensed

        # If too short, add relevant details
        elif current_length < 30:
            if task_type == TaskType.QUESTION_ANSWERING:
                return f"{prompt}\n\nPlease provide a comprehensive answer with relevant details and examples."
            elif task_type == TaskType.SUMMARIZATION:
                return f"{prompt}\n\nPlease create a thorough summary covering all main points."
            else:
                return f"{prompt}\n\nPlease provide a detailed and complete response."

        return prompt

    async def _improve_token_efficiency(self, prompt: str, task_type: TaskType, context: Optional[Dict] = None) -> str:
        """Improve token efficiency while maintaining effectiveness"""
        # Replace verbose phrases with concise alternatives
        replacements = {
            "in order to": "to",
            "due to the fact that": "because",
            "it is important to note that": "note:",
            "the purpose of this is to": "this aims to",
            "a large number of": "many",
            "a significant amount of": "much",
            "in the event that": "if",
            "with regard to": "regarding",
            "on the other hand": "however",
            "as a matter of fact": "in fact"
        }

        efficient_prompt = prompt
        for verbose, concise in replacements.items():
            efficient_prompt = efficient_prompt.replace(verbose, concise)

        # Remove unnecessary articles and prepositions where context allows
        efficient_prompt = re.sub(r'\b(the|a|an)\s+(of|in|on|at|to|for)\s+', ' ', efficient_prompt)

        # Clean up extra whitespace
        efficient_prompt = re.sub(r'\s+', ' ', efficient_prompt).strip()

        return efficient_prompt

    def _should_create_test(self, original: str, optimized: str) -> bool:
        """Determine if an A/B test should be created"""
        # Don't test if prompts are too similar
        similarity = self._calculate_similarity(original, optimized)
        if similarity > 0.8:
            return False

        # Don't test if optimized is much longer (cost concern)
        if len(optimized) > len(original) * 1.5:
            return False

        # Random chance to create test (to avoid too many tests)
        return random.random() < 0.3

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0

    async def _create_ab_test(self, original_prompt: str, optimized_prompt: str, task_type: TaskType) -> str:
        """Create an A/B test for prompt comparison"""
        test_id = hashlib.md5(f"{original_prompt}_{optimized_prompt}_{datetime.now()}".encode()).hexdigest()[:12]

        # Create variants
        original_variant = PromptVariant(
            variant_id=f"{test_id}_original",
            prompt_text=original_prompt,
            strategy=OptimizationStrategy.CLARITY_ENHANCEMENT,  # Placeholder
            original_prompt=original_prompt,
            created_at=datetime.now()
        )

        optimized_variant = PromptVariant(
            variant_id=f"{test_id}_optimized",
            prompt_text=optimized_prompt,
            strategy=OptimizationStrategy.CLARITY_ENHANCEMENT,  # Placeholder
            original_prompt=original_prompt,
            created_at=datetime.now()
        )

        # Create test
        test = PromptTest(
            test_id=test_id,
            original_prompt=original_prompt,
            variants=[original_variant, optimized_variant],
            task_type=task_type,
            created_at=datetime.now()
        )

        self.active_tests[test_id] = test
        logger.info(f"Created A/B test {test_id} for prompt optimization")

        return test_id

    def _find_active_test(self, prompt: str, task_type: TaskType) -> Optional[str]:
        """Find active A/B test for this prompt"""
        for test_id, test in self.active_tests.items():
            if (test.task_type == task_type and
                test.status == "active" and
                self._calculate_similarity(test.original_prompt, prompt) > 0.7):
                return test_id
        return None

    async def _get_test_variant(self, test_id: str) -> str:
        """Get a variant from active A/B test"""
        if test_id not in self.active_tests:
            return None

        test = self.active_tests[test_id]
        if test.status != "active":
            return None

        # Randomly select a variant (with equal probability for now)
        variant = random.choice(test.variants)
        return variant.prompt_text

    async def record_prompt_performance(self, prompt: str, response_time: float,
                                     quality_score: float, success: bool,
                                     token_usage: int, cost: float,
                                     user_feedback: Optional[float] = None):
        """Record performance metrics for a prompt"""
        try:
            prompt_id = hashlib.md5(prompt.encode()).hexdigest()[:16]

            # Get existing metrics or create new
            metrics = self.prompt_metrics[prompt_id]
            metrics.prompt_id = prompt_id

            # Update metrics with exponential moving average
            alpha = 0.1  # Learning rate
            n = metrics.total_requests + 1

            metrics.average_response_time = (
                (metrics.average_response_time * (n - 1) + response_time) / n
            )
            metrics.average_quality_score = (
                (metrics.average_quality_score * (n - 1) + quality_score) / n
            )
            metrics.success_rate = (
                (metrics.success_rate * (n - 1) + (1.0 if success else 0.0)) / n
            )
            metrics.token_efficiency = (
                (metrics.token_efficiency * (n - 1) + (1.0 / token_usage if token_usage > 0 else 0.0)) / n
            )
            metrics.cost_per_request = (
                (metrics.cost_per_request * (n - 1) + cost) / n
            )
            metrics.total_requests = n

            if user_feedback is not None:
                if metrics.user_satisfaction is None:
                    metrics.user_satisfaction = user_feedback
                else:
                    metrics.user_satisfaction = (
                        (metrics.user_satisfaction * (n - 1) + user_feedback) / n
                    )

            # Store in history
            self.request_history.append({
                "prompt_id": prompt_id,
                "prompt": prompt,
                "response_time": response_time,
                "quality_score": quality_score,
                "success": success,
                "token_usage": token_usage,
                "cost": cost,
                "user_feedback": user_feedback,
                "timestamp": datetime.now()
            })

            # Check if any A/B tests need evaluation
            await self._evaluate_active_tests(prompt_id)

        except Exception as e:
            logger.error(f"Failed to record prompt performance: {e}")

    async def _evaluate_active_tests(self, prompt_id: str):
        """Evaluate active A/B tests that might involve this prompt"""
        for test_id, test in self.active_tests.items():
            if test.status != "active":
                continue

            # Check if we have enough samples
            total_samples = sum(
                len([r for r in self.request_history if r["prompt"] == variant.prompt_text])
                for variant in test.variants
            )

            if total_samples >= self.config.min_test_samples:
                await self._complete_test(test_id)

    async def _complete_test(self, test_id: str):
        """Complete an A/B test and determine winner"""
        if test_id not in self.active_tests:
            return

        test = self.active_tests[test_id]
        test.status = "completed"
        test.completed_at = datetime.now()

        # Calculate results for each variant
        variant_results = {}
        for variant in test.variants:
            variant_metrics = [
                r for r in self.request_history
                if r["prompt"] == variant.prompt_text
            ]

            if variant_metrics:
                avg_quality = np.mean([m["quality_score"] for m in variant_metrics])
                avg_time = np.mean([m["response_time"] for m in variant_metrics])
                avg_cost = np.mean([m["cost"] for m in variant_metrics])
                success_rate = np.mean([m["success"] for m in variant_metrics])

                # Calculate overall score
                score = (
                    avg_quality * 0.4 +
                    success_rate * 0.3 +
                    (1.0 / (avg_time + 0.1)) * 0.2 +
                    (1.0 / (avg_cost + 0.001)) * 0.1 * self.config.cost_sensitivity
                )

                variant_results[variant.variant_id] = {
                    "score": score,
                    "avg_quality": avg_quality,
                    "avg_time": avg_time,
                    "avg_cost": avg_cost,
                    "success_rate": success_rate,
                    "samples": len(variant_metrics)
                }

        test.results = variant_results

        # Determine winner
        if variant_results:
            winner_id = max(variant_results.keys(), key=lambda k: variant_results[k]["score"])
            winner_variant = next(v for v in test.variants if v.variant_id == winner_id)

            logger.info(f"A/B test {test_id} completed. Winner: {winner_variant.variant_id} with score {variant_results[winner_id]['score']:.3f}")

            # Record optimization result
            self.optimization_history.append({
                "test_id": test_id,
                "winner": winner_variant.variant_id,
                "improvement": variant_results[winner_id]["score"] - variant_results.get(f"{test_id}_original", {}).get("score", 0),
                "timestamp": datetime.now()
            })

    def get_prompt_metrics(self, prompt: str) -> Optional[PromptMetrics]:
        """Get performance metrics for a specific prompt"""
        prompt_id = hashlib.md5(prompt.encode()).hexdigest()[:16]
        metrics = self.prompt_metrics[prompt_id]
        return metrics if metrics.total_requests > 0 else None

    def get_best_prompts(self, task_type: Optional[TaskType] = None, limit: int = 10) -> List[Tuple[str, PromptMetrics]]:
        """Get best performing prompts"""
        # Filter by task type if specified
        if task_type:
            # For simplicity, we'll filter by recent history
            recent_prompts = [
                (r["prompt"], r["prompt_id"]) for r in list(self.request_history)[-1000:]
            ]
        else:
            recent_prompts = [
                (r["prompt"], r["prompt_id"]) for r in list(self.request_history)[-1000:]
            ]

        # Get unique prompts with their metrics
        unique_prompts = {}
        for prompt, prompt_id in recent_prompts:
            if prompt_id not in unique_prompts:
                unique_prompts[prompt_id] = (prompt, self.prompt_metrics[prompt_id])

        # Sort by performance score
        scored_prompts = []
        for prompt_id, (prompt, metrics) in unique_prompts.items():
            if metrics.total_requests > 0:
                score = (
                    metrics.average_quality_score * 0.4 +
                    metrics.success_rate * 0.3 +
                    metrics.token_efficiency * 0.2 +
                    (1.0 / (metrics.cost_per_request + 0.001)) * 0.1
                )
                scored_prompts.append((prompt, metrics, score))

        scored_prompts.sort(key=lambda x: x[2], reverse=True)

        return [(prompt, metrics) for prompt, metrics, _ in scored_prompts[:limit]]

    def get_optimization_insights(self) -> Dict[str, Any]:
        """Get insights about prompt optimization performance"""
        if not self.optimization_history:
            return {"message": "No optimization history available"}

        # Calculate overall improvement
        improvements = [opt["improvement"] for opt in self.optimization_history]
        avg_improvement = np.mean(improvements)
        successful_optimizations = len([i for i in improvements if i > 0])

        # Most effective strategies
        strategy_performance = defaultdict(list)
        for test_id in self.active_tests:
            if self.active_tests[test_id].results:
                for variant in self.active_tests[test_id].variants:
                    if variant.variant_id in self.active_tests[test_id].results:
                        strategy_performance[variant.strategy].append(
                            self.active_tests[test_id].results[variant.variant_id]["score"]
                        )

        avg_strategy_performance = {
            strategy.value: np.mean(scores) if scores else 0.0
            for strategy, scores in strategy_performance.items()
        }

        return {
            "total_optimizations": len(self.optimization_history),
            "average_improvement": avg_improvement,
            "success_rate": successful_optimizations / len(improvements) if improvements else 0,
            "strategy_performance": avg_strategy_performance,
            "total_tests": len(self.active_tests),
            "active_tests": len([t for t in self.active_tests.values() if t.status == "active"])
        }

    async def analyze_prompt_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in prompt performance"""
        if len(self.request_history) < 100:
            return {"message": "Insufficient data for pattern analysis"}

        recent_requests = list(self.request_history)[-1000:]

        # Analyze prompt length vs performance
        length_performance = defaultdict(list)
        for req in recent_requests:
            prompt_length = len(req["prompt"].split())
            length_bucket = (prompt_length // 50) * 50  # Bucket by 50 words
            length_performance[length_bucket].append(req["quality_score"])

        avg_performance_by_length = {
            length: np.mean(scores) for length, scores in length_performance.items()
        }

        # Analyze specific words/phrases that correlate with better performance
        word_performance = defaultdict(list)
        for req in recent_requests:
            words = req["prompt"].lower().split()
            for word in set(words):  # Unique words per prompt
                if len(word) > 3:  # Skip short words
                    word_performance[word].append(req["quality_score"])

        # Find words with consistently high performance
        high_performance_words = []
        for word, scores in word_performance.items():
            if len(scores) >= 10:  # Minimum samples
                avg_score = np.mean(scores)
                if avg_score > 0.8:
                    high_performance_words.append((word, avg_score, len(scores)))

        high_performance_words.sort(key=lambda x: x[1], reverse=True)

        return {
            "performance_by_length": avg_performance_by_length,
            "high_performance_words": high_performance_words[:20],
            "total_prompts_analyzed": len(recent_requests),
            "average_quality": np.mean([r["quality_score"] for r in recent_requests])
        }

    async def generate_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        return {
            "timestamp": datetime.now().isoformat(),
            "insights": self.get_optimization_insights(),
            "patterns": await self.analyze_prompt_patterns(),
            "best_prompts": [
                {"prompt": prompt[:100] + "...", "metrics": asdict(metrics)}
                for prompt, metrics in self.get_best_prompts(limit=5)
            ],
            "active_tests": len([t for t in self.active_tests.values() if t.status == "active"]),
            "total_optimizations": len(self.optimization_history)
        }

    async def shutdown(self):
        """Cleanup resources"""
        self.executor.shutdown(wait=True)
        logger.info("PromptOptimizer shutdown complete")

# Example usage
async def demonstrate_optimizer():
    """Demonstrate prompt optimization functionality"""
    optimizer = PromptOptimizer()

    # Register some templates
    qa_template = PromptTemplate(
        template="Question: {question}\nContext: {context}\nAnswer:",
        variables=["question", "context"],
        description="Q&A template",
        task_type=TaskType.QUESTION_ANSWERING
    )
    optimizer.register_template("qa_template", qa_template)

    # Optimize a prompt
    original_prompt = "What is artificial intelligence?"
    optimized_prompt = await optimizer.optimize_prompt(
        original_prompt,
        TaskType.QUESTION_ANSWERING,
        context={"domain": "technology", "audience": "general"}
    )

    print(f"Original: {original_prompt}")
    print(f"Optimized: {optimized_prompt}")

    # Simulate some performance data
    for i in range(20):
        await optimizer.record_prompt_performance(
            prompt=optimized_prompt,
            response_time=np.random.normal(0.5, 0.1),
            quality_score=np.random.uniform(0.7, 0.95),
            success=np.random.random() > 0.1,
            token_usage=np.random.normal(100, 20),
            cost=np.random.normal(0.01, 0.002)
        )

    # Get metrics
    metrics = optimizer.get_prompt_metrics(optimized_prompt)
    if metrics:
        print(f"Prompt metrics: Quality={metrics.average_quality_score:.2f}, "
              f"Success Rate={metrics.success_rate:.2f}")

    # Get insights
    insights = optimizer.get_optimization_insights()
    print(f"Optimization insights: {insights}")

    await optimizer.shutdown()

if __name__ == "__main__":
    asyncio.run(demonstrate_optimizer())