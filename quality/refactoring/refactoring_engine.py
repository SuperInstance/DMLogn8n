#!/usr/bin/env python3
"""
Automated Refactoring Engine
Provides safe code transformation suggestions and automated refactoring tools.
"""

import ast
import os
import re
import sys
import difflib
import autopep8
import isort
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Set
from dataclasses import dataclass, asdict
from collections import defaultdict
import black
from libcst import matchers as m, parse_module, MetadataWrapper, CSTNode
from libcst.codemod import CodemodContext, VisitorBasedCodemod
import libcst as cst


@dataclass
class RefactoringSuggestion:
    """Data class for refactoring suggestions."""
    file_path: str
    line_number: int
    issue_type: str
    description: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    auto_fixable: bool
    suggested_code: str
    original_code: str
    confidence: float  # 0.0 to 1.0


@dataclass
class RefactoringPlan:
    """Data class for refactoring plan."""
    suggestions: List[RefactoringSuggestion]
    estimated_effort: Dict[str, int]  # hours by category
    risk_assessment: Dict[str, Any]
    dependencies: List[str]
    test_requirements: List[str]


class ExtractMethodVisitor(VisitorBasedCodemod):
    """CST visitor for extracting methods."""

    def __init__(self, context: CodemodContext, target_line: int, method_name: str):
        super().__init__(context)
        self.target_line = target_line
        self.method_name = method_name

    @m.call()
    def visit_call(self, node: cst.Call) -> None:
        """Identify extractable method calls."""
        if hasattr(node, 'position') and node.position:
            if node.position.line == self.target_line:
                # This is a candidate for method extraction
                pass


class RefactoringEngine:
    """Automated refactoring suggestion and transformation engine."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.refactoring_rules = self._initialize_refactoring_rules()
        self.risk_patterns = self._initialize_risk_patterns()
        self.transformation_history = []

    def _initialize_refactoring_rules(self) -> Dict[str, Any]:
        """Initialize refactoring rules and patterns."""
        return {
            'extract_method': {
                'min_lines': 5,
                'max_lines': 50,
                'complexity_threshold': 3,
                'patterns': [
                    r'if.*:\s*\n\s*(.*\n){3,}',
                    r'for.*:\s*\n\s*(.*\n){3,}',
                    r'try:\s*\n\s*(.*\n){3,}'
                ]
            },
            'extract_variable': {
                'min_length': 20,
                'patterns': [
                    r'\w+\.\w+\(\w+\,\s*\w+.*\)',
                    r'\w+\s*\+\s*\w+\s*\+\s*\w+',
                    r'\w+\s*\*\s*\d+',
                ]
            },
            'inline_variable': {
                'usage_count_threshold': 2,
                'simple_assignment': True,
            },
            'replace_conditional_with_polymorphism': {
                'min_type_checks': 3,
                'if_chain_length': 3,
            },
            'split_temporary_variable': {
                'reassignment_pattern': r'(\w+)\s*=.*\n.*\1\s*=',
            },
            'remove_dead_code': {
                'unused_import_patterns': [],
                'unreachable_code_patterns': [
                    r'return.*\n.*',
                    r'raise.*\n.*',
                    r'break.*\n.*',
                ]
            }
        }

    def _initialize_risk_patterns(self) -> Dict[str, Any]:
        """Initialize high-risk refactoring patterns."""
        return {
            'high_risk': [
                'class_hierarchy_changes',
                'interface_modifications',
                'public_api_changes',
                'database_schema_changes',
            ],
            'medium_risk': [
                'method_signature_changes',
                'access_modifier_changes',
                'exception_handling_changes',
            ],
            'low_risk': [
                'formatting_changes',
                'variable_renaming',
                'comment_additions',
                'import_reorganization',
            ]
        }

    def analyze_file(self, file_path: Path) -> List[RefactoringSuggestion]:
        """Analyze a file for refactoring opportunities."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            suggestions = []

            # Parse AST for analysis
            tree = ast.parse(content)
            cst_tree = parse_module(content)

            # Extract method suggestions
            suggestions.extend(self._suggest_method_extraction(tree, content, file_path))

            # Extract variable suggestions
            suggestions.extend(self._suggest_variable_extraction(tree, content, file_path))

            # Inline variable suggestions
            suggestions.extend(self._suggest_variable_inlining(tree, content, file_path))

            # Conditional to polymorphism suggestions
            suggestions.extend(self._suggest_polymorphism(tree, content, file_path))

            # Split temporary variable suggestions
            suggestions.extend(self._suggest_variable_splitting(tree, content, file_path))

            # Dead code removal suggestions
            suggestions.extend(self._suggest_dead_code_removal(tree, content, file_path))

            # Code formatting suggestions
            suggestions.extend(self._suggest_formatting_improvements(content, file_path))

            # Import organization suggestions
            suggestions.extend(self._suggest_import_organization(tree, content, file_path))

            return sorted(suggestions, key=lambda x: self._severity_priority(x.severity))

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return []

    def _suggest_method_extraction(self, tree: ast.AST, content: str, file_path: Path) -> List[RefactoringSuggestion]:
        """Suggest method extraction opportunities."""
        suggestions = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.If, ast.While, ast.Try)):
                # Check if this block could be extracted
                if hasattr(node, 'end_lineno'):
                    lines = node.end_lineno - node.lineno + 1

                    if (self.refactoring_rules['extract_method']['min_lines'] <= lines <=
                        self.refactoring_rules['extract_method']['max_lines']):

                        # Calculate complexity of this block
                        block_complexity = self._calculate_block_complexity(node)

                        if block_complexity >= self.refactoring_rules['extract_method']['complexity_threshold']:
                            method_name = f"extracted_method_{node.lineno}"

                            # Extract the code block
                            lines_list = content.split('\n')
                            block_code = '\n'.join(lines_list[node.lineno-1:node.end_lineno])

                            suggestions.append(RefactoringSuggestion(
                                file_path=str(file_path),
                                line_number=node.lineno,
                                issue_type='extract_method',
                                description=f"Extract {lines} lines into method '{method_name}' (complexity: {block_complexity})",
                                severity='medium',
                                auto_fixable=True,
                                suggested_code=f"# Extracted method: {method_name}\n{block_code}",
                                original_code=block_code,
                                confidence=0.8
                            ))

        return suggestions

    def _suggest_variable_extraction(self, tree: ast.AST, content: str, file_path: Path) -> List[RefactoringSuggestion]:
        """Suggest variable extraction opportunities."""
        suggestions = []
        lines = content.split('\n')

        for i, line in enumerate(lines):
            if len(line.strip()) > self.refactoring_rules['extract_variable']['min_length']:
                for pattern in self.refactoring_rules['extract_variable']['patterns']:
                    if re.search(pattern, line) and '=' not in line:
                        # This complex expression could be extracted to a variable
                        var_name = f"extracted_var_{i+1}"

                        suggestions.append(RefactoringSuggestion(
                            file_path=str(file_path),
                            line_number=i+1,
                            issue_type='extract_variable',
                            description=f"Extract complex expression to variable '{var_name}'",
                            severity='low',
                            auto_fixable=True,
                            suggested_code=f"{var_name} = {line.strip()}",
                            original_code=line.strip(),
                            confidence=0.7
                        ))
                        break

        return suggestions

    def _suggest_variable_inlining(self, tree: ast.AST, content: str, file_path: Path) -> List[RefactoringSuggestion]:
        """Suggest variable inlining opportunities."""
        suggestions = []
        variable_usage = defaultdict(list)

        # Track variable usage
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                variable_usage[node.id].append(node.lineno)

        # Check for variables that are used few times
        for var_name, line_numbers in variable_usage.items():
            if (len(line_numbers) <= self.refactoring_rules['inline_variable']['usage_count_threshold'] and
                len(line_numbers) > 1):

                suggestions.append(RefactoringSuggestion(
                    file_path=str(file_path),
                    line_number=line_numbers[0],
                    issue_type='inline_variable',
                    description=f"Consider inlining variable '{var_name}' (used {len(line_numbers)} times)",
                    severity='low',
                    auto_fixable=False,  # Requires more complex analysis
                    suggested_code=f"# Inline variable '{var_name}'",
                    original_code=f"{var_name} = ...",
                    confidence=0.6
                ))

        return suggestions

    def _suggest_polymorphism(self, tree: ast.AST, content: str, file_path: Path) -> List[RefactoringSuggestion]:
        """Suggest replacing conditionals with polymorphism."""
        suggestions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                # Count type checks in this if-elif-else chain
                type_checks = self._count_type_checks(node)

                if type_checks >= self.refactoring_rules['replace_conditional_with_polymorphism']['min_type_checks']:
                    suggestions.append(RefactoringSuggestion(
                        file_path=str(file_path),
                        line_number=node.lineno,
                        issue_type='replace_conditional_with_polymorphism',
                        description=f"Replace conditional with polymorphism ({type_checks} type checks)",
                        severity='high',
                        auto_fixable=False,
                        suggested_code="# Use polymorphism instead of type checking",
                        original_code="# Type checking conditional",
                        confidence=0.9
                    ))

        return suggestions

    def _suggest_variable_splitting(self, tree: ast.AST, content: str, file_path: Path) -> List[RefactoringSuggestion]:
        """Suggest splitting temporary variables."""
        suggestions = []
        lines = content.split('\n')
        variable_assignments = defaultdict(list)

        # Track variable assignments
        for i, line in enumerate(lines):
            match = re.match(r'^(\s*)(\w+)\s*=', line)
            if match:
                var_name = match.group(2)
                variable_assignments[var_name].append(i+1)

        # Check for variables with multiple assignments
        for var_name, line_numbers in variable_assignments.items():
            if len(line_numbers) > 1:
                suggestions.append(RefactoringSuggestion(
                    file_path=str(file_path),
                    line_number=line_numbers[0],
                    issue_type='split_temporary_variable',
                    description=f"Split temporary variable '{var_name}' ({len(line_numbers)} assignments)",
                    severity='medium',
                    auto_fixable=False,
                    suggested_code=f"# Split variable '{var_name}' into separate variables",
                    original_code=f"{var_name} = ...",
                    confidence=0.7
                ))

        return suggestions

    def _suggest_dead_code_removal(self, tree: ast.AST, content: str, file_path: Path) -> List[RefactoringSuggestion]:
        """Suggest dead code removal."""
        suggestions = []

        # Find unreachable code
        lines = content.split('\n')
        for i, line in enumerate(lines):
            for pattern in self.refactoring_rules['remove_dead_code']['unreachable_code_patterns']:
                if re.match(pattern, line.strip()):
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and not next_line.startswith('#'):
                            suggestions.append(RefactoringSuggestion(
                                file_path=str(file_path),
                                line_number=i+2,
                                issue_type='remove_dead_code',
                                description=f"Remove unreachable code after '{line.strip()}'",
                                severity='medium',
                                auto_fixable=True,
                                suggested_code="# Remove this unreachable code",
                                original_code=next_line,
                                confidence=0.9
                            ))

        return suggestions

    def _suggest_formatting_improvements(self, content: str, file_path: Path) -> List[RefactoringSuggestion]:
        """Suggest formatting improvements."""
        suggestions = []

        # Check with black
        try:
            formatted_content = black.format_str(content)
            if formatted_content != content:
                suggestions.append(RefactoringSuggestion(
                    file_path=str(file_path),
                    line_number=1,
                    issue_type='formatting',
                    description="Apply black formatting for consistent style",
                    severity='low',
                    auto_fixable=True,
                    suggested_code=formatted_content,
                    original_code=content,
                    confidence=0.95
                ))
        except Exception:
            pass

        # Check with autopep8
        try:
            fixed_content = autopep8.fix_code(content)
            if fixed_content != content:
                suggestions.append(RefactoringSuggestion(
                    file_path=str(file_path),
                    line_number=1,
                    issue_type='pep8_formatting',
                    description="Fix PEP 8 style issues",
                    severity='low',
                    auto_fixable=True,
                    suggested_code=fixed_content,
                    original_code=content,
                    confidence=0.9
                ))
        except Exception:
            pass

        return suggestions

    def _suggest_import_organization(self, tree: ast.AST, content: str, file_path: Path) -> List[RefactoringSuggestion]:
        """Suggest import organization improvements."""
        suggestions = []

        try:
            sorted_imports = isort.code(content)
            if sorted_imports != content:
                suggestions.append(RefactoringSuggestion(
                    file_path=str(file_path),
                    line_number=1,
                    issue_type='import_organization',
                    description="Organize imports according to isort standards",
                    severity='low',
                    auto_fixable=True,
                    suggested_code=sorted_imports,
                    original_code=content,
                    confidence=0.95
                ))
        except Exception:
            pass

        return suggestions

    def _calculate_block_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a code block."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.With)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1

        return complexity

    def _count_type_checks(self, node: ast.If) -> int:
        """Count type checks in an if-elif-else chain."""
        type_checks = 0
        current = node

        while isinstance(current, ast.If):
            # Check if this is a type check
            if isinstance(current.test, ast.Call) and isinstance(current.test.func, ast.Name):
                if current.test.func.id in ['isinstance', 'type', 'hasattr']:
                    type_checks += 1
            elif isinstance(current.test, ast.Compare):
                # Look for type comparisons
                for comparator in current.test.ops:
                    if isinstance(comparator, ast.Is):
                        type_checks += 1

            current = current.orelse[0] if current.orelse else None

        return type_checks

    def _severity_priority(self, severity: str) -> int:
        """Get priority value for severity sorting."""
        priorities = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        return priorities.get(severity, 3)

    def create_refactoring_plan(self, suggestions: List[RefactoringSuggestion]) -> RefactoringPlan:
        """Create a comprehensive refactoring plan."""
        # Categorize suggestions by type and severity
        categories = defaultdict(list)
        for suggestion in suggestions:
            categories[suggestion.issue_type].append(suggestion)

        # Estimate effort in hours
        effort_estimates = {
            'extract_method': 2,
            'extract_variable': 0.5,
            'inline_variable': 1,
            'replace_conditional_with_polymorphism': 8,
            'split_temporary_variable': 1,
            'remove_dead_code': 0.5,
            'formatting': 0.25,
            'import_organization': 0.25,
            'pep8_formatting': 0.25,
        }

        total_effort = {}
        for category, category_suggestions in categories.items():
            effort_per_item = effort_estimates.get(category, 1)
            total_effort[category] = len(category_suggestions) * effort_per_item

        # Risk assessment
        high_risk_count = len([s for s in suggestions if s.severity == 'critical' or s.severity == 'high'])
        medium_risk_count = len([s for s in suggestions if s.severity == 'medium'])
        low_risk_count = len([s for s in suggestions if s.severity == 'low'])

        risk_assessment = {
            'overall_risk': 'high' if high_risk_count > 5 else 'medium' if high_risk_count > 0 else 'low',
            'high_risk_items': high_risk_count,
            'medium_risk_items': medium_risk_count,
            'low_risk_items': low_risk_count,
            'auto_fixable_ratio': len([s for s in suggestions if s.auto_fixable]) / len(suggestions) if suggestions else 0
        }

        # Identify dependencies
        dependencies = []
        if any(s.issue_type == 'replace_conditional_with_polymorphism' for s in suggestions):
            dependencies.append('class_hierarchy_analysis')
        if any(s.issue_type == 'extract_method' for s in suggestions):
            dependencies.append('unit_tests')

        # Test requirements
        test_requirements = []
        if any(s.severity in ['high', 'critical'] for s in suggestions):
            test_requirements.append('comprehensive_unit_tests')
            test_requirements.append('integration_tests')
        if any(s.issue_type == 'replace_conditional_with_polymorphism' for s in suggestions):
            test_requirements.append('polymorphism_tests')

        return RefactoringPlan(
            suggestions=suggestions,
            estimated_effort=total_effort,
            risk_assessment=risk_assessment,
            dependencies=dependencies,
            test_requirements=test_requirements
        )

    def apply_auto_fixable_suggestions(self, suggestions: List[RefactoringSuggestion]) -> Dict[str, Any]:
        """Apply auto-fixable suggestions safely."""
        applied_suggestions = []
        failed_suggestions = []
        backup_files = []

        for suggestion in suggestions:
            if not suggestion.auto_fixable:
                continue

            try:
                file_path = Path(suggestion.file_path)

                # Create backup
                backup_path = f"{file_path}.backup"
                with open(file_path, 'r') as src, open(backup_path, 'w') as backup:
                    backup.write(src.read())
                backup_files.append(backup_path)

                # Apply the fix
                if suggestion.issue_type in ['formatting', 'pep8_formatting']:
                    # Apply formatting
                    with open(file_path, 'r') as f:
                        content = f.read()

                    if suggestion.issue_type == 'formatting':
                        fixed_content = black.format_str(content)
                    else:
                        fixed_content = autopep8.fix_code(content)

                    with open(file_path, 'w') as f:
                        f.write(fixed_content)

                elif suggestion.issue_type == 'import_organization':
                    # Organize imports
                    with open(file_path, 'r') as f:
                        content = f.read()

                    organized_content = isort.code(content)

                    with open(file_path, 'w') as f:
                        f.write(organized_content)

                applied_suggestions.append(suggestion)

            except Exception as e:
                print(f"Failed to apply suggestion {suggestion.issue_type}: {e}")
                failed_suggestions.append(suggestion)

        return {
            'applied_count': len(applied_suggestions),
            'failed_count': len(failed_suggestions),
            'backup_files': backup_files,
            'applied_suggestions': [asdict(s) for s in applied_suggestions],
            'failed_suggestions': [asdict(s) for s in failed_suggestions]
        }

    def analyze_project(self) -> Dict[str, Any]:
        """Analyze entire project for refactoring opportunities."""
        print("Scanning project for refactoring opportunities...")

        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.venv', 'venv', 'node_modules'}]

            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)

        print(f"Found {len(python_files)} Python files")

        all_suggestions = []
        for file_path in python_files:
            print(f"Analyzing {file_path}")
            suggestions = self.analyze_file(file_path)
            all_suggestions.extend(suggestions)

        # Create refactoring plan
        refactoring_plan = self.create_refactoring_plan(all_suggestions)

        return {
            'refactoring_plan': asdict(refactoring_plan),
            'total_suggestions': len(all_suggestions),
            'files_analyzed': len(python_files),
            'analysis_timestamp': __import__('time').time()
        }

    def generate_report(self, analysis_results: Dict[str, Any], output_path: str = None) -> str:
        """Generate refactoring analysis report."""
        if output_path is None:
            output_path = '/home/activeloguser/DMLogn8n/quality/reports/refactoring_report.json'

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w') as f:
            import json
            json.dump(analysis_results, f, indent=2, default=str)

        return output_path


def main():
    """Main function for standalone usage."""
    project_root = '/home/activeloguser/DMLogn8n'
    engine = RefactoringEngine(project_root)

    print("Starting refactoring analysis...")
    results = engine.analyze_project()

    # Generate report
    report_path = engine.generate_report(results)
    print(f"Analysis complete. Report saved to: {report_path}")

    # Print summary
    plan = results['refactoring_plan']
    print(f"\n=== Refactoring Analysis Summary ===")
    print(f"Total suggestions: {results['total_suggestions']}")
    print(f"Files analyzed: {results['files_analyzed']}")

    effort = plan['estimated_effort']
    if effort:
        total_hours = sum(effort.values())
        print(f"Estimated total effort: {total_hours:.1f} hours")

        print("\nEffort by category:")
        for category, hours in effort.items():
            print(f"  {category}: {hours:.1f} hours")

    risk = plan['risk_assessment']
    print(f"\nRisk assessment: {risk['overall_risk']}")
    print(f"  High risk items: {risk['high_risk_items']}")
    print(f"  Medium risk items: {risk['medium_risk_items']}")
    print(f"  Low risk items: {risk['low_risk_items']}")
    print(f"  Auto-fixable ratio: {risk['auto_fixable_ratio']:.1%}")


if __name__ == "__main__":
    main()