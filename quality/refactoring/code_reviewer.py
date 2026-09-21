#!/usr/bin/env python3
"""
Automated Code Reviewer
Provides comprehensive code review with best practice enforcement and suggestions.
"""

import ast
import os
import re
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import difflib


@dataclass
class CodeReviewIssue:
    """Data class for code review issues."""
    id: str
    file_path: str
    line_number: int
    column_number: int
    issue_type: str
    severity: str  # 'info', 'warning', 'error', 'critical'
    category: str
    title: str
    description: str
    suggestion: str
    code_snippet: str
    rule_id: str
    auto_fixable: bool
    confidence: float
    tags: List[str]


@dataclass
class CodeReviewMetrics:
    """Metrics for code review analysis."""
    total_issues: int
    issues_by_severity: Dict[str, int]
    issues_by_category: Dict[str, int]
    issues_by_file: Dict[str, int]
    auto_fixable_count: int
    avg_confidence: float
    review_score: float  # Overall code quality score


class CodeReviewer:
    """Automated code review system with comprehensive analysis."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.review_rules = self._initialize_review_rules()
        self.best_practices = self._initialize_best_practices()
        self.anti_patterns = self._initialize_anti_patterns()
        self.security_rules = self._initialize_security_rules()

    def _initialize_review_rules(self) -> Dict[str, Any]:
        """Initialize comprehensive code review rules."""
        return {
            'naming_conventions': {
                'variable_pattern': r'^[a-z_][a-z0-9_]*$',
                'function_pattern': r'^[a-z_][a-z0-9_]*$',
                'class_pattern': r'^[A-Z][a-zA-Z0-9]*$',
                'constant_pattern': r'^[A-Z_][A-Z0-9_]*$',
                'module_pattern': r'^[a-z_][a-z0-9_]*$',
                'private_pattern': r'^_[a-z_][a-z0-9_]*$',
                'dunder_pattern': r'^__[a-z_][a-z0-9_]*__$'
            },
            'complexity_rules': {
                'max_function_length': 50,
                'max_class_length': 300,
                'max_line_length': 88,  # Black standard
                'max_complexity': 10,
                'max_nesting_depth': 4,
                'max_parameters': 7,
                'max_cognitive_complexity': 15
            },
            'style_rules': {
                'required_imports': [],
                'forbidden_imports': ['from module import *'],
                'required_docstring_length': 10,
                'max_blank_lines': 2,
                'require_type_hints': True,
                'require_docstrings': True,
                'require_error_handling': True
            },
            'structure_rules': {
                'max_class_methods': 20,
                'max_class_attributes': 15,
                'require_init_method': True,
                'prefer_composition_over_inheritance': True,
                'avoid_deep_inheritance': 4
            }
        }

    def _initialize_best_practices(self) -> Dict[str, List[str]]:
        """Initialize best practices guidelines."""
        return {
            'error_handling': [
                'Use specific exceptions instead of generic Exception',
                'Always include try-except blocks for risky operations',
                'Use finally blocks for cleanup',
                'Log exceptions with context',
                'Validate inputs early',
                'Use context managers (with statements) for resource management'
            ],
            'performance': [
                'Use generators for large datasets',
                'Avoid unnecessary list comprehensions',
                'Use appropriate data structures',
                'Cache expensive operations',
                'Avoid string concatenation in loops',
                'Use built-in functions when possible'
            ],
            'security': [
                'Never use eval() with untrusted input',
                'Use parameterized queries for database operations',
                'Validate all user input',
                'Use HTTPS for network communications',
                'Store secrets securely',
                'Implement proper authentication and authorization'
            ],
            'readability': [
                'Use descriptive variable names',
                'Write self-documenting code',
                'Avoid magic numbers',
                'Keep functions small and focused',
                'Use consistent formatting',
                'Add comments for complex logic'
            ],
            'testing': [
                'Write unit tests for all functions',
                'Test edge cases and error conditions',
                'Use descriptive test names',
                'Arrange-Act-Assert pattern',
                'Mock external dependencies',
                'Maintain high test coverage'
            ],
            'documentation': [
                'Document all public APIs',
                'Include examples in docstrings',
                'Document parameters and return values',
                'Explain complex algorithms',
                'Maintain README files',
                'Document configuration options'
            ]
        }

    def _initialize_anti_patterns(self) -> Dict[str, List[str]]:
        """Initialize anti-patterns to detect."""
        return {
            'code_smells': [
                'Long parameter lists',
                'God classes',
                'Feature envy',
                'Data clumps',
                'Primitive obsession',
                'Switch statements',
                'Lazy classes',
                'Speculative generality',
                'Temporary fields',
                'Message chains',
                'Middle man',
                'Inappropriate intimacy',
                'Alternative classes with different interfaces',
                'Incomplete library class',
                'Data class',
                'Refused bequest',
                'Comments'
            ],
            'design_smells': [
                'Rigidity',
                'Fragility',
                'Immobility',
                'Viscosity',
                'Needless complexity',
                'Needless repetition',
                'Opacity',
                'Shotgun surgery',
                'Parallel inheritance hierarchies',
                'Blob',
                'Lava flow',
                'Cyclic dependencies'
            ]
        }

    def _initialize_security_rules(self) -> Dict[str, List[str]]:
        """Initialize security review rules."""
        return {
            'vulnerabilities': [
                'SQL injection',
                'Command injection',
                'Cross-site scripting (XSS)',
                'Path traversal',
                'Insecure deserialization',
                'Weak cryptography',
                'Insufficient authentication',
                'Sensitive data exposure',
                'Security misconfiguration',
                'Broken access control'
            ],
            'anti_patterns': [
                'Hardcoded credentials',
                'Unvalidated input',
                'Unsafe type casting',
                'Race conditions',
                'Memory leaks',
                'Buffer overflows',
                'Integer overflow',
                'Format string vulnerabilities'
            ]
        }

    def review_file(self, file_path: Path) -> List[CodeReviewIssue]:
        """Review a single Python file."""
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            # Parse AST for structural analysis
            tree = ast.parse(content)

            # Review naming conventions
            issues.extend(self._review_naming_conventions(tree, lines, file_path))

            # Review code complexity
            issues.extend(self._review_complexity(tree, lines, file_path))

            # Review style and formatting
            issues.extend(self._review_style(tree, lines, file_path))

            # Review structure and design
            issues.extend(self._review_structure(tree, lines, file_path))

            # Review best practices
            issues.extend(self._review_best_practices(tree, lines, file_path))

            # Review anti-patterns
            issues.extend(self._review_anti_patterns(tree, lines, file_path))

            # Review security issues
            issues.extend(self._review_security(tree, lines, file_path))

            # Review error handling
            issues.extend(self._review_error_handling(tree, lines, file_path))

            # Review documentation
            issues.extend(self._review_documentation(tree, lines, file_path))

            # Review testing
            issues.extend(self._review_testing(tree, lines, file_path))

        except Exception as e:
            issues.append(CodeReviewIssue(
                id=f"parse_error_{hash(str(file_path))}",
                file_path=str(file_path),
                line_number=1,
                column_number=1,
                issue_type="parse_error",
                severity="critical",
                category="syntax",
                title="Parse Error",
                description=f"Unable to parse file: {str(e)}",
                suggestion="Fix syntax errors before reviewing",
                code_snippet="",
                rule_id="parse_error",
                auto_fixable=False,
                confidence=1.0,
                tags=["syntax", "error"]
            ))

        return issues

    def _review_naming_conventions(self, tree: ast.AST, lines: List[str], file_path: Path) -> List[CodeReviewIssue]:
        """Review naming conventions."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check function name
                if not re.match(self.review_rules['naming_conventions']['function_pattern'], node.name):
                    issues.append(CodeReviewIssue(
                        id=f"func_naming_{node.lineno}_{node.col_offset}",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        issue_type="naming_convention",
                        severity="warning",
                        category="style",
                        title="Function Naming Convention",
                        description=f"Function '{node.name}' should follow snake_case convention",
                        suggestion=f"Rename function to '{self._to_snake_case(node.name)}'",
                        code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                        rule_id="func_naming_snake_case",
                        auto_fixable=True,
                        confidence=0.9,
                        tags=["naming", "convention", "function"]
                    ))

                # Check parameter names
                for arg in node.args.args:
                    if not re.match(self.review_rules['naming_conventions']['variable_pattern'], arg.arg):
                        issues.append(CodeReviewIssue(
                            id=f"param_naming_{node.lineno}_{arg.col_offset}",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            column_number=arg.col_offset,
                            issue_type="naming_convention",
                            severity="info",
                            category="style",
                            title="Parameter Naming Convention",
                            description=f"Parameter '{arg.arg}' should follow snake_case convention",
                            suggestion=f"Rename parameter to '{self._to_snake_case(arg.arg)}'",
                            code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                            rule_id="param_naming_snake_case",
                            auto_fixable=True,
                            confidence=0.8,
                            tags=["naming", "convention", "parameter"]
                        ))

            elif isinstance(node, ast.ClassDef):
                # Check class name
                if not re.match(self.review_rules['naming_conventions']['class_pattern'], node.name):
                    issues.append(CodeReviewIssue(
                        id=f"class_naming_{node.lineno}_{node.col_offset}",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        issue_type="naming_convention",
                        severity="warning",
                        category="style",
                        title="Class Naming Convention",
                        description=f"Class '{node.name}' should follow PascalCase convention",
                        suggestion=f"Rename class to '{self._to_pascal_case(node.name)}'",
                        code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                        rule_id="class_naming_pascal_case",
                        auto_fixable=True,
                        confidence=0.9,
                        tags=["naming", "convention", "class"]
                    ))

            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                # Check variable names (avoid checking imports and other special cases)
                if node.id.isupper():
                    # Check constant naming
                    if not re.match(self.review_rules['naming_conventions']['constant_pattern'], node.id):
                        issues.append(CodeReviewIssue(
                            id=f"const_naming_{node.lineno}_{node.col_offset}",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            column_number=node.col_offset,
                            issue_type="naming_convention",
                            severity="info",
                            category="style",
                            title="Constant Naming Convention",
                            description=f"Constant '{node.id}' should follow UPPER_CASE convention",
                            suggestion=f"Rename constant to '{node.id.upper()}'",
                            code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                            rule_id="const_naming_upper_case",
                            auto_fixable=True,
                            confidence=0.7,
                            tags=["naming", "convention", "constant"]
                        ))
                elif not re.match(self.review_rules['naming_conventions']['variable_pattern'], node.id):
                    # Skip if it's likely a special name (private, dunder, etc.)
                    if not (node.id.startswith('_') and node.id.endswith('_')):
                        issues.append(CodeReviewIssue(
                            id=f"var_naming_{node.lineno}_{node.col_offset}",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            column_number=node.col_offset,
                            issue_type="naming_convention",
                            severity="info",
                            category="style",
                            title="Variable Naming Convention",
                            description=f"Variable '{node.id}' should follow snake_case convention",
                            suggestion=f"Rename variable to '{self._to_snake_case(node.id)}'",
                            code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                            rule_id="var_naming_snake_case",
                            auto_fixable=True,
                            confidence=0.6,
                            tags=["naming", "convention", "variable"]
                        ))

        return issues

    def _review_complexity(self, tree: ast.AST, lines: List[str], file_path: Path) -> List[CodeReviewIssue]:
        """Review code complexity."""
        issues = []

        # Check function length
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if hasattr(node, 'end_lineno'):
                    func_length = node.end_lineno - node.lineno + 1
                    if func_length > self.review_rules['complexity_rules']['max_function_length']:
                        issues.append(CodeReviewIssue(
                            id=f"func_length_{node.lineno}_{node.col_offset}",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            column_number=node.col_offset,
                            issue_type="complexity",
                            severity="warning",
                            category="maintainability",
                            title="Long Function",
                            description=f"Function '{node.name}' is {func_length} lines long (threshold: {self.review_rules['complexity_rules']['max_function_length']})",
                            suggestion="Consider breaking this function into smaller, more focused functions",
                            code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                            rule_id="function_too_long",
                            auto_fixable=False,
                            confidence=0.9,
                            tags=["complexity", "refactoring", "function"]
                        ))

                # Check cyclomatic complexity
                complexity = self._calculate_cyclomatic_complexity(node)
                if complexity > self.review_rules['complexity_rules']['max_complexity']:
                    issues.append(CodeReviewIssue(
                        id=f"func_complexity_{node.lineno}_{node.col_offset}",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        issue_type="complexity",
                        severity="warning",
                        category="maintainability",
                        title="High Cyclomatic Complexity",
                        description=f"Function '{node.name}' has cyclomatic complexity {complexity} (threshold: {self.review_rules['complexity_rules']['max_complexity']})",
                        suggestion="Consider simplifying the logic or extracting complex parts into separate functions",
                        code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                        rule_id="cyclomatic_complexity_high",
                        auto_fixable=False,
                        confidence=0.9,
                        tags=["complexity", "cyclomatic", "refactoring"]
                    ))

                # Check parameter count
                param_count = len(node.args.args)
                if param_count > self.review_rules['complexity_rules']['max_parameters']:
                    issues.append(CodeReviewIssue(
                        id=f"param_count_{node.lineno}_{node.col_offset}",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        issue_type="complexity",
                        severity="warning",
                        category="design",
                        title="Too Many Parameters",
                        description=f"Function '{node.name}' has {param_count} parameters (threshold: {self.review_rules['complexity_rules']['max_parameters']})",
                        suggestion="Consider using a parameter object or configuration class",
                        code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                        rule_id="too_many_parameters",
                        auto_fixable=False,
                        confidence=0.8,
                        tags=["complexity", "parameters", "design"]
                    ))

        # Check line length
        for line_num, line in enumerate(lines, 1):
            if len(line) > self.review_rules['complexity_rules']['max_line_length']:
                issues.append(CodeReviewIssue(
                    id=f"line_length_{line_num}",
                    file_path=str(file_path),
                    line_number=line_num,
                    column_number=self.review_rules['complexity_rules']['max_line_length'],
                    issue_type="style",
                    severity="info",
                    category="formatting",
                    title="Line Too Long",
                    description=f"Line is {len(line)} characters long (threshold: {self.review_rules['complexity_rules']['max_line_length']})",
                    suggestion="Break this line into multiple lines or use line continuation",
                    code_snippet=line.strip(),
                    rule_id="line_too_long",
                    auto_fixable=True,
                    confidence=0.9,
                    tags=["style", "formatting", "line_length"]
                ))

        return issues

    def _review_style(self, tree: ast.AST, lines: List[str], file_path: Path) -> List[CodeReviewIssue]:
        """Review code style and formatting."""
        issues = []

        # Check for import style violations
        import_names = []
        import_from_names = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_names.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    import_from_names.append(f"{module}.{alias.name}" if module else alias.name)

        # Check for star imports
        for import_name in import_names + import_from_names:
            if import_name.endswith('.*'):
                issues.append(CodeReviewIssue(
                    id=f"star_import_{hash(import_name)}",
                    file_path=str(file_path),
                    line_number=1,
                    column_number=1,
                    issue_type="style",
                    severity="warning",
                    category="imports",
                    title="Star Import Used",
                    description=f"Star import '{import_name}' can lead to namespace pollution",
                    suggestion="Import specific names instead of using star imports",
                    code_snippet=f"import {import_name}",
                    rule_id="star_import",
                    auto_fixable=True,
                    confidence=0.9,
                    tags=["imports", "style", "namespace"]
                ))

        # Check for required docstrings
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if self.review_rules['style_rules']['require_docstrings']:
                    docstring = ast.get_docstring(node)
                    if not docstring or len(docstring) < self.review_rules['style_rules']['required_docstring_length']:
                        issues.append(CodeReviewIssue(
                            id=f"missing_docstring_{node.lineno}_{node.col_offset}",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            column_number=node.col_offset,
                            issue_type="documentation",
                            severity="info",
                            category="documentation",
                            title=f"Missing Docstring for {type(node).__name__}",
                            description=f"{type(node).__name__.title()} '{node.name}' lacks a proper docstring",
                            suggestion=f"Add a comprehensive docstring explaining purpose, parameters, and return value",
                            code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                            rule_id="missing_docstring",
                            auto_fixable=False,
                            confidence=0.8,
                            tags=["documentation", "docstring", type(node).__name__.lower()]
                        ))

        return issues

    def _review_structure(self, tree: ast.AST, lines: List[str], file_path: Path) -> List[CodeReviewIssue]:
        """Review code structure and design."""
        issues = []

        # Check for large classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Count methods
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                if len(methods) > self.review_rules['structure_rules']['max_class_methods']:
                    issues.append(CodeReviewIssue(
                        id=f"large_class_{node.lineno}_{node.col_offset}",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        issue_type="design",
                        severity="warning",
                        category="design",
                        title="Large Class",
                        description=f"Class '{node.name}' has {len(methods)} methods (threshold: {self.review_rules['structure_rules']['max_class_methods']})",
                        suggestion="Consider breaking this class into smaller, more focused classes",
                        code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                        rule_id="large_class",
                        auto_fixable=False,
                        confidence=0.9,
                        tags=["design", "class", "solid"]
                    ))

                # Check for __init__ method
                if self.review_rules['structure_rules']['require_init_method']:
                    has_init = any(method.name == '__init__' for method in methods)
                    if not has_init:
                        issues.append(CodeReviewIssue(
                            id=f"missing_init_{node.lineno}_{node.col_offset}",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            column_number=node.col_offset,
                            issue_type="design",
                            severity="info",
                            category="design",
                            title="Missing __init__ Method",
                            description=f"Class '{node.name}' lacks an __init__ method",
                            suggestion="Add an __init__ method to properly initialize the class",
                            code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                            rule_id="missing_init",
                            auto_fixable=False,
                            confidence=0.6,
                            tags=["design", "class", "initialization"]
                        ))

        return issues

    def _review_best_practices(self, tree: ast.AST, lines: List[str], file_path: Path) -> List[CodeReviewIssue]:
        """Review adherence to best practices."""
        issues = []

        # Check for magic numbers
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    # Check if it's a magic number (not 0, 1, -1, 2, or common constants)
                    if node.value not in [0, 1, -1, 2, 100, 1000]:
                        issues.append(CodeReviewIssue(
                            id=f"magic_number_{node.lineno}_{node.col_offset}",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            column_number=node.col_offset,
                            issue_type="best_practice",
                            severity="info",
                            category="readability",
                            title="Magic Number",
                            description=f"Magic number {node.value} found in code",
                            suggestion="Replace with a named constant for better readability",
                            code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                            rule_id="magic_number",
                            auto_fixable=False,
                            confidence=0.7,
                            tags=["best_practice", "readability", "constants"]
                        ))

        # Check for bare except clauses
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                issues.append(CodeReviewIssue(
                    id=f"bare_except_{node.lineno}_{node.col_offset}",
                    file_path=str(file_path),
                    line_number=node.lineno,
                    column_number=node.col_offset,
                    issue_type="best_practice",
                    severity="warning",
                    category="error_handling",
                    title="Bare Except Clause",
                    description="Bare except clause can catch and hide important errors",
                    suggestion="Specify the exception types you want to catch",
                    code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                    rule_id="bare_except",
                    auto_fixable=False,
                    confidence=0.9,
                    tags=["best_practice", "error_handling", "exceptions"]
                ))

        return issues

    def _review_anti_patterns(self, tree: ast.AST, lines: List[str], file_path: Path) -> List[CodeReviewIssue]:
        """Review for common anti-patterns."""
        issues = []

        # Check for God class anti-pattern
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Count methods, attributes, and responsibilities
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                attributes = []

                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                attributes.append(target.id)

                # Heuristic for God class detection
                if len(methods) > 15 or len(attributes) > 20:
                    issues.append(CodeReviewIssue(
                        id=f"god_class_{node.lineno}_{node.col_offset}",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        column_number=node.col_offset,
                        issue_type="anti_pattern",
                        severity="warning",
                        category="design",
                        title="God Class Anti-Pattern",
                        description=f"Class '{node.name}' appears to be a God class with {len(methods)} methods and {len(attributes)} attributes",
                        suggestion="Consider breaking this class into smaller, more focused classes following Single Responsibility Principle",
                        code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                        rule_id="god_class",
                        auto_fixable=False,
                        confidence=0.8,
                        tags=["anti_pattern", "design", "solid", "refactoring"]
                    ))

        return issues

    def _review_security(self, tree: ast.AST, lines: List[str], file_path: Path) -> List[CodeReviewIssue]:
        """Review for security issues."""
        issues = []

        # Check for dangerous function usage
        dangerous_functions = ['eval', 'exec', 'compile', '__import__', 'input', 'raw_input']

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name in dangerous_functions:
                        severity = "critical" if func_name in ['eval', 'exec'] else "warning"
                        issues.append(CodeReviewIssue(
                            id=f"dangerous_func_{node.lineno}_{node.col_offset}",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            column_number=node.col_offset,
                            issue_type="security",
                            severity=severity,
                            category="security",
                            title=f"Dangerous Function: {func_name}",
                            description=f"Use of {func_name}() can be dangerous and lead to security vulnerabilities",
                            suggestion=f"Replace {func_name}() with safer alternatives",
                            code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                            rule_id=f"dangerous_function_{func_name}",
                            auto_fixable=False,
                            confidence=0.9,
                            tags=["security", "dangerous", "vulnerability"]
                        ))

        return issues

    def _review_error_handling(self, tree: ast.AST, lines: List[str], file_path: Path) -> List[CodeReviewIssue]:
        """Review error handling practices."""
        issues = []

        # Check for operations that should have error handling
        risky_operations = ['open(', 'json.loads(', 'int(', 'float(', 'dict[', 'list[']

        for line_num, line in enumerate(lines, 1):
            for operation in risky_operations:
                if operation in line:
                    # Check if there's a try block before this operation
                    has_try = False
                    for i in range(max(0, line_num - 5), line_num):
                        if 'try:' in lines[i]:
                            has_try = True
                            break

                    if not has_try:
                        issues.append(CodeReviewIssue(
                            id=f"missing_error_handling_{line_num}",
                            file_path=str(file_path),
                            line_number=line_num,
                            column_number=line.find(operation) + 1,
                            issue_type="error_handling",
                            severity="info",
                            category="error_handling",
                            title="Potentially Unhandled Operation",
                            description=f"Risky operation '{operation}' without error handling",
                            suggestion="Consider wrapping this operation in a try-except block",
                            code_snippet=line.strip(),
                            rule_id="missing_error_handling",
                            auto_fixable=False,
                            confidence=0.6,
                            tags=["error_handling", "safety", "robustness"]
                        ))

        return issues

    def _review_documentation(self, tree: ast.AST, lines: List[str], file_path: Path) -> List[CodeReviewIssue]:
        """Review documentation quality."""
        issues = []

        # Check for module-level docstring
        module_docstring = ast.get_docstring(tree)
        if not module_docstring or len(module_docstring) < 20:
            issues.append(CodeReviewIssue(
                id="missing_module_docstring",
                file_path=str(file_path),
                line_number=1,
                column_number=1,
                issue_type="documentation",
                severity="info",
                category="documentation",
                title="Missing Module Documentation",
                description="Module lacks a proper docstring",
                suggestion="Add a comprehensive module docstring explaining the module's purpose and usage",
                code_snippet=lines[0].strip() if lines else "",
                rule_id="missing_module_docstring",
                auto_fixable=False,
                confidence=0.8,
                tags=["documentation", "module", "readme"]
            ))

        return issues

    def _review_testing(self, tree: ast.AST, lines: List[str], file_path: Path) -> List[CodeReviewIssue]:
        """Review testing-related practices."""
        issues = []

        # If this is a test file, check for proper test structure
        if 'test' in file_path.name.lower():
            # Check for test functions
            test_functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')]

            if not test_functions:
                issues.append(CodeReviewIssue(
                    id="no_test_functions",
                    file_path=str(file_path),
                    line_number=1,
                    column_number=1,
                    issue_type="testing",
                    severity="warning",
                    category="testing",
                    title="No Test Functions Found",
                    description="Test file doesn't contain any test functions (functions starting with 'test_')",
                    suggestion="Add test functions following the naming convention 'test_*'",
                    code_snippet="",
                    rule_id="no_test_functions",
                    auto_fixable=False,
                    confidence=0.9,
                    tags=["testing", "structure", "quality"]
                ))

        return issues

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

        return complexity

    def _to_snake_case(self, name: str) -> str:
        """Convert a name to snake_case."""
        # Insert underscores before capital letters
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        return s2.lower()

    def _to_pascal_case(self, name: str) -> str:
        """Convert a name to PascalCase."""
        # Split by underscores and capitalize each part
        parts = name.split('_')
        return ''.join(part.capitalize() for part in parts if part)

    def analyze_project(self) -> Dict[str, Any]:
        """Analyze entire project for code review."""
        print("Scanning project for code review...")

        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.venv', 'venv', 'node_modules'}]

            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)

        print(f"Found {len(python_files)} Python files")

        # Review each file
        all_issues = []
        for file_path in python_files:
            print(f"Reviewing {file_path}...")
            issues = self.review_file(file_path)
            all_issues.extend(issues)

        # Calculate metrics
        metrics = self._calculate_review_metrics(all_issues, len(python_files))

        return {
            'review_summary': asdict(metrics),
            'issues': [asdict(issue) for issue in all_issues],
            'analysis_timestamp': time.time()
        }

    def _calculate_review_metrics(self, issues: List[CodeReviewIssue], file_count: int) -> CodeReviewMetrics:
        """Calculate code review metrics."""
        if not issues:
            return CodeReviewMetrics(
                total_issues=0,
                issues_by_severity={},
                issues_by_category={},
                issues_by_file={},
                auto_fixable_count=0,
                avg_confidence=0.0,
                review_score=100.0
            )

        # Count issues by various dimensions
        issues_by_severity = defaultdict(int)
        issues_by_category = defaultdict(int)
        issues_by_file = defaultdict(int)
        auto_fixable_count = 0
        total_confidence = 0

        for issue in issues:
            issues_by_severity[issue.severity] += 1
            issues_by_category[issue.category] += 1
            issues_by_file[issue.file_path] += 1
            if issue.auto_fixable:
                auto_fixable_count += 1
            total_confidence += issue.confidence

        # Calculate overall review score (0-100, higher is better)
        severity_weights = {'critical': 10, 'error': 5, 'warning': 2, 'info': 1}
        weighted_issues = sum(severity_weights.get(issue.severity, 1) for issue in issues)
        max_possible_score = 100
        review_score = max(0, max_possible_score - weighted_issues)

        return CodeReviewMetrics(
            total_issues=len(issues),
            issues_by_severity=dict(issues_by_severity),
            issues_by_category=dict(issues_by_category),
            issues_by_file=dict(issues_by_file),
            auto_fixable_count=auto_fixable_count,
            avg_confidence=total_confidence / len(issues),
            review_score=review_score
        )

    def generate_report(self, analysis_results: Dict[str, Any], output_path: str = None) -> str:
        """Generate code review report."""
        if output_path is None:
            output_path = '/home/activeloguser/DMLogn8n/quality/reports/code_review_report.json'

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)

        return output_path


def main():
    """Main function for standalone usage."""
    project_root = '/home/activeloguser/DMLogn8n'
    reviewer = CodeReviewer(project_root)

    print("Starting code review analysis...")
    results = reviewer.analyze_project()

    # Generate report
    report_path = reviewer.generate_report(results)
    print(f"Review complete. Report saved to: {report_path}")

    # Print summary
    summary = results['review_summary']
    print(f"\n=== Code Review Summary ===")
    print(f"Total issues found: {summary['total_issues']}")
    print(f"Overall review score: {summary['review_score']:.1f}/100")
    print(f"Auto-fixable issues: {summary['auto_fixable_count']}")
    print(f"Average confidence: {summary['avg_confidence']:.2f}")

    print(f"\n=== Issues by Severity ===")
    for severity, count in summary['issues_by_severity'].items():
        print(f"{severity}: {count}")

    print(f"\n=== Issues by Category ===")
    for category, count in summary['issues_by_category'].items():
        print(f"{category}: {count}")

    print(f"\n=== Files with Most Issues ===")
    sorted_files = sorted(summary['issues_by_file'].items(), key=lambda x: x[1], reverse=True)
    for file_path, count in sorted_files[:5]:
        print(f"{Path(file_path).name}: {count} issues")


if __name__ == "__main__":
    main()