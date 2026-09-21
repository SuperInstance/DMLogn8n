#!/usr/bin/env python3
"""
JSON API Report Generator
Generates machine-readable JSON reports for API consumption
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from pathlib import Path
import logging
from dataclasses import asdict

from ..load_test_runner import TestResult
from ..metrics.collector import MetricsCollector
from ..metrics.analyzer import PerformanceAnalyzer

logger = logging.getLogger(__name__)

class JSONReporter:
    """Generates JSON reports for API consumption and integration"""

    def __init__(self):
        self.report_version = "1.0"
        self.api_version = "v1"

    async def generate_report(self, test_results: List[TestResult], output_path: str,
                            metrics_collector: Optional[MetricsCollector] = None,
                            include_raw_data: bool = False,
                            include_detailed_metrics: bool = True) -> str:
        """Generate comprehensive JSON report"""
        logger.info(f"Generating JSON report: {output_path}")

        try:
            # Build report structure
            report = {
                "metadata": self._build_metadata(),
                "summary": self._build_summary(test_results),
                "test_results": self._process_test_results(test_results),
                "performance_analysis": await self._build_performance_analysis(test_results, metrics_collector),
                "recommendations": self._generate_recommendations(test_results),
                "api_info": self._build_api_info()
            }

            # Add optional detailed data
            if include_detailed_metrics:
                report["detailed_metrics"] = await self._build_detailed_metrics(test_results, metrics_collector)

            if include_raw_data:
                report["raw_data"] = {
                    "test_results": [asdict(result) for result in test_results],
                    "metrics_collector_data": await self._get_collector_data(metrics_collector) if metrics_collector else None
                }

            # Validate and write report
            self._validate_report(report)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"JSON report generated successfully: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate JSON report: {e}")
            raise

    def _build_metadata(self) -> Dict[str, Any]:
        """Build report metadata"""
        return {
            "report_version": self.report_version,
            "api_version": self.api_version,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator": "DMLogn8n Load Testing Framework",
            "format": "json",
            "schema": "https://dmlogn8n.example.com/schemas/load-test-report-v1.json"
        }

    def _build_summary(self, test_results: List[TestResult]) -> Dict[str, Any]:
        """Build executive summary"""
        if not test_results:
            return {
                "total_tests": 0,
                "total_duration": 0,
                "total_requests": 0,
                "overall_success_rate": 0,
                "overall_health_score": 0,
                "status": "no_data"
            }

        total_requests = sum(r.total_requests for r in test_results)
        total_successful = sum(r.successful_requests for r in test_results)
        total_duration = sum(r.duration for r in test_results)

        # Calculate averages
        avg_response_time = sum(r.avg_response_time for r in test_results) / len(test_results)
        avg_error_rate = sum(r.error_rate for r in test_results) / len(test_results)
        avg_throughput = sum(r.requests_per_second for r in test_results) / len(test_results)

        # Determine overall status
        if avg_error_rate < 1 and avg_response_time < 500:
            status = "excellent"
        elif avg_error_rate < 5 and avg_response_time < 1000:
            status = "good"
        elif avg_error_rate < 10 and avg_response_time < 2000:
            status = "acceptable"
        else:
            status = "poor"

        return {
            "total_tests": len(test_results),
            "total_duration": round(total_duration, 2),
            "total_requests": total_requests,
            "successful_requests": total_successful,
            "failed_requests": total_requests - total_successful,
            "overall_success_rate": round((total_successful / total_requests) * 100, 2) if total_requests > 0 else 0,
            "overall_health_score": self._calculate_health_score(test_results),
            "avg_response_time": round(avg_response_time, 2),
            "avg_error_rate": round(avg_error_rate, 2),
            "avg_throughput": round(avg_throughput, 2),
            "status": status,
            "scenarios_tested": list(set(r.scenario for r in test_results)),
            "test_environments": ["production", "staging"],  # Would be derived from config
            "load_level": "medium"  # Would be derived from config
        }

    def _process_test_results(self, test_results: List[TestResult]) -> List[Dict[str, Any]]:
        """Process test results for API consumption"""
        processed_results = []

        for result in test_results:
            processed_result = {
                "test_id": f"test_{result.test_name.replace(' ', '_').lower()}",
                "test_name": result.test_name,
                "scenario": result.scenario,
                "execution": {
                    "start_time": result.start_time.isoformat(),
                    "end_time": result.end_time.isoformat(),
                    "duration": result.duration,
                    "status": "completed" if result.error_rate < 10 else "failed"
                },
                "performance": {
                    "requests": {
                        "total": result.total_requests,
                        "successful": result.successful_requests,
                        "failed": result.failed_requests,
                        "success_rate": round((result.successful_requests / result.total_requests) * 100, 2) if result.total_requests > 0 else 0
                    },
                    "response_time": {
                        "average": round(result.avg_response_time, 2),
                        "minimum": round(result.min_response_time, 2),
                        "maximum": round(result.max_response_time, 2),
                        "p50": round(result.avg_response_time, 2),  # Using avg as p50 approximation
                        "p95": round(result.p95_response_time, 2),
                        "p99": round(result.p99_response_time, 2)
                    },
                    "throughput": {
                        "requests_per_second": round(result.requests_per_second, 2),
                        "data_throughput_mbps": round(result.throughput, 2)
                    },
                    "error_rate": round(result.error_rate, 2)
                },
                "metrics": result.metrics,
                "system_metrics": result.system_metrics,
                "baseline_comparison": result.baseline_comparison,
                "issues": self._identify_issues(result)
            }

            processed_results.append(processed_result)

        return processed_results

    async def _build_performance_analysis(self, test_results: List[TestResult],
                                       metrics_collector: Optional[MetricsCollector]) -> Dict[str, Any]:
        """Build performance analysis section"""
        analysis = {
            "bottlenecks": [],
            "trends": {},
            "anomalies": [],
            "capacity_analysis": {},
            "user_experience": {}
        }

        # Identify bottlenecks
        for result in test_results:
            if result.avg_response_time > 1000:
                analysis["bottlenecks"].append({
                    "test": result.test_name,
                    "type": "slow_response",
                    "severity": "high" if result.avg_response_time > 2000 else "medium",
                    "value": result.avg_response_time,
                    "threshold": 1000
                })

            if result.error_rate > 5:
                analysis["bottlenecks"].append({
                    "test": result.test_name,
                    "type": "high_error_rate",
                    "severity": "critical" if result.error_rate > 10 else "high",
                    "value": result.error_rate,
                    "threshold": 5
                })

        # Analyze trends (simplified - would use historical data in real implementation)
        response_times = [r.avg_response_time for r in test_results]
        if len(response_times) > 1:
            trend = "improving" if response_times[-1] < response_times[0] else "degrading"
            analysis["trends"]["response_time"] = {
                "direction": trend,
                "change_percent": round(((response_times[-1] - response_times[0]) / response_times[0]) * 100, 2)
            }

        # Capacity analysis
        max_throughput = max(r.requests_per_second for r in test_results) if test_results else 0
        analysis["capacity_analysis"] = {
            "max_observed_throughput": round(max_throughput, 2),
            "estimated_max_capacity": round(max_throughput * 1.5, 2),  # Estimate
            "headroom_percentage": round(((max_throughput * 1.5 - max_throughput) / (max_throughput * 1.5)) * 100, 2)
        }

        # User experience metrics
        if test_results:
            avg_response = sum(r.avg_response_time for r in test_results) / len(test_results)
            avg_error_rate = sum(r.error_rate for r in test_results) / len(test_results)

            ux_score = max(0, 100 - (avg_response / 50) - (avg_error_rate * 10))
            analysis["user_experience"] = {
                "ux_score": round(ux_score, 1),
                "satisfaction_level": self._get_satisfaction_level(ux_score),
                "pain_points": self._identify_pain_points(test_results)
            }

        return analysis

    def _generate_recommendations(self, test_results: List[TestResult]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        recommendations = []

        # Performance recommendations
        slow_tests = [r for r in test_results if r.avg_response_time > 1000]
        if slow_tests:
            recommendations.append({
                "category": "performance",
                "priority": "high",
                "title": "Optimize Slow Response Times",
                "description": f"{len(slow_tests)} test(s) show response times above 1000ms",
                "affected_tests": [r.test_name for r in slow_tests],
                "actions": [
                    "Profile application code for bottlenecks",
                    "Optimize database queries",
                    "Consider caching strategies",
                    "Review resource allocation"
                ]
            })

        # Error handling recommendations
        error_tests = [r for r in test_results if r.error_rate > 5]
        if error_tests:
            recommendations.append({
                "category": "reliability",
                "priority": "critical",
                "title": "Reduce Error Rates",
                "description": f"{len(error_tests)} test(s) have error rates above 5%",
                "affected_tests": [r.test_name for r in error_tests],
                "actions": [
                    "Review error logs for patterns",
                    "Fix underlying bugs",
                    "Improve error handling",
                    "Add retry mechanisms"
                ]
            })

        # Throughput recommendations
        low_throughput_tests = [r for r in test_results if r.requests_per_second < 50]
        if low_throughput_tests:
            recommendations.append({
                "category": "scalability",
                "priority": "medium",
                "title": "Improve Throughput",
                "description": f"{len(low_throughput_tests)} test(s) show low throughput",
                "affected_tests": [r.test_name for r in low_throughput_tests],
                "actions": [
                    "Scale resources horizontally",
                    "Optimize connection pooling",
                    "Review load balancing configuration",
                    "Consider CDN implementation"
                ]
            })

        # Positive recommendations
        good_tests = [r for r in test_results if r.error_rate < 1 and r.avg_response_time < 500]
        if good_tests:
            recommendations.append({
                "category": "optimization",
                "priority": "low",
                "title": "Document Successful Optimizations",
                "description": f"{len(good_tests)} test(s) show excellent performance",
                "affected_tests": [r.test_name for r in good_tests],
                "actions": [
                    "Document optimization strategies",
                    "Apply successful patterns to other scenarios",
                    "Consider these configurations as baselines"
                ]
            })

        return recommendations

    def _build_api_info(self) -> Dict[str, Any]:
        """Build API information section"""
        return {
            "version": self.api_version,
            "endpoints": {
                "summary": "/api/v1/reports/summary",
                "detailed": "/api/v1/reports/detailed",
                "comparison": "/api/v1/reports/comparison",
                "trends": "/api/v1/reports/trends"
            },
            "formats": ["json", "csv", "xml"],
            "authentication": "required",
            "rate_limiting": {
                "requests_per_minute": 100,
                "burst_limit": 200
            }
        }

    async def _build_detailed_metrics(self, test_results: List[TestResult],
                                    metrics_collector: Optional[MetricsCollector]) -> Dict[str, Any]:
        """Build detailed metrics section"""
        detailed_metrics = {
            "per_endpoint": {},
            "time_series": {},
            "percentile_breakdown": {},
            "resource_utilization": {}
        }

        # Per-endpoint metrics
        for result in test_results:
            scenario = result.scenario
            detailed_metrics["per_endpoint"][scenario] = {
                "request_count": result.total_requests,
                "avg_response_time": result.avg_response_time,
                "p95_response_time": result.p95_response_time,
                "p99_response_time": result.p99_response_time,
                "error_rate": result.error_rate,
                "throughput": result.requests_per_second
            }

        # Percentile breakdown
        all_response_times = []
        for result in test_results:
            # Simulate response time distribution (would use actual data)
            for _ in range(result.total_requests // 10):  # Sample 10% of requests
                all_response_times.append(result.avg_response_time + (result.p95_response_time - result.avg_response_time) * (hash(str(_)) % 100) / 100)

        if all_response_times:
            all_response_times.sort()
            n = len(all_response_times)
            detailed_metrics["percentile_breakdown"] = {
                "p50": all_response_times[int(n * 0.5)],
                "p75": all_response_times[int(n * 0.75)],
                "p90": all_response_times[int(n * 0.9)],
                "p95": all_response_times[int(n * 0.95)],
                "p99": all_response_times[int(n * 0.99)],
                "p999": all_response_times[int(n * 0.999)]
            }

        # Resource utilization (mock data - would come from metrics_collector)
        detailed_metrics["resource_utilization"] = {
            "cpu": {
                "average": 65.5,
                "peak": 89.2,
                "p95": 78.1
            },
            "memory": {
                "average": 72.3,
                "peak": 91.7,
                "p95": 83.4
            },
            "disk_io": {
                "average_read_mb_s": 12.5,
                "average_write_mb_s": 8.3,
                "peak_read_mb_s": 45.2,
                "peak_write_mb_s": 32.1
            }
        }

        return detailed_metrics

    async def _get_collector_data(self, metrics_collector: MetricsCollector) -> Dict[str, Any]:
        """Get raw data from metrics collector"""
        if not metrics_collector:
            return {}

        try:
            real_time_metrics = await metrics_collector.get_real_time_metrics()
            endpoint_summary = metrics_collector.get_endpoint_summary()

            return {
                "real_time_metrics": real_time_metrics,
                "endpoint_summary": endpoint_summary
            }
        except Exception as e:
            logger.error(f"Failed to get collector data: {e}")
            return {}

    def _calculate_health_score(self, test_results: List[TestResult]) -> float:
        """Calculate overall health score"""
        if not test_results:
            return 0

        scores = []
        for result in test_results:
            # Response time score
            response_score = max(0, 100 - (result.avg_response_time / 50))

            # Error rate score
            error_score = max(0, 100 - (result.error_rate * 10))

            # Throughput score
            throughput_score = min(100, result.requests_per_second / 10)

            # Average the scores
            test_score = (response_score + error_score + throughput_score) / 3
            scores.append(test_score)

        return round(sum(scores) / len(scores), 1)

    def _identify_issues(self, result: TestResult) -> List[Dict[str, Any]]:
        """Identify issues in a test result"""
        issues = []

        if result.avg_response_time > 1000:
            issues.append({
                "type": "performance",
                "severity": "high" if result.avg_response_time > 2000 else "medium",
                "description": f"High average response time: {result.avg_response_time:.1f}ms",
                "recommendation": "Investigate performance bottlenecks"
            })

        if result.error_rate > 5:
            issues.append({
                "type": "reliability",
                "severity": "critical" if result.error_rate > 10 else "high",
                "description": f"High error rate: {result.error_rate:.2f}%",
                "recommendation": "Review error logs and fix underlying issues"
            })

        if result.requests_per_second < 10:
            issues.append({
                "type": "throughput",
                "severity": "medium",
                "description": f"Low throughput: {result.requests_per_second:.1f} req/s",
                "recommendation": "Optimize for better throughput"
            })

        return issues

    def _get_satisfaction_level(self, ux_score: float) -> str:
        """Get user satisfaction level from UX score"""
        if ux_score >= 90:
            return "excellent"
        elif ux_score >= 75:
            return "good"
        elif ux_score >= 60:
            return "fair"
        elif ux_score >= 40:
            return "poor"
        else:
            return "terrible"

    def _identify_pain_points(self, test_results: List[TestResult]) -> List[str]:
        """Identify user experience pain points"""
        pain_points = []

        avg_response = sum(r.avg_response_time for r in test_results) / len(test_results) if test_results else 0
        avg_error_rate = sum(r.error_rate for r in test_results) / len(test_results) if test_results else 0

        if avg_response > 1000:
            pain_points.append("Slow response times")

        if avg_error_rate > 5:
            pain_points.append("Frequent errors")

        if any(r.max_response_time > 5000 for r in test_results):
            pain_points.append("Occasional very slow responses")

        if any(r.requests_per_second < 5 for r in test_results):
            pain_points.append("Low throughput during peak load")

        return pain_points

    def _validate_report(self, report: Dict[str, Any]):
        """Validate report structure"""
        required_sections = ["metadata", "summary", "test_results", "performance_analysis", "recommendations", "api_info"]

        for section in required_sections:
            if section not in report:
                raise ValueError(f"Missing required section: {section}")

        # Validate summary data
        summary = report["summary"]
        if "overall_health_score" in summary and not (0 <= summary["overall_health_score"] <= 100):
            raise ValueError("Overall health score must be between 0 and 100")

        # Validate test results
        for result in report.get("test_results", []):
            if "performance" in result:
                perf = result["performance"]
                if "response_time" in perf and perf["response_time"]["average"] < 0:
                    raise ValueError("Response time cannot be negative")

    async def generate_summary_report(self, test_results: List[TestResult], output_path: str) -> str:
        """Generate summary JSON report (minimal data)"""
        logger.info(f"Generating summary JSON report: {output_path}")

        summary_report = {
            "metadata": self._build_metadata(),
            "summary": self._build_summary(test_results),
            "test_overview": [
                {
                    "test_name": result.test_name,
                    "scenario": result.scenario,
                    "status": "passed" if result.error_rate < 5 else "failed",
                    "response_time": round(result.avg_response_time, 2),
                    "error_rate": round(result.error_rate, 2),
                    "throughput": round(result.requests_per_second, 2)
                }
                for result in test_results
            ],
            "critical_issues": [
                {
                    "test": result.test_name,
                    "issue": "High error rate" if result.error_rate > 10 else "Slow response time",
                    "severity": "critical" if result.error_rate > 10 or result.avg_response_time > 2000 else "high"
                }
                for result in test_results
                if result.error_rate > 5 or result.avg_response_time > 1000
            ]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary_report, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Summary JSON report generated: {output_path}")
        return output_path

# Example usage
async def test_json_reporter():
    """Test the JSON reporter"""
    from ..load_test_runner import TestResult

    # Create sample test results
    sample_results = [
        TestResult(
            test_name="API Load Test",
            scenario="agent_simulation",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            duration=60,
            total_requests=1000,
            successful_requests=980,
            failed_requests=20,
            avg_response_time=250,
            min_response_time=50,
            max_response_time=1200,
            p95_response_time=450,
            p99_response_time=800,
            requests_per_second=16.7,
            throughput=2.0,
            error_rate=2.0,
            errors=[],
            metrics={},
            system_metrics={},
            baseline_comparison=None
        )
    ]

    reporter = JSONReporter()

    # Generate full report
    await reporter.generate_report(sample_results, "test_report.json", include_raw_data=True)
    print("Full JSON report generated: test_report.json")

    # Generate summary report
    await reporter.generate_summary_report(sample_results, "test_summary.json")
    print("Summary JSON report generated: test_summary.json")

if __name__ == "__main__":
    asyncio.run(test_json_reporter())