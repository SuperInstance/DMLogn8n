#!/usr/bin/env python3
"""
Quality Assurance Orchestrator
Main orchestrator for all code quality and refactoring tools.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import subprocess


# Import all quality assurance modules
try:
    from code_analyzer import CodeAnalyzer
    from refactoring_engine import RefactoringEngine
    from dependency_manager import DependencyManager
    from technical_debt_tracker import TechnicalDebtTracker
    from code_reviewer import CodeReviewer
    from architecture_analyzer import ArchitectureAnalyzer
    from performance_profiler import PerformanceProfiler
    from documentation_generator import DocumentationGenerator
except ImportError as e:
    print(f"Error importing quality modules: {e}")
    print("Make sure all quality modules are in the same directory")
    sys.exit(1)


@dataclass
class QualityReport:
    """Comprehensive quality report."""
    project_name: str
    analysis_timestamp: str
    overall_quality_score: float
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    metrics: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    detailed_reports: Dict[str, str]


class QualityOrchestrator:
    """Main orchestrator for all quality assurance tools."""

    def __init__(self, project_root: str, output_dir: str = None):
        self.project_root = Path(project_root)
        self.output_dir = Path(output_dir) if output_dir else self.project_root / 'quality_reports'
        self.output_dir.mkdir(exist_ok=True)

        # Initialize all quality tools
        self.code_analyzer = CodeAnalyzer(str(self.project_root))
        self.refactoring_engine = RefactoringEngine(str(self.project_root))
        self.dependency_manager = DependencyManager(str(self.project_root))
        self.debt_tracker = TechnicalDebtTracker(str(self.project_root))
        self.code_reviewer = CodeReviewer(str(self.project_root))
        self.architecture_analyzer = ArchitectureAnalyzer(str(self.project_root))
        self.performance_profiler = PerformanceProfiler(str(self.project_root))
        self.documentation_generator = DocumentationGenerator(str(self.project_root))

        self.reports_dir = self.output_dir / 'detailed_reports'
        self.reports_dir.mkdir(exist_ok=True)

    def run_full_analysis(self) -> QualityReport:
        """Run comprehensive quality analysis."""
        print("🚀 Starting comprehensive code quality analysis...")
        print(f"📁 Project: {self.project_root}")
        print(f"📊 Output: {self.output_dir}")
        print()

        start_time = time.time()

        # Run all analyses
        results = {}

        print("1️⃣ Running code analysis...")
        results['code_analysis'] = self._run_code_analysis()

        print("2️⃣ Analyzing refactoring opportunities...")
        results['refactoring'] = self._run_refactoring_analysis()

        print("3️⃣ Analyzing dependencies...")
        results['dependencies'] = self._run_dependency_analysis()

        print("4️⃣ Tracking technical debt...")
        results['technical_debt'] = self._run_technical_debt_analysis()

        print("5️⃣ Performing code review...")
        results['code_review'] = self._run_code_review()

        print("6️⃣ Analyzing architecture...")
        results['architecture'] = self._run_architecture_analysis()

        print("7️⃣ Profiling performance...")
        results['performance'] = self._run_performance_analysis()

        print("8️⃣ Generating documentation...")
        results['documentation'] = self._generate_documentation()

        end_time = time.time()
        analysis_time = end_time - start_time

        print(f"\n✅ Analysis completed in {analysis_time:.2f} seconds")

        # Generate comprehensive report
        quality_report = self._generate_quality_report(results, analysis_time)

        # Save reports
        self._save_reports(quality_report, results)

        return quality_report

    def _run_code_analysis(self) -> Dict[str, Any]:
        """Run code analysis."""
        try:
            return self.code_analyzer.analyze_project()
        except Exception as e:
            print(f"❌ Code analysis failed: {e}")
            return {'error': str(e)}

    def _run_refactoring_analysis(self) -> Dict[str, Any]:
        """Run refactoring analysis."""
        try:
            return self.refactoring_engine.analyze_project()
        except Exception as e:
            print(f"❌ Refactoring analysis failed: {e}")
            return {'error': str(e)}

    def _run_dependency_analysis(self) -> Dict[str, Any]:
        """Run dependency analysis."""
        try:
            return self.dependency_manager.analyze_project()
        except Exception as e:
            print(f"❌ Dependency analysis failed: {e}")
            return {'error': str(e)}

    def _run_technical_debt_analysis(self) -> Dict[str, Any]:
        """Run technical debt analysis."""
        try:
            return self.debt_tracker.analyze_project()
        except Exception as e:
            print(f"❌ Technical debt analysis failed: {e}")
            return {'error': str(e)}

    def _run_code_review(self) -> Dict[str, Any]:
        """Run code review."""
        try:
            return self.code_reviewer.analyze_project()
        except Exception as e:
            print(f"❌ Code review failed: {e}")
            return {'error': str(e)}

    def _run_architecture_analysis(self) -> Dict[str, Any]:
        """Run architecture analysis."""
        try:
            return self.architecture_analyzer.analyze_architecture()
        except Exception as e:
            print(f"❌ Architecture analysis failed: {e}")
            return {'error': str(e)}

    def _run_performance_analysis(self) -> Dict[str, Any]:
        """Run performance analysis."""
        try:
            return self.performance_profiler.analyze_project()
        except Exception as e:
            print(f"❌ Performance analysis failed: {e}")
            return {'error': str(e)}

    def _generate_documentation(self) -> Dict[str, Any]:
        """Generate documentation."""
        try:
            docs_dir = self.output_dir / 'generated_docs'
            return self.documentation_generator.generate_documentation(str(docs_dir))
        except Exception as e:
            print(f"❌ Documentation generation failed: {e}")
            return {'error': str(e)}

    def _generate_quality_report(self, results: Dict[str, Any], analysis_time: float) -> QualityReport:
        """Generate comprehensive quality report."""
        print("📊 Generating quality report...")

        # Calculate overall quality score
        scores = []

        if 'project_summary' in results.get('code_analysis', {}):
            summary = results['code_analysis']['project_summary']
            if 'avg_maintainability' in summary:
                scores.append(summary['avg_maintainability'])

        if 'review_summary' in results.get('code_review', {}):
            review_score = results['code_review']['review_summary']['review_score']
            scores.append(review_score)

        if 'architectural_metrics' in results.get('architecture', {}):
            arch_metrics = results['architecture']['architectural_metrics']
            # Convert architectural metrics to a score (simplified)
            arch_score = max(0, 100 - arch_metrics['coupling_between_objects'] * 10)
            scores.append(arch_score)

        if 'performance_summary' in results.get('performance', {}):
            perf_score = results['performance']['performance_summary']['overall_performance_score']
            scores.append(perf_score)

        overall_score = sum(scores) / len(scores) if scores else 0

        # Count issues by severity
        issue_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        total_issues = 0

        for result_name, result_data in results.items():
            if isinstance(result_data, dict) and 'debt_summary' in result_data:
                # Technical debt issues
                if 'debt_by_severity' in result_data['debt_summary']:
                    for severity, count in result_data['debt_summary']['debt_by_severity'].items():
                        if severity in issue_counts:
                            issue_counts[severity] += count
                            total_issues += count

            if isinstance(result_data, dict) and 'review_summary' in result_data:
                # Code review issues
                if 'issues_by_severity' in result_data['review_summary']:
                    for severity, count in result_data['review_summary']['issues_by_severity'].items():
                        if severity in issue_counts:
                            issue_counts[severity] += count
                            total_issues += count

        # Generate metrics
        metrics = {
            'analysis_time_seconds': analysis_time,
            'files_analyzed': 0,
            'lines_of_code': 0,
            'maintainability_index': 0,
            'test_coverage': 0,
            'cyclomatic_complexity': 0,
            'technical_debt_hours': 0
        }

        # Extract metrics from results
        if 'project_summary' in results.get('code_analysis', {}):
            summary = results['code_analysis']['project_summary']
            metrics['files_analyzed'] = summary.get('files_analyzed', 0)
            metrics['lines_of_code'] = summary.get('total_lines', 0)
            metrics['maintainability_index'] = summary.get('avg_maintainability', 0)

        if 'debt_summary' in results.get('technical_debt', {}):
            debt_summary = results['technical_debt']['debt_summary']
            metrics['technical_debt_hours'] = debt_summary.get('total_estimated_effort', 0)

        # Generate recommendations
        recommendations = self._generate_recommendations(results, issue_counts)

        return QualityReport(
            project_name=self.project_root.name,
            analysis_timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
            overall_quality_score=overall_score,
            total_issues=total_issues,
            critical_issues=issue_counts['critical'],
            high_issues=issue_counts['high'],
            medium_issues=issue_counts['medium'],
            low_issues=issue_counts['low'],
            metrics=metrics,
            recommendations=recommendations,
            detailed_reports={}
        )

    def _generate_recommendations(self, results: Dict[str, Any], issue_counts: Dict[str, int]) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations."""
        recommendations = []

        # Critical issues first
        if issue_counts['critical'] > 0:
            recommendations.append({
                'priority': 'critical',
                'category': 'immediate_action',
                'title': 'Address Critical Issues',
                'description': f'Found {issue_counts["critical"]} critical issues that need immediate attention',
                'action': 'Review and fix critical issues before proceeding with other work',
                'estimated_effort': '1-3 days',
                'impact': 'high'
            })

        # High priority issues
        if issue_counts['high'] > 0:
            recommendations.append({
                'priority': 'high',
                'category': 'quality_improvement',
                'title': 'Fix High Priority Issues',
                'description': f'Found {issue_counts["high"]} high priority issues',
                'action': 'Address high priority issues in the next development cycle',
                'estimated_effort': '2-5 days',
                'impact': 'high'
            })

        # Technical debt
        if 'debt_summary' in results.get('technical_debt', {}):
            debt_summary = results['technical_debt']['debt_summary']
            if debt_summary.get('total_estimated_effort', 0) > 40:  # More than 1 week of work
                recommendations.append({
                    'priority': 'medium',
                    'category': 'technical_debt',
                    'title': 'Manage Technical Debt',
                    'description': f'Significant technical debt detected: {debt_summary["total_estimated_effort"]:.1f} hours',
                    'action': 'Create a technical debt reduction plan and allocate regular time for refactoring',
                    'estimated_effort': f'{debt_summary["total_estimated_effort"]:.1f} hours',
                    'impact': 'medium'
                })

        # Architecture improvements
        if 'architecture_summary' in results.get('architecture', {}):
            arch_summary = results['architecture']['architecture_summary']
            if arch_summary.get('violations_count', 0) > 5:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'architecture',
                    'title': 'Improve Architecture',
                    'description': f'Found {arch_summary["violations_count"]} architectural violations',
                    'action': 'Review and improve architectural design patterns',
                    'estimated_effort': '3-7 days',
                    'impact': 'medium'
                })

        # Performance optimizations
        if 'performance_summary' in results.get('performance', {}):
            perf_summary = results['performance']['performance_summary']
            if perf_summary.get('overall_performance_score', 100) < 70:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'performance',
                    'title': 'Optimize Performance',
                    'description': f'Performance score: {perf_summary["overall_performance_score"]:.1f}/100',
                    'action': 'Address performance bottlenecks and optimization opportunities',
                    'estimated_effort': '2-4 days',
                    'impact': 'medium'
                })

        # Documentation improvements
        if 'review_summary' in results.get('code_review', {}):
            review_summary = results['code_review']['review_summary']
            doc_issues = review_summary['issues_by_category'].get('documentation', 0)
            if doc_issues > 3:
                recommendations.append({
                    'priority': 'low',
                    'category': 'documentation',
                    'title': 'Improve Documentation',
                    'description': f'Found {doc_issues} documentation-related issues',
                    'action': 'Add missing docstrings and improve code documentation',
                    'estimated_effort': '1-2 days',
                    'impact': 'low'
                })

        return recommendations

    def _save_reports(self, quality_report: QualityReport, results: Dict[str, Any]):
        """Save all reports to files."""
        print("💾 Saving reports...")

        # Save main quality report
        main_report_path = self.output_dir / 'quality_report.json'
        with open(main_report_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(quality_report), f, indent=2, default=str)

        # Save detailed reports
        for analysis_type, result_data in results.items():
            if 'error' not in result_data:
                report_path = self.reports_dir / f'{analysis_type}_report.json'
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(result_data, f, indent=2, default=str)
                quality_report.detailed_reports[analysis_type] = str(report_path)

        # Save summary report
        summary_path = self.output_dir / 'quality_summary.md'
        self._save_markdown_summary(quality_report, summary_path)

        print(f"✅ Reports saved to {self.output_dir}")
        print(f"📄 Main report: {main_report_path}")
        print(f"📋 Summary: {summary_path}")
        print(f"📁 Detailed reports: {self.reports_dir}")

    def _save_markdown_summary(self, report: QualityReport, output_path: Path):
        """Save markdown summary report."""
        content = f"""# Code Quality Report

## Project: {report.project_name}
**Generated:** {report.analysis_timestamp}

## Overall Quality Score: {report.overall_quality_score:.1f}/100

---

## Executive Summary

- **Total Issues:** {report.total_issues}
- **Critical Issues:** {report.critical_issues} 🔴
- **High Priority Issues:** {report.high_issues} 🟠
- **Medium Priority Issues:** {report.medium_issues} 🟡
- **Low Priority Issues:** {report.low_issues} 🟢

## Key Metrics

| Metric | Value |
|--------|-------|
| Files Analyzed | {report.metrics['files_analyzed']} |
| Lines of Code | {report.metrics['lines_of_code']:,} |
| Maintainability Index | {report.metrics['maintainability_index']:.1f} |
| Technical Debt (hours) | {report.metrics['technical_debt_hours']:.1f} |
| Analysis Time | {report.metrics['analysis_time_seconds']:.1f}s |

## Recommendations

{self._format_recommendations(report.recommendations)}

## Detailed Reports

"""

        for analysis_type, report_path in report.detailed_reports.items():
            content += f"- [{analysis_type.title()} Report]({report_path.relative_to(self.output_dir)})\n"

        content += """
---

## Quality Assessment Legend

- 🔴 **Critical Issues:** Must be fixed immediately (security, crashes, data loss)
- 🟠 **High Priority:** Should be fixed soon (performance, maintainability)
- 🟡 **Medium Priority:** Can be addressed in next cycle (code quality, documentation)
- 🟢 **Low Priority:** Nice to have improvements (style, minor issues)

---

*This report was generated by the Quality Assurance Orchestrator*
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _format_recommendations(self, recommendations: List[Dict[str, Any]]) -> str:
        """Format recommendations as markdown."""
        if not recommendations:
            return "No specific recommendations at this time."

        content = ""
        for rec in recommendations:
            priority_emoji = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢'
            }.get(rec['priority'], '⚪')

            content += f"""
### {priority_emoji} {rec['title']} ({rec['priority'].upper()})

**Description:** {rec['description']}

**Action:** {rec['action']}

**Estimated Effort:** {rec['estimated_effort']}

**Impact:** {rec['impact']}

---
"""

        return content

    def run_specific_analysis(self, analysis_types: List[str]) -> Dict[str, Any]:
        """Run specific types of analysis."""
        print(f"🎯 Running specific analyses: {', '.join(analysis_types)}")

        results = {}
        available_analyses = {
            'code': self._run_code_analysis,
            'refactor': self._run_refactoring_analysis,
            'deps': self._run_dependency_analysis,
            'debt': self._run_technical_debt_analysis,
            'review': self._run_code_review,
            'arch': self._run_architecture_analysis,
            'perf': self._run_performance_analysis,
            'docs': self._generate_documentation
        }

        for analysis_type in analysis_types:
            if analysis_type in available_analyses:
                print(f"Running {analysis_type} analysis...")
                results[analysis_type] = available_analyses[analysis_type]()
            else:
                print(f"⚠️ Unknown analysis type: {analysis_type}")

        return results


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Code Quality Assurance Orchestrator')
    parser.add_argument('project_path', nargs='?', default='.',
                       help='Path to the project to analyze (default: current directory)')
    parser.add_argument('--output', '-o', default=None,
                       help='Output directory for reports (default: ./quality_reports)')
    parser.add_argument('--analyses', '-a', nargs='+',
                       choices=['code', 'refactor', 'deps', 'debt', 'review', 'arch', 'perf', 'docs', 'all'],
                       default=['all'],
                       help='Specific analyses to run (default: all)')
    parser.add_argument('--summary', '-s', action='store_true',
                       help='Print summary to console')

    args = parser.parse_args()

    # Convert relative path to absolute
    project_path = Path(args.project_path).resolve()

    if not project_path.exists():
        print(f"❌ Project path does not exist: {project_path}")
        sys.exit(1)

    # Initialize orchestrator
    orchestrator = QualityOrchestrator(str(project_path), args.output)

    try:
        if 'all' in args.analyses:
            # Run full analysis
            quality_report = orchestrator.run_full_analysis()

            if args.summary:
                print("\n" + "="*60)
                print("📊 QUALITY ANALYSIS SUMMARY")
                print("="*60)
                print(f"📁 Project: {quality_report.project_name}")
                print(f"🎯 Overall Score: {quality_report.overall_quality_score:.1f}/100")
                print(f"🔢 Total Issues: {quality_report.total_issues}")
                print(f"🔴 Critical: {quality_report.critical_issues}")
                print(f"🟠 High: {quality_report.high_issues}")
                print(f"🟡 Medium: {quality_report.medium_issues}")
                print(f"🟢 Low: {quality_report.low_issues}")
                print("\n🎯 Top Recommendations:")
                for rec in quality_report.recommendations[:3]:
                    print(f"  • {rec['title']}")
                print(f"\n📁 Reports saved to: {orchestrator.output_dir}")
        else:
            # Run specific analyses
            results = orchestrator.run_specific_analysis(args.analyses)
            print(f"\n✅ Completed {len(results)} analyses")
            print(f"📁 Results saved to: {orchestrator.output_dir}")

    except KeyboardInterrupt:
        print("\n⚠️ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()