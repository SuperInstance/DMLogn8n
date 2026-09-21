"""
Adaptive User Interface System for DMLogn8n Platform
AI-driven interface personalization and optimization
"""

import asyncio
import json
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum
import logging

# Machine Learning imports
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

class InteractionType(Enum):
    CLICK = "click"
    HOVER = "hover"
    SCROLL = "scroll"
    TYPE = "type"
    SWIPE = "swipe"
    PINCH = "pinch"
    VOICE = "voice"
    GESTURE = "gesture"

class UserSkillLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class InterfaceComplexity(Enum):
    MINIMAL = "minimal"
    SIMPLE = "simple"
    STANDARD = "standard"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"

@dataclass
class UserInteraction:
    timestamp: datetime
    interaction_type: InteractionType
    element_id: str
    element_type: str
    position: Tuple[float, float]
    duration: float
    success: bool
    context: Dict[str, Any]
    user_id: str
    session_id: str

@dataclass
class UserPreference:
    user_id: str
    preferred_layout: str
    color_scheme: str
    font_size: int
    animation_speed: float
    density_preference: InterfaceComplexity
    interaction_patterns: Dict[str, float]
    accessibility_needs: List[str]
    device_usage: Dict[str, float]
    time_patterns: Dict[str, float]

@dataclass
class UIComponent:
    component_id: str
    component_type: str
    complexity_score: float
    importance_score: float
    usage_frequency: float
    user_satisfaction: float
    optimal_placement: Optional[str]
    adaptive_config: Dict[str, Any]

class AdaptiveUIEngine:
    """AI-driven adaptive user interface system"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # User data storage
        self.user_interactions: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.user_preferences: Dict[str, UserPreference] = {}
        self.ui_components: Dict[str, UIComponent] = {}

        # Machine learning models
        self.clustering_model = None
        self.scaler = StandardScaler()
        self.interface_models: Dict[str, Any] = {}

        # Real-time adaptation
        self.adaptation_threshold = 0.7
        self.learning_rate = 0.01
        self.adaptation_history: Dict[str, List[Dict]] = defaultdict(list)

        # Performance metrics
        self.performance_metrics = {
            'adaptation_accuracy': 0.0,
            'user_satisfaction': 0.0,
            'task_completion_rate': 0.0,
            'error_rate': 0.0
        }

        self._initialize_default_components()
        self._load_ml_models()

    def _initialize_default_components(self):
        """Initialize default UI components with adaptive capabilities"""
        default_components = [
            {
                'component_id': 'main_navigation',
                'component_type': 'navigation',
                'complexity_score': 0.3,
                'importance_score': 0.9,
                'usage_frequency': 1.0,
                'adaptive_config': {
                    'layout_options': ['horizontal', 'vertical', 'circular', 'minimal'],
                    'adaptive_visibility': True,
                    'quick_actions': True
                }
            },
            {
                'component_id': 'workflow_canvas',
                'component_type': 'workspace',
                'complexity_score': 0.8,
                'importance_score': 1.0,
                'usage_frequency': 0.9,
                'adaptive_config': {
                    'zoom_levels': [0.5, 0.75, 1.0, 1.25, 1.5],
                    'grid_options': ['none', 'dots', 'lines', 'both'],
                    'auto_arrange': True
                }
            },
            {
                'component_id': 'node_palette',
                'component_type': 'tools',
                'complexity_score': 0.6,
                'importance_score': 0.8,
                'usage_frequency': 0.7,
                'adaptive_config': {
                    'grouping_options': ['category', 'frequency', 'recent', 'custom'],
                    'search_threshold': 3,
                    'favorites_enabled': True
                }
            },
            {
                'component_id': 'properties_panel',
                'component_type': 'configuration',
                'complexity_score': 0.7,
                'importance_score': 0.7,
                'usage_frequency': 0.6,
                'adaptive_config': {
                    'layout_options': ['tabs', 'accordion', 'scrolling', 'modal'],
                    'group_by': 'category',
                    'advanced_mode_toggle': True
                }
            },
            {
                'component_id': 'help_system',
                'component_type': 'support',
                'complexity_score': 0.4,
                'importance_score': 0.6,
                'usage_frequency': 0.3,
                'adaptive_config': {
                    'context_sensitive': True,
                    'progressive_disclosure': True,
                    'media_types': ['text', 'video', 'interactive']
                }
            }
        ]

        for comp_data in default_components:
            component = UIComponent(
                user_satisfaction=0.5,
                optimal_placement=None,
                **comp_data
            )
            self.ui_components[component.component_id] = component

    def _load_ml_models(self):
        """Load or train machine learning models for UI adaptation"""
        try:
            # Initialize clustering model for user segmentation
            self.clustering_model = KMeans(n_clusters=5, random_state=42)
            self.logger.info("ML models initialized successfully")
        except Exception as e:
            self.logger.warning(f"Could not initialize ML models: {e}")

    async def track_interaction(self, interaction: UserInteraction) -> Dict[str, Any]:
        """Track user interaction and update adaptation models"""
        # Store interaction
        self.user_interactions[interaction.user_id].append(interaction)

        # Update component usage statistics
        if interaction.element_id in self.ui_components:
            component = self.ui_components[interaction.element_id]
            component.usage_frequency = self._update_usage_frequency(
                component.usage_frequency, interaction.success
            )
            component.user_satisfaction = self._update_satisfaction_score(
                component.user_satisfaction, interaction.success, interaction.duration
            )

        # Analyze interaction patterns
        patterns = await self._analyze_interaction_patterns(interaction.user_id)

        # Check if adaptation is needed
        adaptation_needed = await self._evaluate_adaptation_need(interaction.user_id)

        if adaptation_needed:
            adaptation_result = await self._adapt_interface(interaction.user_id)
            return {
                'interaction_tracked': True,
                'patterns_identified': patterns,
                'adaptation_applied': adaptation_result
            }

        return {
            'interaction_tracked': True,
            'patterns_identified': patterns,
            'adaptation_applied': None
        }

    def _update_usage_frequency(self, current_freq: float, success: bool) -> float:
        """Update component usage frequency based on interaction success"""
        if success:
            return min(1.0, current_freq + self.learning_rate)
        else:
            return max(0.0, current_freq - self.learning_rate * 0.5)

    def _update_satisfaction_score(self, current_sat: float, success: bool, duration: float) -> float:
        """Update user satisfaction score based on interaction outcome"""
        duration_factor = max(0.1, 1.0 / (1.0 + duration / 10.0))  # Normalize duration impact

        if success:
            new_sat = current_sat + (self.learning_rate * duration_factor)
        else:
            new_sat = current_sat - (self.learning_rate * 1.5)

        return max(0.0, min(1.0, new_sat))

    async def _analyze_interaction_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze user interaction patterns using machine learning"""
        interactions = list(self.user_interactions[user_id])

        if len(interactions) < 10:
            return {'status': 'insufficient_data'}

        # Extract features for pattern analysis
        features = []
        for interaction in interactions[-50:]:  # Analyze last 50 interactions
            feature_vector = [
                interaction.duration,
                float(interaction.success),
                interaction.position[0],
                interaction.position[1],
                len(interaction.context),
                time.mktime(interaction.timestamp.timetuple())
            ]
            features.append(feature_vector)

        if not features:
            return {'status': 'no_features'}

        # Perform clustering analysis
        try:
            features_scaled = self.scaler.fit_transform(features)
            clusters = self.clustering_model.fit_predict(features_scaled)

            # Analyze patterns
            pattern_analysis = {
                'interaction_velocity': self._calculate_interaction_velocity(interactions),
                'error_patterns': self._identify_error_patterns(interactions),
                'workflow_efficiency': self._calculate_workflow_efficiency(interactions),
                'preferred_components': self._get_preferred_components(interactions),
                'time_patterns': self._analyze_time_patterns(interactions),
                'skill_level': self._estimate_skill_level(interactions),
                'cluster_analysis': {
                    'num_clusters': len(set(clusters)),
                    'silhouette_score': silhouette_score(features_scaled, clusters) if len(set(clusters)) > 1 else 0
                }
            }

            return pattern_analysis

        except Exception as e:
            self.logger.error(f"Pattern analysis failed: {e}")
            return {'status': 'analysis_failed', 'error': str(e)}

    def _calculate_interaction_velocity(self, interactions: List[UserInteraction]) -> float:
        """Calculate average interaction velocity"""
        if len(interactions) < 2:
            return 0.0

        velocities = []
        for i in range(1, len(interactions)):
            time_diff = (interactions[i].timestamp - interactions[i-1].timestamp).total_seconds()
            if time_diff > 0:
                velocities.append(1.0 / time_diff)

        return np.mean(velocities) if velocities else 0.0

    def _identify_error_patterns(self, interactions: List[UserInteraction]) -> Dict[str, Any]:
        """Identify patterns in user errors"""
        error_interactions = [i for i in interactions if not i.success]

        if not error_interactions:
            return {'error_rate': 0.0, 'common_errors': []}

        error_rate = len(error_interactions) / len(interactions)

        # Find common error patterns
        error_types = defaultdict(int)
        for error in error_interactions:
            error_types[error.element_type] += 1

        common_errors = [
            {'element_type': elem_type, 'count': count}
            for elem_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        return {
            'error_rate': error_rate,
            'common_errors': common_errors,
            'total_errors': len(error_interactions)
        }

    def _calculate_workflow_efficiency(self, interactions: List[UserInteraction]) -> float:
        """Calculate workflow efficiency score"""
        if len(interactions) < 5:
            return 0.5

        successful_interactions = [i for i in interactions if i.success]
        success_rate = len(successful_interactions) / len(interactions)

        # Calculate average task completion time
        avg_duration = np.mean([i.duration for i in successful_interactions])

        # Normalize and combine metrics
        efficiency_score = (success_rate * 0.7) + (max(0, 1.0 - avg_duration / 30.0) * 0.3)

        return min(1.0, efficiency_score)

    def _get_preferred_components(self, interactions: List[UserInteraction]) -> List[str]:
        """Get most frequently used components"""
        component_usage = defaultdict(int)
        for interaction in interactions:
            if interaction.success:
                component_usage[interaction.element_id] += 1

        return [comp for comp, _ in sorted(component_usage.items(), key=lambda x: x[1], reverse=True)[:10]]

    def _analyze_time_patterns(self, interactions: List[UserInteraction]) -> Dict[str, Any]:
        """Analyze time-based usage patterns"""
        if not interactions:
            return {}

        # Extract hour patterns
        hours = [i.timestamp.hour for i in interactions]
        hour_distribution = {hour: hours.count(hour) / len(hours) for hour in range(24)}

        # Peak usage times
        peak_hours = sorted(hour_distribution.items(), key=lambda x: x[1], reverse=True)[:3]

        # Session patterns
        session_durations = self._calculate_session_durations(interactions)

        return {
            'hourly_distribution': hour_distribution,
            'peak_hours': peak_hours,
            'avg_session_duration': np.mean(session_durations) if session_durations else 0,
            'total_sessions': len(session_durations)
        }

    def _calculate_session_durations(self, interactions: List[UserInteraction]) -> List[float]:
        """Calculate individual session durations"""
        if not interactions:
            return []

        sessions = []
        current_session = [interactions[0]]

        for i in range(1, len(interactions)):
            time_diff = (interactions[i].timestamp - interactions[i-1].timestamp).total_seconds()

            if time_diff > 1800:  # 30 minutes break starts new session
                if len(current_session) > 1:
                    session_duration = (current_session[-1].timestamp - current_session[0].timestamp).total_seconds()
                    sessions.append(session_duration)
                current_session = [interactions[i]]
            else:
                current_session.append(interactions[i])

        # Add final session
        if len(current_session) > 1:
            session_duration = (current_session[-1].timestamp - current_session[0].timestamp).total_seconds()
            sessions.append(session_duration)

        return sessions

    def _estimate_skill_level(self, interactions: List[UserInteraction]) -> UserSkillLevel:
        """Estimate user skill level based on interaction patterns"""
        if len(interactions) < 10:
            return UserSkillLevel.BEGINNER

        # Calculate metrics
        success_rate = sum(1 for i in interactions if i.success) / len(interactions)
        avg_duration = np.mean([i.duration for i in interactions])
        interaction_velocity = self._calculate_interaction_velocity(interactions)
        workflow_efficiency = self._calculate_workflow_efficiency(interactions)

        # Unique components used
        unique_components = len(set(i.element_id for i in interactions))

        # Calculate skill score
        skill_score = (
            success_rate * 0.3 +
            min(1.0, workflow_efficiency) * 0.3 +
            min(1.0, interaction_velocity / 10.0) * 0.2 +
            min(1.0, unique_components / 20.0) * 0.2
        )

        if skill_score >= 0.8:
            return UserSkillLevel.EXPERT
        elif skill_score >= 0.6:
            return UserSkillLevel.ADVANCED
        elif skill_score >= 0.4:
            return UserSkillLevel.INTERMEDIATE
        else:
            return UserSkillLevel.BEGINNER

    async def _evaluate_adaptation_need(self, user_id: str) -> bool:
        """Evaluate if interface adaptation is needed"""
        interactions = list(self.user_interactions[user_id])

        if len(interactions) < 20:
            return False

        # Check recent performance
        recent_interactions = interactions[-20:]
        recent_success_rate = sum(1 for i in recent_interactions if i.success) / len(recent_interactions)

        # Check if user is struggling
        if recent_success_rate < 0.7:
            return True

        # Check satisfaction trends
        satisfaction_trend = self._calculate_satisfaction_trend(user_id)
        if satisfaction_trend < -0.1:  # Declining satisfaction
            return True

        # Check for efficiency improvements
        efficiency = self._calculate_workflow_efficiency(recent_interactions)
        if efficiency < 0.6:
            return True

        return False

    def _calculate_satisfaction_trend(self, user_id: str) -> float:
        """Calculate user satisfaction trend"""
        if user_id not in self.adaptation_history:
            return 0.0

        history = self.adaptation_history[user_id][-10:]  # Last 10 adaptations
        if len(history) < 2:
            return 0.0

        satisfaction_scores = [h.get('satisfaction_score', 0.5) for h in history]

        # Calculate linear trend
        x = np.arange(len(satisfaction_scores))
        slope = np.polyfit(x, satisfaction_scores, 1)[0]

        return slope

    async def _adapt_interface(self, user_id: str) -> Dict[str, Any]:
        """Perform interface adaptation based on user analysis"""
        # Analyze current user state
        patterns = await self._analyze_interaction_patterns(user_id)
        skill_level = patterns.get('skill_level', UserSkillLevel.BEGINNER)

        # Generate adaptation recommendations
        adaptations = []

        # Layout adaptations
        layout_adaptations = await self._generate_layout_adaptations(user_id, skill_level)
        adaptations.extend(layout_adaptations)

        # Component adaptations
        component_adaptations = await self._generate_component_adaptations(user_id, patterns)
        adaptations.extend(component_adaptations)

        # Complexity adaptations
        complexity_adaptations = await self._generate_complexity_adaptations(user_id, skill_level)
        adaptations.extend(complexity_adaptations)

        # Record adaptation
        adaptation_record = {
            'timestamp': datetime.now(),
            'user_id': user_id,
            'skill_level': skill_level.value,
            'adaptations': adaptations,
            'patterns': patterns
        }

        self.adaptation_history[user_id].append(adaptation_record)

        return {
            'adaptation_id': f"adapt_{int(time.time())}_{user_id}",
            'adaptations': adaptations,
            'skill_level': skill_level.value,
            'confidence': self._calculate_adaptation_confidence(patterns)
        }

    async def _generate_layout_adaptations(self, user_id: str, skill_level: UserSkillLevel) -> List[Dict]:
        """Generate layout adaptation recommendations"""
        adaptations = []

        # Analyze preferred components
        interactions = list(self.user_interactions[user_id])
        preferred_components = self._get_preferred_components(interactions)

        if skill_level == UserSkillLevel.BEGINNER:
            adaptations.append({
                'type': 'layout_simplification',
                'action': 'simplify_layout',
                'description': 'Simplify layout to focus on essential components',
                'changes': {
                    'hide_advanced_panels': True,
                    'prioritize_help_components': True,
                    'increase_button_sizes': True
                }
            })

        elif skill_level in [UserSkillLevel.ADVANCED, UserSkillLevel.EXPERT]:
            adaptations.append({
                'type': 'layout_optimization',
                'action': 'optimize_layout',
                'description': 'Optimize layout for power users',
                'changes': {
                    'enable_quick_access': True,
                    'add_keyboard_shortcuts': True,
                    'customize_workspace': True
                }
            })

        return adaptations

    async def _generate_component_adaptations(self, user_id: str, patterns: Dict[str, Any]) -> List[Dict]:
        """Generate component-specific adaptations"""
        adaptations = []

        error_patterns = patterns.get('error_patterns', {})
        if error_patterns.get('error_rate', 0) > 0.3:
            common_errors = error_patterns.get('common_errors', [])
            for error in common_errors[:3]:
                adaptations.append({
                    'type': 'component_enhancement',
                    'action': 'enhance_component',
                    'description': f'Enhance {error["element_type"]} to reduce errors',
                    'changes': {
                        'component_id': error["element_type"],
                        'add_guidance': True,
                        'increase_visual_cues': True,
                        'simplify_interaction': True
                    }
                })

        # Preferred components optimization
        preferred_components = patterns.get('preferred_components', [])
        for component_id in preferred_components[:5]:
            if component_id in self.ui_components:
                adaptations.append({
                    'type': 'component_optimization',
                    'action': 'optimize_preferred_component',
                    'description': f'Optimize preferred component: {component_id}',
                    'changes': {
                        'component_id': component_id,
                        'enhance_accessibility': True,
                        'add_quick_actions': True,
                        'improve_performance': True
                    }
                })

        return adaptations

    async def _generate_complexity_adaptations(self, user_id: str, skill_level: UserSkillLevel) -> List[Dict]:
        """Generate complexity level adaptations"""
        adaptations = []

        complexity_mapping = {
            UserSkillLevel.BEGINNER: InterfaceComplexity.SIMPLE,
            UserSkillLevel.INTERMEDIATE: InterfaceComplexity.STANDARD,
            UserSkillLevel.ADVANCED: InterfaceComplexity.DETAILED,
            UserSkillLevel.EXPERT: InterfaceComplexity.COMPREHENSIVE
        }

        target_complexity = complexity_mapping[skill_level]

        adaptations.append({
            'type': 'complexity_adjustment',
            'action': 'adjust_complexity',
            'description': f'Adjust interface complexity to {target_complexity.value}',
            'changes': {
                'target_complexity': target_complexity.value,
                'progressive_disclosure': skill_level != UserSkillLevel.EXPERT,
                'advanced_features_visible': skill_level in [UserSkillLevel.ADVANCED, UserSkillLevel.EXPERT]
            }
        })

        return adaptations

    def _calculate_adaptation_confidence(self, patterns: Dict[str, Any]) -> float:
        """Calculate confidence score for adaptation recommendations"""
        factors = []

        # Data quality factor
        if 'cluster_analysis' in patterns:
            silhouette_score = patterns['cluster_analysis'].get('silhouette_score', 0)
            factors.append(max(0, silhouette_score))

        # Workflow efficiency factor
        efficiency = patterns.get('workflow_efficiency', 0.5)
        factors.append(1.0 - abs(efficiency - 0.7))  # Optimal around 0.7

        # Error rate factor
        error_rate = patterns.get('error_patterns', {}).get('error_rate', 0)
        factors.append(min(1.0, error_rate * 2))  # Higher error rate increases confidence

        return np.mean(factors) if factors else 0.5

    async def get_personalized_interface(self, user_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get personalized interface configuration for user"""
        # Get or create user preference
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = await self._create_default_preference(user_id)

        preference = self.user_preferences[user_id]

        # Analyze current patterns
        patterns = await self._analyze_interaction_patterns(user_id)

        # Generate interface configuration
        interface_config = {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'layout': {
                'type': preference.preferred_layout,
                'density': preference.density_preference.value,
                'responsive': True
            },
            'theme': {
                'color_scheme': preference.color_scheme,
                'font_size': preference.font_size,
                'animation_speed': preference.animation_speed
            },
            'components': {},
            'accessibility': {
                'needs_met': preference.accessibility_needs,
                'screen_reader_optimized': True,
                'keyboard_navigation': True,
                'high_contrast_available': True
            },
            'adaptations': {
                'skill_level': patterns.get('skill_level', UserSkillLevel.BEGINNER).value,
                'personalization_score': self._calculate_personalization_score(user_id),
                'last_adaptation': self._get_last_adaptation(user_id)
            }
        }

        # Add component-specific configurations
        for component_id, component in self.ui_components.items():
            interface_config['components'][component_id] = {
                'visible': self._should_show_component(user_id, component_id),
                'placement': component.optimal_placement or 'default',
                'config': component.adaptive_config,
                'personalization': {
                    'usage_frequency': component.usage_frequency,
                    'satisfaction_score': component.user_satisfaction
                }
            }

        return interface_config

    async def _create_default_preference(self, user_id: str) -> UserPreference:
        """Create default user preference profile"""
        return UserPreference(
            user_id=user_id,
            preferred_layout='standard',
            color_scheme='light',
            font_size=14,
            animation_speed=1.0,
            density_preference=InterfaceComplexity.STANDARD,
            interaction_patterns={},
            accessibility_needs=[],
            device_usage={'desktop': 1.0},
            time_patterns={'morning': 0.3, 'afternoon': 0.5, 'evening': 0.2}
        )

    def _calculate_personalization_score(self, user_id: str) -> float:
        """Calculate how personalized the interface is for a user"""
        interactions = list(self.user_interactions[user_id])

        if len(interactions) < 10:
            return 0.0

        # Factors for personalization score
        data_volume = min(1.0, len(interactions) / 100.0)
        adaptation_frequency = min(1.0, len(self.adaptation_history.get(user_id, [])) / 10.0)
        satisfaction_score = np.mean([comp.user_satisfaction for comp in self.ui_components.values()])

        personalization_score = (data_volume * 0.4 + adaptation_frequency * 0.3 + satisfaction_score * 0.3)

        return min(1.0, personalization_score)

    def _get_last_adaptation(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the last adaptation applied to user"""
        if user_id in self.adaptation_history and self.adaptation_history[user_id]:
            return self.adaptation_history[user_id][-1]
        return None

    def _should_show_component(self, user_id: str, component_id: str) -> bool:
        """Determine if component should be shown to user"""
        if component_id not in self.ui_components:
            return False

        component = self.ui_components[component_id]

        # Hide components with very low usage and satisfaction
        if component.usage_frequency < 0.1 and component.user_satisfaction < 0.3:
            return False

        # Always show essential components
        if component.importance_score > 0.8:
            return True

        # Show based on user skill level
        if component.complexity_score > 0.7:
            skill_level = self._estimate_skill_level(list(self.user_interactions[user_id]))
            return skill_level in [UserSkillLevel.ADVANCED, UserSkillLevel.EXPERT]

        return True

    async def update_preference(self, user_id: str, preference_updates: Dict[str, Any]) -> bool:
        """Update user preferences"""
        try:
            if user_id not in self.user_preferences:
                self.user_preferences[user_id] = await self._create_default_preference(user_id)

            current_pref = self.user_preferences[user_id]

            # Apply updates
            for key, value in preference_updates.items():
                if hasattr(current_pref, key):
                    setattr(current_pref, key, value)

            self.logger.info(f"Updated preferences for user {user_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update preferences for user {user_id}: {e}")
            return False

    async def get_ui_analytics(self, user_id: str = None, time_range: int = 7) -> Dict[str, Any]:
        """Get UI/UX analytics and insights"""
        cutoff_date = datetime.now() - timedelta(days=time_range)

        # Filter interactions by time range
        filtered_interactions = []
        for uid, interactions in self.user_interactions.items():
            if user_id and uid != user_id:
                continue

            for interaction in interactions:
                if interaction.timestamp >= cutoff_date:
                    filtered_interactions.append(interaction)

        if not filtered_interactions:
            return {'status': 'no_data', 'message': 'No interactions found in time range'}

        # Calculate analytics
        analytics = {
            'time_range_days': time_range,
            'total_interactions': len(filtered_interactions),
            'unique_users': len(set(i.user_id for i in filtered_interactions)),
            'success_rate': sum(1 for i in filtered_interactions if i.success) / len(filtered_interactions),
            'avg_interaction_duration': np.mean([i.duration for i in filtered_interactions]),
            'component_usage': self._analyze_component_usage(filtered_interactions),
            'error_analysis': self._analyze_errors(filtered_interactions),
            'skill_distribution': self._analyze_skill_distribution(filtered_interactions),
            'adaptation_effectiveness': self._analyze_adaptation_effectiveness(filtered_interactions),
            'performance_metrics': self.performance_metrics
        }

        return analytics

    def _analyze_component_usage(self, interactions: List[UserInteraction]) -> Dict[str, Any]:
        """Analyze component usage patterns"""
        component_stats = defaultdict(lambda: {'count': 0, 'success': 0, 'duration': []})

        for interaction in interactions:
            comp_id = interaction.element_id
            component_stats[comp_id]['count'] += 1
            if interaction.success:
                component_stats[comp_id]['success'] += 1
            component_stats[comp_id]['duration'].append(interaction.duration)

        # Calculate metrics for each component
        usage_analysis = {}
        for comp_id, stats in component_stats.items():
            usage_analysis[comp_id] = {
                'usage_count': stats['count'],
                'success_rate': stats['success'] / stats['count'] if stats['count'] > 0 else 0,
                'avg_duration': np.mean(stats['duration']) if stats['duration'] else 0,
                'satisfaction_score': self.ui_components.get(comp_id, UIComponent('', '', 0, 0, 0, 0.5, None, {})).user_satisfaction
            }

        return usage_analysis

    def _analyze_errors(self, interactions: List[UserInteraction]) -> Dict[str, Any]:
        """Analyze error patterns"""
        errors = [i for i in interactions if not i.success]

        if not errors:
            return {'total_errors': 0, 'error_rate': 0.0}

        error_types = defaultdict(int)
        error_components = defaultdict(int)

        for error in errors:
            error_types[error.element_type] += 1
            error_components[error.element_id] += 1

        return {
            'total_errors': len(errors),
            'error_rate': len(errors) / len(interactions),
            'error_types': dict(error_types),
            'error_components': dict(error_components),
            'most_problematic': max(error_components.items(), key=lambda x: x[1]) if error_components else None
        }

    def _analyze_skill_distribution(self, interactions: List[UserInteraction]) -> Dict[str, float]:
        """Analyze skill level distribution across users"""
        user_skill_levels = defaultdict(list)

        for interaction in interactions:
            user_interactions = [i for i in interactions if i.user_id == interaction.user_id]
            if len(user_interactions) >= 10:
                skill_level = self._estimate_skill_level(user_interactions)
                user_skill_levels[skill_level.value].append(interaction.user_id)

        # Calculate distribution
        total_users = sum(len(users) for users in user_skill_levels.values())
        if total_users == 0:
            return {}

        distribution = {}
        for skill_level, users in user_skill_levels.items():
            distribution[skill_level] = len(users) / total_users

        return distribution

    def _analyze_adaptation_effectiveness(self, interactions: List[UserInteraction]) -> Dict[str, Any]:
        """Analyze effectiveness of interface adaptations"""
        adaptations_applied = []

        for user_id in set(i.user_id for i in interactions):
            if user_id in self.adaptation_history:
                adaptations_applied.extend(self.adaptation_history[user_id])

        if not adaptations_applied:
            return {'status': 'no_adaptations'}

        # Calculate adaptation effectiveness
        effectiveness_scores = []
        for adaptation in adaptations_applied:
            # Check if user satisfaction improved after adaptation
            adaptation_time = adaptation['timestamp']
            post_adaptation_interactions = [
                i for i in interactions
                if i.user_id == adaptation['user_id'] and i.timestamp > adaptation_time
            ]

            if len(post_adaptation_interactions) >= 5:
                post_success_rate = sum(1 for i in post_adaptation_interactions if i.success) / len(post_adaptation_interactions)
                effectiveness_scores.append(post_success_rate)

        return {
            'total_adaptations': len(adaptations_applied),
            'avg_effectiveness': np.mean(effectiveness_scores) if effectiveness_scores else 0.0,
            'adaptation_types': list(set(a.get('adaptations', [{}])[0].get('type', 'unknown') for a in adaptations_applied))
        }

    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export user data for privacy and analysis"""
        return {
            'user_id': user_id,
            'interactions': [asdict(i) for i in self.user_interactions[user_id]],
            'preferences': asdict(self.user_preferences.get(user_id, UserPreference('', '', '', 0, 0, InterfaceComplexity.STANDARD, {}, [], {}, {}))),
            'adaptation_history': self.adaptation_history.get(user_id, []),
            'export_timestamp': datetime.now().isoformat()
        }

    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old interaction data"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        for user_id in self.user_interactions:
            # Filter old interactions
            filtered_interactions = deque(
                (i for i in self.user_interactions[user_id] if i.timestamp >= cutoff_date),
                maxlen=1000
            )
            self.user_interactions[user_id] = filtered_interactions

        # Clean up old adaptation history
        for user_id in self.adaptation_history:
            self.adaptation_history[user_id] = [
                a for a in self.adaptation_history[user_id]
                if a['timestamp'] >= cutoff_date
            ]

        self.logger.info(f"Cleaned up data older than {days_to_keep} days")


# Helper functions for integration
async def create_adaptive_ui_system(config: Dict[str, Any] = None) -> AdaptiveUIEngine:
    """Create and initialize adaptive UI system"""
    return AdaptiveUIEngine(config)

# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize adaptive UI system
        adaptive_ui = await create_adaptive_ui_system()

        # Simulate user interaction
        interaction = UserInteraction(
            timestamp=datetime.now(),
            interaction_type=InteractionType.CLICK,
            element_id="main_navigation",
            element_type="navigation",
            position=(100, 50),
            duration=1.2,
            success=True,
            context={"page": "workflow_editor"},
            user_id="user123",
            session_id="session456"
        )

        # Track interaction
        result = await adaptive_ui.track_interaction(interaction)
        print("Interaction tracked:", result)

        # Get personalized interface
        interface_config = await adaptive_ui.get_personalized_interface("user123")
        print("Personalized interface:", interface_config)

        # Get analytics
        analytics = await adaptive_ui.get_ui_analytics()
        print("UI Analytics:", analytics)

    asyncio.run(main())