#!/usr/bin/env python3
"""
Conversation Optimizer - Enhances AI dialogue quality and coherence

This module improves conversation flow, coherence, and naturalness through
advanced prompt engineering, context management, and response optimization.
"""

import re
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

class ConversationStyle(Enum):
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    EMPATHETIC = "empathetic"
    CREATIVE = "creative"
    TECHNICAL = "technical"

@dataclass
class ConversationMetrics:
    coherence_score: float
    relevance_score: float
    naturalness_score: float
    engagement_score: float
    response_time: float
    context_usage: float

class ConversationOptimizer:
    """
    Advanced conversation optimization system for AI agents.

    Features:
    - Dialogue coherence enhancement
    - Context-aware responses
    - Natural language flow optimization
    - Personality-consistent messaging
    - Real-time conversation analysis
    """

    def __init__(self, agent_id: str, style: ConversationStyle = ConversationStyle.FRIENDLY):
        self.agent_id = agent_id
        self.style = style
        self.conversation_history = []
        self.context_window = []
        self.performance_metrics = []
        self.coherence_patterns = self._load_coherence_patterns()
        self.style_templates = self._load_style_templates()

        # Configuration
        self.max_context_length = 10
        self.coherence_threshold = 0.7
        self.response_optimization_enabled = True

        # Logging
        self.logger = logging.getLogger(f"conversation_optimizer_{agent_id}")

    def optimize_conversation(self, user_input: str, current_response: str,
                            context: Dict[str, Any] = None) -> Tuple[str, ConversationMetrics]:
        """
        Optimize a conversation response for better quality and engagement.

        Args:
            user_input: The user's message
            current_response: The AI's current response
            context: Additional context information

        Returns:
            Tuple of (optimized_response, metrics)
        """
        start_time = time.time()

        # Analyze current response
        current_metrics = self._analyze_response_quality(user_input, current_response)

        # Apply optimization strategies
        optimized_response = current_response

        if self.response_optimization_enabled:
            # Enhance coherence
            optimized_response = self._enhance_coherence(user_input, optimized_response)

            # Improve naturalness
            optimized_response = self._improve_naturalness(optimized_response)

            # Apply style consistency
            optimized_response = self._apply_style_consistency(optimized_response)

            # Optimize for engagement
            optimized_response = self._enhance_engagement(user_input, optimized_response)

        # Calculate final metrics
        processing_time = time.time() - start_time
        final_metrics = self._calculate_final_metrics(
            user_input, optimized_response, processing_time, context
        )

        # Update conversation history
        self._update_conversation_history(user_input, optimized_response, final_metrics)

        return optimized_response, final_metrics

    def _enhance_coherence(self, user_input: str, response: str) -> str:
        """Enhance response coherence and logical flow."""
        # Check for logical transitions
        sentences = re.split(r'[.!?]+', response)
        enhanced_sentences = []

        for i, sentence in enumerate(sentences):
            if sentence.strip():
                # Add transition words where needed
                if i > 0 and not self._has_transition(sentence):
                    sentence = self._add_appropriate_transition(sentence, sentences[i-1])

                # Ensure logical consistency with context
                sentence = self._ensure_logical_consistency(sentence, user_input)
                enhanced_sentences.append(sentence)

        return '. '.join(enhanced_sentences).strip()

    def _improve_naturalness(self, response: str) -> str:
        """Improve natural language flow and human-like expression."""
        # Remove overly formal or robotic language
        natural_response = response

        # Replace formal phrases with natural alternatives
        formal_to_natural = {
            r'\bI would like to\b': "I'd like to",
            r'\bIt is important to note that\b': "It's worth noting that",
            r'\bIn order to\b': "To",
            r'\bPlease be advised that\b': "Just so you know",
            r'\bThank you for your patience\b': "Thanks for waiting",
            r'\bI apologize for the inconvenience\b': "Sorry about that"
        }

        for formal, natural in formal_to_natural.items():
            natural_response = re.sub(formal, natural, natural_response, flags=re.IGNORECASE)

        # Add conversational markers based on style
        if self.style == ConversationStyle.FRIENDLY:
            natural_response = self._add_friendly_markers(natural_response)
        elif self.style == ConversationStyle.CASUAL:
            natural_response = self._add_casual_markers(natural_response)

        return natural_response

    def _apply_style_consistency(self, response: str) -> str:
        """Apply consistent style and tone throughout the response."""
        style_config = self.style_templates.get(self.style, {})

        # Adjust formality level
        if style_config.get('formality') == 'high':
            response = self._increase_formality(response)
        elif style_config.get('formality') == 'low':
            response = self._decrease_formality(response)

        # Apply style-specific vocabulary
        response = self._apply_style_vocabulary(response, style_config)

        # Adjust sentence structure
        response = self._adjust_sentence_structure(response, style_config)

        return response

    def _enhance_engagement(self, user_input: str, response: str) -> str:
        """Enhance response to improve user engagement."""
        # Add relevant questions when appropriate
        if not self._has_question(response) and self._should_ask_question(user_input):
            response = self._add_engaging_question(user_input, response)

        # Include personalized references if context allows
        response = self._add_personalization(response, user_input)

        # Add encouraging or supportive language for certain contexts
        response = self._add_supportive_language(response, user_input)

        return response

    def _analyze_response_quality(self, user_input: str, response: str) -> ConversationMetrics:
        """Analyze response quality across multiple dimensions."""
        # Coherence scoring
        coherence_score = self._calculate_coherence_score(response)

        # Relevance scoring
        relevance_score = self._calculate_relevance_score(user_input, response)

        # Naturalness scoring
        naturalness_score = self._calculate_naturalness_score(response)

        # Engagement scoring
        engagement_score = self._calculate_engagement_score(response)

        return ConversationMetrics(
            coherence_score=coherence_score,
            relevance_score=relevance_score,
            naturalness_score=naturalness_score,
            engagement_score=engagement_score,
            response_time=0.0,  # Will be calculated separately
            context_usage=0.0   # Will be calculated separately
        )

    def _calculate_coherence_score(self, response: str) -> float:
        """Calculate coherence score based on logical flow and consistency."""
        # Check for proper transitions
        transition_score = self._score_transitions(response)

        # Check for logical consistency
        consistency_score = self._score_logical_consistency(response)

        # Check for topical unity
        unity_score = self._score_topical_unity(response)

        return (transition_score + consistency_score + unity_score) / 3

    def _calculate_relevance_score(self, user_input: str, response: str) -> float:
        """Calculate relevance score based on how well response addresses user input."""
        # Extract key topics from user input and response
        user_topics = self._extract_topics(user_input)
        response_topics = self._extract_topics(response)

        # Calculate topic overlap
        topic_overlap = len(set(user_topics) & set(response_topics)) / max(len(set(user_topics)), 1)

        # Check for direct addressing of user questions
        question_addressed = self._addresses_user_question(user_input, response)

        return (topic_overlap * 0.7 + question_addressed * 0.3)

    def _calculate_naturalness_score(self, response: str) -> float:
        """Calculate naturalness score based on human-like language patterns."""
        # Penalize overly formal or robotic language
        formal_penalties = len(re.findall(r'\b(I would|It is|Please be|In order to)\b', response))

        # Reward conversational elements
        conversational_elements = len(re.findall(r'\b(you know|I think|maybe|actually)\b', response))

        # Check sentence length variation
        sentences = re.split(r'[.!?]+', response)
        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
        length_variation = self._calculate_variation(sentence_lengths)

        base_score = 0.8
        formality_penalty = min(formal_penalties * 0.1, 0.3)
        conversational_bonus = min(conversational_elements * 0.05, 0.2)
        variation_bonus = min(length_variation * 0.1, 0.1)

        return max(0, min(1, base_score - formality_penalty + conversational_bonus + variation_bonus))

    def _calculate_engagement_score(self, response: str) -> float:
        """Calculate engagement score based on interactive elements."""
        # Check for questions
        has_questions = len(re.findall(r'\?', response)) > 0

        # Check for encouraging language
        encouraging_words = ['great', 'excellent', 'wonderful', 'fantastic', 'amazing']
        encouraging_count = sum(1 for word in encouraging_words if word in response.lower())

        # Check for personal references
        personal_references = len(re.findall(r'\b(you|your)\b', response))

        engagement_score = 0.3 * (1 if has_questions else 0)
        engagement_score += 0.3 * min(encouraging_count * 0.2, 1)
        engagement_score += 0.4 * min(personal_references * 0.1, 1)

        return min(engagement_score, 1.0)

    def _update_conversation_history(self, user_input: str, response: str, metrics: ConversationMetrics):
        """Update conversation history with latest interaction."""
        interaction = {
            'timestamp': time.time(),
            'user_input': user_input,
            'response': response,
            'metrics': metrics,
            'style': self.style.value
        }

        self.conversation_history.append(interaction)

        # Keep history manageable
        if len(self.conversation_history) > 100:
            self.conversation_history = self.conversation_history[-100:]

        # Update context window
        self.context_window.append(interaction)
        if len(self.context_window) > self.max_context_length:
            self.context_window = self.context_window[-self.max_context_length:]

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics and insights."""
        if not self.conversation_history:
            return {'message': 'No conversation history available'}

        # Calculate average metrics
        avg_coherence = sum(m.metrics.coherence_score for m in self.conversation_history) / len(self.conversation_history)
        avg_relevance = sum(m.metrics.relevance_score for m in self.conversation_history) / len(self.conversation_history)
        avg_naturalness = sum(m.metrics.naturalness_score for m in self.conversation_history) / len(self.conversation_history)
        avg_engagement = sum(m.metrics.engagement_score for m in self.conversation_history) / len(self.conversation_history)

        # Calculate improvement trends
        if len(self.conversation_history) >= 10:
            recent = self.conversation_history[-10:]
            early = self.conversation_history[:10]

            recent_avg = sum(m.metrics.coherence_score for m in recent) / len(recent)
            early_avg = sum(m.metrics.coherence_score for m in early) / len(early)

            improvement_trend = recent_avg - early_avg
        else:
            improvement_trend = 0

        return {
            'total_conversations': len(self.conversation_history),
            'average_metrics': {
                'coherence': avg_coherence,
                'relevance': avg_relevance,
                'naturalness': avg_naturalness,
                'engagement': avg_engagement
            },
            'improvement_trend': improvement_trend,
            'current_style': self.style.value,
            'optimization_enabled': self.response_optimization_enabled
        }

    # Helper methods
    def _load_coherence_patterns(self) -> Dict[str, List[str]]:
        """Load coherence improvement patterns."""
        return {
            'transitions': [
                'Additionally', 'Furthermore', 'Moreover', 'However', 'Nevertheless',
                'On the other hand', 'In contrast', 'Similarly', 'Likewise',
                'Therefore', 'Consequently', 'As a result', 'For this reason'
            ],
            'connectors': [
                'because', 'since', 'while', 'although', 'though', 'if', 'when'
            ]
        }

    def _load_style_templates(self) -> Dict[ConversationStyle, Dict[str, Any]]:
        """Load style-specific templates and configurations."""
        return {
            ConversationStyle.FRIENDLY: {
                'formality': 'low',
                'vocabulary': ['awesome', 'great', 'cool', 'definitely'],
                'sentence_structure': 'varied'
            },
            ConversationStyle.PROFESSIONAL: {
                'formality': 'high',
                'vocabulary': ['excellent', 'outstanding', 'comprehensive', 'thorough'],
                'sentence_structure': 'complex'
            },
            ConversationStyle.CASUAL: {
                'formality': 'very_low',
                'vocabulary': ['cool', 'nice', 'yeah', 'totally'],
                'sentence_structure': 'simple'
            },
            ConversationStyle.EMPATHETIC: {
                'formality': 'medium',
                'vocabulary': ['understand', 'appreciate', 'recognize', 'value'],
                'sentence_structure': 'gentle'
            }
        }

    def _has_transition(self, sentence: str) -> bool:
        """Check if sentence has transition words."""
        transitions = self.coherence_patterns['transitions']
        return any(transition.lower() in sentence.lower() for transition in transitions)

    def _add_appropriate_transition(self, current: str, previous: str) -> str:
        """Add appropriate transition word based on context."""
        # Simple logic - can be enhanced with ML
        if '?' in previous:
            return f"In response to that, {current.lower()}"
        elif 'but' in previous.lower() or 'however' in previous.lower():
            return f"Additionally, {current.lower()}"
        else:
            return current

    def _ensure_logical_consistency(self, sentence: str, context: str) -> str:
        """Ensure sentence is logically consistent with context."""
        # Placeholder for more sophisticated consistency checking
        return sentence

    def _add_friendly_markers(self, response: str) -> str:
        """Add friendly conversational markers."""
        if not response.startswith(('Hey', 'Hi', 'Hello')):
            return f"Hey! {response}"
        return response

    def _add_casual_markers(self, response: str) -> str:
        """Add casual conversational markers."""
        casual_markers = ['you know', 'like I said', 'basically']
        # Add occasional casual markers
        return response

    def _increase_formality(self, response: str) -> str:
        """Increase formality level of response."""
        formal_replacements = {
            r'\bcool\b': 'excellent',
            r'\bgot it\b': 'I understand',
            r'\bsure\b': 'certainly',
            r'\byeah\b': 'yes'
        }

        for informal, formal in formal_replacements.items():
            response = re.sub(informal, formal, response, flags=re.IGNORECASE)

        return response

    def _decrease_formality(self, response: str) -> str:
        """Decrease formality level of response."""
        formal_replacements = {
            r'\bI would like to\b': "I'd like to",
            r'\bit is\b': "it's",
            r'\byou are\b': "you're",
            r'\bthey are\b': "they're"
        }

        for formal, informal in formal_replacements.items():
            response = re.sub(formal, informal, response, flags=re.IGNORECASE)

        return response

    def _apply_style_vocabulary(self, response: str, style_config: Dict[str, Any]) -> str:
        """Apply style-specific vocabulary."""
        vocabulary = style_config.get('vocabulary', [])
        # Placeholder for vocabulary enhancement
        return response

    def _adjust_sentence_structure(self, response: str, style_config: Dict[str, Any]) -> str:
        """Adjust sentence structure based on style."""
        structure = style_config.get('sentence_structure', 'varied')
        # Placeholder for sentence structure adjustment
        return response

    def _has_question(self, response: str) -> bool:
        """Check if response contains questions."""
        return '?' in response

    def _should_ask_question(self, user_input: str) -> bool:
        """Determine if AI should ask a follow-up question."""
        # Don't ask questions if user seems to be giving final statements
        final_indicators = ['thank you', 'thanks', 'goodbye', 'bye', 'done', 'finished']
        return not any(indicator in user_input.lower() for indicator in final_indicators)

    def _add_engaging_question(self, user_input: str, response: str) -> str:
        """Add engaging follow-up question to response."""
        # Simple logic - can be enhanced with contextual understanding
        if 'how' in user_input.lower():
            response += " Does that make sense?"
        elif 'what' in user_input.lower():
            response += " What are your thoughts on that?"
        else:
            response += " Would you like to know more about this?"

        return response

    def _add_personalization(self, response: str, user_input: str) -> str:
        """Add personalized elements to response."""
        # Placeholder for personalization logic
        return response

    def _add_supportive_language(self, response: str, user_input: str) -> str:
        """Add supportive language when appropriate."""
        # Check if user is expressing difficulty or frustration
        frustration_indicators = ['difficult', 'hard', 'struggling', 'confused', 'frustrated']

        if any(indicator in user_input.lower() for indicator in frustration_indicators):
            if not any(support in response.lower() for support in ['understand', 'help', 'support']):
                response = f"I understand this might be challenging. {response}"

        return response

    def _extract_topics(self, text: str) -> List[str]:
        """Extract key topics from text."""
        # Simple keyword extraction - can be enhanced with NLP
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        topics = [word for word in words if word not in stop_words and len(word) > 3]
        return topics[:5]  # Return top 5 topics

    def _addresses_user_question(self, user_input: str, response: str) -> float:
        """Check if response addresses user's question."""
        if '?' not in user_input:
            return 1.0

        # Simple heuristic - can be enhanced with semantic analysis
        return 0.8 if len(response) > 20 else 0.4

    def _score_transitions(self, response: str) -> float:
        """Score response based on transition usage."""
        sentences = re.split(r'[.!?]+', response)
        transitions_used = sum(1 for s in sentences if self._has_transition(s))

        if len(sentences) <= 1:
            return 1.0

        return min(transitions_used / (len(sentences) - 1), 1.0)

    def _score_logical_consistency(self, response: str) -> float:
        """Score response logical consistency."""
        # Placeholder for sophisticated consistency scoring
        return 0.8

    def _score_topical_unity(self, response: str) -> float:
        """Score response for maintaining consistent topic."""
        # Simple heuristic - can be enhanced with topic modeling
        topics = self._extract_topics(response)
        unique_topics = set(topics)

        # Higher score for fewer topic changes
        if len(topics) == 0:
            return 1.0

        unity = len(topics) / len(unique_topics) if unique_topics else 1.0
        return min(unity, 1.0)

    def _calculate_variation(self, values: List[float]) -> float:
        """Calculate variation in a list of values."""
        if not values:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    def _calculate_final_metrics(self, user_input: str, response: str,
                               processing_time: float, context: Dict[str, Any]) -> ConversationMetrics:
        """Calculate final comprehensive metrics."""
        base_metrics = self._analyze_response_quality(user_input, response)

        # Update processing time
        base_metrics.response_time = processing_time

        # Calculate context usage
        context_usage = self._calculate_context_usage(context)
        base_metrics.context_usage = context_usage

        return base_metrics

    def _calculate_context_usage(self, context: Dict[str, Any]) -> float:
        """Calculate how effectively context is being used."""
        if not context:
            return 0.0

        # Simple heuristic based on context utilization
        used_context = sum(1 for value in context.values() if value)
        total_context = len(context)

        return used_context / total_context if total_context > 0 else 0.0

# Example usage and testing
if __name__ == "__main__":
    # Initialize optimizer
    optimizer = ConversationOptimizer("test_agent_1", ConversationStyle.FRIENDLY)

    # Test conversation optimization
    user_input = "I'm having trouble understanding how to use this new software"
    ai_response = "The software can be used by following the instructions in the manual."

    optimized_response, metrics = optimizer.optimize_conversation(user_input, ai_response)

    print("Original response:", ai_response)
    print("Optimized response:", optimized_response)
    print("Metrics:", f"Coherence: {metrics.coherence_score:.2f}, "
                     f"Naturalness: {metrics.naturalness_score:.2f}, "
                     f"Engagement: {metrics.engagement_score:.2f}")

    # Get performance stats
    stats = optimizer.get_performance_stats()
    print("\nPerformance Stats:", json.dumps(stats, indent=2))