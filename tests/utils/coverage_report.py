#!/usr/bin/env python3
"""
Coverage Report Generator for DMLog

Generates detailed coverage reports including:
- Line and branch coverage metrics
- Coverage trends over time
- Uncovered code analysis
- Coverage badges and visualizations
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import xml.etree.ElementTree as ET
from datetime import datetime
import argparse


class CoverageReportGenerator:
    """Generate comprehensive coverage reports"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.coverage_file = project_root / "coverage.xml"
        self.htmlcov_dir = project_root / "htmlcov"
        self.reports_dir = project_root / "test_results"
        self.history_file = self.reports_dir / "coverage_history.json"

    def parse_coverage_xml(self) -> Dict[str, Any]:
        """Parse coverage.xml file"""
        if not self.coverage_file.exists():
            print(f"Coverage file not found: {self.coverage_file}")
            return {}

        try:
            tree = ET.parse(self.coverage_file)
            root = tree.getroot()

            coverage_data = {
                "timestamp": datetime.now().isoformat(),
                "total_lines": 0,
                "covered_lines": 0,
                "total_branches": 0,
                "covered_branches": 0,
                "line_coverage": 0.0,
                "branch_coverage": 0.0,
                "packages": {},
                "files": {}
            }

            # Parse overall coverage
            for source in root.findall(".//sources/source"):
                # This would need actual parsing based on coverage tool format
                pass

            # Parse package coverage
            for package in root.findall(".//package"):
                package_name = package.get("name", "unknown")
                line_rate = float(package.get("line-rate", 0))
                branch_rate = float(package.get("branch-rate", 0))
                lines_covered = int(package.get("lines-covered", 0))
                lines_valid = int(package.get("lines-valid", 0))
                branches_covered = int(package.get("branches-covered", 0))
                branches_valid = int(package.get("branches-valid", 0))

                coverage_data["packages"][package_name] = {
                    "line_coverage": line_rate * 100,
                    "branch_coverage": branch_rate * 100,
                    "lines_covered": lines_covered,
                    "lines_valid": lines_valid,
                    "branches_covered": branches_covered,
                    "branches_valid": branches_valid,
                    "files": {}
                }

                coverage_data["total_lines"] += lines_valid
                coverage_data["covered_lines"] += lines_covered
                coverage_data["total_branches"] += branches_valid
                coverage_data["covered_branches"] += branches_covered

                # Parse file coverage within package
                for class_elem in package.findall(".//class"):
                    filename = class_elem.get("filename", "unknown")
                    class_line_rate = float(class_elem.get("line-rate", 0))
                    class_branch_rate = float(class_elem.get("branch-rate", 0))

                    coverage_data["packages"][package_name]["files"][filename] = {
                        "line_coverage": class_line_rate * 100,
                        "branch_coverage": class_branch_rate * 100
                    }
                    coverage_data["files"][filename] = {
                        "package": package_name,
                        "line_coverage": class_line_rate * 100,
                        "branch_coverage": class_branch_rate * 100
                    }

            # Calculate overall coverage percentages
            if coverage_data["total_lines"] > 0:
                coverage_data["line_coverage"] = (coverage_data["covered_lines"] / coverage_data["total_lines"]) * 100
            if coverage_data["total_branches"] > 0:
                coverage_data["branch_coverage"] = (coverage_data["covered_branches"] / coverage_data["total_branches"]) * 100

            return coverage_data

        except Exception as e:
            print(f"Error parsing coverage file: {e}")
            return {}

    def generate_trend_analysis(self) -> Dict[str, Any]:
        """Analyze coverage trends over time"""
        if not self.history_file.exists():
            return {"trend": "no_data", "message": "No historical data available"}

        try:
            with open(self.history_file, 'r') as f:
                history = json.load(f)

            if len(history) < 2:
                return {"trend": "insufficient_data", "message": "Need at least 2 data points"}

            # Get last 10 entries
            recent_history = history[-10:]

            # Calculate trend
            line_coverages = [entry["line_coverage"] for entry in recent_history]
            branch_coverages = [entry["branch_coverage"] for entry in recent_history]

            # Simple trend calculation
            line_trend = line_coverages[-1] - line_coverages[0]
            branch_trend = branch_coverages[-1] - branch_coverages[0]

            trend_direction = "stable"
            if abs(line_trend) > 1.0:
                trend_direction = "improving" if line_trend > 0 else "declining"

            return {
                "trend": trend_direction,
                "line_trend": line_trend,
                "branch_trend": branch_trend,
                "data_points": len(recent_history),
                "recent_average": {
                    "line_coverage": sum(line_coverages) / len(line_coverages),
                    "branch_coverage": sum(branch_coverages) / len(branch_coverages)
                }
            }

        except Exception as e:
            return {"trend": "error", "message": str(e)}

    def identify_uncovered_critical_paths(self, coverage_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify uncovered critical code paths"""
        uncovered_critical = []

        # Define critical file patterns
        critical_patterns = [
            "authentication",
            "authorization",
            "security",
            "payment",
            "api",
            "database",
            "validation"
        ]

        for filename, file_data in coverage_data.get("files", {}).items():
            file_path = filename.lower()
            line_coverage = file_data.get("line_coverage", 0)

            # Check if file matches critical patterns
            is_critical = any(pattern in file_path for pattern in critical_patterns)

            if is_critical and line_coverage < 80:  # Less than 80% coverage
                uncovered_critical.append({
                    "file": filename,
                    "package": file_data.get("package", "unknown"),
                    "line_coverage": line_coverage,
                    "branch_coverage": file_data.get("branch_coverage", 0),
                    "priority": "high" if line_coverage < 50 else "medium"
                })

        # Sort by coverage (lowest first)
        uncovered_critical.sort(key=lambda x: x["line_coverage"])

        return uncovered_critical

    def save_coverage_history(self, coverage_data: Dict[str, Any]) -> None:
        """Save coverage data to history file"""
        history = []

        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
            except:
                history = []

        # Add new entry
        history.append({
            "timestamp": coverage_data["timestamp"],
            "line_coverage": coverage_data["line_coverage"],
            "branch_coverage": coverage_data["branch_coverage"],
            "total_lines": coverage_data["total_lines"],
            "covered_lines": coverage_data["covered_lines"]
        })

        # Keep only last 100 entries
        history = history[-100:]

        # Save history
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)

    def generate_coverage_badge(self, coverage_percentage: float) -> str:
        """Generate coverage badge SVG"""
        color = "#4c1" if coverage_percentage >= 90 else "#97ca00" if coverage_percentage >= 80 else "#dfb317" if coverage_percentage >= 60 else "#e05d44"

        badge_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="100" height="20">
            <linearGradient id="b" x2="0" y2="100%">
                <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
                <stop offset="1" stop-opacity=".1"/>
            </linearGradient>
            <mask id="a">
                <rect width="100" height="20" rx="3" fill="#fff"/>
            </mask>
            <g mask="url(#a)">
                <path fill="#555" d="M0 0h43v20H0z"/>
                <path fill="{color}" d="M43 0h57v20H43z"/>
                <path fill="url(#b)" d="M0 0h100v20H0z"/>
            </g>
            <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
                <text x="21.5" y="15" fill="#010101" fill-opacity=".3">coverage</text>
                <text x="21.5" y="14">coverage</text>
                <text x="71.5" y="15" fill="#010101" fill-opacity=".3">{coverage_percentage:.1f}%</text>
                <text x="71.5" y="14">{coverage_percentage:.1f}%</text>
            </g>
        </svg>"""

        return badge_svg

    def generate_detailed_report(self) -> Dict[str, Any]:
        """Generate comprehensive coverage report"""
        coverage_data = self.parse_coverage_xml()
        if not coverage_data:
            return {"error": "No coverage data available"}

        # Add trend analysis
        coverage_data["trend_analysis"] = self.generate_trend_analysis()

        # Identify uncovered critical paths
        coverage_data["uncovered_critical"] = self.identify_uncovered_critical_paths(coverage_data)

        # Generate recommendations
        coverage_data["recommendations"] = self._generate_recommendations(coverage_data)

        # Save to history
        self.save_coverage_history(coverage_data)

        return coverage_data

    def _generate_recommendations(self, coverage_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate coverage improvement recommendations"""
        recommendations = []

        # Overall coverage recommendations
        line_coverage = coverage_data.get("line_coverage", 0)
        branch_coverage = coverage_data.get("branch_coverage", 0)

        if line_coverage < 80:
            recommendations.append({
                "type": "overall",
                "priority": "high",
                "message": f"Overall line coverage is {line_coverage:.1f}%. Target is 80%+.",
                "action": "Focus on adding unit tests for uncovered code paths."
            })

        if branch_coverage < 70:
            recommendations.append({
                "type": "branch",
                "priority": "medium",
                "message": f"Branch coverage is {branch_coverage:.1f}%. Consider testing edge cases and conditional logic.",
                "action": "Add tests that cover different branches of conditional statements."
            })

        # Critical path recommendations
        uncovered_critical = coverage_data.get("uncovered_critical", [])
        if uncovered_critical:
            recommendations.append({
                "type": "critical_paths",
                "priority": "high",
                "message": f"{len(uncovered_critical)} critical files have low coverage.",
                "action": "Prioritize testing security, authentication, and API-related files.",
                "files": [item["file"] for item in uncovered_critical[:5]]
            })

        # Package-specific recommendations
        for package_name, package_data in coverage_data.get("packages", {}).items():
            if package_data["line_coverage"] < 60:
                recommendations.append({
                    "type": "package",
                    "priority": "medium",
                    "message": f"Package '{package_name}' has low coverage ({package_data['line_coverage']:.1f}%).",
                    "action": f"Add comprehensive tests for {package_name} module."
                })

        return recommendations

    def export_to_markdown(self, coverage_data: Dict[str, Any]) -> str:
        """Export coverage report to Markdown"""
        md = f"""# DMLog Coverage Report

Generated on: {coverage_data.get('timestamp', 'Unknown')}

## Summary

- **Line Coverage**: {coverage_data.get('line_coverage', 0):.1f}%
- **Branch Coverage**: {coverage_data.get('branch_coverage', 0):.1f}%
- **Total Lines**: {coverage_data.get('total_lines', 0)}
- **Covered Lines**: {coverage_data.get('covered_lines', 0)}

## Coverage Trend

{self._format_trend_markdown(coverage_data.get('trend_analysis', {}))}

## Package Coverage

| Package | Line Coverage | Branch Coverage |
|---------|---------------|-----------------|
"""

        for package_name, package_data in coverage_data.get('packages', {}).items():
            md += f"| {package_name} | {package_data['line_coverage']:.1f}% | {package_data['branch_coverage']:.1f}% |\n"

        # Add uncovered critical paths
        uncovered_critical = coverage_data.get('uncovered_critical', [])
        if uncovered_critical:
            md += f"""
## Uncovered Critical Paths

The following critical files have low test coverage and should be prioritized:

| File | Line Coverage | Priority |
|------|---------------|----------|
"""
            for item in uncovered_critical:
                md += f"| {item['file']} | {item['line_coverage']:.1f}% | {item['priority']} |\n"

        # Add recommendations
        recommendations = coverage_data.get('recommendations', [])
        if recommendations:
            md += "\n## Recommendations\n\n"
            for rec in recommendations:
                md += f"### {rec['type'].title()} (Priority: {rec['priority']})\n"
                md += f"**Issue**: {rec['message']}\n\n"
                md += f"**Action**: {rec['action']}\n\n"

        return md

    def _format_trend_markdown(self, trend_data: Dict[str, Any]) -> str:
        """Format trend analysis for Markdown"""
        if not trend_data or trend_data.get("trend") == "no_data":
            return "No historical data available."

        trend_emoji = {
            "improving": "📈",
            "declining": "📉",
            "stable": "➡️"
        }

        trend = trend_data.get("trend", "stable")
        emoji = trend_emoji.get(trend, "➡️")

        if trend in ["improving", "declining"]:
            return f"{emoji} Coverage is {trend} (change: {trend_data.get('line_trend', 0):+.1f}% line coverage)"
        else:
            return f"{emoji} Coverage is stable (average: {trend_data.get('recent_average', {}).get('line_coverage', 0):.1f}%)"

    def save_reports(self, coverage_data: Dict[str, Any]) -> None:
        """Save all coverage reports"""
        if not coverage_data:
            print("No coverage data to save")
            return

        # Save JSON report
        json_file = self.reports_dir / "coverage_report.json"
        with open(json_file, 'w') as f:
            json.dump(coverage_data, f, indent=2)
        print(f"JSON report saved: {json_file}")

        # Save Markdown report
        md_content = self.export_to_markdown(coverage_data)
        md_file = self.reports_dir / "coverage_report.md"
        with open(md_file, 'w') as f:
            f.write(md_content)
        print(f"Markdown report saved: {md_file}")

        # Save coverage badge
        badge_svg = self.generate_coverage_badge(coverage_data.get('line_coverage', 0))
        badge_file = self.reports_dir / "coverage_badge.svg"
        with open(badge_file, 'w') as f:
            f.write(badge_svg)
        print(f"Coverage badge saved: {badge_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Generate coverage reports for DMLog")
    parser.add_argument("--project-root", type=Path, help="Project root directory")
    parser.add_argument("--output-dir", type=Path, help="Output directory for reports")
    parser.add_argument("--format", choices=["json", "markdown", "all"], default="all", help="Report format")
    parser.add_argument("--badge-only", action="store_true", help="Generate only coverage badge")

    args = parser.parse_args()

    # Determine project root
    if args.project_root:
        project_root = args.project_root
    else:
        project_root = Path(__file__).parent.parent.parent

    # Override output directory if specified
    if args.output_dir:
        reports_dir = args.output_dir
    else:
        reports_dir = project_root / "test_results"

    # Create generator
    generator = CoverageReportGenerator(project_root)
    generator.reports_dir = reports_dir

    # Generate reports
    coverage_data = generator.generate_detailed_report()

    if not coverage_data:
        print("No coverage data found. Run tests with coverage first.")
        sys.exit(1)

    if args.badge_only:
        # Generate only badge
        badge_svg = generator.generate_coverage_badge(coverage_data.get('line_coverage', 0))
        badge_file = reports_dir / "coverage_badge.svg"
        with open(badge_file, 'w') as f:
            f.write(badge_svg)
        print(f"Coverage badge saved: {badge_file}")
    else:
        # Generate all reports
        generator.save_reports(coverage_data)

        # Print summary
        print(f"\n=== Coverage Summary ===")
        print(f"Line Coverage: {coverage_data.get('line_coverage', 0):.1f}%")
        print(f"Branch Coverage: {coverage_data.get('branch_coverage', 0):.1f}%")
        print(f"Trend: {coverage_data.get('trend_analysis', {}).get('trend', 'unknown')}")

        uncovered_critical = coverage_data.get('uncovered_critical', [])
        if uncovered_critical:
            print(f"\n⚠️  {len(uncovered_critical)} critical files need more test coverage")


if __name__ == "__main__":
    main()