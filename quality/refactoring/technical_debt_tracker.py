#!/usr/bin/env python3
"""
Technical Debt Tracker
Identifies, tracks, and manages technical debt across the codebase.
"""

import ast
import os
import re
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass, asdict, field
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum


class DebtCategory(Enum):
    """Categories of technical debt."""
    CODE_QUALITY = "code_quality"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    CONFIGURATION = "configuration"


class DebtSeverity(Enum):
    """Severity levels for technical debt."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DebtStatus(Enum):
    """Status of technical debt items."""
    IDENTIFIED = "identified"
    ASSESSED = "assessed"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DEFERRED = "deferred"
    ACCEPTED = "accepted"


@dataclass
class TechnicalDebtItem:
    """Data class for a technical debt item."""
    id: str
    title: str
    description: str
    category: DebtCategory
    severity: DebtSeverity
    status: DebtStatus
    file_path: str
    line_number: int
    estimated_effort_hours: float
    business_impact: str
    remediation_suggestion: str
    created_date: datetime
    due_date: Optional[datetime] = None
    resolved_date: Optional[datetime] = None
    assignee: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    block_reasons: List[str] = field(default_factory=list)
    priority_score: float = 0.0
    interest_rate: float = 0.1  # Daily accumulation of "interest"


@dataclass
class DebtMetrics:
    """Metrics for technical debt analysis."""
    total_debt_items: int
    total_estimated_effort: float
    debt_by_category: Dict[str, int]
    debt_by_severity: Dict[str, int]
    debt_by_status: Dict[str, int]
    average_debt_age_days: float
    technical_debt_ratio: float  # Effort hours / total code size
    principal: float  # Base effort
    accumulated_interest: float  # Interest over time
    technical_debt_trend: List[Dict[str, Any]]


class TechnicalDebtTracker:
    """Advanced technical debt tracking and management system."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.debt_items: Dict[str, TechnicalDebtItem] = {}
        self.debt_history: List[Dict[str, Any]] = []
        self.debt_patterns = self._initialize_debt_patterns()
        self.business_impact_weights = self._initialize_impact_weights()
        self.debt_rules = self._initialize_debt_rules()

    def _initialize_debt_patterns(self) -> Dict[DebtCategory, List[str]]:
        """Initialize patterns for detecting technical debt."""
        return {
            DebtCategory.CODE_QUALITY: [
                r'#+\s*TODO|FIXME|HACK|XXX',
                r'#+\s*BROKEN|BUG|KLUDGE',
                r'pass\s*#.*temp|temporary|placeholder',
                r'Exception\s*:\s*\n\s*pass',
                r'#.*no.*test|untested',
                r'def\s+\w+\(\):\s*\n\s*pass',
                r'#.*hardcoded|magic.*number',
                r'#.*duplicate|repeated',
                r'#.*should.*refactor|clean.*up'
            ],
            DebtCategory.ARCHITECTURE: [
                r'#.*god.*class|too.*big',
                r'#.*circular.*dependency|cycle',
                r'#.*tight.*coupling|coupled',
                r'#.*violation.*SRP|single.*responsibility',
                r'#.*spaghetti.*code|complex',
                r'#.*layer.*violation|architectural',
                r'#.*static.*method|class.*method',
                r'#.*singleton|global.*state'
            ],
            DebtCategory.TESTING: [
                r'#.*no.*test|untested',
                r'#.*test.*needed|test.*missing',
                r'#.*assert.*missing|no.*assertion',
                r'#.*mock.*needed|stub',
                r'#.*coverage.*low|no.*coverage',
                r'#.*integration.*test|e2e.*test',
                r'#.*unit.*test|isolated.*test',
                r'#.*test.*slow|performance.*test'
            ],
            DebtCategory.DOCUMENTATION: [
                r'#.*doc.*needed|document.*this',
                r'#.*explain.*this|what.*does.*this',
                r'#.*why.*this|purpose.*unclear',
                r'#.*example.*needed|usage.*example',
                r'#.*README.*needed|documentation.*missing',
                r'#.*API.*doc|interface.*document',
                r'#.*change.*log|changelog.*needed',
                r'#.*deprecated|will.*remove'
            ],
            DebtCategory.SECURITY: [
                r'#.*security.*issue|vulnerability',
                r'#.*sql.*injection|xss',
                r'#.*plain.*text|no.*encryption',
                r'#.*hardcoded.*password|secret',
                r'#.*unsafe|dangerous',
                r'#.*auth.*needed|authentication',
                r'#.*validation.*needed|input.*validation',
                r'#.*csrf|cross.*site'
            ],
            DebtCategory.PERFORMANCE: [
                r'#.*slow|performance.*issue',
                r'#.*optimize|optimization',
                r'#.*bottleneck|hotspot',
                r'#.*memory.*leak|leak',
                r'#.*inefficient|expensive',
                r'#.*cache.*needed|caching',
                r'#.*n\+1|query.*problem',
                r'#.*index.*needed|database.*index'
            ],
            DebtCategory.MAINTAINABILITY: [
                r'#.*complex|complicated',
                r'#.*confusing|unclear',
                r'#.*duplicate|repeated',
                r'#.*magic.*number|hardcoded',
                r'#.*inconsistent|not.*consistent',
                r'#.*naming.*issue|bad.*name',
                r'#.*format.*issue|style.*issue',
                r'#.*refactor.*needed|clean.*up'
            ],
            DebtCategory.CONFIGURATION: [
                r'#.*config.*needed|configuration',
                r'#.*environment.*var|env.*var',
                r'#.*hardcoded.*config|static.*config',
                r'#.*deployment.*config|production.*config',
                r'#.*feature.*flag|toggle',
                r'#.*secret.*management|credential',
                r'#.*version.*dependency|dependency.*version',
                r'#.*build.*config|makefile'
            ]
        }

    def _initialize_impact_weights(self) -> Dict[str, float]:
        """Initialize business impact weights."""
        return {
            'security': 1.0,      # Highest impact
            'performance': 0.8,
            'reliability': 0.9,
            'maintainability': 0.6,
            'user_experience': 0.7,
            'developer_experience': 0.5,
            'compliance': 0.8,
            'scalability': 0.7
        }

    def _initialize_debt_rules(self) -> Dict[str, Any]:
        """Initialize rules for debt classification."""
        return {
            'complexity_threshold': 10,
            'function_length_threshold': 50,
            'class_length_threshold': 300,
            'file_length_threshold': 500,
            'parameter_count_threshold': 7,
            'nesting_depth_threshold': 4,
            'duplicate_lines_threshold': 5,
            'test_coverage_threshold': 80,
            'documentation_coverage_threshold': 70
        }

    def scan_for_technical_debt(self, file_path: Path) -> List[TechnicalDebtItem]:
        """Scan a file for technical debt indicators."""
        debt_items = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            # Parse AST for structural analysis
            tree = ast.parse(content)

            # Check for explicit debt markers
            debt_items.extend(self._scan_for_explicit_debt_markers(file_path, lines))

            # Check for structural debt
            debt_items.extend(self._scan_for_structural_debt(file_path, tree, lines))

            # Check for complexity debt
            debt_items.extend(self._scan_for_complexity_debt(file_path, tree, lines))

            # Check for testing debt
            debt_items.extend(self._scan_for_testing_debt(file_path, tree, content))

            # Check for documentation debt
            debt_items.extend(self._scan_for_documentation_debt(file_path, tree, lines))

            # Check for security debt
            debt_items.extend(self._scan_for_security_debt(file_path, content))

            # Check for performance debt
            debt_items.extend(self._scan_for_performance_debt(file_path, tree, content))

        except Exception as e:
            print(f"Error scanning {file_path} for technical debt: {e}")

        return debt_items

    def _scan_for_explicit_debt_markers(self, file_path: Path, lines: List[str]) -> List[TechnicalDebtItem]:
        """Scan for explicit technical debt markers in comments."""
        debt_items = []

        for line_num, line in enumerate(lines, 1):
            for category, patterns in self.debt_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Extract the debt description
                        match = re.search(r'#+\s*(.+)', line)
                        description = match.group(1) if match else line.strip()

                        # Determine severity based on keywords
                        severity = self._determine_severity_from_description(description)

                        # Generate unique ID
                        debt_id = hashlib.md5(
                            f"{file_path}:{line_num}:{description}".encode()
                        ).hexdigest()[:12]

                        debt_item = TechnicalDebtItem(
                            id=debt_id,
                            title=self._extract_title_from_description(description),
                            description=description,
                            category=category,
                            severity=severity,
                            status=DebtStatus.IDENTIFIED,
                            file_path=str(file_path),
                            line_number=line_num,
                            estimated_effort_hours=self._estimate_effort_for_debt_type(category, severity),
                            business_impact=self._assess_business_impact(category, severity),
                            remediation_suggestion=self._generate_remediation_suggestion(category, description),
                            created_date=datetime.now(),
                            tags=self._extract_tags_from_description(description)
                        )

                        debt_items.append(debt_item)

        return debt_items

    def _scan_for_structural_debt(self, file_path: Path, tree: ast.AST, lines: List[str]) -> List[TechnicalDebtItem]:
        """Scan for structural technical debt."""
        debt_items = []

        # Check for large files
        if len(lines) > self.debt_rules['file_length_threshold']:
            debt_id = hashlib.md5(f"{file_path}:large_file".encode()).hexdigest()[:12]

            debt_items.append(TechnicalDebtItem(
                id=debt_id,
                title="Large file detected",
                description=f"File has {len(lines)} lines (threshold: {self.debt_rules['file_length_threshold']})",
                category=DebtCategory.MAINTAINABILITY,
                severity=DebtSeverity.MEDIUM,
                status=DebtStatus.IDENTIFIED,
                file_path=str(file_path),
                line_number=1,
                estimated_effort_hours=4.0,
                business_impact="reduced_maintainability",
                remediation_suggestion="Consider splitting this file into smaller, more focused modules",
                created_date=datetime.now(),
                tags=["file_size", "structure", "maintainability"]
            ))

        # Check for large classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
                if class_lines > self.debt_rules['class_length_threshold']:
                    debt_id = hashlib.md5(f"{file_path}:{node.name}:large_class".encode()).hexdigest()[:12]

                    debt_items.append(TechnicalDebtItem(
                        id=debt_id,
                        title=f"Large class: {node.name}",
                        description=f"Class {node.name} has {class_lines} lines (threshold: {self.debt_rules['class_length_threshold']})",
                        category=DebtCategory.ARCHITECTURE,
                        severity=DebtSeverity.HIGH,
                        status=DebtStatus.IDENTIFIED,
                        file_path=str(file_path),
                        line_number=node.lineno,
                        estimated_effort_hours=8.0,
                        business_impact="violates_single_responsibility",
                        remediation_suggestion="Consider breaking down this class into smaller, more focused classes",
                        created_date=datetime.now(),
                        tags=["large_class", "architecture", "solid"]
                    ))

        # Check for functions with too many parameters
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                param_count = len(node.args.args)
                if param_count > self.debt_rules['parameter_count_threshold']:
                    debt_id = hashlib.md5(f"{file_path}:{node.name}:many_params".encode()).hexdigest()[:12]

                    debt_items.append(TechnicalDebtItem(
                        id=debt_id,
                        title=f"Too many parameters: {node.name}",
                        description=f"Function {node.name} has {param_count} parameters (threshold: {self.debt_rules['parameter_count_threshold']})",
                        category=DebtCategory.CODE_QUALITY,
                        severity=DebtSeverity.MEDIUM,
                        status=DebtStatus.IDENTIFIED,
                        file_path=str(file_path),
                        line_number=node.lineno,
                        estimated_effort_hours=2.0,
                        business_impact="reduced_readability",
                        remediation_suggestion="Consider using a parameter object or configuration class",
                        created_date=datetime.now(),
                        tags=["parameters", "code_quality", "refactoring"]
                    ))

        return debt_items

    def _scan_for_complexity_debt(self, file_path: Path, tree: ast.AST, lines: List[str]) -> List[TechnicalDebtItem]:
        """Scan for complexity-related technical debt."""
        debt_items = []

        # Calculate cyclomatic complexity for functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_cyclomatic_complexity(node)
                if complexity > self.debt_rules['complexity_threshold']:
                    debt_id = hashlib.md5(f"{file_path}:{node.name}:high_complexity".encode()).hexdigest()[:12]

                    severity = DebtSeverity.CRITICAL if complexity > 20 else DebtSeverity.HIGH

                    debt_items.append(TechnicalDebtItem(
                        id=debt_id,
                        title=f"High complexity: {node.name}",
                        description=f"Function {node.name} has cyclomatic complexity {complexity} (threshold: {self.debt_rules['complexity_threshold']})",
                        category=DebtCategory.CODE_QUALITY,
                        severity=severity,
                        status=DebtStatus.IDENTIFIED,
                        file_path=str(file_path),
                        line_number=node.lineno,
                        estimated_effort_hours=complexity * 0.5,  # 0.5 hours per complexity point
                        business_impact="difficult_to_maintain_and_test",
                        remediation_suggestion="Break down this function into smaller, simpler functions",
                        created_date=datetime.now(),
                        tags=["complexity", "cyclomatic", "refactoring"]
                    ))

        return debt_items

    def _scan_for_testing_debt(self, file_path: Path, tree: ast.AST, content: str) -> List[TechnicalDebtItem]:
        """Scan for testing-related technical debt."""
        debt_items = []

        # Check if file has corresponding test file
        test_file_patterns = [
            f"test_{file_path.name}",
            f"{file_path.stem}_test.py",
            f"tests/{file_path.name}",
            f"tests/{file_path.stem}_test.py"
        ]

        has_test_file = False
        for pattern in test_file_patterns:
            if (file_path.parent / pattern).exists() or (self.project_root / pattern).exists():
                has_test_file = True
                break

        if not has_test_file and not file_path.name.startswith('test_'):
            debt_id = hashlib.md5(f"{file_path}:no_tests".encode()).hexdigest()[:12]

            debt_items.append(TechnicalDebtItem(
                id=debt_id,
                title="Missing unit tests",
                description=f"No test file found for {file_path.name}",
                category=DebtCategory.TESTING,
                severity=DebtSeverity.HIGH,
                status=DebtStatus.IDENTIFIED,
                file_path=str(file_path),
                line_number=1,
                estimated_effort_hours=len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]) * 1.0,
                business_impact="unverified_functionality",
                remediation_suggestion="Create comprehensive unit tests for this module",
                created_date=datetime.now(),
                tags=["testing", "coverage", "quality_assurance"]
            ))

        return debt_items

    def _scan_for_documentation_debt(self, file_path: Path, tree: ast.AST, lines: List[str]) -> List[TechnicalDebtItem]:
        """Scan for documentation-related technical debt."""
        debt_items = []

        # Check for missing module docstring
        has_module_docstring = ast.get_docstring(tree) is not None

        if not has_module_docstring:
            debt_id = hashlib.md5(f"{file_path}:no_module_docstring".encode()).hexdigest()[:12]

            debt_items.append(TechnicalDebtItem(
                id=debt_id,
                title="Missing module documentation",
                description=f"Module {file_path.name} lacks a docstring",
                category=DebtCategory.DOCUMENTATION,
                severity=DebtSeverity.MEDIUM,
                status=DebtStatus.IDENTIFIED,
                file_path=str(file_path),
                line_number=1,
                estimated_effort_hours=0.5,
                business_impact="poor_understandability",
                remediation_suggestion="Add a comprehensive module docstring explaining purpose and usage",
                created_date=datetime.now(),
                tags=["documentation", "docstring", "module"]
            ))

        # Check for classes without docstrings
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and not ast.get_docstring(node):
                debt_id = hashlib.md5(f"{file_path}:{node.name}:no_class_docstring".encode()).hexdigest()[:12]

                debt_items.append(TechnicalDebtItem(
                    id=debt_id,
                    title=f"Missing class documentation: {node.name}",
                    description=f"Class {node.name} lacks a docstring",
                    category=DebtCategory.DOCUMENTATION,
                    severity=DebtSeverity.LOW,
                    status=DebtStatus.IDENTIFIED,
                    file_path=str(file_path),
                    line_number=node.lineno,
                    estimated_effort_hours=0.25,
                    business_impact="reduced_understandability",
                    remediation_suggestion="Add a docstring explaining the class purpose and usage",
                    created_date=datetime.now(),
                    tags=["documentation", "docstring", "class"]
                ))

        return debt_items

    def _scan_for_security_debt(self, file_path: Path, content: str) -> List[TechnicalDebtItem]:
        """Scan for security-related technical debt."""
        debt_items = []

        # Security patterns to check
        security_patterns = [
            (r'eval\s*\(', "Use of eval() function", "critical"),
            (r'exec\s*\(', "Use of exec() function", "critical"),
            (r'pickle\.loads?\s*\(', "Use of pickle without verification", "high"),
            (r'subprocess\.call\s*\([^)]*shell\s*=\s*True', "Shell injection vulnerability", "critical"),
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password", "critical"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret", "critical"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key", "critical"),
            (r'input\s*\([^)]*\)', "Unvalidated user input", "medium"),
            (r'urllib\.request\.urlopen\s*\(', "Unvalidated HTTP request", "medium"),
        ]

        for pattern, description, severity_level in security_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                debt_id = hashlib.md5(f"{file_path}:{line_num}:{description}".encode()).hexdigest()[:12]

                severity = DebtSeverity[severity_level.upper()]

                debt_items.append(TechnicalDebtItem(
                    id=debt_id,
                    title=f"Security issue: {description}",
                    description=f"{description} found at line {line_num}",
                    category=DebtCategory.SECURITY,
                    severity=severity,
                    status=DebtStatus.IDENTIFIED,
                    file_path=str(file_path),
                    line_number=line_num,
                    estimated_effort_hours=4.0 if severity == DebtSeverity.CRITICAL else 2.0,
                    business_impact="security_vulnerability",
                    remediation_suggestion=self._generate_security_remediation(description),
                    created_date=datetime.now(),
                    tags=["security", "vulnerability", "immediate_attention"]
                ))

        return debt_items

    def _scan_for_performance_debt(self, file_path: Path, tree: ast.AST, content: str) -> List[TechnicalDebtItem]:
        """Scan for performance-related technical debt."""
        debt_items = []

        # Performance anti-patterns
        performance_patterns = [
            (r'for\s+\w+\s+in\s+range\(len\(', "Use enumerate() instead of range(len())", "low"),
            (r'\.find\(.*\)\s*!=\s*-1', "Use 'in' operator instead of find()", "low"),
            (r'for\s+\w+\s+in\s+\w+\.keys\(\)', "Iterate directly over dictionary", "low"),
            (r'if\s+\w+\s+in\s+\w+\.keys\(\)', "Use direct key lookup instead", "low"),
            (r'\+\s*["\'][^"\']*["\']', "String concatenation in loop (consider f-strings or join)", "medium"),
        ]

        for pattern, description, severity_level in performance_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                debt_id = hashlib.md5(f"{file_path}:{line_num}:{description}".encode()).hexdigest()[:12]

                severity = DebtSeverity[severity_level.upper()]

                debt_items.append(TechnicalDebtItem(
                    id=debt_id,
                    title=f"Performance issue: {description}",
                    description=f"{description} found at line {line_num}",
                    category=DebtCategory.PERFORMANCE,
                    severity=severity,
                    status=DebtStatus.IDENTIFIED,
                    file_path=str(file_path),
                    line_number=line_num,
                    estimated_effort_hours=1.0,
                    business_impact="performance_optimization",
                    remediation_suggestion=f"Optimize: {description}",
                    created_date=datetime.now(),
                    tags=["performance", "optimization", "anti_pattern"]
                ))

        return debt_items

    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity for an AST node."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.With)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.ListComp):
                complexity += 1
            elif isinstance(child, ast.DictComp):
                complexity += 1
            elif isinstance(child, ast.SetComp):
                complexity += 1
            elif isinstance(child, ast.GeneratorExp):
                complexity += 1

        return complexity

    def _determine_severity_from_description(self, description: str) -> DebtSeverity:
        """Determine severity based on description keywords."""
        description_lower = description.lower()

        critical_keywords = ['critical', 'security', 'vulnerability', 'broken', 'crash', 'data loss']
        high_keywords = ['high', 'urgent', 'major', 'blocker', 'must fix', 'hack', 'kludge']
        medium_keywords = ['medium', 'should', 'recommend', 'improve', 'optimize']
        low_keywords = ['low', 'minor', 'nice to have', 'could', 'maybe']

        if any(keyword in description_lower for keyword in critical_keywords):
            return DebtSeverity.CRITICAL
        elif any(keyword in description_lower for keyword in high_keywords):
            return DebtSeverity.HIGH
        elif any(keyword in description_lower for keyword in medium_keywords):
            return DebtSeverity.MEDIUM
        else:
            return DebtSeverity.LOW

    def _extract_title_from_description(self, description: str) -> str:
        """Extract a concise title from description."""
        # Remove common prefixes
        title = re.sub(r'^(TODO|FIXME|HACK|XXX|NOTE|BUG):\s*', '', description, flags=re.IGNORECASE)
        # Limit length
        if len(title) > 50:
            title = title[:47] + '...'
        return title

    def _estimate_effort_for_debt_type(self, category: DebtCategory, severity: DebtSeverity) -> float:
        """Estimate effort hours based on debt type and severity."""
        base_efforts = {
            DebtCategory.CODE_QUALITY: 2.0,
            DebtCategory.ARCHITECTURE: 8.0,
            DebtCategory.TESTING: 4.0,
            DebtCategory.DOCUMENTATION: 1.0,
            DebtCategory.SECURITY: 6.0,
            DebtCategory.PERFORMANCE: 4.0,
            DebtCategory.MAINTAINABILITY: 3.0,
            DebtCategory.CONFIGURATION: 2.0
        }

        severity_multipliers = {
            DebtSeverity.LOW: 0.5,
            DebtSeverity.MEDIUM: 1.0,
            DebtSeverity.HIGH: 2.0,
            DebtSeverity.CRITICAL: 4.0
        }

        base_effort = base_efforts.get(category, 2.0)
        multiplier = severity_multipliers.get(severity, 1.0)

        return base_effort * multiplier

    def _assess_business_impact(self, category: DebtCategory, severity: DebtSeverity) -> str:
        """Assess business impact based on category and severity."""
        impact_mapping = {
            DebtCategory.SECURITY: "security_risk",
            DebtCategory.PERFORMANCE: "user_experience",
            DebtCategory.ARCHITECTURE: "scalability",
            DebtCategory.CODE_QUALITY: "developer_productivity",
            DebtCategory.TESTING: "quality_assurance",
            DebtCategory.DOCUMENTATION: "knowledge_transfer",
            DebtCategory.MAINTAINABILITY: "maintenance_cost",
            DebtCategory.CONFIGURATION: "deployment_complexity"
        }

        return impact_mapping.get(category, "general_debt")

    def _generate_remediation_suggestion(self, category: DebtCategory, description: str) -> str:
        """Generate specific remediation suggestions."""
        suggestions = {
            DebtCategory.CODE_QUALITY: "Refactor code to improve readability and maintainability",
            DebtCategory.ARCHITECTURE: "Review and improve architectural design patterns",
            DebtCategory.TESTING: "Add comprehensive tests to ensure code reliability",
            DebtCategory.DOCUMENTATION: "Improve code documentation and comments",
            DebtCategory.SECURITY: "Address security vulnerabilities immediately",
            DebtCategory.PERFORMANCE: "Optimize code for better performance",
            DebtCategory.MAINTAINABILITY: "Refactor for better maintainability",
            DebtCategory.CONFIGURATION: "Improve configuration management"
        }

        base_suggestion = suggestions.get(category, "Address the identified technical debt")

        # Add specific suggestions based on description
        if 'refactor' in description.lower():
            return f"Refactor the code: {description}"
        elif 'test' in description.lower():
            return f"Add appropriate tests: {description}"
        elif 'document' in description.lower():
            return f"Add documentation: {description}"
        else:
            return f"{base_suggestion}: {description}"

    def _generate_security_remediation(self, issue_description: str) -> str:
        """Generate specific security remediation suggestions."""
        remediation_map = {
            "Use of eval() function": "Remove eval() and use safer alternatives like ast.literal_eval",
            "Use of exec() function": "Remove exec() and implement proper function dispatch",
            "Shell injection vulnerability": "Use parameterized commands or proper escaping",
            "Hardcoded password": "Use environment variables or secure credential management",
            "Hardcoded secret": "Use secure secret management system",
            "Hardcoded API key": "Use environment variables or key management service",
            "Unvalidated user input": "Add proper input validation and sanitization"
        }

        return remediation_map.get(issue_description, "Review and fix security issue immediately")

    def _extract_tags_from_description(self, description: str) -> List[str]:
        """Extract relevant tags from description."""
        tags = []
        description_lower = description.lower()

        tag_mapping = {
            'security': ['security', 'vulnerability', 'auth', 'encrypt', 'password'],
            'performance': ['slow', 'optimize', 'performance', 'cache', 'memory'],
            'testing': ['test', 'unit', 'integration', 'coverage', 'mock'],
            'documentation': ['doc', 'document', 'readme', 'example', 'usage'],
            'refactoring': ['refactor', 'clean', 'improve', 'simplify'],
            'architecture': ['architecture', 'design', 'pattern', 'structure'],
            'bug': ['bug', 'fix', 'broken', 'error', 'issue'],
            'feature': ['feature', 'add', 'implement', 'new'],
            'temporary': ['temp', 'temporary', 'placeholder', 'hack']
        }

        for tag, keywords in tag_mapping.items():
            if any(keyword in description_lower for keyword in keywords):
                tags.append(tag)

        return tags

    def analyze_project(self) -> Dict[str, Any]:
        """Analyze entire project for technical debt."""
        print("Scanning project for technical debt...")

        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.venv', 'venv', 'node_modules'}]

            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)

        print(f"Found {len(python_files)} Python files")

        # Scan each file for technical debt
        all_debt_items = []
        for file_path in python_files:
            print(f"Scanning {file_path} for technical debt...")
            debt_items = self.scan_for_technical_debt(file_path)
            all_debt_items.extend(debt_items)

            # Store debt items
            for item in debt_items:
                self.debt_items[item.id] = item

        # Calculate metrics
        metrics = self._calculate_debt_metrics()

        # Generate recommendations
        recommendations = self._generate_debt_recommendations()

        return {
            'debt_summary': asdict(metrics),
            'debt_items': [asdict(item) for item in all_debt_items],
            'recommendations': recommendations,
            'analysis_timestamp': time.time()
        }

    def _calculate_debt_metrics(self) -> DebtMetrics:
        """Calculate comprehensive debt metrics."""
        if not self.debt_items:
            return DebtMetrics(
                total_debt_items=0,
                total_estimated_effort=0.0,
                debt_by_category={},
                debt_by_severity={},
                debt_by_status={},
                average_debt_age_days=0.0,
                technical_debt_ratio=0.0,
                principal=0.0,
                accumulated_interest=0.0,
                technical_debt_trend=[]
            )

        # Basic counts
        total_items = len(self.debt_items)
        total_effort = sum(item.estimated_effort_hours for item in self.debt_items.values())

        # Category breakdown
        debt_by_category = defaultdict(int)
        for item in self.debt_items.values():
            debt_by_category[item.category.value] += 1

        # Severity breakdown
        debt_by_severity = defaultdict(int)
        for item in self.debt_items.values():
            debt_by_severity[item.severity.value] += 1

        # Status breakdown
        debt_by_status = defaultdict(int)
        for item in self.debt_items.values():
            debt_by_status[item.status.value] += 1

        # Calculate age metrics
        now = datetime.now()
        ages = [(now - item.created_date).days for item in self.debt_items.values()]
        average_age = sum(ages) / len(ages) if ages else 0

        # Calculate interest (accumulated technical debt)
        principal = total_effort
        accumulated_interest = sum(
            item.estimated_effort_hours * item.interest_rate *
            (now - item.created_date).days
            for item in self.debt_items.values()
        )

        # Calculate technical debt ratio (effort per 1000 lines of code)
        total_loc = self._calculate_total_lines_of_code()
        debt_ratio = (total_effort / total_loc * 1000) if total_loc > 0 else 0

        return DebtMetrics(
            total_debt_items=total_items,
            total_estimated_effort=total_effort,
            debt_by_category=dict(debt_by_category),
            debt_by_severity=dict(debt_by_severity),
            debt_by_status=dict(debt_by_status),
            average_debt_age_days=average_age,
            technical_debt_ratio=debt_ratio,
            principal=principal,
            accumulated_interest=accumulated_interest,
            technical_debt_trend=[]  # Would need historical data
        )

    def _calculate_total_lines_of_code(self) -> int:
        """Calculate total lines of code in project."""
        total_lines = 0

        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.venv', 'venv', 'node_modules'}]

            for file in files:
                if file.endswith('.py'):
                    try:
                        with open(Path(root) / file, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
                            total_lines += code_lines
                    except Exception:
                        continue

        return total_lines

    def _generate_debt_recommendations(self) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations for addressing technical debt."""
        recommendations = []

        # Group debt by severity and category
        critical_items = [item for item in self.debt_items.values() if item.severity == DebtSeverity.CRITICAL]
        high_items = [item for item in self.debt_items.values() if item.severity == DebtSeverity.HIGH]
        security_items = [item for item in self.debt_items.values() if item.category == DebtCategory.SECURITY]

        # Prioritize critical security issues
        if security_items:
            security_critical = [item for item in security_items if item.severity in [DebtSeverity.CRITICAL, DebtSeverity.HIGH]]
            if security_critical:
                recommendations.append({
                    'priority': 1,
                    'category': 'security',
                    'title': 'Address Critical Security Issues',
                    'description': f'Found {len(security_critical)} critical security vulnerabilities',
                    'estimated_effort': sum(item.estimated_effort_hours for item in security_critical),
                    'items': [item.id for item in security_critical],
                    'action': 'immediate_attention_required'
                })

        # Recommend addressing critical items
        if critical_items:
            non_security_critical = [item for item in critical_items if item.category != DebtCategory.SECURITY]
            if non_security_critical:
                recommendations.append({
                    'priority': 2,
                    'category': 'critical_debt',
                    'title': 'Resolve Critical Technical Debt',
                    'description': f'Found {len(non_security_critical)} critical technical debt items',
                    'estimated_effort': sum(item.estimated_effort_hours for item in non_security_critical),
                    'items': [item.id for item in non_security_critical],
                    'action': 'address_in_current_sprint'
                })

        # Recommend high-priority items
        if high_items:
            recommendations.append({
                'priority': 3,
                'category': 'high_priority',
                'title': 'Address High-Priority Technical Debt',
                'description': f'Found {len(high_items)} high-priority technical debt items',
                'estimated_effort': sum(item.estimated_effort_hours for item in high_items),
                'items': [item.id for item in high_items],
                'action': 'plan_for_next_sprint'
            })

        # Recommend systematic testing improvements
        testing_items = [item for item in self.debt_items.values() if item.category == DebtCategory.TESTING]
        if testing_items:
            recommendations.append({
                'priority': 4,
                'category': 'testing',
                'title': 'Improve Test Coverage',
                'description': f'Found {len(testing_items)} testing-related issues',
                'estimated_effort': sum(item.estimated_effort_hours for item in testing_items),
                'items': [item.id for item in testing_items],
                'action': 'systematic_improvement'
            })

        # Recommend documentation improvements
        doc_items = [item for item in self.debt_items.values() if item.category == DebtCategory.DOCUMENTATION]
        if doc_items:
            recommendations.append({
                'priority': 5,
                'category': 'documentation',
                'title': 'Improve Documentation',
                'description': f'Found {len(doc_items)} documentation-related issues',
                'estimated_effort': sum(item.estimated_effort_hours for item in doc_items),
                'items': [item.id for item in doc_items],
                'action': 'continuous_improvement'
            })

        return recommendations

    def generate_report(self, analysis_results: Dict[str, Any], output_path: str = None) -> str:
        """Generate technical debt analysis report."""
        if output_path is None:
            output_path = '/home/activeloguser/DMLogn8n/quality/reports/technical_debt_report.json'

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)

        return output_path


def main():
    """Main function for standalone usage."""
    project_root = '/home/activeloguser/DMLogn8n'
    tracker = TechnicalDebtTracker(project_root)

    print("Starting technical debt analysis...")
    results = tracker.analyze_project()

    # Generate report
    report_path = tracker.generate_report(results)
    print(f"Analysis complete. Report saved to: {report_path}")

    # Print summary
    summary = results['debt_summary']
    print(f"\n=== Technical Debt Summary ===")
    print(f"Total debt items: {summary['total_debt_items']}")
    print(f"Total estimated effort: {summary['total_estimated_effort']:.1f} hours")
    print(f"Average debt age: {summary['average_debt_age_days']:.1f} days")
    print(f"Technical debt ratio: {summary['technical_debt_ratio']:.2f} per 1000 LOC")
    print(f"Principal: {summary['principal']:.1f} hours")
    print(f"Accumulated interest: {summary['accumulated_interest']:.1f} hours")

    print(f"\n=== Debt by Category ===")
    for category, count in summary['debt_by_category'].items():
        print(f"{category}: {count}")

    print(f"\n=== Debt by Severity ===")
    for severity, count in summary['debt_by_severity'].items():
        print(f"{severity}: {count}")

    print(f"\n=== Top Recommendations ===")
    for rec in results['recommendations'][:3]:
        print(f"{rec['priority']}. {rec['title']}")
        print(f"   {rec['description']}")
        print(f"   Estimated effort: {rec['estimated_effort']:.1f} hours")
        print()


if __name__ == "__main__":
    main()