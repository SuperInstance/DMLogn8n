#!/usr/bin/env python3
"""
Quality Validator - Validates and improves AI output quality

This module provides comprehensive quality assessment, validation, and
improvement mechanisms for AI-generated content across multiple dimensions.
"""

import json
import time
import re
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque
import statistics
import threading

class QualityDimension(Enum):
    ACCURACY = "accuracy"
    CLARITY = "clarity"
    COHERENCE = "coherence"
    COMPLETENESS = "completeness"
    CONCISENESS = "conciseness"
    RELEVANCE = "relevance"
    ENGAGEMENT = "engagement"
    APPROPRIATENESS = "appropriateness"
    ORIGINALITY = "originality"
    DEPTH = "depth"
    CONSISTENCY = "consistency"

class ValidationLevel(Enum):
    BASIC = "basic"
    STANDARD = "standard"
    THOROUGH = "thorough"
    COMPREHENSIVE = "comprehensive"

class ContentCategory(Enum):
    INFORMATIONAL = "informational"
    CREATIVE = "creative"
    CONVERSATIONAL = "conversational"
    TECHNICAL = "technical"
    EDUCATIONAL = "educational"
    ENTERTAINMENT = "entertainment"
    PERSUASIVE = "persuasive"

class ValidationOutcome(Enum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    NEEDS_REVIEW = "needs_review"

@dataclass
class QualityScore:
    """Represents quality score for a specific dimension."""
    dimension: QualityDimension
    score: float
    confidence: float
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

@dataclass
class ValidationResult:
    """Comprehensive validation result for content."""
    overall_score: float
    dimension_scores: List[QualityScore]
    outcome: ValidationOutcome
    issues: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    validation_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class QualityMetrics:
    """Metrics for quality validation performance."""
    validation_accuracy: float
    false_positive_rate: float
    false_negative_rate: float
    processing_time: float
    improvement_suggestion_quality: float

class QualityValidator:
    """
    Advanced quality validation system for AI-generated content.

    Features:
    - Multi-dimensional quality assessment
    - Real-time content validation
    - Automated improvement suggestions
    - Quality trend analysis
    - Context-aware validation
    - Customizable quality thresholds
    - Performance monitoring
    - Adaptive learning from feedback
    """

    def __init__(self, agent_id: str, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        self.agent_id = agent_id
        self.validation_level = validation_level

        # Quality thresholds
        self.quality_thresholds = {
            QualityDimension.ACCURACY: 0.8,
            QualityDimension.CLARITY: 0.7,
            QualityDimension.COHERENCE: 0.8,
            QualityDimension.COMPLETENESS: 0.7,
            QualityDimension.CONCISENESS: 0.6,
            QualityDimension.RELEVANCE: 0.8,
            QualityDimension.ENGAGEMENT: 0.6,
            QualityDimension.APPROPRIATENESS: 0.9,
            QualityDimension.ORIGINALITY: 0.5,
            QualityDimension.DEPTH: 0.6,
            QualityDimension.CONSISTENCY: 0.8
        }

        # Validation history and learning
        self.validation_history = deque(maxlen=1000)
        self.quality_patterns = {}
        self.feedback_history = defaultdict(list)
        self.improvement_suggestions = {}

        # Validation rules and patterns
        self.validation_rules = self._load_validation_rules()
        self.quality_patterns = self._load_quality_patterns()
        self.improvement_templates = self._load_improvement_templates()

        # Performance tracking
        self.performance_metrics = defaultdict(list)
        self.validation_stats = defaultdict(int)

        # Adaptive learning
        self.adaptive_thresholds = self.quality_thresholds.copy()
        self.learning_rate = 0.05
        self.feedback_weight = 0.3

        # Thread safety
        self.validation_lock = threading.RLock()

        # Logging
        self.logger = logging.getLogger(f"quality_validator_{agent_id}")

    def validate_content(self, content: str, context: Dict[str, Any] = None,
                        category: ContentCategory = ContentCategory.CONVERSATIONAL) -> ValidationResult:
        """
        Validate content quality across multiple dimensions.

        Args:
            content: Content to validate
            context: Additional context information
            category: Content category for category-specific validation

        Returns:
            Comprehensive validation result
        """
        with self.validation_lock:
            start_time = time.time()

            # Initialize validation result
            dimension_scores = []

            # Validate each quality dimension
            for dimension in QualityDimension:
                if self._should_validate_dimension(dimension, category):
                    score = self._validate_dimension(content, dimension, context, category)
                    dimension_scores.append(score)

            # Calculate overall score
            overall_score = self._calculate_overall_score(dimension_scores)

            # Determine validation outcome
            outcome = self._determine_outcome(overall_score, dimension_scores)

            # Generate improvement suggestions
            improvements = self._generate_improvements(content, dimension_scores, context, category)

            # Create validation result
            result = ValidationResult(
                overall_score=overall_score,
                dimension_scores=dimension_scores,
                outcome=outcome,
                issues=self._collect_issues(dimension_scores),
                improvements=improvements,
                validation_time=time.time() - start_time,
                metadata={
                    'category': category.value,
                    'content_length': len(content),
                    'validation_level': self.validation_level.value
                }
            )

            # Update validation history
            self._update_validation_history(content, result, context)

            return result

    def validate_and_improve(self, content: str, context: Dict[str, Any] = None,
                           category: ContentCategory = ContentCategory.CONVERSATIONAL,
                           auto_improve: bool = True) -> Tuple[str, ValidationResult]:
        """
        Validate content and optionally apply automatic improvements.

        Args:
            content: Content to validate and improve
            context: Additional context information
            category: Content category
            auto_improve: Whether to automatically apply improvements

        Returns:
            Tuple of (improved_content, validation_result)
        """
        # Initial validation
        validation_result = self.validate_content(content, context, category)

        # Apply improvements if needed
        improved_content = content
        if auto_improve and validation_result.outcome in [ValidationOutcome.WARNING, ValidationOutcome.FAIL]:
            improved_content = self._apply_improvements(content, validation_result.improvements)

            # Re-validate improved content
            validation_result = self.validate_content(improved_content, context, category)

        return improved_content, validation_result

    def batch_validate(self, content_list: List[str], contexts: List[Dict[str, Any]] = None,
                      category: ContentCategory = ContentCategory.CONVERSATIONAL) -> List[ValidationResult]:
        """
        Validate multiple content items in batch.

        Args:
            content_list: List of content items to validate
            contexts: List of context dictionaries (optional)
            category: Content category

        Returns:
            List of validation results
        """
        results = []

        for i, content in enumerate(content_list):
            context = contexts[i] if contexts and i < len(contexts) else None
            result = self.validate_content(content, context, category)
            results.append(result)

        return results

    def provide_feedback(self, content: str, validation_result: ValidationResult,
                        feedback_data: Dict[str, Any]) -> bool:
        """
        Provide feedback on validation quality for learning.

        Args:
            content: Original content
            validation_result: Validation result that was provided
            feedback_data: Feedback on validation quality

        Returns:
            Success status of feedback processing
        """
        with self.validation_lock:
            try:
                # Process feedback
                self._process_validation_feedback(content, validation_result, feedback_data)

                # Update adaptive thresholds
                self._update_adaptive_thresholds(feedback_data)

                # Learn from feedback
                self._learn_from_feedback(feedback_data)

                return True

            except Exception as e:
                self.logger.error(f"Error processing feedback: {e}")
                return False

    def get_quality_trends(self, time_window: int = 24) -> Dict[str, Any]:
        """
        Get quality trend analysis.

        Args:
            time_window: Time window in hours

        Returns:
            Quality trend analysis
        """
        with self.validation_lock:
            # Filter recent validations
            current_time = time.time()
            time_threshold = current_time - (time_window * 3600)

            recent_validations = [
                validation for validation in self.validation_history
                if validation['timestamp'] > time_threshold
            ]

            if not recent_validations:
                return {'message': 'No recent validation data available'}

            # Calculate trends
            trends = self._calculate_quality_trends(recent_validations)

            # Dimension-specific trends
            dimension_trends = self._calculate_dimension_trends(recent_validations)

            # Performance trends
            performance_trends = self._calculate_performance_trends(recent_validations)

            return {
                'time_window_hours': time_window,
                'total_validations': len(recent_validations),
                'overall_trends': trends,
                'dimension_trends': dimension_trends,
                'performance_trends': performance_trends,
                'average_quality_score': statistics.mean([
                    v['result'].overall_score for v in recent_validations
                ]),
                'pass_rate': sum(1 for v in recent_validations
                               if v['result'].outcome == ValidationOutcome.PASS) / len(recent_validations)
            }

    def update_quality_thresholds(self, new_thresholds: Dict[QualityDimension, float]):
        """
        Update quality thresholds for validation.

        Args:
            new_thresholds: New threshold values
        """
        with self.validation_lock:
            for dimension, threshold in new_thresholds.items():
                if 0.0 <= threshold <= 1.0:
                    self.quality_thresholds[dimension] = threshold
                    self.adaptive_thresholds[dimension] = threshold

            self.logger.info(f"Updated quality thresholds: {new_thresholds}")

    def get_validation_analytics(self) -> Dict[str, Any]:
        """Get comprehensive validation analytics."""
        with self.validation_lock:
            # Basic statistics
            total_validations = len(self.validation_history)
            if total_validations == 0:
                return {'message': 'No validation data available'}

            # Calculate statistics
            overall_scores = [v['result'].overall_score for v in self.validation_history]
            pass_count = sum(1 for v in self.validation_history
                           if v['result'].outcome == ValidationOutcome.PASS)

            # Dimension performance
            dimension_performance = self._calculate_dimension_performance()

            # Common issues
            common_issues = self._identify_common_issues()

            # Improvement effectiveness
            improvement_effectiveness = self._calculate_improvement_effectiveness()

            return {
                'agent_id': self.agent_id,
                'total_validations': total_validations,
                'validation_level': self.validation_level.value,
                'pass_rate': pass_count / total_validations,
                'average_quality_score': statistics.mean(overall_scores),
                'score_distribution': {
                    'min': min(overall_scores),
                    'max': max(overall_scores),
                    'median': statistics.median(overall_scores),
                    'std_dev': statistics.stdev(overall_scores) if len(overall_scores) > 1 else 0
                },
                'dimension_performance': dimension_performance,
                'common_issues': common_issues,
                'improvement_effectiveness': improvement_effectiveness,
                'current_thresholds': {dim.value: thresh for dim, thresh in self.quality_thresholds.items()},
                'adaptive_thresholds': {dim.value: thresh for dim, thresh in self.adaptive_thresholds.items()}
            }

    # Helper methods
    def _should_validate_dimension(self, dimension: QualityDimension, category: ContentCategory) -> bool:
        """Determine if a dimension should be validated for the given category."""
        # Category-specific dimension relevance
        category_relevance = {
            ContentCategory.INFORMATIONAL: [
                QualityDimension.ACCURACY, QualityDimension.CLARITY, QualityDimension.COMPLETENESS,
                QualityDimension.RELEVANCE, QualityDimension.DEPTH
            ],
            ContentCategory.CREATIVE: [
                QualityDimension.ORIGINALITY, QualityDimension.ENGAGEMENT, QualityDimension.CLARITY,
                QualityDimension.COHERENCE
            ],
            ContentCategory.CONVERSATIONAL: [
                QualityDimension.CLARITY, QualityDimension.RELEVANCE, QualityDimension.ENGAGEMENT,
                QualityDimension.APPROPRIATENESS, QualityDimension.CONSISTENCY
            ],
            ContentCategory.TECHNICAL: [
                QualityDimension.ACCURACY, QualityDimension.COMPLETENESS, QualityDimension.CLARITY,
                QualityDimension.RELEVANCE
            ],
            ContentCategory.EDUCATIONAL: [
                QualityDimension.CLARITY, QualityDimension.COMPLETENESS, QualityDimension.RELEVANCE,
                QualityDimension.DEPTH, QualityDimension.ENGAGEMENT
            ]
        }

        relevant_dimensions = category_relevance.get(category, list(QualityDimension))
        return dimension in relevant_dimensions

    def _validate_dimension(self, content: str, dimension: QualityDimension,
                          context: Dict[str, Any], category: ContentCategory) -> QualityScore:
        """Validate a specific quality dimension."""
        if dimension == QualityDimension.ACCURACY:
            return self._validate_accuracy(content, context)
        elif dimension == QualityDimension.CLARITY:
            return self._validate_clarity(content)
        elif dimension == QualityDimension.COHERENCE:
            return self._validate_coherence(content)
        elif dimension == QualityDimension.COMPLETENESS:
            return self._validate_completeness(content, context)
        elif dimension == QualityDimension.CONCISENESS:
            return self._validate_conciseness(content)
        elif dimension == QualityDimension.RELEVANCE:
            return self._validate_relevance(content, context)
        elif dimension == QualityDimension.ENGAGEMENT:
            return self._validate_engagement(content)
        elif dimension == QualityDimension.APPROPRIATENESS:
            return self._validate_appropriateness(content, context)
        elif dimension == QualityDimension.ORIGINALITY:
            return self._validate_originality(content)
        elif dimension == QualityDimension.DEPTH:
            return self._validate_depth(content, context)
        elif dimension == QualityDimension.CONSISTENCY:
            return self._validate_consistency(content)
        else:
            return QualityScore(dimension, 0.5, 0.5)

    def _validate_accuracy(self, content: str, context: Dict[str, Any]) -> QualityScore:
        """Validate accuracy of content."""
        issues = []
        suggestions = []
        score = 0.8  # Base score

        # Check for factual claims that might need verification
        fact_indicators = ['according to', 'research shows', 'studies indicate', 'experts say']
        for indicator in fact_indicators:
            if indicator in content.lower():
                suggestions.append("Consider citing sources for factual claims")
                score -= 0.1

        # Check for absolute claims
        absolute_words = ['always', 'never', 'all', 'none', 'every']
        for word in absolute_words:
            if word in content.lower():
                issues.append(f"Contains absolute claim: '{word}'")
                score -= 0.1
                suggestions.append("Consider softening absolute claims")

        # Check for contradictions
        sentences = content.split('.')
        if len(sentences) > 3:
            # Simple contradiction check
            for i, sentence1 in enumerate(sentences[:-1]):
                for sentence2 in sentences[i+1:]:
                    if self._are_contradictory(sentence1.strip(), sentence2.strip()):
                        issues.append("Potential contradiction detected")
                        score -= 0.2
                        suggestions.append("Review content for contradictions")
                        break

        score = max(0.0, min(1.0, score))
        confidence = 0.7  # Accuracy validation confidence

        return QualityScore(QualityDimension.ACCURACY, score, confidence, issues, suggestions)

    def _validate_clarity(self, content: str) -> QualityScore:
        """Validate clarity of content."""
        issues = []
        suggestions = []
        score = 0.8  # Base score

        # Check sentence length
        sentences = [s.strip() for s in content.split('.') if s.strip()]
        long_sentences = [s for s in sentences if len(s.split()) > 30]
        if long_sentences:
            issues.append(f"Found {len(long_sentences)} long sentences")
            score -= min(0.2, len(long_sentences) * 0.05)
            suggestions.append("Consider breaking up long sentences")

        # Check for jargon and technical terms
        jargon_words = ['utilize', 'leverage', 'synergize', 'paradigm', 'optimize']
        jargon_count = sum(1 for word in jargon_words if word in content.lower())
        if jargon_count > 2:
            issues.append("High usage of jargon or business speak")
            score -= min(0.15, jargon_count * 0.05)
            suggestions.append("Consider using simpler language")

        # Check for ambiguous terms
        ambiguous_terms = ['thing', 'stuff', 'something', 'anything', 'everything']
        ambiguous_count = sum(1 for term in ambiguous_terms if term in content.lower())
        if ambiguous_count > 3:
            issues.append("High usage of ambiguous terms")
            score -= min(0.1, ambiguous_count * 0.03)
            suggestions.append("Be more specific with language")

        # Check for clear structure
        if len(content) > 200 and not any(indicator in content.lower() for indicator in ['first', 'second', 'finally', 'however', 'therefore']):
            issues.append("Lacks clear structural indicators")
            score -= 0.1
            suggestions.append("Add structural words to improve flow")

        score = max(0.0, min(1.0, score))
        confidence = 0.8  # Clarity validation confidence

        return QualityScore(QualityDimension.CLARITY, score, confidence, issues, suggestions)

    def _validate_coherence(self, content: str) -> QualityScore:
        """Validate coherence of content."""
        issues = []
        suggestions = []
        score = 0.8  # Base score

        # Check for topic consistency
        sentences = [s.strip() for s in content.split('.') if s.strip()]
        if len(sentences) > 1:
            topics = [self._extract_topic(sentence) for sentence in sentences]
            unique_topics = set(topics)

            if len(unique_topics) > len(sentences) * 0.7:
                issues.append("Topic may be inconsistent across sentences")
                score -= 0.2
                suggestions.append("Ensure content stays focused on main topic")

        # Check for logical flow
        transition_words = ['however', 'therefore', 'furthermore', 'moreover', 'consequently', 'additionally']
        transition_count = sum(1 for word in transition_words if word in content.lower())

        if len(sentences) > 3 and transition_count == 0:
            issues.append("Lacks transition words for logical flow")
            score -= 0.1
            suggestions.append("Add transition words to improve coherence")

        # Check pronoun references
        pronouns = ['it', 'they', 'this', 'that', 'these', 'those']
        pronoun_issues = 0
        for pronoun in pronouns:
            if content.lower().count(pronoun) > 0:
                # Simple check for unclear pronoun references
                if pronoun in content.lower().split()[-1]:  # Pronoun at end might be unclear
                    pronoun_issues += 1

        if pronoun_issues > 0:
            issues.append("Some pronoun references may be unclear")
            score -= min(0.15, pronoun_issues * 0.05)
            suggestions.append("Ensure pronouns have clear antecedents")

        score = max(0.0, min(1.0, score))
        confidence = 0.7  # Coherence validation confidence

        return QualityScore(QualityDimension.COHERENCE, score, confidence, issues, suggestions)

    def _validate_completeness(self, content: str, context: Dict[str, Any]) -> QualityScore:
        """Validate completeness of content."""
        issues = []
        suggestions = []
        score = 0.7  # Base score

        # Check for unanswered questions
        if '?' in content:
            # Check if questions are rhetorical or answered
            questions = [q.strip() for q in content.split('?') if q.strip() and '?' in q]
            for question in questions:
                if not any(indicator in question.lower() for indicator in ['what about', 'how about', 'have you']):
                    issues.append("Contains unanswered question")
                    score -= 0.1

        # Check content length based on context
        if context:
            expected_length = context.get('expected_length', 'medium')
            content_length = len(content.split())

            if expected_length == 'short' and content_length > 100:
                issues.append("Response longer than expected")
                score -= 0.1
                suggestions.append("Consider being more concise")
            elif expected_length == 'long' and content_length < 200:
                issues.append("Response shorter than expected")
                score -= 0.1
                suggestions.append("Consider providing more detail")

        # Check for missing components in specific contexts
        if context and context.get('task_type') == 'explanation':
            if not any(word in content.lower() for word in ['example', 'for instance', 'such as']):
                issues.append("Explanation lacks examples")
                score -= 0.15
                suggestions.append("Add examples to improve understanding")

        score = max(0.0, min(1.0, score))
        confidence = 0.6  # Completeness validation confidence

        return QualityScore(QualityDimension.COMPLETENESS, score, confidence, issues, suggestions)

    def _validate_conciseness(self, content: str) -> QualityScore:
        """Validate conciseness of content."""
        issues = []
        suggestions = []
        score = 0.7  # Base score

        # Check for redundant phrases
        redundant_phrases = [
            'in order to', 'due to the fact that', 'in spite of the fact that',
            'at this point in time', 'for all intents and purposes', 'in the event that'
        ]

        redundant_count = sum(1 for phrase in redundant_phrases if phrase in content.lower())
        if redundant_count > 0:
            issues.append(f"Found {redundant_count} redundant phrases")
            score -= min(0.2, redundant_count * 0.1)
            suggestions.append("Remove redundant phrases for conciseness")

        # Check for word repetition
        words = content.lower().split()
        word_freq = defaultdict(int)
        for word in words:
            if len(word) > 4:  # Only check words longer than 4 characters
                word_freq[word] += 1

        repeated_words = [(word, freq) for word, freq in word_freq.items() if freq > 3]
        if repeated_words:
            issues.append(f"Words repeated frequently: {[word for word, _ in repeated_words[:3]]}")
            score -= min(0.15, len(repeated_words) * 0.05)
            suggestions.append("Consider using synonyms for repeated words")

        # Check overall length efficiency
        if len(content) > 500:
            # Check if content could be more concise
            filler_words = ['very', 'really', 'quite', 'rather', 'somewhat', 'actually']
            filler_count = sum(1 for word in filler_words if word in content.lower())
            if filler_count > len(words) * 0.1:
                issues.append("High usage of filler words")
                score -= 0.1
                suggestions.append("Reduce filler words for more concise expression")

        score = max(0.0, min(1.0, score))
        confidence = 0.8  # Conciseness validation confidence

        return QualityScore(QualityDimension.CONCISENESS, score, confidence, issues, suggestions)

    def _validate_relevance(self, content: str, context: Dict[str, Any]) -> QualityScore:
        """Validate relevance of content."""
        issues = []
        suggestions = []
        score = 0.8  # Base score

        if not context:
            return QualityScore(QualityDimension.RELEVANCE, score, 0.5, ['No context provided for relevance check'])

        # Check if content addresses the main topic
        main_topic = context.get('main_topic', '').lower()
        if main_topic:
            topic_mentions = content.lower().count(main_topic)
            if topic_mentions == 0:
                issues.append("Content may not address the main topic")
                score -= 0.3
                suggestions.append("Ensure content directly addresses the main topic")
            elif topic_mentions < len(content.split()) * 0.05:
                issues.append("Main topic mentioned infrequently")
                score -= 0.15
                suggestions.append("Increase relevance to main topic")

        # Check for off-topic content
        if 'user_query' in context:
            query_words = set(context['user_query'].lower().split())
            content_words = set(content.lower().split())
            overlap = len(query_words & content_words)

            if overlap < min(3, len(query_words) * 0.5):
                issues.append("Content may not be directly relevant to user query")
                score -= 0.2
                suggestions.append("Increase relevance to user query")

        score = max(0.0, min(1.0, score))
        confidence = 0.7  # Relevance validation confidence

        return QualityScore(QualityDimension.RELEVANCE, score, confidence, issues, suggestions)

    def _validate_engagement(self, content: str) -> QualityScore:
        """Validate engagement potential of content."""
        issues = []
        suggestions = []
        score = 0.6  # Base score

        # Check for interactive elements
        questions = content.count('?')
        if questions == 0:
            issues.append("No questions to encourage engagement")
            score -= 0.2
            suggestions.append("Add questions to increase engagement")

        # Check for active voice usage
        passive_indicators = ['is done by', 'was made by', 'are caused by', 'will be done by']
        passive_count = sum(1 for indicator in passive_indicators if indicator in content.lower())
        if passive_count > 0:
            issues.append("Uses passive voice which can reduce engagement")
            score -= min(0.15, passive_count * 0.05)
            suggestions.append("Use more active voice for engaging content")

        # Check for engaging language
        engaging_words = ['you', 'your', 'imagine', 'discover', 'explore', 'create', 'achieve']
        engaging_count = sum(1 for word in engaging_words if word in content.lower())
        if engaging_count < 2:
            issues.append("Limited use of engaging language")
            score -= 0.1
            suggestions.append("Add more engaging and personal language")

        # Check for variety in sentence structure
        sentences = [s.strip() for s in content.split('.') if s.strip()]
        if len(sentences) > 3:
            sentence_lengths = [len(s.split()) for s in sentences]
            length_variance = statistics.stdev(sentence_lengths) if len(sentence_lengths) > 1 else 0
            if length_variance < 3:
                issues.append("Sentence structure lacks variety")
                score -= 0.1
                suggestions.append("Vary sentence structure for better engagement")

        score = max(0.0, min(1.0, score))
        confidence = 0.6  # Engagement validation confidence

        return QualityScore(QualityDimension.ENGAGEMENT, score, confidence, issues, suggestions)

    def _validate_appropriateness(self, content: str, context: Dict[str, Any]) -> QualityScore:
        """Validate appropriateness of content."""
        issues = []
        suggestions = []
        score = 0.9  # Base score (high because inappropriate content should be rare)

        # Check for potentially inappropriate language
        inappropriate_words = ['stupid', 'dumb', 'idiot', 'hate', 'kill']  # Simplified list
        inappropriate_count = sum(1 for word in inappropriate_words if word in content.lower())
        if inappropriate_count > 0:
            issues.append(f"Contains potentially inappropriate language")
            score -= 0.5
            suggestions.append("Remove or replace inappropriate language")

        # Check tone appropriateness based on context
        if context:
            context_tone = context.get('expected_tone', 'neutral')
            content_tone = self._detect_tone(content)

            if context_tone != content_tone:
                issues.append(f"Tone mismatch: expected {context_tone}, detected {content_tone}")
                score -= 0.2
                suggestions.append(f"Adjust tone to match expected {context_tone} tone")

        # Check for cultural sensitivity
        cultural_insensitive_patterns = [
            'all men are', 'all women are', 'obviously', 'everyone knows'
        ]
        for pattern in cultural_insensitive_patterns:
            if pattern in content.lower():
                issues.append("May contain culturally insensitive assumptions")
                score -= 0.3
                suggestions.append("Review content for cultural sensitivity")

        score = max(0.0, min(1.0, score))
        confidence = 0.8  # Appropriateness validation confidence

        return QualityScore(QualityDimension.APPROPRIATENESS, score, confidence, issues, suggestions)

    def _validate_originality(self, content: str) -> QualityScore:
        """Validate originality of content."""
        issues = []
        suggestions = []
        score = 0.7  # Base score

        # Check for clichés and overused phrases
        cliches = [
            'at the end of the day', 'think outside the box', 'low hanging fruit',
            'synergy', 'paradigm shift', 'game changer', 'win-win situation'
        ]
        cliche_count = sum(1 for cliche in cliches if cliche in content.lower())
        if cliche_count > 0:
            issues.append(f"Contains {cliche_count} cliché(s) or overused phrases")
            score -= min(0.2, cliche_count * 0.05)
            suggestions.append("Replace clichés with more original expressions")

        # Check for unique phrasing (simplified)
        common_phrases = [
            'in conclusion', 'to summarize', 'on the other hand', 'in my opinion',
            'first of all', 'last but not least'
        ]
        common_count = sum(1 for phrase in common_phrases if phrase in content.lower())
        if common_count > len(content.split('.')):
            issues.append("Relies heavily on common transitional phrases")
            score -= 0.1
            suggestions.append("Use more original transitional phrases")

        score = max(0.0, min(1.0, score))
        confidence = 0.5  # Originality validation confidence (subjective)

        return QualityScore(QualityDimension.ORIGINALITY, score, confidence, issues, suggestions)

    def _validate_depth(self, content: str, context: Dict[str, Any]) -> QualityScore:
        """Validate depth of content."""
        issues = []
        suggestions = []
        score = 0.6  # Base score

        # Check for specific examples or evidence
        example_indicators = ['for example', 'for instance', 'such as', 'specifically']
        example_count = sum(1 for indicator in example_indicators if indicator in content.lower())
        if example_count == 0 and len(content) > 100:
            issues.append("Lacks specific examples or evidence")
            score -= 0.2
            suggestions.append("Add specific examples to increase depth")

        # Check for analytical elements
        analytical_words = ['analyze', 'examine', 'consider', 'evaluate', 'compare', 'contrast']
        analytical_count = sum(1 for word in analytical_words if word in content.lower())
        if analytical_count == 0 and context and context.get('task_type') == 'analysis':
            issues.append("Lacks analytical depth")
            score -= 0.3
            suggestions.append("Include more analytical elements")

        # Check content depth based on length
        content_length = len(content.split())
        if content_length < 50:
            issues.append("Content may be too brief for substantive discussion")
            score -= 0.3
            suggestions.append("Expand content to provide more depth")
        elif content_length > 50 and content_length < 100:
            # Check if there's substantive content
            substantive_words = ['because', 'therefore', 'however', 'although', 'since', 'due to']
            substantive_count = sum(1 for word in substantive_words if word in content.lower())
            if substantive_count == 0:
                issues.append("Content lacks substantive reasoning")
                score -= 0.15
                suggestions.append("Add more reasoning and explanation")

        score = max(0.0, min(1.0, score))
        confidence = 0.6  # Depth validation confidence

        return QualityScore(QualityDimension.DEPTH, score, confidence, issues, suggestions)

    def _validate_consistency(self, content: str) -> QualityScore:
        """Validate consistency of content."""
        issues = []
        suggestions = []
        score = 0.8  # Base score

        # Check for consistent terminology
        sentences = [s.strip() for s in content.split('.') if s.strip()]
        if len(sentences) > 2:
            # Extract key terms and check for consistent usage
            terms = self._extract_key_terms(content)
            for term in terms:
                variations = self._find_term_variations(term, sentences)
                if len(variations) > 1:
                    issues.append(f"Inconsistent terminology: '{term}' has variations: {variations}")
                    score -= 0.1
                    suggestions.append(f"Use consistent terminology for '{term}'")

        # Check for consistent formatting
        if content.count('!') > len(content.split('.')) * 0.3:
            issues.append("Excessive use of exclamation marks")
            score -= 0.1
            suggestions.append("Use exclamation marks more sparingly for consistency")

        # Check for consistent point of view
        first_person = content.lower().count(' i ') + content.lower().count(' my ')
        second_person = content.lower().count(' you ') + content.lower().count(' your ')
        third_person = content.lower().count(' they ') + content.lower().count(' their ')

        pov_counts = [(first_person, 'first'), (second_person, 'second'), (third_person, 'third')]
        dominant_pov = max(pov_counts, key=lambda x: x[0])
        other_pov_count = sum(count for count, _ in pov_counts if count != dominant_pov[0])

        if dominant_pov[0] > 0 and other_pov_count > dominant_pov[0] * 0.5:
            issues.append("Inconsistent point of view")
            score -= 0.15
            suggestions.append("Maintain consistent point of view throughout")

        score = max(0.0, min(1.0, score))
        confidence = 0.7  # Consistency validation confidence

        return QualityScore(QualityDimension.CONSISTENCY, score, confidence, issues, suggestions)

    def _calculate_overall_score(self, dimension_scores: List[QualityScore]) -> float:
        """Calculate overall quality score from dimension scores."""
        if not dimension_scores:
            return 0.5

        # Weight dimensions based on their confidence scores
        weighted_scores = []
        total_weight = 0

        for score in dimension_scores:
            weight = score.confidence
            weighted_scores.append(score.score * weight)
            total_weight += weight

        return sum(weighted_scores) / total_weight if total_weight > 0 else 0.5

    def _determine_outcome(self, overall_score: float, dimension_scores: List[QualityScore]) -> ValidationOutcome:
        """Determine validation outcome based on scores."""
        # Check critical dimensions
        critical_dimensions = [QualityDimension.ACCURACY, QualityDimension.APPROPRIATENESS]
        for dimension in critical_dimensions:
            dim_score = next((s for s in dimension_scores if s.dimension == dimension), None)
            if dim_score and dim_score.score < self.quality_thresholds[dimension]:
                return ValidationOutcome.FAIL

        # Check overall score
        if overall_score >= 0.8:
            return ValidationOutcome.PASS
        elif overall_score >= 0.6:
            return ValidationOutcome.WARNING
        else:
            return ValidationOutcome.NEEDS_REVIEW

    def _generate_improvements(self, content: str, dimension_scores: List[QualityScore],
                             context: Dict[str, Any], category: ContentCategory) -> List[str]:
        """Generate improvement suggestions based on validation results."""
        improvements = []

        # Collect suggestions from all dimensions
        all_suggestions = []
        for score in dimension_scores:
            all_suggestions.extend(score.suggestions)

        # Prioritize suggestions based on score impact
        low_score_dimensions = [s for s in dimension_scores if s.score < self.quality_thresholds[s.dimension]]
        low_score_dimensions.sort(key=lambda x: x.score)

        for dim_score in low_score_dimensions[:3]:  # Top 3 issues
            if dim_score.suggestions:
                improvements.append(dim_score.suggestions[0])

        # Add category-specific improvements
        if category == ContentCategory.INFORMATIONAL:
            improvements.append("Ensure factual accuracy with proper citations")
        elif category == ContentCategory.CREATIVE:
            improvements.append("Consider adding more creative elements")
        elif category == ContentCategory.CONVERSATIONAL:
            improvements.append("Maintain natural, engaging conversational tone")

        return improvements[:5]  # Return top 5 suggestions

    def _apply_improvements(self, content: str, improvements: List[str]) -> str:
        """Apply automatic improvements to content."""
        improved_content = content

        for improvement in improvements:
            # Simple automatic improvements
            if "more concise" in improvement.lower():
                improved_content = self._make_more_concise(improved_content)
            elif "transition words" in improvement.lower():
                improved_content = self._add_transitions(improved_content)
            elif "examples" in improvement.lower():
                improved_content = self._add_examples(improved_content)

        return improved_content

    def _collect_issues(self, dimension_scores: List[QualityScore]) -> List[str]:
        """Collect all issues from dimension validation."""
        all_issues = []
        for score in dimension_scores:
            all_issues.extend(score.issues)
        return all_issues

    def _update_validation_history(self, content: str, result: ValidationResult, context: Dict[str, Any]):
        """Update validation history for learning."""
        history_entry = {
            'timestamp': time.time(),
            'content_hash': hashlib.md5(content.encode()).hexdigest()[:8],
            'result': result,
            'context': context
        }

        self.validation_history.append(history_entry)

    def _are_contradictory(self, sentence1: str, sentence2: str) -> bool:
        """Check if two sentences are contradictory."""
        # Simplified contradiction detection
        contradictions = [
            ('always', 'never'), ('all', 'none'), ('every', 'no'),
            ('good', 'bad'), ('right', 'wrong'), ('true', 'false')
        ]

        for word1, word2 in contradictions:
            if word1 in sentence1.lower() and word2 in sentence2.lower():
                return True
            if word2 in sentence1.lower() and word1 in sentence2.lower():
                return True

        return False

    def _extract_topic(self, sentence: str) -> str:
        """Extract main topic from sentence."""
        # Simple topic extraction - return most frequent meaningful word
        words = sentence.lower().split()
        meaningful_words = [w for w in words if len(w) > 3 and w not in ['the', 'and', 'but', 'for', 'with', 'that', 'this', 'from', 'have', 'been', 'will', 'would', 'could', 'should']]

        if meaningful_words:
            return meaningful_words[0]
        return "unknown"

    def _detect_tone(self, content: str) -> str:
        """Detect the tone of content."""
        content_lower = content.lower()

        if any(word in content_lower for word in ['formal', 'respectfully', 'accordingly']):
            return 'formal'
        elif any(word in content_lower for word in ['happy', 'excited', 'great']):
            return 'enthusiastic'
        elif any(word in content_lower for word in ['sorry', 'apologize', 'regret']):
            return 'apologetic'
        else:
            return 'neutral'

    def _extract_key_terms(self, content: str) -> List[str]:
        """Extract key terms from content."""
        words = content.lower().split()
        # Filter out common words and return terms that appear multiple times
        word_freq = defaultdict(int)
        for word in words:
            if len(word) > 4 and word not in ['the', 'and', 'but', 'for', 'with', 'that', 'this']:
                word_freq[word] += 1

        return [word for word, freq in word_freq.items() if freq > 1]

    def _find_term_variations(self, term: str, sentences: List[str]) -> List[str]:
        """Find variations of a term across sentences."""
        variations = set()
        term_lower = term.lower()

        for sentence in sentences:
            sentence_lower = sentence.lower()
            if term_lower in sentence_lower:
                # Find the exact term as used in this sentence
                words = sentence_lower.split()
                for word in words:
                    if term_lower in word:
                        variations.add(word)

        return list(variations)

    def _make_more_concise(self, content: str) -> str:
        """Make content more concise."""
        # Remove redundant phrases
        redundant_phrases = [
            'in order to', 'due to the fact that', 'in spite of the fact that',
            'at this point in time', 'for all intents and purposes'
        ]

        improved = content
        for phrase in redundant_phrases:
            improved = improved.replace(phrase, phrase.replace(' ', ' '))

        return improved

    def _add_transitions(self, content: str) -> str:
        """Add transition words to improve flow."""
        sentences = [s.strip() for s in content.split('.') if s.strip()]
        if len(sentences) < 2:
            return content

        transitions = ['However, ', 'Furthermore, ', 'Therefore, ', 'In addition, ', 'Consequently, ']
        improved_sentences = [sentences[0]]

        for i, sentence in enumerate(sentences[1:], 1):
            if i % 2 == 0:  # Add transitions to every other sentence
                transition = transitions[i % len(transitions)]
                improved_sentences.append(transition + sentence)
            else:
                improved_sentences.append(sentence)

        return '. '.join(improved_sentences) + '.'

    def _add_examples(self, content: str) -> str:
        """Add examples to content."""
        # Simple example addition
        if 'for example' not in content.lower() and 'for instance' not in content.lower():
            content += " For example, this approach can be applied in various scenarios."

        return content

    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules."""
        return {
            'accuracy': {
                'fact_check_required': True,
                'contradiction_penalty': 0.2,
                'absolute_claim_penalty': 0.1
            },
            'clarity': {
                'max_sentence_length': 30,
                'jargon_penalty': 0.05,
                'ambiguity_penalty': 0.03
            }
        }

    def _load_quality_patterns(self) -> Dict[str, Any]:
        """Load quality patterns for recognition."""
        return {
            'high_quality_patterns': [
                'clear_structure', 'logical_flow', 'supporting_evidence',
                'appropriate_tone', 'engaging_language'
            ],
            'low_quality_patterns': [
                'repetitive_content', 'unclear_references', 'abrupt_transitions',
                'inconsistent_terminology', 'lacking_examples'
            ]
        }

    def _load_improvement_templates(self) -> Dict[str, str]:
        """Load improvement suggestion templates."""
        return {
            'accuracy': "Verify factual claims and cite sources when making assertions",
            'clarity': "Use simpler language and break down complex sentences",
            'coherence': "Add transition words to improve logical flow",
            'completeness': "Provide more comprehensive coverage of the topic",
            'conciseness': "Remove redundant phrases and filler words",
            'relevance': "Ensure content directly addresses the main topic",
            'engagement': "Add questions and use active voice to engage the reader",
            'appropriateness': "Adjust tone to match the expected context",
            'originality': "Replace clichés with more original expressions",
            'depth': "Add specific examples and deeper analysis",
            'consistency': "Maintain consistent terminology and point of view"
        }

    def _process_validation_feedback(self, content: str, validation_result: ValidationResult,
                                   feedback_data: Dict[str, Any]):
        """Process feedback on validation quality."""
        # Store feedback for learning
        feedback_entry = {
            'timestamp': time.time(),
            'content_hash': hashlib.md5(content.encode()).hexdigest()[:8],
            'validation_result': validation_result,
            'feedback_data': feedback_data
        }

        self.feedback_history['validation_feedback'].append(feedback_entry)

    def _update_adaptive_thresholds(self, feedback_data: Dict[str, Any]):
        """Update adaptive thresholds based on feedback."""
        if 'threshold_adjustment' in feedback_data:
            adjustments = feedback_data['threshold_adjustment']
            for dimension, adjustment in adjustments.items():
                if dimension in self.adaptive_thresholds:
                    current = self.adaptive_thresholds[dimension]
                    new_value = current + (adjustment * self.learning_rate * self.feedback_weight)
                    self.adaptive_thresholds[dimension] = max(0.0, min(1.0, new_value))

    def _learn_from_feedback(self, feedback_data: Dict[str, Any]):
        """Learn from feedback to improve validation."""
        if 'improvement_effectiveness' in feedback_data:
            effectiveness = feedback_data['improvement_effectiveness']
            self.performance_metrics['improvement_effectiveness'].append(effectiveness)

    def _calculate_quality_trends(self, recent_validations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate quality trends over time."""
        if len(recent_validations) < 2:
            return {'message': 'Insufficient data for trend analysis'}

        scores = [v['result'].overall_score for v in recent_validations]
        first_half = scores[:len(scores)//2]
        second_half = scores[len(scores)//2:]

        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)

        trend = 'improving' if second_avg > first_avg else 'declining' if second_avg < first_avg else 'stable'
        magnitude = abs(second_avg - first_avg)

        return {
            'trend': trend,
            'magnitude': magnitude,
            'first_period_average': first_avg,
            'second_period_average': second_avg
        }

    def _calculate_dimension_trends(self, recent_validations: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Calculate trends for specific dimensions."""
        dimension_trends = {}

        for dimension in QualityDimension:
            scores = []
            for validation in recent_validations:
                dim_score = next((s for s in validation['result'].dimension_scores if s.dimension == dimension), None)
                if dim_score:
                    scores.append(dim_score.score)

            if len(scores) >= 2:
                first_half = scores[:len(scores)//2]
                second_half = scores[len(scores)//2:]
                trend = statistics.mean(second_half) - statistics.mean(first_half)
                dimension_trends[dimension.value] = {'trend': trend, 'average': statistics.mean(scores)}

        return dimension_trends

    def _calculate_performance_trends(self, recent_validations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance trends."""
        validation_times = [v['result'].validation_time for v in recent_validations]
        pass_count = sum(1 for v in recent_validations if v['result'].outcome == ValidationOutcome.PASS)

        return {
            'average_validation_time': statistics.mean(validation_times),
            'validation_time_variance': statistics.stdev(validation_times) if len(validation_times) > 1 else 0,
            'pass_rate': pass_count / len(recent_validations),
            'validation_frequency': len(recent_validations) / 24  # Validations per hour
        }

    def _calculate_dimension_performance(self) -> Dict[str, Dict[str, float]]:
        """Calculate performance by dimension."""
        dimension_performance = {}

        for dimension in QualityDimension:
            scores = []
            confidences = []

            for validation in self.validation_history:
                dim_score = next((s for s in validation['result'].dimension_scores if s.dimension == dimension), None)
                if dim_score:
                    scores.append(dim_score.score)
                    confidences.append(dim_score.confidence)

            if scores:
                dimension_performance[dimension.value] = {
                    'average_score': statistics.mean(scores),
                    'average_confidence': statistics.mean(confidences),
                    'score_variance': statistics.stdev(scores) if len(scores) > 1 else 0,
                    'total_validations': len(scores)
                }

        return dimension_performance

    def _identify_common_issues(self) -> List[Dict[str, Any]]:
        """Identify most common validation issues."""
        issue_counts = defaultdict(int)

        for validation in self.validation_history:
            for issue in validation['result'].issues:
                issue_counts[issue] += 1

        # Sort by frequency and return top issues
        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        return [
            {'issue': issue, 'frequency': count, 'percentage': (count / len(self.validation_history)) * 100}
            for issue, count in sorted_issues[:10]
        ]

    def _calculate_improvement_effectiveness(self) -> Dict[str, float]:
        """Calculate effectiveness of improvement suggestions."""
        if 'improvement_effectiveness' not in self.performance_metrics:
            return {'message': 'No improvement effectiveness data available'}

        effectiveness_scores = self.performance_metrics['improvement_effectiveness']
        if not effectiveness_scores:
            return {'message': 'No improvement effectiveness data available'}

        return {
            'average_effectiveness': statistics.mean(effectiveness_scores),
            'effectiveness_trend': 'improving' if len(effectiveness_scores) > 1 and effectiveness_scores[-1] > effectiveness_scores[0] else 'stable',
            'total_improvements_assessed': len(effectiveness_scores)
        }

# Example usage and testing
if __name__ == "__main__":
    # Create quality validator
    validator = QualityValidator("test_agent_1", ValidationLevel.STANDARD)

    # Test content validation
    content = "Machine learning is a really cool technology that can help solve many problems. It is used in many different applications and can be very beneficial for organizations that want to leverage data."
    context = {
        'main_topic': 'machine learning',
        'task_type': 'explanation',
        'expected_tone': 'informative'
    }

    result = validator.validate_content(content, context, ContentCategory.INFORMATIONAL)

    print(f"Validation Result:")
    print(f"  Overall Score: {result.overall_score:.2f}")
    print(f"  Outcome: {result.outcome.value}")
    print(f"  Validation Time: {result.validation_time:.3f}s")

    print("\nDimension Scores:")
    for score in result.dimension_scores:
        print(f"  {score.dimension.value}: {score.score:.2f} (confidence: {score.confidence:.2f})")
        if score.issues:
            print(f"    Issues: {', '.join(score.issues)}")

    print("\nImprovement Suggestions:")
    for suggestion in result.improvements:
        print(f"  - {suggestion}")

    # Get analytics
    analytics = validator.get_validation_analytics()
    print("\nValidation Analytics:", json.dumps(analytics, indent=2))