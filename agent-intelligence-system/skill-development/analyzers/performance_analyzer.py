"""
Performance Analyzer for skill effectiveness in DMlogn8n

This module provides comprehensive analysis of skill performance,
effectiveness metrics, and improvement recommendations.
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import statistics
import math

from ..core.skill import Skill, SkillCategory, MasteryLevel, SkillUsageRecord
from ..core.skill_progression import SkillProgression


class PerformanceTier(Enum):
    """Performance tier classifications"""
    EXCELLENT = auto()  # 90-100%
    GOOD = auto()       # 75-89%
    AVERAGE = auto()    # 50-74%
    BELOW_AVERAGE = auto()  # 25-49%
    POOR = auto()       # 0-24%

    @classmethod
    def from_percentage(cls, percentage: float) -> 'PerformanceTier':
        """Get performance tier from percentage"""
        if percentage >= 90:
            return cls.EXCELLENT
        elif percentage >= 75:
            return cls.GOOD
        elif percentage >= 50:
            return cls.AVERAGE
        elif percentage >= 25:
            return cls.BELOW_AVERAGE
        else:
            return cls.POOR


class TrendDirection(Enum):
    """Trend direction for performance over time"""
    IMPROVING = auto()
    STABLE = auto()
    DECLINING = auto()
    INSUFFICIENT_DATA = auto()


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics for a skill"""
    skill_name: str
    total_uses: int
    successful_uses: int
    critical_successes: int
    success_rate: float
    critical_success_rate: float
    average_difficulty: float
    average_xp_per_use: float
    total_xp_earned: int
    mastery_level: MasteryLevel
    performance_tier: PerformanceTier
    trend_direction: TrendDirection
    last_used: Optional[datetime]
    usage_frequency: float  # Uses per day
    effectiveness_score: float  # 0-100 overall effectiveness


@dataclass
class SkillEffectiveness:
    """Detailed effectiveness analysis for a skill"""
    skill_name: str
    metrics: PerformanceMetrics
    strengths: List[str]
    weaknesses: List[str]
    improvement_areas: List[str]
    recommended_focus: List[str]
    synergy_potential: Dict[str, float]
    contextual_performance: Dict[str, float]  # Performance in different contexts
    development_recommendations: List[Dict[str, Any]]


@dataclass
class ComparativeAnalysis:
    """Comparative analysis between skills or agents"""
    comparison_type: str  # 'skill_vs_skill', 'agent_vs_agent', 'category_vs_category'
    subject_a: str
    subject_b: str
    metrics_comparison: Dict[str, Tuple[float, float]]
    winner: str
    analysis_summary: str
    recommendations: List[str]


class PerformanceAnalyzer:
    """
    Advanced performance analysis system for skills

    This class provides comprehensive analysis of skill performance,
    including trends, effectiveness metrics, and improvement recommendations.
    """

    def __init__(self):
        self.analysis_cache: Dict[str, Tuple[PerformanceMetrics, datetime]] = {}
        self.cache_duration = timedelta(minutes=5)  # Cache analysis for 5 minutes
        self.historical_data: Dict[str, List[PerformanceMetrics]] = {}

    def analyze_skill_performance(
        self,
        skill: Skill,
        progression: Optional[SkillProgression] = None,
        analysis_period_days: int = 30
    ) -> PerformanceMetrics:
        """
        Analyze performance of a single skill

        Args:
            skill: The skill to analyze
            progression: Skill progression data (optional)
            analysis_period_days: Number of days to consider for analysis

        Returns:
            PerformanceMetrics object with comprehensive analysis
        """
        # Check cache first
        cache_key = f"{skill.name}_{analysis_period_days}"
        if cache_key in self.analysis_cache:
            cached_metrics, cached_time = self.analysis_cache[cache_key]
            if datetime.now() - cached_time < self.cache_duration:
                return cached_metrics

        # Calculate basic metrics
        total_uses = skill.total_uses
        successful_uses = skill.successful_uses
        critical_successes = skill.critical_successes

        success_rate = (successful_uses / total_uses * 100.0) if total_uses > 0 else 0.0
        critical_success_rate = (critical_successes / total_uses * 100.0) if total_uses > 0 else 0.0

        # Calculate average difficulty and XP
        if skill.usage_history:
            recent_history = self._get_recent_usage(skill, analysis_period_days)
            average_difficulty = statistics.mean(use.difficulty for use in recent_history)
            average_xp_per_use = statistics.mean(use.xp_gained + use.bonus_xp for use in recent_history)
        else:
            average_difficulty = 0.0
            average_xp_per_use = 0.0

        # Calculate usage frequency
        usage_frequency = self._calculate_usage_frequency(skill, analysis_period_days)

        # Calculate effectiveness score
        effectiveness_score = self._calculate_effectiveness_score(
            success_rate, critical_success_rate, average_difficulty, usage_frequency
        )

        # Determine performance tier
        performance_tier = PerformanceTier.from_percentage(effectiveness_score)

        # Analyze trend
        trend_direction = self._analyze_trend(skill, analysis_period_days)

        # Create metrics object
        metrics = PerformanceMetrics(
            skill_name=skill.name,
            total_uses=total_uses,
            successful_uses=successful_uses,
            critical_successes=critical_successes,
            success_rate=success_rate,
            critical_success_rate=critical_success_rate,
            average_difficulty=average_difficulty,
            average_xp_per_use=average_xp_per_use,
            total_xp_earned=skill.total_xp,
            mastery_level=skill.current_level,
            performance_tier=performance_tier,
            trend_direction=trend_direction,
            last_used=skill.last_used,
            usage_frequency=usage_frequency,
            effectiveness_score=effectiveness_score
        )

        # Cache the results
        self.analysis_cache[cache_key] = (metrics, datetime.now())

        # Store in historical data
        if skill.name not in self.historical_data:
            self.historical_data[skill.name] = []
        self.historical_data[skill.name].append(metrics)

        # Keep only last 100 entries per skill
        if len(self.historical_data[skill.name]) > 100:
            self.historical_data[skill.name] = self.historical_data[skill.name][-100:]

        return metrics

    def analyze_skill_effectiveness(
        self,
        skill: Skill,
        progression: SkillProgression,
        analysis_period_days: int = 30
    ) -> SkillEffectiveness:
        """
        Comprehensive effectiveness analysis for a skill

        Args:
            skill: The skill to analyze
            progression: Skill progression data
            analysis_period_days: Number of days to consider

        Returns:
            SkillEffectiveness object with detailed analysis
        """
        metrics = self.analyze_skill_performance(skill, progression, analysis_period_days)

        # Identify strengths and weaknesses
        strengths = self._identify_strengths(metrics)
        weaknesses = self._identify_weaknesses(metrics)
        improvement_areas = self._identify_improvement_areas(metrics, skill)

        # Get recommended focus areas
        recommended_focus = self._get_recommended_focus(metrics, skill, progression)

        # Analyze synergy potential
        synergy_potential = self._analyze_synergy_potential(skill, progression)

        # Analyze contextual performance
        contextual_performance = self._analyze_contextual_performance(skill, analysis_period_days)

        # Generate development recommendations
        development_recommendations = self._generate_development_recommendations(
            metrics, skill, progression
        )

        return SkillEffectiveness(
            skill_name=skill.name,
            metrics=metrics,
            strengths=strengths,
            weaknesses=weaknesses,
            improvement_areas=improvement_areas,
            recommended_focus=recommended_focus,
            synergy_potential=synergy_potential,
            contextual_performance=contextual_performance,
            development_recommendations=development_recommendations
        )

    def compare_skills(
        self,
        skill_a: Skill,
        skill_b: Skill,
        progression: Optional[SkillProgression] = None
    ) -> ComparativeAnalysis:
        """
        Compare performance between two skills

        Args:
            skill_a: First skill to compare
            skill_b: Second skill to compare
            progression: Skill progression data

        Returns:
            ComparativeAnalysis object
        """
        metrics_a = self.analyze_skill_performance(skill_a, progression)
        metrics_b = self.analyze_skill_performance(skill_b, progression)

        # Compare key metrics
        metrics_comparison = {
            'success_rate': (metrics_a.success_rate, metrics_b.success_rate),
            'effectiveness_score': (metrics_a.effectiveness_score, metrics_b.effectiveness_score),
            'usage_frequency': (metrics_a.usage_frequency, metrics_b.usage_frequency),
            'average_xp_per_use': (metrics_a.average_xp_per_use, metrics_b.average_xp_per_use),
            'critical_success_rate': (metrics_a.critical_success_rate, metrics_b.critical_success_rate)
        }

        # Determine winner based on effectiveness score
        winner = skill_a.name if metrics_a.effectiveness_score > metrics_b.effectiveness_score else skill_b.name

        # Generate analysis summary
        analysis_summary = self._generate_comparison_summary(metrics_a, metrics_b)

        # Generate recommendations
        recommendations = self._generate_comparison_recommendations(metrics_a, metrics_b)

        return ComparativeAnalysis(
            comparison_type='skill_vs_skill',
            subject_a=skill_a.name,
            subject_b=skill_b.name,
            metrics_comparison=metrics_comparison,
            winner=winner,
            analysis_summary=analysis_summary,
            recommendations=recommendations
        )

    def analyze_category_performance(
        self,
        skills: List[Skill],
        category: SkillCategory
    ) -> Dict[str, Any]:
        """
        Analyze performance across an entire skill category

        Args:
            skills: List of skills to analyze
            category: Category to analyze

        Returns:
            Dictionary with category performance analysis
        """
        category_skills = [skill for skill in skills if skill.category == category]

        if not category_skills:
            return {
                'category': category.value,
                'total_skills': 0,
                'average_effectiveness': 0.0,
                'top_performers': [],
                'needs_improvement': []
            }

        # Analyze each skill
        skill_metrics = {}
        for skill in category_skills:
            metrics = self.analyze_skill_performance(skill)
            skill_metrics[skill.name] = metrics

        # Calculate category averages
        avg_effectiveness = statistics.mean(m.effectiveness_score for m in skill_metrics.values())
        avg_success_rate = statistics.mean(m.success_rate for m in skill_metrics.values())
        avg_usage_freq = statistics.mean(m.usage_frequency for m in skill_metrics.values())

        # Find top performers and skills needing improvement
        sorted_skills = sorted(
            skill_metrics.items(),
            key=lambda x: x[1].effectiveness_score,
            reverse=True
        )

        top_performers = [name for name, _ in sorted_skills[:3]]
        needs_improvement = [name for name, _ in sorted_skills[-3:]]

        return {
            'category': category.value,
            'total_skills': len(category_skills),
            'average_effectiveness': avg_effectiveness,
            'average_success_rate': avg_success_rate,
            'average_usage_frequency': avg_usage_freq,
            'top_performers': top_performers,
            'needs_improvement': needs_improvement,
            'skill_breakdown': {
                name: {
                    'effectiveness': metrics.effectiveness_score,
                    'success_rate': metrics.success_rate,
                    'mastery_level': metrics.mastery_level.name
                } for name, metrics in skill_metrics.items()
            }
        }

    def get_performance_trends(
        self,
        skill: Skill,
        days: int = 30
    ) -> Dict[str, List[Tuple[datetime, float]]]:
        """
        Get performance trends over time

        Args:
            skill: Skill to analyze
            days: Number of days to analyze

        Returns:
            Dictionary with trend data
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_usage = [
            use for use in skill.usage_history
            if use.timestamp >= cutoff_date
        ]

        if not recent_usage:
            return {
                'success_rate_trend': [],
                'xp_gain_trend': [],
                'difficulty_trend': []
            }

        # Group by day
        daily_data = {}
        for use in recent_usage:
            day_key = use.timestamp.date()
            if day_key not in daily_data:
                daily_data[day_key] = {'successes': 0, 'total': 0, 'xp': 0, 'difficulty': 0}

            daily_data[day_key]['total'] += 1
            if use.success:
                daily_data[day_key]['successes'] += 1
            daily_data[day_key]['xp'] += use.xp_gained + use.bonus_xp
            daily_data[day_key]['difficulty'] += use.difficulty

        # Calculate daily averages
        success_rate_trend = []
        xp_gain_trend = []
        difficulty_trend = []

        for day, data in sorted(daily_data.items()):
            success_rate = (data['successes'] / data['total'] * 100.0) if data['total'] > 0 else 0.0
            avg_xp = data['xp'] / data['total'] if data['total'] > 0 else 0.0
            avg_difficulty = data['difficulty'] / data['total'] if data['total'] > 0 else 0.0

            timestamp = datetime.combine(day, datetime.min.time())
            success_rate_trend.append((timestamp, success_rate))
            xp_gain_trend.append((timestamp, avg_xp))
            difficulty_trend.append((timestamp, avg_difficulty))

        return {
            'success_rate_trend': success_rate_trend,
            'xp_gain_trend': xp_gain_trend,
            'difficulty_trend': difficulty_trend
        }

    def _get_recent_usage(self, skill: Skill, days: int) -> List[SkillUsageRecord]:
        """Get recent usage records within specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return [use for use in skill.usage_history if use.timestamp >= cutoff_date]

    def _calculate_usage_frequency(self, skill: Skill, days: int) -> float:
        """Calculate usage frequency (uses per day)"""
        recent_usage = self._get_recent_usage(skill, days)
        return len(recent_usage) / max(1, days)

    def _calculate_effectiveness_score(
        self,
        success_rate: float,
        critical_success_rate: float,
        average_difficulty: float,
        usage_frequency: float
    ) -> float:
        """Calculate overall effectiveness score (0-100)"""
        # Weight different factors
        success_weight = 0.4
        critical_weight = 0.2
        difficulty_weight = 0.2
        frequency_weight = 0.2

        # Normalize and weight each component
        success_component = min(100.0, success_rate) * success_weight
        critical_component = min(100.0, critical_success_rate * 5) * critical_weight  # Scale up critical rate
        difficulty_component = average_difficulty * 100 * difficulty_weight
        frequency_component = min(100.0, usage_frequency * 10) * frequency_weight  # Scale up frequency

        return success_component + critical_component + difficulty_component + frequency_component

    def _analyze_trend(self, skill: Skill, days: int) -> TrendDirection:
        """Analyze performance trend over time"""
        recent_usage = self._get_recent_usage(skill, days)

        if len(recent_usage) < 5:  # Not enough data
            return TrendDirection.INSUFFICIENT_DATA

        # Split data into two halves
        mid_point = len(recent_usage) // 2
        first_half = recent_usage[:mid_point]
        second_half = recent_usage[mid_point:]

        # Calculate success rates for each half
        first_success_rate = sum(1 for use in first_half if use.success) / len(first_half) * 100.0
        second_success_rate = sum(1 for use in second_half if use.success) / len(second_half) * 100.0

        # Determine trend
        difference = second_success_rate - first_success_rate
        if difference > 5.0:
            return TrendDirection.IMPROVING
        elif difference < -5.0:
            return TrendDirection.DECLINING
        else:
            return TrendDirection.STABLE

    def _identify_strengths(self, metrics: PerformanceMetrics) -> List[str]:
        """Identify skill strengths based on metrics"""
        strengths = []

        if metrics.success_rate >= 80:
            strengths.append("High success rate")
        if metrics.critical_success_rate >= 15:
            strengths.append("Frequent critical successes")
        if metrics.average_difficulty >= 0.7:
            strengths.append("Effective against difficult challenges")
        if metrics.usage_frequency >= 2.0:
            strengths.append("Consistent usage patterns")
        if metrics.average_xp_per_use >= 20:
            strengths.append("High XP efficiency")
        if metrics.effectiveness_score >= 80:
            strengths.append("Overall excellent performance")

        return strengths

    def _identify_weaknesses(self, metrics: PerformanceMetrics) -> List[str]:
        """Identify skill weaknesses based on metrics"""
        weaknesses = []

        if metrics.success_rate < 40:
            weaknesses.append("Low success rate")
        if metrics.critical_success_rate < 5:
            weaknesses.append("Rare critical successes")
        if metrics.usage_frequency < 0.2:
            weaknesses.append("Infrequent usage")
        if metrics.average_xp_per_use < 10:
            weaknesses.append("Low XP efficiency")
        if metrics.effectiveness_score < 30:
            weaknesses.append("Poor overall performance")
        if metrics.trend_direction == TrendDirection.DECLINING:
            weaknesses.append("Declining performance trend")

        return weaknesses

    def _identify_improvement_areas(self, metrics: PerformanceMetrics, skill: Skill) -> List[str]:
        """Identify specific areas for improvement"""
        areas = []

        if metrics.success_rate < 60:
            areas.append("Practice fundamental technique")
        if metrics.critical_success_rate < 10:
            areas.append("Focus on precision and timing")
        if metrics.usage_frequency < 1.0:
            areas.append("Increase usage frequency")
        if metrics.average_difficulty < 0.4:
            areas.append("Challenge with higher difficulty tasks")
        if skill.current_level == MasteryLevel.NOVICE:
            areas.append("Develop basic proficiency")

        return areas

    def _get_recommended_focus(
        self,
        metrics: PerformanceMetrics,
        skill: Skill,
        progression: SkillProgression
    ) -> List[str]:
        """Get recommended focus areas for development"""
        focus_areas = []

        if metrics.success_rate < 50:
            focus_areas.append("Improve basic success rate")
        elif metrics.success_rate < 75:
            focus_areas.append("Enhance consistency")
        else:
            focus_areas.append("Master advanced techniques")

        if metrics.critical_success_rate < 10:
            focus_areas.append("Develop precision for critical successes")

        if metrics.usage_frequency < 1.0:
            focus_areas.append("Increase practice opportunities")

        # Check mastery level
        if skill.current_level == MasteryLevel.NOVICE:
            focus_areas.append("Reach Apprentice level")
        elif skill.current_level == MasteryLevel.APPRENTICE:
            focus_areas.append("Progress toward Journeyman")

        return focus_areas[:3]  # Top 3 priorities

    def _analyze_synergy_potential(self, skill: Skill, progression: SkillProgression) -> Dict[str, float]:
        """Analyze synergy potential with other skills"""
        synergy_potential = {}

        for synergy in skill.synergies:
            if synergy.skill_name in progression.skills:
                ally_skill = progression.skills[synergy.skill_name]
                # Calculate synergy score based on both skills' development
                synergy_score = (skill.total_xp + ally_skill.total_xp) / 2000.0  # Normalize to 0-1
                synergy_potential[synergy.skill_name] = min(1.0, synergy_score)

        return synergy_potential

    def _analyze_contextual_performance(self, skill: Skill, days: int) -> Dict[str, float]:
        """Analyze performance in different contexts"""
        recent_usage = self._get_recent_usage(skill, days)
        context_performance = {}

        # Group by context keywords
        contexts = {}
        for use in recent_usage:
            # Extract simple context keywords
            context_keywords = []
            if 'combat' in use.context.lower():
                context_keywords.append('combat')
            if 'social' in use.context.lower() or 'talk' in use.context.lower():
                context_keywords.append('social')
            if 'explore' in use.context.lower() or 'search' in use.context.lower():
                context_keywords.append('exploration')

            for keyword in context_keywords:
                if keyword not in contexts:
                    contexts[keyword] = {'successes': 0, 'total': 0}
                contexts[keyword]['total'] += 1
                if use.success:
                    contexts[keyword]['successes'] += 1

        # Calculate success rates by context
        for context, data in contexts.items():
            if data['total'] > 0:
                context_performance[context] = (data['successes'] / data['total']) * 100.0

        return context_performance

    def _generate_development_recommendations(
        self,
        metrics: PerformanceMetrics,
        skill: Skill,
        progression: SkillProgression
    ) -> List[Dict[str, Any]]:
        """Generate specific development recommendations"""
        recommendations = []

        # Success rate recommendations
        if metrics.success_rate < 40:
            recommendations.append({
                'type': 'practice',
                'priority': 'high',
                'description': f"Focus on basic {skill.name} techniques to improve success rate",
                'expected_improvement': '+15-25% success rate'
            })
        elif metrics.success_rate < 70:
            recommendations.append({
                'type': 'refinement',
                'priority': 'medium',
                'description': f"Refine {skill.name} technique for better consistency",
                'expected_improvement': '+10-15% success rate'
            })

        # Usage frequency recommendations
        if metrics.usage_frequency < 0.5:
            recommendations.append({
                'type': 'frequency',
                'priority': 'high',
                'description': f"Increase {skill.name} usage to build muscle memory",
                'expected_improvement': '+5-10% effectiveness per use'
            })

        # Difficulty recommendations
        if metrics.average_difficulty < 0.5:
            recommendations.append({
                'type': 'challenge',
                'priority': 'medium',
                'description': f"Take on more challenging {skill.name} tasks",
                'expected_improvement': '+20% XP gain rate'
            })

        # Mastery recommendations
        if skill.current_level == MasteryLevel.NOVICE and metrics.effectiveness_score > 60:
            recommendations.append({
                'type': 'advancement',
                'priority': 'high',
                'description': f"Ready to advance {skill.name} to Apprentice level",
                'expected_improvement': 'Unlock new abilities and bonuses'
            })

        return recommendations[:5]  # Top 5 recommendations

    def _generate_comparison_summary(self, metrics_a: PerformanceMetrics, metrics_b: PerformanceMetrics) -> str:
        """Generate human-readable comparison summary"""
        if abs(metrics_a.effectiveness_score - metrics_b.effectiveness_score) < 5:
            return f"Both {metrics_a.skill_name} and {metrics_b.skill_name} show similar performance levels"

        better = metrics_a if metrics_a.effectiveness_score > metrics_b.effectiveness_score else metrics_b
        worse = metrics_b if better == metrics_a else metrics_a

        diff = better.effectiveness_score - worse.effectiveness_score

        return f"{better.skill_name} significantly outperforms {worse.skill_name} by {diff:.1f} points, primarily due to {'higher success rate' if better.success_rate > worse.success_rate else 'better consistency' if better.usage_frequency > worse.usage_frequency else 'superior overall efficiency'}"

    def _generate_comparison_recommendations(self, metrics_a: PerformanceMetrics, metrics_b: PerformanceMetrics) -> List[str]:
        """Generate recommendations based on skill comparison"""
        recommendations = []

        if metrics_a.effectiveness_score > metrics_b.effectiveness_score:
            weaker, stronger = metrics_b, metrics_a
        else:
            weaker, stronger = metrics_a, metrics_b

        if weaker.success_rate < stronger.success_rate - 10:
            recommendations.append(f"Study {stronger.skill_name} techniques to improve {weaker.skill_name} success rate")

        if weaker.usage_frequency < stronger.usage_frequency - 0.5:
            recommendations.append(f"Increase {weaker.skill_name} usage frequency to match {stronger.skill_name}")

        if stronger.average_difficulty > weaker.average_difficulty + 0.2:
            recommendations.append(f"Challenge {weaker.skill_name} with more difficult tasks like {stronger.skill_name}")

        return recommendations

    def clear_cache(self) -> None:
        """Clear the analysis cache"""
        self.analysis_cache.clear()

    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of analysis system state"""
        return {
            'cached_analyses': len(self.analysis_cache),
            'tracked_skills': len(self.historical_data),
            'total_historical_records': sum(len(records) for records in self.historical_data.values())
        }