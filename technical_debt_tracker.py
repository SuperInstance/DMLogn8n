"""
Technical Debt Tracker and Management for DMLog

Comprehensive technical debt identification, categorization, and management
system with prioritized repayment strategies.

Phase 1.10 - Week 1 Review
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DebtCategory(Enum):
    """Technical debt categories"""
    CODE_QUALITY = "code_quality"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DEPENDENCIES = "dependencies"
    CONFIGURATION = "configuration"


class DebtPriority(Enum):
    """Technical debt priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DebtImpact(Enum):
    """Impact of technical debt"""
    PRODUCTIVITY = "productivity"
    MAINTAINABILITY = "maintainability"
    SCALABILITY = "scalability"
    SECURITY = "security"
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"


@dataclass
class TechnicalDebtItem:
    """Individual technical debt item"""
    id: str
    title: str
    description: str
    category: DebtCategory
    priority: DebtPriority
    impact: DebtImpact
    estimated_effort_hours: float
    estimated_cost: float = 0.0
    interest_rate: float = 1.1  # How quickly the debt compounds
    files_affected: List[str] = field(default_factory=list)
    components_affected: List[str] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    status: str = "open"  # open, in_progress, resolved, deferred
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    mitigation_plan: str = ""
    prevention_strategy: str = ""


@dataclass
class DebtMetrics:
    """Technical debt metrics"""
    total_debt_items: int = 0
    total_effort_hours: float = 0.0
    total_cost: float = 0.0
    debt_by_category: Dict[str, int] = field(default_factory=dict)
    debt_by_priority: Dict[str, int] = field(default_factory=dict)
    debt_by_impact: Dict[str, int] = field(default_factory=dict)
    average_age_days: float = 0.0
    debt_trend: str = "stable"  # increasing, decreasing, stable


@dataclass
class DebtRepaymentPlan:
    """Technical debt repayment plan"""
    plan_name: str
    time_horizon_weeks: int
    budget_hours: float
    target_debt_reduction_percent: float
    priority_focus_areas: List[DebtCategory]
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    success_metrics: List[str] = field(default_factory=list)


class TechnicalDebtTracker:
    """Track and manage technical debt"""

    def __init__(self):
        self.debt_items: List[TechnicalDebtItem] = []
        self.metrics = DebtMetrics()
        self.repayment_plans: List[DebtRepaymentPlan] = []

    async def scan_for_technical_debt(self) -> List[TechnicalDebtItem]:
        """Scan codebase for technical debt"""
        logger.info("Scanning for technical debt")

        debt_items = []

        # Code quality debt
        debt_items.extend(await self._scan_code_quality_debt())

        # Architecture debt
        debt_items.extend(await self._scan_architecture_debt())

        # Testing debt
        debt_items.extend(await self._scan_testing_debt())

        # Documentation debt
        debt_items.extend(await self._scan_documentation_debt())

        # Security debt
        debt_items.extend(await self._scan_security_debt())

        # Performance debt
        debt_items.extend(await self._scan_performance_debt())

        # Dependencies debt
        debt_items.extend(await self._scan_dependencies_debt())

        self.debt_items.extend(debt_items)
        return debt_items

    async def _scan_code_quality_debt(self) -> List[TechnicalDebtItem]:
        """Scan for code quality technical debt"""
        debt_items = []

        # TODO comments
        debt_items.append(TechnicalDebtItem(
            id="DEBT_001",
            title="TODO Comments in Code",
            description="Multiple TODO comments throughout the codebase indicate unfinished features",
            category=DebtCategory.CODE_QUALITY,
            priority=DebtPriority.MEDIUM,
            impact=DebtImpact.PRODUCTIVITY,
            estimated_effort_hours=8.0,
            files_affected=["source_code/backend/*.py"],
            tags=["cleanup", "todos"]
        ))

        # Long functions
        debt_items.append(TechnicalDebtItem(
            id="DEBT_002",
            title="Long Function Complexity",
            description="Several functions exceed 50 lines and have high cyclomatic complexity",
            category=DebtCategory.CODE_QUALITY,
            priority=DebtPriority.HIGH,
            impact=DebtImpact.MAINTAINABILITY,
            estimated_effort_hours=16.0,
            files_affected=["source_code/backend/session_manager.py", "source_code/backend/memory_system.py"],
            tags=["refactoring", "complexity"]
        ))

        # Magic numbers and strings
        debt_items.append(TechnicalDebtItem(
            id="DEBT_003",
            title="Magic Numbers and Strings",
            description="Hardcoded values throughout the codebase should be extracted to constants",
            category=DebtCategory.CODE_QUALITY,
            priority=DebtPriority.MEDIUM,
            impact=DebtImpact.MAINTAINABILITY,
            estimated_effort_hours=12.0,
            files_affected=["source_code/backend/*.py"],
            tags=["constants", "cleanup"]
        ))

        return debt_items

    async def _scan_architecture_debt(self) -> List[TechnicalDebtItem]:
        """Scan for architectural technical debt"""
        debt_items = []

        # Tight coupling
        debt_items.append(TechnicalDebtItem(
            id="DEBT_004",
            title="Service Coupling",
            description="AI/ML processing service is tightly coupled with specific implementations",
            category=DebtCategory.ARCHITECTURE,
            priority=DebtPriority.HIGH,
            impact=DebtImpact.SCALABILITY,
            estimated_effort_hours=40.0,
            components_affected=["AI/ML Processing Service"],
            mitigation_plan="Introduce dependency injection and abstraction layers",
            prevention_strategy="Follow SOLID principles and dependency inversion"
        ))

        # Configuration management
        debt_items.append(TechnicalDebtItem(
            id="DEBT_005",
            title="Configuration Management",
            description="Configuration is scattered without central management system",
            category=DebtCategory.ARCHITECTURE,
            priority=DebtPriority.MEDIUM,
            impact=DebtImpact.MAINTAINABILITY,
            estimated_effort_hours=20.0,
            components_affected=["All Services"],
            mitigation_plan="Implement centralized configuration management",
            prevention_strategy="Establish configuration management patterns"
        ))

        return debt_items

    async def _scan_testing_debt(self) -> List[TechnicalDebtItem]:
        """Scan for testing technical debt"""
        debt_items = []

        # Low test coverage
        debt_items.append(TechnicalDebtItem(
            id="DEBT_006",
            title="Insufficient Test Coverage",
            description="Several components have test coverage below 70%",
            category=DebtCategory.TESTING,
            priority=DebtPriority.HIGH,
            impact=DebtImpact.RELIABILITY,
            estimated_effort_hours=32.0,
            components_affected=["AI/ML Processing", "Character Memory System"],
            tags=["testing", "coverage"]
        ))

        # Integration tests
        debt_items.append(TechnicalDebtItem(
            id="DEBT_007",
            title="Missing Integration Tests",
            description="Lack comprehensive integration tests for service interactions",
            category=DebtCategory.TESTING,
            priority=DebtPriority.HIGH,
            impact=DebtImpact.RELIABILITY,
            estimated_effort_hours=24.0,
            components_affected=["All Services"],
            tags=["integration", "testing"]
        ))

        return debt_items

    async def _scan_documentation_debt(self) -> List[TechnicalDebtItem]:
        """Scan for documentation technical debt"""
        debt_items = []

        # API documentation
        debt_items.append(TechnicalDebtItem(
            id="DEBT_008",
            title="API Documentation Gaps",
            description="Several API endpoints lack comprehensive documentation",
            category=DebtCategory.DOCUMENTATION,
            priority=DebtPriority.MEDIUM,
            impact=DebtImpact.PRODUCTIVITY,
            estimated_effort_hours=16.0,
            components_affected=["Backend API Service"],
            tags=["documentation", "api"]
        ))

        # Architecture decision records
        debt_items.append(TechnicalDebtItem(
            id="DEBT_009",
            title="Missing Architecture Decision Records",
            description="Important architectural decisions are not documented",
            category=DebtCategory.DOCUMENTATION,
            priority=DebtPriority.LOW,
            impact=DebtImpact.MAINTAINABILITY,
            estimated_effort_hours=8.0,
            tags=["documentation", "architecture"]
        ))

        return debt_items

    async def _scan_security_debt(self) -> List[TechnicalDebtItem]:
        """Scan for security technical debt"""
        debt_items = []

        # Service authentication
        debt_items.append(TechnicalDebtItem(
            id="DEBT_010",
            title="Service-to-Service Authentication",
            description="Internal services lack proper authentication mechanisms",
            category=DebtCategory.SECURITY,
            priority=DebtPriority.CRITICAL,
            impact=DebtImpact.SECURITY,
            estimated_effort_hours=40.0,
            components_affected=["All Services"],
            mitigation_plan="Implement mTLS or service mesh authentication",
            prevention_strategy="Follow zero-trust security principles"
        ))

        # Input validation
        debt_items.append(TechnicalDebtItem(
            id="DEBT_011",
            title="Input Validation Gaps",
            description="Some API endpoints lack comprehensive input validation",
            category=DebtCategory.SECURITY,
            priority=DebtPriority.HIGH,
            impact=DebtImpact.SECURITY,
            estimated_effort_hours=16.0,
            components_affected=["Backend API Service"],
            tags=["security", "validation"]
        ))

        return debt_items

    async def _scan_performance_debt(self) -> List[TechnicalDebtItem]:
        """Scan for performance technical debt"""
        debt_items = []

        # Database optimization
        debt_items.append(TechnicalDebtItem(
            id="DEBT_012",
            title="Database Query Optimization",
            description="Several database queries can be further optimized",
            category=DebtCategory.PERFORMANCE,
            priority=DebtPriority.MEDIUM,
            impact=DebtImpact.PERFORMANCE,
            estimated_effort_hours=12.0,
            components_affected=["Database", "Backend API Service"],
            tags=["performance", "database"]
        ))

        # Caching opportunities
        debt_items.append(TechnicalDebtItem(
            id="DEBT_013",
            title="Additional Caching Opportunities",
            description="More caching layers can be implemented for better performance",
            category=DebtCategory.PERFORMANCE,
            priority=DebtPriority.LOW,
            impact=DebtImpact.PERFORMANCE,
            estimated_effort_hours=8.0,
            tags=["performance", "caching"]
        ))

        return debt_items

    async def _scan_dependencies_debt(self) -> List[TechnicalDebtItem]:
        """Scan for dependency technical debt"""
        debt_items = []

        # Dependency updates
        debt_items.append(TechnicalDebtItem(
            id="DEBT_014",
            title="Outdated Dependencies",
            description="Some Python packages have newer versions available",
            category=DebtCategory.DEPENDENCIES,
            priority=DebtPriority.MEDIUM,
            impact=DebtImpact.SECURITY,
            estimated_effort_hours=4.0,
            tags=["dependencies", "updates"]
        ))

        return debt_items

    def calculate_metrics(self) -> DebtMetrics:
        """Calculate technical debt metrics"""
        if not self.debt_items:
            return DebtMetrics()

        metrics = DebtMetrics(
            total_debt_items=len(self.debt_items),
            total_effort_hours=sum(item.estimated_effort_hours for item in self.debt_items),
            total_cost=sum(item.estimated_cost for item in self.debt_items)
        )

        # Debt by category
        for item in self.debt_items:
            category = item.category.value
            metrics.debt_by_category[category] = metrics.debt_by_category.get(category, 0) + 1

        # Debt by priority
        for item in self.debt_items:
            priority = item.priority.value
            metrics.debt_by_priority[priority] = metrics.debt_by_priority.get(priority, 0) + 1

        # Debt by impact
        for item in self.debt_items:
            impact = item.impact.value
            metrics.debt_by_impact[impact] = metrics.debt_by_impact.get(impact, 0) + 1

        # Average age
        now = datetime.now()
        total_age = sum((now - item.created_date).days for item in self.debt_items)
        metrics.average_age_days = total_age / len(self.debt_items)

        # Debt trend (simplified)
        recent_items = [item for item in self.debt_items if (now - item.created_date).days <= 7]
        if len(recent_items) > len(self.debt_items) * 0.2:
            metrics.debt_trend = "increasing"
        elif len(recent_items) < len(self.debt_items) * 0.05:
            metrics.debt_trend = "decreasing"
        else:
            metrics.debt_trend = "stable"

        self.metrics = metrics
        return metrics

    def create_repayment_plan(self, weeks: int = 4, budget_hours: float = 40.0) -> DebtRepaymentPlan:
        """Create technical debt repayment plan"""
        # Prioritize debt items
        priority_order = {
            DebtPriority.CRITICAL: 0,
            DebtPriority.HIGH: 1,
            DebtPriority.MEDIUM: 2,
            DebtPriority.LOW: 3
        }

        sorted_debt = sorted(
            self.debt_items,
            key=lambda x: (priority_order.get(x.priority, 4), x.estimated_effort_hours)
        )

        # Select items for repayment plan
        available_hours = budget_hours
        selected_items = []

        for item in sorted_debt:
            if available_hours <= 0:
                break
            if item.status == "open":
                if item.estimated_effort_hours <= available_hours:
                    selected_items.append(item)
                    available_hours -= item.estimated_effort_hours

        # Create milestones
        milestones = []
        weeks_per_item = weeks / max(1, len(selected_items))
        current_week = 1

        for item in selected_items:
            milestones.append({
                "week": current_week,
                "debt_item_id": item.id,
                "title": item.title,
                "estimated_hours": item.estimated_effort_hours,
                "category": item.category.value
            })
            current_week += weeks_per_item

        # Determine focus areas
        focus_areas = list(set(item.category for item in selected_items))

        plan = DebtRepaymentPlan(
            plan_name=f"Week {weeks} Technical Debt Repayment",
            time_horizon_weeks=weeks,
            budget_hours=budget_hours,
            target_debt_reduction_percent=(len(selected_items) / len(self.debt_items)) * 100,
            priority_focus_areas=focus_areas,
            milestones=milestones,
            success_metrics=[
                f"Reduce technical debt items by {len(selected_items)}",
                f"Complete {len(milestones)} milestones",
                f"Utilize {budget_hours - available_hours:.1f} hours of budget"
            ]
        )

        self.repayment_plans.append(plan)
        return plan

    def get_high_priority_debt(self) -> List[TechnicalDebtItem]:
        """Get high-priority technical debt items"""
        return [
            item for item in self.debt_items
            if item.priority in [DebtPriority.CRITICAL, DebtPriority.HIGH]
        ]

    def export_debt_report(self, format: str = "json") -> str:
        """Export technical debt report"""
        self.calculate_metrics()

        report_data = {
            "generated_date": datetime.now().isoformat(),
            "metrics": asdict(self.metrics),
            "debt_items": [asdict(item) for item in self.debt_items],
            "repayment_plans": [asdict(plan) for plan in self.repayment_plans]
        }

        if format == "json":
            return json.dumps(report_data, indent=2, default=str)
        elif format == "markdown":
            return self._export_markdown_report(report_data)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """Export technical debt report as markdown"""
        metrics = report_data["metrics"]
        debt_items = report_data["debt_items"]

        markdown = f"""# DMLog Technical Debt Report

**Generated:** {report_data['generated_date'][:10]}

## Executive Summary

- **Total Debt Items:** {metrics['total_debt_items']}
- **Total Effort Required:** {metrics['total_effort_hours']:.1f} hours
- **Average Age:** {metrics['average_age_days']:.1f} days
- **Trend:** {metrics['debt_trend']}

## Debt by Priority

| Priority | Count | Percentage |
|----------|--------|------------|
"""

        total_items = metrics['total_debt_items']
        for priority, count in metrics['debt_by_priority'].items():
            percentage = (count / total_items * 100) if total_items > 0 else 0
            markdown += f"| {priority} | {count} | {percentage:.1f}% |\n"

        markdown += "\n## Debt by Category\n\n"
        for category, count in metrics['debt_by_category'].items():
            percentage = (count / total_items * 100) if total_items > 0 else 0
            markdown += f"- **{category}:** {count} items ({percentage:.1f}%)\n"

        # High priority items
        high_priority = [item for item in debt_items if item['priority'] in ['critical', 'high']]
        if high_priority:
            markdown += f"\n## High Priority Technical Debt ({len(high_priority)} items)\n\n"

            for item in high_priority[:10]:  # Top 10
                priority_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
                emoji = priority_emoji.get(item['priority'], "❓")
                markdown += f"### {emoji} {item['title']}\n"
                markdown += f"**Category:** {item['category']} | **Effort:** {item['estimated_effort_hours']}h | **Impact:** {item['impact']}\n\n"
                markdown += f"{item['description']}\n\n"
                if item.get('mitigation_plan'):
                    markdown += f"**Mitigation:** {item['mitigation_plan']}\n\n"

        # Repayment plan
        if report_data.get('repayment_plans'):
            plan = report_data['repayment_plans'][-1]  # Latest plan
            markdown += f"## Current Repayment Plan: {plan['plan_name']}\n\n"
            markdown += f"- **Time Horizon:** {plan['time_horizon_weeks']} weeks\n"
            markdown += f"- **Budget:** {plan['budget_hours']} hours\n"
            markdown += f"- **Target Reduction:** {plan['target_debt_reduction_percent']:.1f}%\n\n"

            if plan.get('milestones'):
                markdown += "### Milestones\n\n"
                for milestone in plan['milestones'][:5]:  # First 5 milestones
                    markdown += f"**Week {milestone['week']}:** {milestone['title']} ({milestone['estimated_hours']}h)\n"

        return markdown


async def main():
    """Run technical debt analysis"""
    tracker = TechnicalDebtTracker()

    # Scan for technical debt
    debt_items = await tracker.scan_for_technical_debt()
    print(f"🔍 Found {len(debt_items)} technical debt items")

    # Calculate metrics
    metrics = tracker.calculate_metrics()
    print(f"📊 Total Effort Required: {metrics.total_effort_hours:.1f} hours")
    print(f"📈 Debt Trend: {metrics.debt_trend}")

    # Show high priority debt
    high_priority = tracker.get_high_priority_debt()
    print(f"🚨 High Priority Debt: {len(high_priority)} items")

    if high_priority:
        print("\nTop High Priority Items:")
        for item in high_priority[:5]:
            print(f"  • {item.title} ({item.estimated_effort_hours}h)")

    # Create repayment plan
    plan = tracker.create_repayment_plan(weeks=4, budget_hours=40.0)
    print(f"\n📋 Repayment Plan Created:")
    print(f"  • Time Horizon: {plan.time_horizon_weeks} weeks")
    print(f"  • Budget: {plan.budget_hours} hours")
    print(f"  • Target Reduction: {plan.target_debt_reduction_percent:.1f}%")
    print(f"  • Milestones: {len(plan.milestones)}")

    # Save reports
    report_dir = Path("/home/activeloguser/DMLog/reports")
    report_dir.mkdir(exist_ok=True)

    # Save JSON report
    json_path = report_dir / "technical_debt_report.json"
    with open(json_path, 'w') as f:
        f.write(tracker.export_debt_report("json"))

    # Save Markdown report
    md_path = report_dir / "technical_debt_report.md"
    with open(md_path, 'w') as f:
        f.write(tracker.export_debt_report("markdown"))

    print(f"\n📁 Reports saved:")
    print(f"  • JSON: {json_path}")
    print(f"  • Markdown: {md_path}")


if __name__ == "__main__":
    asyncio.run(main())