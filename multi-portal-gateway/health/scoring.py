"""
Health Score Calculation

Calculates health scores for individual components and overall system health.
Includes trend analysis and predictive scoring.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from .health_service import HealthCheckResult, HealthStatus, CheckLevel

class ScoreTrend(Enum):
    """Health score trend direction"""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    UNKNOWN = "unknown"

@dataclass
class HealthScore:
    """Health score with metadata"""
    score: float
    status: HealthStatus
    trend: ScoreTrend
    confidence: float
    details: Dict[str, Any]
    timestamp: datetime

class HealthScorer:
    """Health score calculation and analysis"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.weights = config.get('weights', {
            'component': 0.3,
            'service': 0.3,
            'system': 0.2,
            'business': 0.2
        })
        self.thresholds = config.get('thresholds', {
            'healthy': 90,
            'warning': 70,
            'degraded': 50
        })

    def calculate_overall_health(self, check_results: List[HealthCheckResult]) -> Tuple[HealthStatus, float]:
        """Calculate overall system health from check results"""
        if not check_results:
            return HealthStatus.UNKNOWN, 0.0

        # Group results by level
        level_scores = {
            CheckLevel.COMPONENT: [],
            CheckLevel.SERVICE: [],
            CheckLevel.SYSTEM: [],
            CheckLevel.BUSINESS: []
        }

        for result in check_results:
            level_scores[result.level].append(result.metrics.get('score', 0))

        # Calculate weighted average
        weighted_score = 0.0
        total_weight = 0.0

        for level, scores in level_scores.items():
            if scores:
                level_avg = statistics.mean(scores)
                weight = self.weights.get(level.value, 0.25)
                weighted_score += level_avg * weight
                total_weight += weight

        if total_weight > 0:
            overall_score = weighted_score / total_weight
        else:
            overall_score = 0.0

        # Determine overall status
        overall_status = self._score_to_status(overall_score)

        return overall_status, overall_score

    def calculate_component_score(self, results: List[HealthCheckResult]) -> HealthScore:
        """Calculate component-level health score"""
        component_results = [r for r in results if r.level == CheckLevel.COMPONENT]

        if not component_results:
            return HealthScore(
                score=0.0,
                status=HealthStatus.UNKNOWN,
                trend=ScoreTrend.UNKNOWN,
                confidence=0.0,
                details={"message": "No component results available"},
                timestamp=datetime.now()
            )

        # Calculate base score
        scores = [r.metrics.get('score', 0) for r in component_results]
        base_score = statistics.mean(scores)

        # Apply critical component weighting
        critical_components = ['database', 'cache', 'message-queue']
        critical_results = [r for r in component_results if r.check_id in critical_components]

        if critical_results:
            critical_scores = [r.metrics.get('score', 0) for r in critical_results]
            critical_avg = statistics.mean(critical_scores)

            # Critical components have higher impact
            final_score = (base_score * 0.7) + (critical_avg * 0.3)
        else:
            final_score = base_score

        # Calculate trend
        trend = self._calculate_trend(component_results)

        # Calculate confidence based on result consistency
        confidence = self._calculate_confidence(scores)

        return HealthScore(
            score=min(100, max(0, final_score)),
            status=self._score_to_status(final_score),
            trend=trend,
            confidence=confidence,
            details={
                "component_count": len(component_results),
                "critical_components": len(critical_results),
                "individual_scores": scores,
                "critical_score": critical_avg if critical_results else None
            },
            timestamp=datetime.now()
        )

    def calculate_service_score(self, results: List[HealthCheckResult]) -> HealthScore:
        """Calculate service-level health score"""
        service_results = [r for r in results if r.level == CheckLevel.SERVICE]

        if not service_results:
            return HealthScore(
                score=0.0,
                status=HealthStatus.UNKNOWN,
                trend=ScoreTrend.UNKNOWN,
                confidence=0.0,
                details={"message": "No service results available"},
                timestamp=datetime.now()
            )

        # Calculate base score
        scores = [r.metrics.get('score', 0) for r in service_results]
        base_score = statistics.mean(scores)

        # Apply critical service weighting
        critical_services = ['api-gateway', 'character-portal', 'dialogue-service']
        critical_results = [r for r in service_results if r.check_id in critical_services]

        if critical_results:
            critical_scores = [r.metrics.get('score', 0) for r in critical_results]
            critical_avg = statistics.mean(critical_scores)

            # Critical services have higher impact
            final_score = (base_score * 0.6) + (critical_avg * 0.4)
        else:
            final_score = base_score

        # Penalty for failed dependencies
        dependency_penalty = self._calculate_dependency_penalty(service_results)
        final_score = max(0, final_score - dependency_penalty)

        # Calculate trend
        trend = self._calculate_trend(service_results)

        # Calculate confidence
        confidence = self._calculate_confidence(scores)

        return HealthScore(
            score=min(100, max(0, final_score)),
            status=self._score_to_status(final_score),
            trend=trend,
            confidence=confidence,
            details={
                "service_count": len(service_results),
                "critical_services": len(critical_results),
                "individual_scores": scores,
                "critical_score": critical_avg if critical_results else None,
                "dependency_penalty": dependency_penalty
            },
            timestamp=datetime.now()
        )

    def calculate_system_score(self, results: List[HealthCheckResult]) -> HealthScore:
        """Calculate system-level health score"""
        system_results = [r for r in results if r.level == CheckLevel.SYSTEM]

        if not system_results:
            return HealthScore(
                score=0.0,
                status=HealthStatus.UNKNOWN,
                trend=ScoreTrend.UNKNOWN,
                confidence=0.0,
                details={"message": "No system results available"},
                timestamp=datetime.now()
            )

        # Calculate base score
        scores = [r.metrics.get('score', 0) for r in system_results]
        base_score = statistics.mean(scores)

        # Weight critical system resources higher
        critical_system_checks = ['cpu-usage', 'memory-usage', 'disk-io']
        critical_results = [r for r in system_results if r.check_id in critical_system_checks]

        if critical_results:
            critical_scores = [r.metrics.get('score', 0) for r in critical_results]
            critical_avg = statistics.mean(critical_scores)

            # System resources are very important
            final_score = (base_score * 0.5) + (critical_avg * 0.5)
        else:
            final_score = base_score

        # Calculate trend
        trend = self._calculate_trend(system_results)

        # Calculate confidence
        confidence = self._calculate_confidence(scores)

        return HealthScore(
            score=min(100, max(0, final_score)),
            status=self._score_to_status(final_score),
            trend=trend,
            confidence=confidence,
            details={
                "system_check_count": len(system_results),
                "critical_checks": len(critical_results),
                "individual_scores": scores,
                "critical_score": critical_avg if critical_results else None
            },
            timestamp=datetime.now()
        )

    def calculate_business_score(self, results: List[HealthCheckResult]) -> HealthScore:
        """Calculate business-level health score"""
        business_results = [r for r in results if r.level == CheckLevel.BUSINESS]

        if not business_results:
            return HealthScore(
                score=0.0,
                status=HealthStatus.UNKNOWN,
                trend=ScoreTrend.UNKNOWN,
                confidence=0.0,
                details={"message": "No business results available"},
                timestamp=datetime.now()
            )

        # Calculate base score
        scores = [r.metrics.get('score', 0) for r in business_results]
        base_score = statistics.mean(scores)

        # Weight critical business metrics higher
        critical_business_checks = ['error-rates', 'user-activity']
        critical_results = [r for r in business_results if r.check_id in critical_business_checks]

        if critical_results:
            critical_scores = [r.metrics.get('score', 0) for r in critical_results]
            critical_avg = statistics.mean(critical_scores)

            # Business metrics are important but less critical than system resources
            final_score = (base_score * 0.7) + (critical_avg * 0.3)
        else:
            final_score = base_score

        # Calculate trend
        trend = self._calculate_trend(business_results)

        # Calculate confidence
        confidence = self._calculate_confidence(scores)

        return HealthScore(
            score=min(100, max(0, final_score)),
            status=self._score_to_status(final_score),
            trend=trend,
            confidence=confidence,
            details={
                "business_check_count": len(business_results),
                "critical_checks": len(critical_results),
                "individual_scores": scores,
                "critical_score": critical_avg if critical_results else None
            },
            timestamp=datetime.now()
        )

    def predict_health_trend(self, historical_data: List[Dict[str, Any]], hours_ahead: int = 24) -> Dict[str, Any]:
        """Predict health trends based on historical data"""
        if len(historical_data) < 10:
            return {
                "prediction": "insufficient_data",
                "confidence": 0.0,
                "predicted_score": None,
                "trend_direction": ScoreTrend.UNKNOWN
            }

        # Extract scores and timestamps
        scores = [entry.get("score", 0) for entry in historical_data[-20:]]  # Use last 20 entries
        timestamps = [datetime.fromisoformat(entry.get("timestamp", "")) for entry in historical_data[-20:]]

        if len(scores) < 5:
            return {
                "prediction": "insufficient_data",
                "confidence": 0.0,
                "predicted_score": None,
                "trend_direction": ScoreTrend.UNKNOWN
            }

        # Simple linear regression for trend prediction
        try:
            x = list(range(len(scores)))
            y = scores

            # Calculate regression coefficients
            n = len(scores)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            intercept = (sum_y - slope * sum_x) / n

            # Predict future score
            future_x = len(scores) + (hours_ahead / 1)  # Assuming data points are roughly hourly
            predicted_score = slope * future_x + intercept

            # Calculate confidence based on R-squared
            mean_y = sum_y / n
            ss_tot = sum((y[i] - mean_y) ** 2 for i in range(n))
            ss_res = sum((y[i] - (slope * x[i] + intercept)) ** 2 for i in range(n))
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            # Determine trend direction
            if slope > 1:
                trend_direction = ScoreTrend.IMPROVING
            elif slope < -1:
                trend_direction = ScoreTrend.DECLINING
            else:
                trend_direction = ScoreTrend.STABLE

            # Cap predicted score between 0 and 100
            predicted_score = max(0, min(100, predicted_score))

            return {
                "prediction": "available",
                "confidence": max(0, min(1, r_squared)),
                "predicted_score": predicted_score,
                "trend_direction": trend_direction,
                "slope": slope,
                "intercept": intercept,
                "data_points": len(scores)
            }

        except Exception as e:
            self.logger.error(f"Failed to predict health trend: {e}")
            return {
                "prediction": "error",
                "confidence": 0.0,
                "predicted_score": None,
                "trend_direction": ScoreTrend.UNKNOWN,
                "error": str(e)
            }

    def analyze_score_volatility(self, historical_data: List[Dict[str, Any]], window_hours: int = 24) -> Dict[str, Any]:
        """Analyze score volatility over time"""
        cutoff_time = datetime.now() - timedelta(hours=window_hours)
        recent_data = [
            entry for entry in historical_data
            if datetime.fromisoformat(entry.get("timestamp", "")) >= cutoff_time
        ]

        if len(recent_data) < 3:
            return {
                "volatility": "unknown",
                "standard_deviation": 0.0,
                "variance": 0.0,
                "min_score": None,
                "max_score": None,
                "data_points": len(recent_data)
            }

        scores = [entry.get("score", 0) for entry in recent_data]

        # Calculate statistics
        mean_score = statistics.mean(scores)
        variance = statistics.variance(scores) if len(scores) > 1 else 0.0
        std_dev = statistics.stdev(scores) if len(scores) > 1 else 0.0
        min_score = min(scores)
        max_score = max(scores)

        # Determine volatility level
        if std_dev < 5:
            volatility_level = "low"
        elif std_dev < 15:
            volatility_level = "moderate"
        else:
            volatility_level = "high"

        return {
            "volatility": volatility_level,
            "standard_deviation": std_dev,
            "variance": variance,
            "mean_score": mean_score,
            "min_score": min_score,
            "max_score": max_score,
            "range": max_score - min_score,
            "data_points": len(scores)
        }

    def _score_to_status(self, score: float) -> HealthStatus:
        """Convert numeric score to health status"""
        if score >= self.thresholds.get('healthy', 90):
            return HealthStatus.HEALTHY
        elif score >= self.thresholds.get('warning', 70):
            return HealthStatus.WARNING
        elif score >= self.thresholds.get('degraded', 50):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.CRITICAL

    def _calculate_trend(self, results: List[HealthCheckResult]) -> ScoreTrend:
        """Calculate trend direction based on recent results"""
        if len(results) < 2:
            return ScoreTrend.UNKNOWN

        # Simple trend calculation based on recent vs older scores
        recent_scores = [r.metrics.get('score', 0) for r in results[-3:]]
        older_scores = [r.metrics.get('score', 0) for r in results[:-3]] if len(results) > 3 else recent_scores

        if not recent_scores or not older_scores:
            return ScoreTrend.UNKNOWN

        recent_avg = statistics.mean(recent_scores)
        older_avg = statistics.mean(older_scores)

        diff = recent_avg - older_avg

        if diff > 5:
            return ScoreTrend.IMPROVING
        elif diff < -5:
            return ScoreTrend.DECLINING
        else:
            return ScoreTrend.STABLE

    def _calculate_confidence(self, scores: List[float]) -> float:
        """Calculate confidence score based on score consistency"""
        if len(scores) < 2:
            return 0.5

        # Calculate standard deviation
        std_dev = statistics.stdev(scores)
        mean_score = statistics.mean(scores)

        # Confidence decreases with higher standard deviation
        if mean_score > 0:
            coefficient_of_variation = std_dev / mean_score
            confidence = max(0.1, 1.0 - coefficient_of_variation)
        else:
            confidence = 0.1

        return min(1.0, confidence)

    def _calculate_dependency_penalty(self, service_results: List[HealthCheckResult]) -> float:
        """Calculate penalty for failed dependencies"""
        penalty = 0.0

        for result in service_results:
            # Check if service has dependency issues mentioned in details
            if "dependency" in result.message.lower() or "dependency" in str(result.details).lower():
                penalty += 10

            # Higher penalty for critical services with dependency issues
            if result.check_id in ['api-gateway', 'character-portal', 'dialogue-service']:
                penalty += 5

        return min(30, penalty)  # Cap penalty at 30 points

    def generate_health_summary(self, check_results: List[HealthCheckResult]) -> Dict[str, Any]:
        """Generate comprehensive health summary"""
        if not check_results:
            return {
                "overall_status": HealthStatus.UNKNOWN,
                "overall_score": 0.0,
                "summary": "No health check results available",
                "recommendations": ["Run health checks to get system status"],
                "timestamp": datetime.now().isoformat()
            }

        # Calculate scores for each level
        component_score = self.calculate_component_score(check_results)
        service_score = self.calculate_service_score(check_results)
        system_score = self.calculate_system_score(check_results)
        business_score = self.calculate_business_score(check_results)

        # Calculate overall
        overall_status, overall_score = self.calculate_overall_health(check_results)

        # Count issues by severity
        critical_count = len([r for r in check_results if r.status == HealthStatus.CRITICAL])
        degraded_count = len([r for r in check_results if r.status == HealthStatus.DEGRADED])
        warning_count = len([r for r in check_results if r.status == HealthStatus.WARNING])

        # Generate recommendations
        recommendations = []

        if critical_count > 0:
            recommendations.append(f"Address {critical_count} critical issues immediately")

        if degraded_count > 0:
            recommendations.append(f"Investigate {degraded_count} degraded services")

        if warning_count > 0:
            recommendations.append(f"Monitor {warning_count} services with warnings")

        if overall_score < 80:
            recommendations.append("System performance is below optimal levels")

        # Specific recommendations based on level scores
        if component_score.score < 70:
            recommendations.append("Check infrastructure components (database, cache, message queue)")

        if service_score.score < 70:
            recommendations.append("Review application service health and performance")

        if system_score.score < 70:
            recommendations.append("Monitor system resources (CPU, memory, disk)")

        if business_score.score < 70:
            recommendations.append("Investigate business metrics and user experience")

        return {
            "overall_status": overall_status.value,
            "overall_score": round(overall_score, 1),
            "component_score": {
                "score": round(component_score.score, 1),
                "status": component_score.status.value,
                "trend": component_score.trend.value
            },
            "service_score": {
                "score": round(service_score.score, 1),
                "status": service_score.status.value,
                "trend": service_score.trend.value
            },
            "system_score": {
                "score": round(system_score.score, 1),
                "status": system_score.status.value,
                "trend": system_score.trend.value
            },
            "business_score": {
                "score": round(business_score.score, 1),
                "status": business_score.status.value,
                "trend": business_score.trend.value
            },
            "issue_counts": {
                "critical": critical_count,
                "degraded": degraded_count,
                "warning": warning_count
            },
            "summary": self._generate_summary_text(overall_status, overall_score, critical_count),
            "recommendations": recommendations,
            "timestamp": datetime.now().isoformat()
        }

    def _generate_summary_text(self, status: HealthStatus, score: float, critical_count: int) -> str:
        """Generate human-readable summary text"""
        if critical_count > 0:
            return f"System is in CRITICAL state with {critical_count} critical issues requiring immediate attention"

        if status == HealthStatus.HEALTHY:
            return f"System is operating normally with a health score of {score:.1f}%"
        elif status == HealthStatus.WARNING:
            return f"System has some performance concerns with a health score of {score:.1f}%"
        elif status == HealthStatus.DEGRADED:
            return f"System performance is degraded with a health score of {score:.1f}%"
        else:
            return f"System is in an unknown state with a health score of {score:.1f}%"