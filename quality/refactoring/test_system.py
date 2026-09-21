#!/usr/bin/env python3
"""
Simple test script to verify the quality assurance system functionality.
This test works without external dependencies.
"""

import ast
import json
import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_code_analyzer():
    """Test the code analyzer with basic functionality."""
    print("🧪 Testing Code Analyzer...")

    try:
        # Import the analyzer
        from code_analyzer import CodeAnalyzer

        # Test on our demo file
        analyzer = CodeAnalyzer('.')
        demo_file = Path('demo.py')

        if demo_file.exists():
            metrics = analyzer.analyze_file(demo_file)
            if metrics:
                print(f"✅ Code Analyzer works!")
                print(f"   - Lines analyzed: {metrics.total_lines}")
                print(f"   - Functions found: {len(metrics.function_complexity)}")
                print(f"   - Classes found: {len(metrics.class_metrics)}")
                return True
            else:
                print("❌ Code Analyzer returned no metrics")
                return False
        else:
            print("❌ Demo file not found")
            return False

    except Exception as e:
        print(f"❌ Code Analyzer test failed: {e}")
        return False

def test_architecture_analyzer():
    """Test the architecture analyzer."""
    print("\n🧪 Testing Architecture Analyzer...")

    try:
        from architecture_analyzer import ArchitectureAnalyzer

        analyzer = ArchitectureAnalyzer('.')
        demo_file = Path('demo.py')

        if demo_file.exists():
            classes, module_info = analyzer._analyze_file_architecture(demo_file)
            print(f"✅ Architecture Analyzer works!")
            print(f"   - Classes analyzed: {len(classes)}")
            print(f"   - Module info: {len(module_info)} keys")
            return True
        else:
            print("❌ Demo file not found")
            return False

    except Exception as e:
        print(f"❌ Architecture Analyzer test failed: {e}")
        return False

def test_code_reviewer():
    """Test the code reviewer."""
    print("\n🧪 Testing Code Reviewer...")

    try:
        from code_reviewer import CodeReviewer

        reviewer = CodeReviewer('.')
        demo_file = Path('demo.py')

        if demo_file.exists():
            issues = reviewer.review_file(demo_file)
            print(f"✅ Code Reviewer works!")
            print(f"   - Issues found: {len(issues)}")

            # Count issues by severity
            severity_counts = {}
            for issue in issues:
                severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1

            for severity, count in severity_counts.items():
                print(f"   - {severity}: {count}")

            return True
        else:
            print("❌ Demo file not found")
            return False

    except Exception as e:
        print(f"❌ Code Reviewer test failed: {e}")
        return False

def test_technical_debt_tracker():
    """Test the technical debt tracker."""
    print("\n🧪 Testing Technical Debt Tracker...")

    try:
        from technical_debt_tracker import TechnicalDebtTracker

        tracker = TechnicalDebtTracker('.')
        demo_file = Path('demo.py')

        if demo_file.exists():
            debt_items = tracker.scan_for_technical_debt(demo_file)
            print(f"✅ Technical Debt Tracker works!")
            print(f"   - Debt items found: {len(debt_items)}")

            # Count by category
            category_counts = {}
            for item in debt_items:
                category_counts[item.category.value] = category_counts.get(item.category.value, 0) + 1

            for category, count in category_counts.items():
                print(f"   - {category}: {count}")

            return True
        else:
            print("❌ Demo file not found")
            return False

    except Exception as e:
        print(f"❌ Technical Debt Tracker test failed: {e}")
        return False

def test_refactoring_engine():
    """Test the refactoring engine."""
    print("\n🧪 Testing Refactoring Engine...")

    try:
        from refactoring_engine import RefactoringEngine

        engine = RefactoringEngine('.')
        demo_file = Path('demo.py')

        if demo_file.exists():
            suggestions = engine.analyze_file(demo_file)
            print(f"✅ Refactoring Engine works!")
            print(f"   - Refactoring suggestions: {len(suggestions)}")

            # Count by type
            type_counts = {}
            for suggestion in suggestions:
                type_counts[suggestion.issue_type] = type_counts.get(suggestion.issue_type, 0) + 1

            for issue_type, count in type_counts.items():
                print(f"   - {issue_type}: {count}")

            return True
        else:
            print("❌ Demo file not found")
            return False

    except Exception as e:
        print(f"❌ Refactoring Engine test failed: {e}")
        return False

def test_performance_profiler():
    """Test the performance profiler."""
    print("\n🧪 Testing Performance Profiler...")

    try:
        from performance_profiler import PerformanceProfiler

        profiler = PerformanceProfiler('.')
        demo_file = Path('demo.py')

        if demo_file.exists():
            issues = profiler.profile_file(demo_file)
            print(f"✅ Performance Profiler works!")
            print(f"   - Performance issues: {len(issues)}")

            # Count by type
            type_counts = {}
            for issue in issues:
                type_counts[issue.issue_type] = type_counts.get(issue.issue_type, 0) + 1

            for issue_type, count in type_counts.items():
                print(f"   - {issue_type}: {count}")

            return True
        else:
            print("❌ Demo file not found")
            return False

    except Exception as e:
        print(f"❌ Performance Profiler test failed: {e}")
        return False

def test_documentation_generator():
    """Test the documentation generator."""
    print("\n🧪 Testing Documentation Generator...")

    try:
        from documentation_generator import DocumentationGenerator

        generator = DocumentationGenerator('.')
        structure = generator._analyze_project_structure()
        print(f"✅ Documentation Generator works!")
        print(f"   - Modules found: {len(structure['modules'])}")
        print(f"   - Packages found: {len(structure['packages'])}")
        print(f"   - Test files: {len(structure['test_files'])}")

        return True

    except Exception as e:
        print(f"❌ Documentation Generator test failed: {e}")
        return False

def test_demo_file_analysis():
    """Analyze the demo file and show what issues it contains."""
    print("\n🔍 Analyzing Demo File for Issues...")

    demo_file = Path('demo.py')
    if not demo_file.exists():
        print("❌ Demo file not found")
        return

    try:
        with open(demo_file, 'r') as f:
            content = f.read()

        tree = ast.parse(content)

        # Count various elements
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]

        print(f"📊 Demo File Analysis:")
        print(f"   - Lines of code: {len(content.splitlines())}")
        print(f"   - Functions: {len(functions)}")
        print(f"   - Classes: {len(classes)}")
        print(f"   - Imports: {len(imports)}")

        # Look for specific issues
        issues_found = []

        # Check for functions with many parameters
        for func in functions:
            if len(func.args.args) > 5:
                issues_found.append(f"Function '{func.name}' has {len(func.args.args)} parameters")

        # Check for TODO/FIXME comments
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            if any(keyword in line.upper() for keyword in ['TODO', 'FIXME', 'HACK', 'XXX']):
                issues_found.append(f"Line {i}: Contains comment - {line.strip()[:50]}...")

        # Check for bare except clauses
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                if hasattr(node, 'lineno'):
                    issues_found.append(f"Line {node.lineno}: Bare except clause")

        # Check for nested loops
        for func in functions:
            nested_loops = 0
            for node in ast.walk(func):
                if isinstance(node, (ast.For, ast.While)):
                    nested_loops += 1
            if nested_loops > 2:
                issues_found.append(f"Function '{func.name}' has nested loops")

        print(f"   - Issues detected: {len(issues_found)}")
        for issue in issues_found[:5]:  # Show first 5 issues
            print(f"     • {issue}")
        if len(issues_found) > 5:
            print(f"     • ... and {len(issues_found) - 5} more issues")

    except Exception as e:
        print(f"❌ Demo file analysis failed: {e}")

def main():
    """Run all tests."""
    print("🚀 Testing Advanced Code Quality and Refactoring System")
    print("=" * 60)

    # Test all components
    tests = [
        test_code_analyzer,
        test_architecture_analyzer,
        test_code_reviewer,
        test_technical_debt_tracker,
        test_refactoring_engine,
        test_performance_profiler,
        test_documentation_generator
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")

    # Analyze demo file
    test_demo_file_analysis()

    # Print summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The quality assurance system is working correctly.")
    else:
        print(f"⚠️  {total - passed} tests failed. Check the output above for details.")

    print("\n💡 To run the full system:")
    print("   python quality_orchestrator.py . --summary")
    print("\n📚 See README.md for complete usage instructions.")

if __name__ == "__main__":
    main()