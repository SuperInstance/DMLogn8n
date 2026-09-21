#!/usr/bin/env python3
"""
Learning Accelerator - Faster learning from interactions for AI agents

This module accelerates AI learning through feedback mechanisms, experience
tracking, pattern recognition, and adaptive knowledge acquisition.
"""

import json
import time
import hashlib
import pickle
from typing import Dict, List, Optional, Tuple, Any, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque
import numpy as np
import threading

class LearningType(Enum):
    SUPERVISED = "supervised"
    REINFORCEMENT = "reinforcement"
    UNSUPERVISED = "unsupervised"
    TRANSFER = "transfer"
    ACTIVE = "active"
    ONLINE = "online"
    BATCH = "batch"

class FeedbackType(Enum):
    EXPLICIT = "explicit"  # Direct user feedback
    IMPLICIT = "implicit"  # Inferred from behavior
    CORRECTIVE = "corrective"  # Error correction
    AFFIRMATIVE = "affirmative"  # Positive reinforcement
    CONSTRUCTIVE = "constructive"  # Improvement suggestions

class KnowledgeDomain(Enum):
    CONVERSATION = "conversation"
    TASK_COMPLETION = "task_completion"
    USER_PREFERENCES = "user_preferences"
    DOMAIN_KNOWLEDGE = "domain_knowledge"
    PROBLEM_SOLVING = "problem_solving"
    CREATIVITY = "creativity"
    EMOTIONAL_INTELLIGENCE = "emotional_intelligence"

class LearningStrategy(Enum):
    GRADUAL_IMPROVEMENT = "gradual_improvement"
    RAPID_ACQUISITION = "rapid_acquisition"
    CONSERVATIVE_LEARNING = "conservative_learning"
    AGGRESSIVE_LEARNING = "aggressive_learning"
    BALANCED = "balanced"

@dataclass
class LearningExperience:
    """Represents a learning experience."""
    experience_id: str
    domain: KnowledgeDomain
    input_data: Any
    output_data: Any
    feedback: Dict[str, float]
    timestamp: float
    context: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.5
    retention_score: float = 1.0
    related_experiences: List[str] = field(default_factory=list)

@dataclass
class LearningMetrics:
    """Metrics for learning performance."""
    learning_rate: float
    knowledge_retention: float
    adaptation_speed: float
    feedback_utilization: float
    pattern_recognition: float
    transfer_efficiency: float

class LearningAccelerator:
    """
    Advanced learning acceleration system for AI agents.

    Features:
    - Multi-modal learning from various feedback types
    - Experience tracking and analysis
    - Pattern recognition and knowledge extraction
    - Adaptive learning rates
    - Knowledge consolidation and transfer
    - Performance monitoring and optimization
    - Forgetting curve management
    - Active learning strategies
    """

    def __init__(self, agent_id: str, max_experiences: int = 10000):
        self.agent_id = agent_id
        self.max_experiences = max_experiences

        # Experience storage
        self.experience_database = []
        self.domain_experiences = defaultdict(list)
        self.feedback_history = defaultdict(list)
        self.learning_patterns = {}

        # Learning state
        self.learning_rates = {domain: 0.1 for domain in KnowledgeDomain}
        self.knowledge_weights = defaultdict(float)
        self.performance_history = defaultdict(list)
        self.adaptation_history = []

        # Configuration
        self.learning_strategy = LearningStrategy.BALANCED
        self.feedback_sensitivity = 0.7
        self.forgetting_rate = 0.95
        self.consolidation_threshold = 50
        self.pattern_recognition_enabled = True
        self.transfer_learning_enabled = True

        # Advanced learning parameters
        self.experience_replay_buffer = deque(maxlen=1000)
        self.priority_experiences = []
        self.consolidated_knowledge = {}
        self.learning_momentum = defaultdict(float)

        # Neural network weights (simplified representation)
        self.neural_weights = defaultdict(lambda: defaultdict(float))
        self.activation_patterns = defaultdict(list)

        # Thread safety
        self.learning_lock = threading.RLock()

        # Logging
        self.logger = logging.getLogger(f"learning_accelerator_{agent_id}")

    def learn_from_interaction(self, input_data: Any, output_data: Any, feedback: Dict[str, Any],
                             domain: KnowledgeDomain, context: Dict[str, Any] = None) -> LearningMetrics:
        """
        Learn from a single interaction with feedback.

        Args:
            input_data: Input to the AI system
            output_data: Output produced by the AI
            feedback: Feedback data (scores, corrections, etc.)
            domain: Knowledge domain of the interaction
            context: Additional context information

        Returns:
            Learning metrics for this interaction
        """
        with self.learning_lock:
            # Create learning experience
            experience = self._create_learning_experience(
                input_data, output_data, feedback, domain, context
            )

            # Process feedback
            processed_feedback = self._process_feedback(feedback, experience)

            # Update learning parameters
            self._update_learning_parameters(experience, processed_feedback)

            # Store experience
            self._store_experience(experience)

            # Perform pattern recognition
            if self.pattern_recognition_enabled:
                self._recognize_patterns(experience)

            # Update neural weights
            self._update_neural_weights(experience, processed_feedback)

            # Check for consolidation
            if len(self.experience_database) >= self.consolidation_threshold:
                self._consolidate_knowledge()

            # Calculate learning metrics
            metrics = self._calculate_learning_metrics(experience, processed_feedback)

            # Update performance history
            self._update_performance_history(domain, metrics)

            return metrics

    def batch_learn(self, experiences: List[Dict[str, Any]]) -> LearningMetrics:
        """
        Learn from a batch of experiences.

        Args:
            experiences: List of experience dictionaries

        Returns:
            Aggregate learning metrics
        """
        with self.learning_lock:
            all_metrics = []

            for exp_data in experiences:
                metrics = self.learn_from_interaction(
                    exp_data.get('input_data'),
                    exp_data.get('output_data'),
                    exp_data.get('feedback', {}),
                    KnowledgeDomain(exp_data.get('domain', 'conversation')),
                    exp_data.get('context', {})
                )
                all_metrics.append(metrics)

            # Calculate aggregate metrics
            aggregate_metrics = self._aggregate_learning_metrics(all_metrics)

            # Perform batch consolidation
            self._batch_consolidation()

            return aggregate_metrics

    def adapt_to_feedback(self, feedback_type: FeedbackType, feedback_data: Dict[str, Any],
                         target_domain: KnowledgeDomain = None) -> bool:
        """
        Adapt AI behavior based on specific feedback.

        Args:
            feedback_type: Type of feedback
            feedback_data: Feedback content
            target_domain: Target domain for adaptation

        Returns:
            Success status of adaptation
        """
        with self.learning_lock:
            try:
                # Process feedback based on type
                if feedback_type == FeedbackType.EXPLICIT:
                    adaptation_success = self._process_explicit_feedback(feedback_data, target_domain)
                elif feedback_type == FeedbackType.IMPLICIT:
                    adaptation_success = self._process_implicit_feedback(feedback_data, target_domain)
                elif feedback_type == FeedbackType.CORRECTIVE:
                    adaptation_success = self._process_corrective_feedback(feedback_data, target_domain)
                elif feedback_type == FeedbackType.AFFIRMATIVE:
                    adaptation_success = self._process_affirmative_feedback(feedback_data, target_domain)
                elif feedback_type == FeedbackType.CONSTRUCTIVE:
                    adaptation_success = self._process_constructive_feedback(feedback_data, target_domain)
                else:
                    adaptation_success = False

                if adaptation_success:
                    self._update_adaptation_history(feedback_type, feedback_data, target_domain)

                return adaptation_success

            except Exception as e:
                self.logger.error(f"Error adapting to feedback: {e}")
                return False

    def get_knowledge_summary(self, domain: KnowledgeDomain = None) -> Dict[str, Any]:
        """
        Get summary of learned knowledge.

        Args:
            domain: Specific domain to summarize (optional)

        Returns:
            Knowledge summary dictionary
        """
        with self.learning_lock:
            if domain:
                return self._get_domain_knowledge_summary(domain)
            else:
                return self._get_overall_knowledge_summary()

    def optimize_learning_strategy(self, performance_data: Dict[str, float]) -> LearningStrategy:
        """
        Optimize learning strategy based on performance data.

        Args:
            performance_data: Performance metrics data

        Returns:
            Optimized learning strategy
        """
        with self.learning_lock:
            # Analyze performance trends
            current_performance = performance_data.get('overall_performance', 0.5)
            learning_velocity = performance_data.get('learning_velocity', 0.1)
            stability_score = performance_data.get('stability', 0.7)

            # Determine optimal strategy
            if learning_velocity < 0.05 and stability_score > 0.8:
                new_strategy = LearningStrategy.RAPID_ACQUISITION
            elif learning_velocity > 0.2 and stability_score < 0.5:
                new_strategy = LearningStrategy.CONSERVATIVE_LEARNING
            elif current_performance < 0.3:
                new_strategy = LearningStrategy.AGGRESSIVE_LEARNING
            elif stability_score < 0.4:
                new_strategy = LearningStrategy.GRADUAL_IMPROVEMENT
            else:
                new_strategy = LearningStrategy.BALANCED

            # Update strategy
            old_strategy = self.learning_strategy
            self.learning_strategy = new_strategy

            self.logger.info(f"Learning strategy changed from {old_strategy.value} to {new_strategy.value}")

            return new_strategy

    def reinforce_learning(self, successful_patterns: List[str], reward_magnitude: float = 1.0):
        """
        Reinforce successful learning patterns.

        Args:
            successful_patterns: List of successful pattern identifiers
            reward_magnitude: Magnitude of reinforcement reward
        """
        with self.learning_lock:
            for pattern in successful_patterns:
                if pattern in self.learning_patterns:
                    # Increase pattern weight
                    self.learning_patterns[pattern]['weight'] += reward_magnitude * 0.1
                    self.learning_patterns[pattern]['success_count'] += 1

                    # Update related neural weights
                    for neuron_id in self.learning_patterns[pattern].get('neurons', []):
                        self.neural_weights[neuron_id]['activation'] += reward_magnitude * 0.05

                    # Update learning momentum
                    domain = self.learning_patterns[pattern].get('domain', KnowledgeDomain.CONVERSATION)
                    self.learning_momentum[domain] += reward_magnitude * 0.1

    def forget_irrelevant_knowledge(self, relevance_threshold: float = 0.1):
        """
        Forget irrelevant knowledge to maintain efficiency.

        Args:
            relevance_threshold: Threshold below which knowledge is forgotten
        """
        with self.learning_lock:
            # Apply forgetting curve to experiences
            for experience in self.experience_database:
                experience.retention_score *= self.forgetting_rate

            # Remove experiences below threshold
            self.experience_database = [
                exp for exp in self.experience_database
                if exp.retention_score > relevance_threshold
            ]

            # Update domain experiences
            for domain in KnowledgeDomain:
                self.domain_experiences[domain] = [
                    exp for exp in self.domain_experiences[domain]
                    if exp.retention_score > relevance_threshold
                ]

            # Decay knowledge weights
            for key in self.knowledge_weights:
                self.knowledge_weights[key] *= self.forgetting_rate

            # Remove weights below threshold
            self.knowledge_weights = {
                key: weight for key, weight in self.knowledge_weights.items()
                if weight > relevance_threshold
            }

    def get_learning_analytics(self) -> Dict[str, Any]:
        """Get comprehensive learning analytics."""
        with self.learning_lock:
            # Basic statistics
            total_experiences = len(self.experience_database)
            domain_distribution = {
                domain.value: len(experiences)
                for domain, experiences in self.domain_experiences.items()
            }

            # Learning efficiency metrics
            learning_efficiency = self._calculate_learning_efficiency()
            knowledge_retention = self._calculate_knowledge_retention()
            adaptation_speed = self._calculate_adaptation_speed()

            # Pattern analysis
            pattern_analysis = self._analyze_learning_patterns()

            # Performance trends
            performance_trends = self._analyze_performance_trends()

            return {
                'agent_id': self.agent_id,
                'timestamp': time.time(),
                'total_experiences': total_experiences,
                'domain_distribution': domain_distribution,
                'learning_efficiency': learning_efficiency,
                'knowledge_retention': knowledge_retention,
                'adaptation_speed': adaptation_speed,
                'current_strategy': self.learning_strategy.value,
                'pattern_analysis': pattern_analysis,
                'performance_trends': performance_trends,
                'learning_rates': {domain.value: rate for domain, rate in self.learning_rates.items()},
                'knowledge_base_size': len(self.consolidated_knowledge)
            }

    # Helper methods
    def _create_learning_experience(self, input_data: Any, output_data: Any,
                                  feedback: Dict[str, Any], domain: KnowledgeDomain,
                                  context: Dict[str, Any]) -> LearningExperience:
        """Create a learning experience from interaction data."""
        experience_id = hashlib.md5(
            f"{input_data}_{output_data}_{time.time()}".encode()
        ).hexdigest()[:12]

        # Calculate initial confidence based on feedback
        confidence_score = self._calculate_confidence_score(feedback)

        return LearningExperience(
            experience_id=experience_id,
            domain=domain,
            input_data=input_data,
            output_data=output_data,
            feedback=feedback,
            timestamp=time.time(),
            context=context or {},
            confidence_score=confidence_score
        )

    def _process_feedback(self, feedback: Dict[str, Any], experience: LearningExperience) -> Dict[str, float]:
        """Process and normalize feedback data."""
        processed = {}

        # Extract numerical feedback values
        for key, value in feedback.items():
            if isinstance(value, (int, float)):
                processed[key] = max(0.0, min(1.0, float(value)))
            elif isinstance(value, str):
                # Convert qualitative feedback to quantitative
                processed[key] = self._qualitative_to_quantitative(value)
            else:
                processed[key] = 0.5  # Neutral default

        # Apply feedback sensitivity
        for key in processed:
            processed[key] *= self.feedback_sensitivity

        return processed

    def _update_learning_parameters(self, experience: LearningExperience, feedback: Dict[str, float]):
        """Update learning parameters based on experience."""
        domain = experience.domain

        # Update learning rate based on performance
        performance_score = np.mean(list(feedback.values())) if feedback else 0.5

        if performance_score > 0.7:
            # Good performance - can increase learning rate
            self.learning_rates[domain] = min(
                self.learning_rates[domain] * 1.05, 0.5
            )
        elif performance_score < 0.3:
            # Poor performance - decrease learning rate for stability
            self.learning_rates[domain] = max(
                self.learning_rates[domain] * 0.95, 0.01
            )

        # Apply learning strategy
        if self.learning_strategy == LearningStrategy.RAPID_ACQUISITION:
            self.learning_rates[domain] *= 1.2
        elif self.learning_strategy == LearningStrategy.CONSERVATIVE_LEARNING:
            self.learning_rates[domain] *= 0.8
        elif self.learning_strategy == LearningStrategy.AGGRESSIVE_LEARNING:
            self.learning_rates[domain] *= 1.5

        # Update knowledge weights
        for key, value in feedback.items():
            weight_key = f"{domain.value}_{key}"
            self.knowledge_weights[weight_key] = (
                self.knowledge_weights[weight_key] * 0.9 +
                value * self.learning_rates[domain] * 0.1
            )

    def _store_experience(self, experience: LearningExperience):
        """Store learning experience in appropriate containers."""
        # Add to main database
        self.experience_database.append(experience)

        # Add to domain-specific storage
        self.domain_experiences[experience.domain].append(experience)

        # Add to experience replay buffer
        self.experience_replay_buffer.append(experience)

        # Check if it's a priority experience
        if experience.confidence_score > 0.8 or experience.feedback.get('importance', 0) > 0.7:
            self.priority_experiences.append(experience)

        # Maintain storage limits
        if len(self.experience_database) > self.max_experiences:
            self.experience_database = self.experience_database[-self.max_experiences:]

        # Limit domain experiences
        for domain in KnowledgeDomain:
            max_domain_experiences = self.max_experiences // len(KnowledgeDomain)
            if len(self.domain_experiences[domain]) > max_domain_experiences:
                self.domain_experiences[domain] = self.domain_experiences[domain][-max_domain_experiences:]

    def _recognize_patterns(self, experience: LearningExperience):
        """Recognize patterns in learning experiences."""
        # Extract features from experience
        features = self._extract_features(experience)

        # Check for existing patterns
        for pattern_id, pattern_data in self.learning_patterns.items():
            similarity = self._calculate_pattern_similarity(features, pattern_data['features'])
            if similarity > 0.7:
                # Strengthen existing pattern
                pattern_data['weight'] += 0.1
                pattern_data['frequency'] += 1
                experience.related_experiences.append(pattern_id)
                return

        # Create new pattern if strong enough
        if experience.confidence_score > 0.6:
            pattern_id = f"pattern_{len(self.learning_patterns)}"
            self.learning_patterns[pattern_id] = {
                'features': features,
                'weight': experience.confidence_score,
                'frequency': 1,
                'domain': experience.domain,
                'neurons': self._associate_neurons(features)
            }
            experience.related_experiences.append(pattern_id)

    def _update_neural_weights(self, experience: LearningExperience, feedback: Dict[str, float]):
        """Update neural network weights based on experience."""
        # Simplified neural weight update
        features = self._extract_features(experience)

        for feature_name, feature_value in features.items():
            neuron_id = f"{experience.domain.value}_{feature_name}"

            # Update weight based on feedback
            feedback_signal = np.mean(list(feedback.values())) if feedback else 0.5
            weight_change = self.learning_rates[experience.domain] * (feedback_signal - 0.5) * feature_value

            self.neural_weights[neuron_id]['weight'] += weight_change
            self.neural_weights[neuron_id]['last_update'] = time.time()

            # Record activation pattern
            self.activation_patterns[neuron_id].append({
                'timestamp': experience.timestamp,
                'activation': feature_value,
                'feedback': feedback_signal
            })

            # Limit activation history
            if len(self.activation_patterns[neuron_id]) > 100:
                self.activation_patterns[neuron_id] = self.activation_patterns[neuron_id][-100:]

    def _consolidate_knowledge(self):
        """Consolidate learned knowledge into more compact form."""
        # Group experiences by patterns
        pattern_groups = defaultdict(list)
        for experience in self.experience_database:
            for pattern_id in experience.related_experiences:
                pattern_groups[pattern_id].append(experience)

        # Consolidate each pattern group
        for pattern_id, experiences in pattern_groups.items():
            if len(experiences) >= 5:  # Only consolidate groups with sufficient experiences
                consolidated_knowledge = self._create_consolidated_knowledge(experiences)
                self.consolidated_knowledge[pattern_id] = consolidated_knowledge

        # Reduce individual experience retention scores after consolidation
        for experience in self.experience_database:
            if experience.related_experiences:
                experience.retention_score *= 0.8

    def _calculate_learning_metrics(self, experience: LearningExperience,
                                  feedback: Dict[str, float]) -> LearningMetrics:
        """Calculate learning metrics for an experience."""
        # Learning rate
        learning_rate = self.learning_rates[experience.domain]

        # Knowledge retention (based on recent performance)
        recent_experiences = [
            exp for exp in self.experience_database
            if exp.domain == experience.domain and
            time.time() - exp.timestamp < 3600  # Last hour
        ]

        if recent_experiences:
            knowledge_retention = np.mean([
                exp.confidence_score for exp in recent_experiences
            ])
        else:
            knowledge_retention = experience.confidence_score

        # Adaptation speed (how quickly the system is improving)
        adaptation_speed = self._calculate_adaptation_speed_for_domain(experience.domain)

        # Feedback utilization
        feedback_utilization = np.mean(list(feedback.values())) if feedback else 0.5

        # Pattern recognition
        pattern_recognition = min(len(experience.related_experiences) / 3.0, 1.0)

        # Transfer efficiency (how well knowledge transfers)
        transfer_efficiency = self._calculate_transfer_efficiency(experience)

        return LearningMetrics(
            learning_rate=learning_rate,
            knowledge_retention=knowledge_retention,
            adaptation_speed=adaptation_speed,
            feedback_utilization=feedback_utilization,
            pattern_recognition=pattern_recognition,
            transfer_efficiency=transfer_efficiency
        )

    def _update_performance_history(self, domain: KnowledgeDomain, metrics: LearningMetrics):
        """Update performance history for a domain."""
        self.performance_history[domain].append({
            'timestamp': time.time(),
            'metrics': metrics
        })

        # Limit history size
        if len(self.performance_history[domain]) > 1000:
            self.performance_history[domain] = self.performance_history[domain][-1000:]

    def _process_explicit_feedback(self, feedback_data: Dict[str, Any],
                                 target_domain: KnowledgeDomain = None) -> bool:
        """Process explicit user feedback."""
        domain = target_domain or KnowledgeDomain.CONVERSATION

        # Extract explicit ratings
        if 'rating' in feedback_data:
            rating = feedback_data['rating']
            self.knowledge_weights[f"{domain.value}_explicit_rating"] = rating

        # Extract specific corrections
        if 'corrections' in feedback_data:
            corrections = feedback_data['corrections']
            for correction in corrections:
                self.knowledge_weights[f"{domain.value}_correction_{correction}"] = 0.8

        return True

    def _process_implicit_feedback(self, feedback_data: Dict[str, Any],
                                 target_domain: KnowledgeDomain = None) -> bool:
        """Process implicit feedback from user behavior."""
        domain = target_domain or KnowledgeDomain.CONVERSATION

        # Extract engagement metrics
        if 'engagement_time' in feedback_data:
            engagement = feedback_data['engagement_time']
            normalized_engagement = min(engagement / 300.0, 1.0)  # 5 minutes max
            self.knowledge_weights[f"{domain.value}_engagement"] = normalized_engagement

        # Extract follow-up questions (indicates interest)
        if 'follow_up_questions' in feedback_data:
            follow_ups = feedback_data['follow_up_questions']
            self.knowledge_weights[f"{domain.value}_interest"] = min(follow_ups / 5.0, 1.0)

        return True

    def _process_corrective_feedback(self, feedback_data: Dict[str, Any],
                                   target_domain: KnowledgeDomain = None) -> bool:
        """Process corrective feedback."""
        domain = target_domain or KnowledgeDomain.CONVERSATION

        if 'error_type' in feedback_data:
            error_type = feedback_data['error_type']
            self.knowledge_weights[f"{domain.value}_avoid_{error_type}"] = 0.9

        if 'correction' in feedback_data:
            correction = feedback_data['correction']
            self.knowledge_weights[f"{domain.value}_prefer_{correction}"] = 0.8

        return True

    def _process_affirmative_feedback(self, feedback_data: Dict[str, Any],
                                    target_domain: KnowledgeDomain = None) -> bool:
        """Process positive/affirmative feedback."""
        domain = target_domain or KnowledgeDomain.CONVERSATION

        if 'positive_aspect' in feedback_data:
            aspect = feedback_data['positive_aspect']
            self.knowledge_weights[f"{domain.value}_strength_{aspect}"] = 0.9

        # Increase learning momentum for positive feedback
        self.learning_momentum[domain] += 0.1

        return True

    def _process_constructive_feedback(self, feedback_data: Dict[str, Any],
                                     target_domain: KnowledgeDomain = None) -> bool:
        """Process constructive improvement suggestions."""
        domain = target_domain or KnowledgeDomain.CONVERSATION

        if 'suggestion' in feedback_data:
            suggestion = feedback_data['suggestion']
            self.knowledge_weights[f"{domain.value}_suggestion_{suggestion}"] = 0.7

        if 'improvement_area' in feedback_data:
            area = feedback_data['improvement_area']
            self.learning_rates[domain] *= 1.1  # Increase learning rate for improvement areas

        return True

    def _update_adaptation_history(self, feedback_type: FeedbackType,
                                 feedback_data: Dict[str, Any],
                                 target_domain: KnowledgeDomain):
        """Update adaptation history."""
        adaptation_record = {
            'timestamp': time.time(),
            'feedback_type': feedback_type.value,
            'domain': target_domain.value if target_domain else 'general',
            'data_summary': {k: str(v)[:50] for k, v in feedback_data.items()}
        }

        self.adaptation_history.append(adaptation_record)

        # Limit history size
        if len(self.adaptation_history) > 1000:
            self.adaptation_history = self.adaptation_history[-1000:]

    def _get_domain_knowledge_summary(self, domain: KnowledgeDomain) -> Dict[str, Any]:
        """Get knowledge summary for specific domain."""
        experiences = self.domain_experiences[domain]

        if not experiences:
            return {'message': f'No experiences in {domain.value} domain'}

        # Calculate domain-specific metrics
        recent_experiences = [
            exp for exp in experiences
            if time.time() - exp.timestamp < 86400  # Last 24 hours
        ]

        confidence_scores = [exp.confidence_score for exp in experiences]
        retention_scores = [exp.retention_score for exp in experiences]

        return {
            'domain': domain.value,
            'total_experiences': len(experiences),
            'recent_experiences': len(recent_experiences),
            'average_confidence': np.mean(confidence_scores) if confidence_scores else 0,
            'average_retention': np.mean(retention_scores) if retention_scores else 0,
            'learning_rate': self.learning_rates[domain],
            'learning_momentum': self.learning_momentum[domain],
            'dominant_patterns': self._get_dominant_patterns(domain),
            'knowledge_weight_summary': self._get_domain_weight_summary(domain)
        }

    def _get_overall_knowledge_summary(self) -> Dict[str, Any]:
        """Get overall knowledge summary across all domains."""
        return {
            'total_experiences': len(self.experience_database),
            'domain_breakdown': {
                domain.value: len(experiences)
                for domain, experiences in self.domain_experiences.items()
            },
            'consolidated_knowledge_units': len(self.consolidated_knowledge),
            'recognized_patterns': len(self.learning_patterns),
            'average_learning_rate': np.mean(list(self.learning_rates.values())),
            'total_adaptations': len(self.adaptation_history),
            'priority_experiences': len(self.priority_experiences)
        }

    def _aggregate_learning_metrics(self, metrics_list: List[LearningMetrics]) -> LearningMetrics:
        """Aggregate learning metrics from multiple experiences."""
        if not metrics_list:
            return LearningMetrics(0, 0, 0, 0, 0, 0)

        return LearningMetrics(
            learning_rate=np.mean([m.learning_rate for m in metrics_list]),
            knowledge_retention=np.mean([m.knowledge_retention for m in metrics_list]),
            adaptation_speed=np.mean([m.adaptation_speed for m in metrics_list]),
            feedback_utilization=np.mean([m.feedback_utilization for m in metrics_list]),
            pattern_recognition=np.mean([m.pattern_recognition for m in metrics_list]),
            transfer_efficiency=np.mean([m.transfer_efficiency for m in metrics_list])
        )

    def _batch_consolidation(self):
        """Perform batch knowledge consolidation."""
        # Group similar experiences
        experience_groups = self._group_similar_experiences()

        # Consolidate each group
        for group_id, experiences in experience_groups.items():
            if len(experiences) >= 3:
                consolidated = self._create_consolidated_knowledge(experiences)
                self.consolidated_knowledge[f"batch_{group_id}"] = consolidated

    # Additional helper methods would be implemented here
    def _calculate_confidence_score(self, feedback: Dict[str, Any]) -> float:
        """Calculate confidence score from feedback."""
        if not feedback:
            return 0.5

        scores = []
        for key, value in feedback.items():
            if isinstance(value, (int, float)):
                scores.append(max(0.0, min(1.0, float(value))))
            elif isinstance(value, str):
                scores.append(self._qualitative_to_quantitative(value))

        return np.mean(scores) if scores else 0.5

    def _qualitative_to_quantitative(self, qualitative: str) -> float:
        """Convert qualitative feedback to quantitative score."""
        positive_words = ['good', 'great', 'excellent', 'helpful', 'useful', 'perfect']
        negative_words = ['bad', 'poor', 'unhelpful', 'wrong', 'incorrect', 'confusing']

        qualitative_lower = qualitative.lower()
        positive_count = sum(1 for word in positive_words if word in qualitative_lower)
        negative_count = sum(1 for word in negative_words if word in qualitative_lower)

        if positive_count > negative_count:
            return 0.5 + (positive_count - negative_count) * 0.1
        elif negative_count > positive_count:
            return 0.5 - (negative_count - positive_count) * 0.1
        else:
            return 0.5

    def _extract_features(self, experience: LearningExperience) -> Dict[str, float]:
        """Extract features from learning experience."""
        features = {}

        # Input-based features
        if isinstance(experience.input_data, str):
            text_length = len(experience.input_data.split())
            features['input_length'] = min(text_length / 100.0, 1.0)

        # Feedback-based features
        for key, value in experience.feedback.items():
            if isinstance(value, (int, float)):
                features[f"feedback_{key}"] = value

        # Context-based features
        if experience.context:
            features['context_complexity'] = min(len(experience.context) / 10.0, 1.0)

        return features

    def _calculate_pattern_similarity(self, features1: Dict[str, float],
                                   features2: Dict[str, float]) -> float:
        """Calculate similarity between two feature sets."""
        common_features = set(features1.keys()) & set(features2.keys())

        if not common_features:
            return 0.0

        similarities = []
        for feature in common_features:
            similarities.append(1 - abs(features1[feature] - features2[feature]))

        return np.mean(similarities)

    def _associate_neurons(self, features: Dict[str, float]) -> List[str]:
        """Associate features with neural representations."""
        neurons = []
        for feature_name in features.keys():
            neuron_id = f"neuron_{hash(feature_name) % 1000}"
            neurons.append(neuron_id)
        return neurons

    def _create_consolidated_knowledge(self, experiences: List[LearningExperience]) -> Dict[str, Any]:
        """Create consolidated knowledge from experience group."""
        return {
            'experiences_count': len(experiences),
            'domain': experiences[0].domain.value,
            'average_confidence': np.mean([exp.confidence_score for exp in experiences]),
            'creation_time': time.time(),
            'key_features': self._extract_group_features(experiences),
            'common_patterns': self._find_common_patterns(experiences)
        }

    def _calculate_adaptation_speed_for_domain(self, domain: KnowledgeDomain) -> float:
        """Calculate adaptation speed for a specific domain."""
        history = self.performance_history.get(domain, [])
        if len(history) < 2:
            return 0.1

        recent = history[-5:]
        early = history[:5]

        recent_avg = np.mean([m['metrics'].knowledge_retention for m in recent])
        early_avg = np.mean([m['metrics'].knowledge_retention for m in early])

        adaptation_speed = (recent_avg - early_avg) / len(recent)
        return max(0.0, min(adaptation_speed, 1.0))

    def _calculate_transfer_efficiency(self, experience: LearningExperience) -> float:
        """Calculate how well knowledge transfers for this experience."""
        # Simplified transfer efficiency calculation
        related_patterns = len(experience.related_experiences)
        return min(related_patterns / 5.0, 1.0)

    def _calculate_learning_efficiency(self) -> float:
        """Calculate overall learning efficiency."""
        if not self.experience_database:
            return 0.0

        # Calculate improvement over time
        recent_experiences = self.experience_database[-100:]
        early_experiences = self.experience_database[:100]

        recent_avg = np.mean([exp.confidence_score for exp in recent_experiences])
        early_avg = np.mean([exp.confidence_score for exp in early_experiences])

        efficiency = (recent_avg - early_avg) / max(early_avg, 0.1)
        return max(0.0, min(efficiency, 1.0))

    def _calculate_knowledge_retention(self) -> float:
        """Calculate overall knowledge retention."""
        if not self.experience_database:
            return 0.0

        retention_scores = [exp.retention_score for exp in self.experience_database]
        return np.mean(retention_scores)

    def _calculate_adaptation_speed(self) -> float:
        """Calculate overall adaptation speed."""
        speeds = []
        for domain in KnowledgeDomain:
            speed = self._calculate_adaptation_speed_for_domain(domain)
            speeds.append(speed)

        return np.mean(speeds) if speeds else 0.0

    def _analyze_learning_patterns(self) -> Dict[str, Any]:
        """Analyze recognized learning patterns."""
        if not self.learning_patterns:
            return {'message': 'No patterns recognized yet'}

        pattern_analysis = {
            'total_patterns': len(self.learning_patterns),
            'high_weight_patterns': [],
            'domain_distribution': defaultdict(int)
        }

        for pattern_id, pattern_data in self.learning_patterns.items():
            if pattern_data['weight'] > 0.7:
                pattern_analysis['high_weight_patterns'].append({
                    'id': pattern_id,
                    'weight': pattern_data['weight'],
                    'frequency': pattern_data['frequency']
                })

            domain = pattern_data.get('domain', KnowledgeDomain.CONVERSATION)
            pattern_analysis['domain_distribution'][domain.value] += 1

        return pattern_analysis

    def _analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        trends = {}

        for domain in KnowledgeDomain:
            history = self.performance_history.get(domain, [])
            if len(history) >= 10:
                recent_scores = [m['metrics'].knowledge_retention for m in history[-10:]]
                early_scores = [m['metrics'].knowledge_retention for m in history[:10]]

                trend = np.mean(recent_scores) - np.mean(early_scores)
                trends[domain.value] = {
                    'trend': 'improving' if trend > 0.05 else 'declining' if trend < -0.05 else 'stable',
                    'magnitude': abs(trend)
                }

        return trends

    def _group_similar_experiences(self) -> Dict[int, List[LearningExperience]]:
        """Group similar experiences for batch consolidation."""
        # Simple grouping by domain and confidence
        groups = defaultdict(list)
        group_id = 0

        for domain in KnowledgeDomain:
            domain_experiences = self.domain_experiences[domain]

            # Group by confidence ranges
            confidence_ranges = [(0.0, 0.3), (0.3, 0.6), (0.6, 0.8), (0.8, 1.0)]

            for low, high in confidence_ranges:
                group_experiences = [
                    exp for exp in domain_experiences
                    if low <= exp.confidence_score < high
                ]

                if group_experiences:
                    groups[group_id] = group_experiences
                    group_id += 1

        return dict(groups)

    def _extract_group_features(self, experiences: List[LearningExperience]) -> Dict[str, float]:
        """Extract common features from experience group."""
        all_features = defaultdict(list)

        for exp in experiences:
            features = self._extract_features(exp)
            for key, value in features.items():
                all_features[key].append(value)

        # Calculate averages
        return {key: np.mean(values) for key, values in all_features.items()}

    def _find_common_patterns(self, experiences: List[LearningExperience]) -> List[str]:
        """Find common patterns across experiences."""
        pattern_counts = defaultdict(int)

        for exp in experiences:
            for pattern_id in exp.related_experiences:
                pattern_counts[pattern_id] += 1

        # Return patterns that appear in multiple experiences
        return [
            pattern_id for pattern_id, count in pattern_counts.items()
            if count >= len(experiences) * 0.3
        ]

    def _get_dominant_patterns(self, domain: KnowledgeDomain) -> List[Dict[str, Any]]:
        """Get dominant patterns for a domain."""
        domain_patterns = []

        for pattern_id, pattern_data in self.learning_patterns.items():
            if pattern_data.get('domain') == domain and pattern_data['weight'] > 0.5:
                domain_patterns.append({
                    'id': pattern_id,
                    'weight': pattern_data['weight'],
                    'frequency': pattern_data['frequency']
                })

        return sorted(domain_patterns, key=lambda x: x['weight'], reverse=True)[:5]

    def _get_domain_weight_summary(self, domain: KnowledgeDomain) -> Dict[str, float]:
        """Get weight summary for a domain."""
        domain_weights = {}

        for key, weight in self.knowledge_weights.items():
            if key.startswith(f"{domain.value}_"):
                clean_key = key.replace(f"{domain.value}_", "")
                domain_weights[clean_key] = weight

        return domain_weights

# Example usage and testing
if __name__ == "__main__":
    # Create learning accelerator
    accelerator = LearningAccelerator("test_agent_1")

    # Simulate learning from interaction
    input_data = "User asked about machine learning"
    output_data = "I explained machine learning concepts"
    feedback = {
        'accuracy': 0.8,
        'clarity': 0.7,
        'helpfulness': 0.9,
        'user_rating': 'good'
    }

    metrics = accelerator.learn_from_interaction(
        input_data, output_data, feedback,
        KnowledgeDomain.CONVERSATION
    )

    print(f"Learning Metrics:")
    print(f"  Learning Rate: {metrics.learning_rate:.3f}")
    print(f"  Knowledge Retention: {metrics.knowledge_retention:.3f}")
    print(f"  Adaptation Speed: {metrics.adaptation_speed:.3f}")
    print(f"  Feedback Utilization: {metrics.feedback_utilization:.3f}")

    # Get learning analytics
    analytics = accelerator.get_learning_analytics()
    print("\nLearning Analytics:", json.dumps(analytics, indent=2))