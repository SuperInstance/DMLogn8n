#!/usr/bin/env python3
"""
Comprehensive Code Quality Analyzer
Analyzes Python code for quality metrics, complexity, and maintainability issues.
"""

import ast
import os
import re
import sys
import json
import time
import hashlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import radon.complexity as radon_cc
import radon.metrics as radon_metrics
from pylint.lint import Run
from pylint.reporters import JSONReporter
import bandit
from bandit.core import manager


@dataclass
class CodeMetrics:
    """Data class for code quality metrics."""
    file_path: str
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    cyclomatic_complexity: float
    maintainability_index: float
    halstead_metrics: Dict[str, float]
    function_complexity: List[Dict[str, Any]]
    class_metrics: List[Dict[str, Any]]
    imports: List[str]
    dependencies: List[str]
    code_smells: List[str]
    duplicates: List[Dict[str, Any]]
    security_issues: List[Dict[str, Any]]
    naming_issues: List[Dict[str, Any]]
    docstring_coverage: float
    type_annotation_coverage: float


class CodeAnalyzer:
    """Comprehensive code quality analysis system."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.metrics_cache = {}
        self.excluded_dirs = {'.git', '__pycache__', '.venv', 'venv', 'env', 'node_modules'}
        self.excluded_files = {'.pyc', '.pyo', '.pyd'}
        self.python_files = []

    def scan_project(self) -> List[Path]:
        """Scan project for Python files."""
        python_files = []

        for root, dirs, files in os.walk(self.project_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]

            for file in files:
                if file.endswith('.py') and not any(file.endswith(ext) for ext in self.excluded_files):
                    python_files.append(Path(root) / file)

        self.python_files = python_files
        return python_files

    def analyze_file(self, file_path: Path) -> CodeMetrics:
        """Analyze a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Calculate basic metrics
            lines = content.split('\n')
            total_lines = len(lines)
            code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            comment_lines = len([line for line in lines if line.strip().startswith('#')])
            blank_lines = len([line for line in lines if not line.strip()])

            # Parse AST
            tree = ast.parse(content)

            # Calculate complexity metrics
            complexity = self._calculate_complexity(tree)
            maintainability = self._calculate_maintainability(content)
            halstead = self._calculate_halstead_metrics(tree)

            # Analyze functions and classes
            function_metrics = self._analyze_functions(tree)
            class_metrics = self._analyze_classes(tree)

            # Extract imports and dependencies
            imports = self._extract_imports(tree)
            dependencies = self._analyze_dependencies(content, imports)

            # Detect code issues
            code_smells = self._detect_code_smells(tree, content)
            duplicates = self._detect_duplicates(content, file_path)
            security_issues = self._analyze_security(content, file_path)
            naming_issues = self._analyze_naming_conventions(tree)

            # Calculate coverage metrics
            docstring_coverage = self._calculate_docstring_coverage(tree)
            type_coverage = self._calculate_type_annotation_coverage(tree)

            return CodeMetrics(
                file_path=str(file_path),
                total_lines=total_lines,
                code_lines=code_lines,
                comment_lines=comment_lines,
                blank_lines=blank_lines,
                cyclomatic_complexity=complexity,
                maintainability_index=maintainability,
                halstead_metrics=halstead,
                function_complexity=function_metrics,
                class_metrics=class_metrics,
                imports=imports,
                dependencies=dependencies,
                code_smells=code_smells,
                duplicates=duplicates,
                security_issues=security_issues,
                naming_issues=naming_issues,
                docstring_coverage=docstring_coverage,
                type_annotation_coverage=type_coverage
            )

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None

    def _calculate_complexity(self, tree: ast.AST) -> float:
        """Calculate cyclomatic complexity using radon."""
        try:
            complexity = radon_cc.cc_visit(tree)
            total_complexity = sum(item.complexity for item in complexity)
            return total_complexity
        except Exception:
            return 0.0

    def _calculate_maintainability(self, content: str) -> float:
        """Calculate maintainability index."""
        try:
            mi = radon_metrics.mi_visit(content, multi=True)
            return mi
        except Exception:
            return 0.0

    def _calculate_halstead_metrics(self, tree: ast.AST) -> Dict[str, float]:
        """Calculate Halstead metrics."""
        try:
            h1 = h2 = N1 = N2 = 0
            operators = set()
            operands = set()

            for node in ast.walk(tree):
                if isinstance(node, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod)):
                    operators.add(type(node).__name__)
                    h1 += 1
                elif isinstance(node, ast.Name):
                    operands.add(node.id)
                    h2 += 1
                elif isinstance(node, ast.Constant):
                    operands.add(str(node.value))
                    h2 += 1

            N1 = h1
            N2 = h2

            # Calculate Halstead metrics
            vocabulary = len(operators) + len(operands)
            length = N1 + N2

            if vocabulary > 0 and length > 0:
                difficulty = (len(operators) / 2) * (N2 / len(operands)) if len(operands) > 0 else 0
                effort = difficulty * length
                volume = length * (math.log2(vocabulary) if vocabulary > 0 else 0)

                return {
                    'vocabulary': vocabulary,
                    'length': length,
                    'difficulty': difficulty,
                    'effort': effort,
                    'volume': volume
                }

            return {'vocabulary': 0, 'length': 0, 'difficulty': 0, 'effort': 0, 'volume': 0}

        except Exception:
            return {'vocabulary': 0, 'length': 0, 'difficulty': 0, 'effort': 0, 'volume': 0}

    def _analyze_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Analyze function metrics."""
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Calculate function complexity
                func_complexity = radon_cc.cc_visit(node)
                complexity = func_complexity[0].complexity if func_complexity else 1

                # Count parameters
                args = len(node.args.args)
                defaults = len(node.args.defaults)

                # Check for docstring
                has_docstring = (ast.get_docstring(node) is not None)

                # Count lines
                lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0

                functions.append({
                    'name': node.name,
                    'line': node.lineno,
                    'complexity': complexity,
                    'parameters': args,
                    'defaults': defaults,
                    'has_docstring': has_docstring,
                    'lines': lines
                })

        return functions

    def _analyze_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Analyze class metrics."""
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Count methods
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                method_count = len(methods)

                # Count attributes
                attributes = []
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                attributes.append(target.id)

                # Check base classes
                base_classes = [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases]

                # Check for docstring
                has_docstring = (ast.get_docstring(node) is not None)

                classes.append({
                    'name': node.name,
                    'line': node.lineno,
                    'methods': method_count,
                    'attributes': len(attributes),
                    'base_classes': base_classes,
                    'has_docstring': has_docstring
                })

        return classes

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements."""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)

        return imports

    def _analyze_dependencies(self, content: str, imports: List[str]) -> List[str]:
        """Analyze external dependencies."""
        dependencies = []

        for import_name in imports:
            # Check if it's a standard library import
            if not self._is_standard_library(import_name.split('.')[0]):
                dependencies.append(import_name)

        return dependencies

    def _is_standard_library(self, module_name: str) -> bool:
        """Check if a module is from Python standard library."""
        try:
            importlib.import_module(module_name)
            # If it's importable and in the stdlib path, consider it standard
            return module_name in sys.builtin_module_names
        except ImportError:
            return False

    def _detect_code_smells(self, tree: ast.AST, content: str) -> List[str]:
        """Detect common code smells."""
        smells = []

        # Long method detection
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
                if lines > 50:
                    smells.append(f"Long method: {node.name} ({lines} lines)")

                # Too many parameters
                if len(node.args.args) > 7:
                    smells.append(f"Too many parameters: {node.name} ({len(node.args.args)} params)")

        # Large class detection
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                if len(methods) > 20:
                    smells.append(f"Large class: {node.name} ({len(methods)} methods)")

        # Duplicate code detection (simple)
        lines = content.split('\n')
        line_counts = Counter(lines)
        for line, count in line_counts.items():
            if count > 3 and len(line.strip()) > 20:  # Ignore short lines
                smells.append(f"Duplicate code line (appears {count} times): {line[:50]}...")

        return smells

    def _detect_duplicates(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Detect code duplicates using hash-based approach."""
        duplicates = []
        lines = content.split('\n')
        line_hashes = {}

        for i, line in enumerate(lines, 1):
            if len(line.strip()) < 10:  # Skip short lines
                continue

            line_hash = hashlib.md5(line.strip().encode()).hexdigest()

            if line_hash in line_hashes:
                duplicates.append({
                    'line': i,
                    'content': line.strip(),
                    'duplicate_of': line_hashes[line_hash]
                })
            else:
                line_hashes[line_hash] = i

        return duplicates

    def _analyze_security(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Analyze security issues using bandit."""
        try:
            # Create a temporary file for bandit analysis
            temp_file = f"/tmp/bandit_{hash(str(file_path))}.py"
            with open(temp_file, 'w') as f:
                f.write(content)

            # Run bandit
            b_mgr = manager.BanditManager(bandit.config.BanditConfig(), 'file')
            b_mgr.discover_files([temp_file], False)
            b_mgr.run_tests()

            issues = []
            for result in b_mgr.get_issue_list():
                issues.append({
                    'severity': result.severity,
                    'confidence': result.confidence,
                    'text': result.text,
                    'line': result.lineno,
                    'test_id': result.test_id
                })

            # Clean up
            os.remove(temp_file)
            return issues

        except Exception:
            return []

    def _analyze_naming_conventions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Analyze naming conventions."""
        issues = []

        # Check function names (should be snake_case)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                    issues.append({
                        'type': 'function_naming',
                        'name': node.name,
                        'line': node.lineno,
                        'issue': 'Function name should be snake_case'
                    })

        # Check class names (should be PascalCase)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                    issues.append({
                        'type': 'class_naming',
                        'name': node.name,
                        'line': node.lineno,
                        'issue': 'Class name should be PascalCase'
                    })

        return issues

    def _calculate_docstring_coverage(self, tree: ast.AST) -> float:
        """Calculate docstring coverage."""
        total_functions = 0
        documented_functions = 0
        total_classes = 0
        documented_classes = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                total_functions += 1
                if ast.get_docstring(node):
                    documented_functions += 1
            elif isinstance(node, ast.ClassDef):
                total_classes += 1
                if ast.get_docstring(node):
                    documented_classes += 1

        total_items = total_functions + total_classes
        documented_items = documented_functions + documented_classes

        return (documented_items / total_items * 100) if total_items > 0 else 0.0

    def _calculate_type_annotation_coverage(self, tree: ast.AST) -> float:
        """Calculate type annotation coverage."""
        total_functions = 0
        annotated_functions = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                total_functions += 1
                has_annotations = (
                    node.returns is not None or
                    any(arg.annotation is not None for arg in node.args.args)
                )
                if has_annotations:
                    annotated_functions += 1

        return (annotated_functions / total_functions * 100) if total_functions > 0 else 0.0

    def analyze_project(self) -> Dict[str, Any]:
        """Analyze entire project."""
        print(f"Scanning project for Python files...")
        python_files = self.scan_project()

        print(f"Found {len(python_files)} Python files")

        all_metrics = []
        project_summary = {
            'total_files': len(python_files),
            'total_lines': 0,
            'total_complexity': 0,
            'avg_maintainability': 0,
            'security_issues': 0,
            'code_smells': 0,
            'files_analyzed': 0
        }

        for file_path in python_files:
            print(f"Analyzing {file_path}")
            metrics = self.analyze_file(file_path)

            if metrics:
                all_metrics.append(metrics)
                project_summary['total_lines'] += metrics.total_lines
                project_summary['total_complexity'] += metrics.cyclomatic_complexity
                project_summary['security_issues'] += len(metrics.security_issues)
                project_summary['code_smells'] += len(metrics.code_smells)
                project_summary['files_analyzed'] += 1

        # Calculate averages
        if all_metrics:
            project_summary['avg_maintainability'] = sum(
                m.maintainability_index for m in all_metrics
            ) / len(all_metrics)

        return {
            'project_summary': project_summary,
            'file_metrics': [asdict(m) for m in all_metrics],
            'analysis_timestamp': time.time()
        }

    def generate_report(self, analysis_results: Dict[str, Any], output_path: str = None) -> str:
        """Generate comprehensive analysis report."""
        if output_path is None:
            output_path = '/home/activeloguser/DMLogn8n/quality/reports/code_analysis_report.json'

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)

        return output_path


def main():
    """Main function for standalone usage."""
    import math

    project_root = '/home/activeloguser/DMLogn8n'
    analyzer = CodeAnalyzer(project_root)

    print("Starting comprehensive code analysis...")
    results = analyzer.analyze_project()

    # Generate report
    report_path = analyzer.generate_report(results)
    print(f"Analysis complete. Report saved to: {report_path}")

    # Print summary
    summary = results['project_summary']
    print(f"\n=== Code Analysis Summary ===")
    print(f"Files analyzed: {summary['files_analyzed']}")
    print(f"Total lines of code: {summary['total_lines']}")
    print(f"Total complexity: {summary['total_complexity']:.1f}")
    print(f"Average maintainability: {summary['avg_maintainability']:.1f}")
    print(f"Security issues found: {summary['security_issues']}")
    print(f"Code smells detected: {summary['code_smells']}")


if __name__ == "__main__":
    main()