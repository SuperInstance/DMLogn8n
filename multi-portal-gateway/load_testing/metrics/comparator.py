#!/usr/bin/env python3
"""
Baseline Comparison and Regression Detection System
Compares current performance against baselines and detects regressions
"""

import asyncio
import json
import statistics
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import logging
import sqlite3
from scipy import stats
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class BaselineMetric:
    """Baseline metric for comparison"""
    metric_name: str
    endpoint: Optional[str]
    baseline_value: float
    baseline_std: float
    sample_size: int
    created_at: datetime
    test_conditions: Dict[str, Any]
    confidence_level: float  # 0-1
    acceptable_deviation: float  # percentage

@dataclass
class PerformanceComparison:
    """Comparison result between current and baseline"""
    metric_name: str
    endpoint: Optional[str]
    baseline_value: float
    current_value: float
    deviation_percent: float
    deviation_significance: float  # p-value
    regression_detected: bool
    improvement_detected: bool
    severity: str  # minor, moderate, major, critical
    confidence: float  # 0-1
    recommendation: str

@dataclass
class RegressionReport:
    """Complete regression analysis report"""
    comparison_timestamp: datetime
    baseline_timestamp: datetime
    test_duration: timedelta
    total_comparisons: int
    regressions_detected: int
    improvements_detected: int
    critical_issues: int
    overall_health_impact: str  # significant, moderate, minimal
    comparisons: List[PerformanceComparison]
    summary: Dict[str, Any]
    recommendations: List[str]

class BaselineComparator:
    """Compares performance against baselines and detects regressions"""

    def __init__(self, baseline_storage_path: str = "baselines.db"):
        self.baseline_storage_path = baseline_storage_path
        self.baseline_cache: Dict[str, BaselineMetric] = {}
        self.comparison_history: List[RegressionReport] = []

        # Setup baseline storage
        self._setup_baseline_storage()

        # Default thresholds
        self.default_thresholds = {
            "response_time": {
                "warning_deviation": 10.0,  # 10%
                "critical_deviation": 25.0,  # 25%
                "min_sample_size": 30
            },
            "error_rate": {
                "warning_deviation": 20.0,  # 20%
                "critical_deviation": 50.0,  # 50%
                "min_sample_size": 100
            },
            "throughput": {
                "warning_deviation": 15.0,  # 15%
                "critical_deviation": 30.0,  # 30%
                "min_sample_size": 50
            },
            "cpu_usage": {
                "warning_deviation": 10.0,  # 10%
                "critical_deviation": 20.0,  # 20%
                "min_sample_size": 20
            },
            "memory_usage": {
                "warning_deviation": 10.0,  # 10%
                "critical_deviation": 20.0,  # 20%
                "min_sample_size": 20
            }
        }

    def _setup_baseline_storage(self):
        """Setup database for baseline storage"""
        try:
            conn = sqlite3.connect(self.baseline_storage_path)
            cursor = conn.cursor()

            # Create baselines table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_baselines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    endpoint TEXT,
                    baseline_value REAL NOT NULL,
                    baseline_std REAL NOT NULL,
                    sample_size INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    test_conditions TEXT,
                    confidence_level REAL,
                    acceptable_deviation REAL,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')

            # Create comparison history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS comparison_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    comparison_timestamp TEXT NOT NULL,
                    baseline_timestamp TEXT NOT NULL,
                    test_duration TEXT,
                    total_comparisons INTEGER,
                    regressions_detected INTEGER,
                    improvements_detected INTEGER,
                    critical_issues INTEGER,
                    overall_health_impact TEXT,
                    summary TEXT,
                    recommendations TEXT
                )
            ''')

            # Create detailed comparisons table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS detailed_comparisons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    comparison_id INTEGER,
                    metric_name TEXT NOT NULL,
                    endpoint TEXT,
                    baseline_value REAL NOT NULL,
                    current_value REAL NOT NULL,
                    deviation_percent REAL,
                    deviation_significance REAL,
                    regression_detected BOOLEAN,
                    improvement_detected BOOLEAN,
                    severity TEXT,
                    confidence REAL,
                    recommendation TEXT,
                    FOREIGN KEY (comparison_id) REFERENCES comparison_history (id)
                )
            ''')

            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_baseline_metric ON performance_baselines(metric_name, endpoint)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_baseline_created ON performance_baselines(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_comparison_timestamp ON comparison_history(comparison_timestamp)')

            conn.commit()
            conn.close()

            logger.info(f"Baseline storage initialized at {self.baseline_storage_path}")

        except Exception as e:
            logger.error(f"Failed to setup baseline storage: {e}")
            raise

    async def establish_baseline(self, test_name: str, metrics_data: Dict[str, Any], test_conditions: Dict[str, Any]) -> bool:
        """Establish a new performance baseline"""
        logger.info(f"Establishing baseline for test: {test_name}")

        try:
            conn = sqlite3.connect(self.baseline_storage_path)
            cursor = conn.cursor()

            # Deactivate existing baselines for the same test
            cursor.execute('''
                UPDATE performance_baselines
                SET is_active = FALSE
                WHERE metric_name LIKE ? || '%'
            ''', (test_name,))

            # Process metrics and create baselines
            baselines_created = 0

            for metric_name, metric_data in metrics_data.items():
                if isinstance(metric_data, dict) and 'values' in metric_data:
                    # Calculate baseline statistics
                    values = metric_data['values']
                    if len(values) >= self._get_min_sample_size(metric_name):
                        baseline_value = statistics.mean(values)
                        baseline_std = statistics.stdev(values) if len(values) > 1 else 0
                        sample_size = len(values)

                        # Determine acceptable deviation based on metric type
                        acceptable_deviation = self._get_acceptable_deviation(metric_name)

                        # Insert baseline
                        cursor.execute('''
                            INSERT INTO performance_baselines (
                                metric_name, endpoint, baseline_value, baseline_std,
                                sample_size, created_at, test_conditions,
                                confidence_level, acceptable_deviation, is_active
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE)
                        ''', (
                            f"{test_name}_{metric_name}",
                            metric_data.get('endpoint'),
                            baseline_value,
                            baseline_std,
                            sample_size,
                            datetime.now(timezone.utc).isoformat(),
                            json.dumps(test_conditions),
                            0.95,  # 95% confidence
                            acceptable_deviation
                        ))

                        baselines_created += 1

                        # Update cache
                        baseline_key = f"{test_name}_{metric_name}_{metric_data.get('endpoint', 'global')}"
                        self.baseline_cache[baseline_key] = BaselineMetric(
                            metric_name=f"{test_name}_{metric_name}",
                            endpoint=metric_data.get('endpoint'),
                            baseline_value=baseline_value,
                            baseline_std=baseline_std,
                            sample_size=sample_size,
                            created_at=datetime.now(timezone.utc),
                            test_conditions=test_conditions,
                            confidence_level=0.95,
                            acceptable_deviation=acceptable_deviation
                        )

            conn.commit()
            conn.close()

            logger.info(f"Established {baselines_created} new baselines for test: {test_name}")
            return baselines_created > 0

        except Exception as e:
            logger.error(f"Failed to establish baseline for {test_name}: {e}")
            return False

    async def compare_with_baseline(self, test_name: str, current_metrics: Dict[str, Any]) -> Optional[RegressionReport]:
        """Compare current metrics with established baseline"""
        logger.info(f"Comparing metrics with baseline for test: {test_name}")

        try:
            # Load active baselines for this test
            baselines = await self._load_active_baselines(test_name)

            if not baselines:
                logger.warning(f"No active baselines found for test: {test_name}")
                return None

            comparisons = []
            total_comparisons = 0
            regressions_detected = 0
            improvements_detected = 0
            critical_issues = 0

            # Compare each metric
            for metric_name, metric_data in current_metrics.items():
                if isinstance(metric_data, dict) and 'current_value' in metric_data:
                    endpoint = metric_data.get('endpoint')
                    baseline_key = f"{test_name}_{metric_name}_{endpoint or 'global'}"

                    if baseline_key in self.baseline_cache:
                        baseline = self.baseline_cache[baseline_key]
                        comparison = self._compare_metric(baseline, metric_data)

                        if comparison:
                            comparisons.append(comparison)
                            total_comparisons += 1

                            if comparison.regression_detected:
                                regressions_detected += 1
                                if comparison.severity == "critical":
                                    critical_issues += 1

                            if comparison.improvement_detected:
                                improvements_detected += 1

            # Generate summary and recommendations
            summary = self._generate_comparison_summary(comparisons)
            recommendations = self._generate_recommendations(comparisons)

            # Determine overall health impact
            overall_impact = self._determine_overall_impact(critical_issues, regressions_detected, total_comparisons)

            # Create report
            report = RegressionReport(
                comparison_timestamp=datetime.now(timezone.utc),
                baseline_timestamp=baselines[0].created_at if baselines else datetime.now(timezone.utc),
                test_duration=timedelta(minutes=30),  # This should come from test data
                total_comparisons=total_comparisons,
                regressions_detected=regressions_detected,
                improvements_detected=improvements_detected,
                critical_issues=critical_issues,
                overall_health_impact=overall_impact,
                comparisons=comparisons,
                summary=summary,
                recommendations=recommendations
            )

            # Store comparison in database
            await self._store_comparison_report(test_name, report)

            # Add to history
            self.comparison_history.append(report)

            logger.info(f"Comparison completed: {regressions_detected} regressions, {improvements_detected} improvements detected")
            return report

        except Exception as e:
            logger.error(f"Failed to compare metrics with baseline for {test_name}: {e}")
            return None

    def _compare_metric(self, baseline: BaselineMetric, current_data: Dict[str, Any]) -> Optional[PerformanceComparison]:
        """Compare a single metric against its baseline"""
        try:
            current_value = current_data['current_value']
            baseline_value = baseline.baseline_value
            baseline_std = baseline.baseline_std

            # Calculate percentage deviation
            if baseline_value != 0:
                deviation_percent = ((current_value - baseline_value) / baseline_value) * 100
            else:
                deviation_percent = 0

            # Statistical significance test (t-test)
            # For now, use simplified approach based on standard deviations
            if baseline_std > 0:
                z_score = abs(current_value - baseline_value) / baseline_std
                significance = 2 * (1 - stats.norm.cdf(z_score))  # Two-tailed test
            else:
                significance = 0.05  # Default significance

            # Determine if regression or improvement detected
            threshold = baseline.acceptable_deviation
            regression_detected = deviation_percent > threshold and significance < 0.05
            improvement_detected = deviation_percent < -threshold and significance < 0.05

            # Determine severity
            if abs(deviation_percent) > threshold * 2:
                severity = "critical"
            elif abs(deviation_percent) > threshold * 1.5:
                severity = "major"
            elif abs(deviation_percent) > threshold:
                severity = "moderate"
            else:
                severity = "minor"

            # Calculate confidence based on sample size and significance
            confidence = min(0.99, 1.0 - significance) if significance < 0.5 else 0.5

            # Generate recommendation
            recommendation = self._generate_metric_recommendation(
                baseline.metric_name, deviation_percent, regression_detected, improvement_detected
            )

            return PerformanceComparison(
                metric_name=baseline.metric_name,
                endpoint=baseline.endpoint,
                baseline_value=baseline_value,
                current_value=current_value,
                deviation_percent=deviation_percent,
                deviation_significance=significance,
                regression_detected=regression_detected,
                improvement_detected=improvement_detected,
                severity=severity,
                confidence=confidence,
                recommendation=recommendation
            )

        except Exception as e:
            logger.error(f"Error comparing metric: {e}")
            return None

    def _generate_metric_recommendation(self, metric_name: str, deviation_percent: float, regression: bool, improvement: bool) -> str:
        """Generate recommendation for a specific metric comparison"""
        if regression:
            if deviation_percent > 50:
                return "Critical performance regression detected. Immediate investigation and remediation required."
            elif deviation_percent > 25:
                return "Significant performance regression detected. Investigation recommended."
            else:
                return "Minor performance regression detected. Monitor trends and consider optimization."

        elif improvement:
            if deviation_percent < -25:
                return "Excellent performance improvement achieved. Consider documenting successful changes."
            else:
                return "Performance improvement detected. Good progress on optimization efforts."

        else:
            return "Performance is within acceptable range of baseline. Continue monitoring."

    async def _load_active_baselines(self, test_name: str) -> List[BaselineMetric]:
        """Load active baselines for a specific test"""
        try:
            conn = sqlite3.connect(self.baseline_storage_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT metric_name, endpoint, baseline_value, baseline_std,
                       sample_size, created_at, test_conditions, confidence_level,
                       acceptable_deviation
                FROM performance_baselines
                WHERE metric_name LIKE ? || '%' AND is_active = TRUE
                ORDER BY created_at DESC
            ''', (test_name,))

            rows = cursor.fetchall()
            conn.close()

            baselines = []
            for row in rows:
                baseline = BaselineMetric(
                    metric_name=row[0],
                    endpoint=row[1],
                    baseline_value=row[2],
                    baseline_std=row[3],
                    sample_size=row[4],
                    created_at=datetime.fromisoformat(row[5].replace('Z', '+00:00')),
                    test_conditions=json.loads(row[6]) if row[6] else {},
                    confidence_level=row[7],
                    acceptable_deviation=row[8]
                )
                baselines.append(baseline)

                # Update cache
                cache_key = f"{baseline.metric_name}_{baseline.endpoint or 'global'}"
                self.baseline_cache[cache_key] = baseline

            return baselines

        except Exception as e:
            logger.error(f"Failed to load baselines for {test_name}: {e}")
            return []

    async def _store_comparison_report(self, test_name: str, report: RegressionReport):
        """Store comparison report in database"""
        try:
            conn = sqlite3.connect(self.baseline_storage_path)
            cursor = conn.cursor()

            # Insert main report
            cursor.execute('''
                INSERT INTO comparison_history (
                    comparison_timestamp, baseline_timestamp, test_duration,
                    total_comparisons, regressions_detected, improvements_detected,
                    critical_issues, overall_health_impact, summary, recommendations
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                report.comparison_timestamp.isoformat(),
                report.baseline_timestamp.isoformat(),
                str(report.test_duration),
                report.total_comparisons,
                report.regressions_detected,
                report.improvements_detected,
                report.critical_issues,
                report.overall_health_impact,
                json.dumps(report.summary),
                json.dumps(report.recommendations)
            ))

            comparison_id = cursor.lastrowid

            # Insert detailed comparisons
            for comparison in report.comparisons:
                cursor.execute('''
                    INSERT INTO detailed_comparisons (
                        comparison_id, metric_name, endpoint, baseline_value,
                        current_value, deviation_percent, deviation_significance,
                        regression_detected, improvement_detected, severity,
                        confidence, recommendation
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    comparison_id,
                    comparison.metric_name,
                    comparison.endpoint,
                    comparison.baseline_value,
                    comparison.current_value,
                    comparison.deviation_percent,
                    comparison.deviation_significance,
                    comparison.regression_detected,
                    comparison.improvement_detected,
                    comparison.severity,
                    comparison.confidence,
                    comparison.recommendation
                ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to store comparison report: {e}")

    def _get_min_sample_size(self, metric_name: str) -> int:
        """Get minimum sample size for a metric type"""
        for metric_type, thresholds in self.default_thresholds.items():
            if metric_type in metric_name.lower():
                return thresholds["min_sample_size"]
        return 30  # Default minimum

    def _get_acceptable_deviation(self, metric_name: str) -> float:
        """Get acceptable deviation percentage for a metric type"""
        for metric_type, thresholds in self.default_thresholds.items():
            if metric_type in metric_name.lower():
                return thresholds["warning_deviation"]
        return 10.0  # Default 10%

    def _generate_comparison_summary(self, comparisons: List[PerformanceComparison]) -> Dict[str, Any]:
        """Generate summary of comparison results"""
        if not comparisons:
            return {"status": "no_data"}

        total = len(comparisons)
        regressions = [c for c in comparisons if c.regression_detected]
        improvements = [c for c in comparisons if c.improvement_detected]
        critical = [c for c in comparisons if c.severity == "critical"]

        # Calculate average deviations
        regressions_deviation = [c.deviation_percent for c in regressions]
        improvements_deviation = [c.deviation_percent for c in improvements]

        return {
            "total_comparisons": total,
            "regressions_count": len(regressions),
            "improvements_count": len(improvements),
            "critical_issues_count": len(critical),
            "regression_rate": (len(regressions) / total * 100) if total > 0 else 0,
            "improvement_rate": (len(improvements) / total * 100) if total > 0 else 0,
            "avg_regression_deviation": statistics.mean(regressions_deviation) if regressions_deviation else 0,
            "avg_improvement_deviation": statistics.mean(improvements_deviation) if improvements_deviation else 0,
            "most_affected_metrics": [c.metric_name for c in sorted(regressions, key=lambda x: abs(x.deviation_percent), reverse=True)[:5]],
            "most_improved_metrics": [c.metric_name for c in sorted(improvements, key=lambda x: abs(x.deviation_percent), reverse=True)[:5]]
        }

    def _generate_recommendations(self, comparisons: List[PerformanceComparison]) -> List[str]:
        """Generate overall recommendations based on comparisons"""
        recommendations = []

        regressions = [c for c in comparisons if c.regression_detected]
        critical = [c for c in regressions if c.severity == "critical"]

        if critical:
            recommendations.append("CRITICAL: Address critical performance regressions immediately. These may significantly impact user experience.")

        if len(regressions) > len(comparisons) * 0.3:
            recommendations.append("High regression rate detected. Review recent changes and consider rollback if necessary.")

        if any("response_time" in c.metric_name.lower() for c in regressions):
            recommendations.append("Response time regressions detected. Review code changes, database queries, and system resources.")

        if any("error_rate" in c.metric_name.lower() for c in regressions):
            recommendations.append("Error rate regressions detected. Review error logs and fix underlying issues.")

        if any("cpu_usage" in c.metric_name.lower() or "memory_usage" in c.metric_name.lower() for c in regressions):
            recommendations.append("Resource usage regressions detected. Profile application for resource bottlenecks.")

        improvements = [c for c in comparisons if c.improvement_detected]
        if improvements:
            recommendations.append(f"Positive: {len(improvements)} metrics show improvement. Document successful optimizations.")

        return recommendations

    def _determine_overall_impact(self, critical_issues: int, regressions: int, total: int) -> str:
        """Determine overall health impact"""
        if critical_issues > 0:
            return "significant"
        elif regressions > total * 0.2:
            return "moderate"
        elif regressions > 0:
            return "minimal"
        else:
            return "positive"

    async def get_comparison_history(self, test_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get comparison history for a test"""
        try:
            conn = sqlite3.connect(self.baseline_storage_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT comparison_timestamp, baseline_timestamp, test_duration,
                       total_comparisons, regressions_detected, improvements_detected,
                       critical_issues, overall_health_impact, summary, recommendations
                FROM comparison_history
                ORDER BY comparison_timestamp DESC
                LIMIT ?
            ''', (limit,))

            rows = cursor.fetchall()
            conn.close()

            history = []
            for row in rows:
                history.append({
                    "comparison_timestamp": row[0],
                    "baseline_timestamp": row[1],
                    "test_duration": row[2],
                    "total_comparisons": row[3],
                    "regressions_detected": row[4],
                    "improvements_detected": row[5],
                    "critical_issues": row[6],
                    "overall_health_impact": row[7],
                    "summary": json.loads(row[8]) if row[8] else {},
                    "recommendations": json.loads(row[9]) if row[9] else []
                })

            return history

        except Exception as e:
            logger.error(f"Failed to get comparison history: {e}")
            return []

    async def export_baseline_report(self, filename: str, test_name: Optional[str] = None):
        """Export baseline comparison report"""
        try:
            report_data = {
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "test_name": test_name,
                "active_baselines": await self._get_all_active_baselines(test_name),
                "recent_comparisons": await self.get_comparison_history(test_name or "", limit=20),
                "comparison_summary": self._summarize_comparison_history(test_name)
            }

            with open(filename, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)

            logger.info(f"Baseline report exported to {filename}")

        except Exception as e:
            logger.error(f"Failed to export baseline report: {e}")

    async def _get_all_active_baselines(self, test_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all active baselines"""
        try:
            conn = sqlite3.connect(self.baseline_storage_path)
            cursor = conn.cursor()

            query = '''
                SELECT metric_name, endpoint, baseline_value, baseline_std,
                       sample_size, created_at, test_conditions, confidence_level,
                       acceptable_deviation
                FROM performance_baselines
                WHERE is_active = TRUE
            '''
            params = []

            if test_name:
                query += ' AND metric_name LIKE ? || "%"'
                params.append(test_name)

            query += ' ORDER BY created_at DESC'

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            baselines = []
            for row in rows:
                baselines.append({
                    "metric_name": row[0],
                    "endpoint": row[1],
                    "baseline_value": row[2],
                    "baseline_std": row[3],
                    "sample_size": row[4],
                    "created_at": row[5],
                    "test_conditions": json.loads(row[6]) if row[6] else {},
                    "confidence_level": row[7],
                    "acceptable_deviation": row[8]
                })

            return baselines

        except Exception as e:
            logger.error(f"Failed to get active baselines: {e}")
            return []

    def _summarize_comparison_history(self, test_name: Optional[str] = None) -> Dict[str, Any]:
        """Summarize comparison history"""
        if not self.comparison_history:
            return {"status": "no_history"}

        recent_reports = self.comparison_history[-10:]  # Last 10 comparisons

        total_comparisons = sum(r.total_comparisons for r in recent_reports)
        total_regressions = sum(r.regressions_detected for r in recent_reports)
        total_improvements = sum(r.improvements_detected for r in recent_reports)
        total_critical = sum(r.critical_issues for r in recent_reports)

        return {
            "recent_comparisons": len(recent_reports),
            "total_comparisons_made": total_comparisons,
            "total_regressions_detected": total_regressions,
            "total_improvements_detected": total_improvements,
            "total_critical_issues": total_critical,
            "average_regression_rate": (total_regressions / total_comparisons * 100) if total_comparisons > 0 else 0,
            "trend": self._analyze_regression_trend(recent_reports)
        }

    def _analyze_regression_trend(self, reports: List[RegressionReport]) -> str:
        """Analyze regression trend over time"""
        if len(reports) < 3:
            return "insufficient_data"

        # Calculate regression rates over time
        regression_rates = []
        for report in reports:
            if report.total_comparisons > 0:
                rate = (report.regressions_detected / report.total_comparisons) * 100
                regression_rates.append(rate)

        if len(regression_rates) < 3:
            return "insufficient_data"

        # Simple trend analysis
        recent_rate = regression_rates[-1]
        avg_rate = statistics.mean(regression_rates[:-1])

        if recent_rate > avg_rate * 1.5:
            return "worsening"
        elif recent_rate < avg_rate * 0.7:
            return "improving"
        else:
            return "stable"

# Example usage
async def test_baseline_comparator():
    """Test the baseline comparator"""
    comparator = BaselineComparator(":memory:")

    # Establish baseline
    baseline_metrics = {
        "response_time": {
            "values": [100, 120, 110, 105, 115, 95, 125, 108, 112, 98] * 3,
            "endpoint": "/api/test"
        },
        "error_rate": {
            "values": [0.1, 0.2, 0.15, 0.1, 0.05, 0.3, 0.1, 0.2] * 3,
            "endpoint": "/api/test"
        }
    }

    test_conditions = {
        "environment": "staging",
        "load_level": "medium",
        "duration": "30 minutes"
    }

    success = await comparator.establish_baseline("test_api", baseline_metrics, test_conditions)
    print(f"Baseline established: {success}")

    # Compare with current metrics
    current_metrics = {
        "response_time": {
            "current_value": 150,  # 25% regression
            "endpoint": "/api/test"
        },
        "error_rate": {
            "current_value": 0.4,  # 100% regression
            "endpoint": "/api/test"
        }
    }

    report = await comparator.compare_with_baseline("test_api", current_metrics)
    if report:
        print("\nComparison Report:")
        print(json.dumps(asdict(report), indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(test_baseline_comparator())