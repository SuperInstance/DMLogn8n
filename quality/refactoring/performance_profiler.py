#!/usr/bin/env python3
"""
Performance Profiler
Analyzes code performance, identifies bottlenecks, and provides optimization recommendations.
"""

import ast
import os
import time
import cProfile
import pstats
import io
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import subprocess
import sys


@dataclass
class PerformanceIssue:
    """Data class for performance issues."""
    id: str
    file_path: str
    line_number: int
    issue_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    title: str
    description: str
    performance_impact: str
    optimization_suggestion: str
    code_snippet: str
    estimated_improvement: str
    complexity_score: float
    tags: List[str]


@dataclass
class PerformanceMetrics:
    """Metrics for performance analysis."""
    total_functions_analyzed: int
    slow_functions: List[Dict[str, Any]]
    memory_intensive_functions: List[Dict[str, Any]]
    io_intensive_operations: List[Dict[str, Any]]
    algorithmic_complexity_issues: List[Dict[str, Any]]
    cache_opportunities: List[Dict[str, Any]]
    concurrency_opportunities: List[Dict[str, Any]]
    database_query_issues: List[Dict[str, Any]]
    overall_performance_score: float


class PerformanceProfiler:
    """Advanced performance profiling and optimization system."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.performance_rules = self._initialize_performance_rules()
        self.optimization_patterns = self._initialize_optimization_patterns()
        self.bottleneck_patterns = self._initialize_bottleneck_patterns()

    def _initialize_performance_rules(self) -> Dict[str, Any]:
        """Initialize performance analysis rules."""
        return {
            'algorithmic_complexity': {
                'max_nested_loops': 2,
                'max_recursion_depth': 10,
                'expensive_operations': [
                    'list.index', 'list.count', 'str.find', 're.match',
                    'sorted', 'sort', 'min', 'max', 'sum', 'any', 'all'
                ]
            },
            'memory_usage': {
                'max_list_comprehension_size': 1000,
                'max_string_operations': 100,
                'memory_intensive_operations': [
                    'list()', 'dict()', 'set()', 'copy.deepcopy',
                    'json.loads', 'pickle.loads', 'pandas.read_'
                ]
            },
            'io_operations': {
                'max_file_size_mb': 100,
                'max_concurrent_io': 10,
                'io_intensive_operations': [
                    'open(', 'file.read', 'file.write', 'requests.',
                    'urllib.request', 'subprocess.run', 'os.system'
                ]
            },
            'database_operations': {
                'max_query_rows': 10000,
                'n_plus_one_threshold': 5,
                'query_patterns': [
                    'SELECT', 'INSERT', 'UPDATE', 'DELETE',
                    'cursor.execute', 'session.query', 'db.query'
                ]
            },
            'timing_thresholds': {
                'function_call_time_ms': 100,
                'io_operation_time_ms': 1000,
                'database_query_time_ms': 500,
                'memory_operation_time_ms': 10
            }
        }

    def _initialize_optimization_patterns(self) -> Dict[str, List[str]]:
        """Initialize optimization patterns."""
        return {
            'algorithmic': [
                'Use sets for membership testing instead of lists',
                'Use dict.get() with default values instead of if/else',
                'Use list comprehensions instead of for loops with append',
                'Use generators for large datasets',
                'Use bisect for sorted list searches',
                'Use collections.deque for queue operations'
            ],
            'memory': [
                'Use __slots__ for classes with many instances',
                'Use generators instead of lists where possible',
                'Use memoryviews for large binary data',
                'Use weak references for caching',
                'Delete large objects when no longer needed',
                'Use arrays instead of lists for numeric data'
            ],
            'io': [
                'Use buffered I/O operations',
                'Use context managers for file operations',
                'Use async/await for I/O bound operations',
                'Batch multiple small I/O operations',
                'Use connection pooling for database operations',
                'Cache frequently accessed data'
            ],
            'concurrency': [
                'Use threading for I/O bound operations',
                'Use multiprocessing for CPU bound operations',
                'Use asyncio for concurrent I/O operations',
                'Use concurrent.futures for task parallelism',
                'Use multiprocessing.Pool for parallel processing',
                'Use threading.Lock for shared resources'
            ]
        }

    def _initialize_bottleneck_patterns(self) -> Dict[str, List[str]]:
        """Initialize common bottleneck patterns."""
        return {
            'cpu_bottlenecks': [
                'nested_loops', 'recursive_calls', 'string_concatenation',
                'list_comprehensions_large', 'regex_operations', 'sorting_operations'
            ],
            'memory_bottlenecks': [
                'large_lists', 'string_operations', 'object_creation',
                'deep_copies', 'caching_issues', 'memory_leaks'
            ],
            'io_bottlenecks': [
                'file_operations', 'network_requests', 'database_queries',
                'subprocess_calls', 'logging_operations', 'disk_io'
            ],
            'algorithmic_bottlenecks': [
                'quadratic_algorithms', 'linear_search', 'inefficient_data_structures',
                'repeated_calculations', 'suboptimal_algorithms', 'brute_force'
            ]
        }

    def profile_file(self, file_path: Path) -> List[PerformanceIssue]:
        """Profile a single Python file for performance issues."""
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            # Parse AST for structural analysis
            tree = ast.parse(content)

            # Analyze algorithmic complexity
            issues.extend(self._analyze_algorithmic_complexity(tree, lines, file_path))

            # Analyze memory usage patterns
            issues.extend(self._analyze_memory_usage(tree, lines, file_path))

            # Analyze I/O operations
            issues.extend(self._analyze_io_operations(tree, lines, file_path))

            # Analyze database operations
            issues.extend(self._analyze_database_operations(tree, lines, file_path))

            # Analyze caching opportunities
            issues.extend(self._analyze_caching_opportunities(tree, lines, file_path))

            # Analyze concurrency opportunities
            issues.extend(self._analyze_concurrency_opportunities(tree, lines, file_path))

            # Analyze string operations
            issues.extend(self._analyze_string_operations(tree, lines, file_path))

        except Exception as e:
            issues.append(PerformanceIssue(
                id=f"profile_error_{hash(str(file_path))}",
                file_path=str(file_path),
                line_number=1,
                issue_type="profile_error",
                severity="critical",
                title="Profiling Error",
                description=f"Unable to profile file: {str(e)}",
                performance_impact="unknown",
                optimization_suggestion="Fix syntax errors before profiling",
                code_snippet="",
                estimated_improvement="unknown",
                complexity_score=0.0,
                tags=["error", "profiling"]
            ))

        return issues

    def _analyze_algorithmic_complexity(self, tree: ast.AST, lines: List[str], file_path: Path) -> List[PerformanceIssue]:
        """Analyze algorithmic complexity issues."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for nested loops
                nested_loops = self._count_nested_loops(node)
                if nested_loops > self.performance_rules['algorithmic_complexity']['max_nested_loops']:
                    issues.append(PerformanceIssue(
                        id=f"nested_loops_{node.lineno}_{node.col_offset}",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        issue_type="algorithmic_complexity",
                        severity="high",
                        title="Nested Loops Detected",
                        description=f"Function {node.name} contains {nested_loops} levels of nested loops",
                        performance_impact="O(n^k) complexity where k={nested_loops}",
                        optimization_suggestion="Consider reducing nesting or using more efficient algorithms",
                        code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                        estimated_improvement="50-90% execution time reduction",
                        complexity_score=nested_loops * 2.0,
                        tags=["algorithm", "nested_loops", "complexity"]
                    ))

                # Check for expensive operations in loops
                expensive_in_loops = self._find_expensive_operations_in_loops(node)
                for op_info in expensive_in_loops:
                    issues.append(PerformanceIssue(
                        id=f"expensive_in_loop_{op_info['line']}",
                        file_path=str(file_path),
                        line_number=op_info['line'],
                        issue_type="algorithmic_complexity",
                        severity="medium",
                        title="Expensive Operation in Loop",
                        description=f"Expensive operation '{op_info['operation']}' found inside loop",
                        performance_impact=f"O(n * cost({op_info['operation']})) complexity",
                        optimization_suggestion="Move expensive operations outside loops or cache results",
                        code_snippet=op_info['code'],
                        estimated_improvement="30-70% execution time reduction",
                        complexity_score=1.5,
                        tags=["algorithm", "loop", "optimization"]
                    ))

                # Check for recursion depth
                recursion_depth = self._estimate_recursion_depth(node)
                if recursion_depth > self.performance_rules['algorithmic_complexity']['max_recursion_depth']:
                    issues.append(PerformanceIssue(
                        id=f"deep_recursion_{node.lineno}",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        issue_type="algorithmic_complexity",
                        severity="medium",
                        title="Deep Recursion Detected",
                        description=f"Function {node.name} may have recursion depth up to {recursion_depth}",
                        performance_impact="Potential stack overflow and exponential time complexity",
                        optimization_suggestion="Consider using iteration or memoization",
                        code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                        estimated_improvement="Prevents stack overflow, potential speedup",
                        complexity_score=recursion_depth * 0.5,
                        tags=["algorithm", "recursion", "stack"]
                    ))

        return issues

    def _analyze_memory_usage(self, tree: ast.AST, lines: List[str], file_path: Path) -> List[PerformanceIssue]:
        """Analyze memory usage patterns."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for memory-intensive operations
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in self.performance_rules['memory_usage']['memory_intensive_operations']:
                        issues.append(PerformanceIssue(
                            id=f"memory_intensive_{node.lineno}_{node.col_offset}",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            issue_type="memory_usage",
                            severity="medium",
                            title="Memory-Intensive Operation",
                            description=f"Memory-intensive operation '{node.func.attr}' detected",
                            performance_impact="High memory consumption and potential GC pressure",
                            optimization_suggestion="Consider streaming, chunking, or more memory-efficient alternatives",
                            code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                            estimated_improvement="50-80% memory reduction",
                            complexity_score=1.0,
                            tags=["memory", "optimization", "gc"]
                        ))

            elif isinstance(node, ast.ListComp):
                # Check for large list comprehensions
                if self._estimate_list_comprehension_size(node) > self.performance_rules['memory_usage']['max_list_comprehension_size']:
                    issues.append(PerformanceIssue(
                        id=f"large_list_comp_{node.lineno}_{node.col_offset}",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        issue_type="memory_usage",
                        severity="medium",
                        title="Large List Comprehension",
                        description="List comprehension that may generate large result set",
                        performance_impact="High memory usage for large datasets",
                        optimization_suggestion="Consider using generator expression or processing in chunks",
                        code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                        estimated_improvement="60-90% memory reduction",
                        complexity_score=1.2,
                        tags=["memory", "list_comprehension", "generator"]
                    ))

        return issues

    def _analyze_io_operations(self, tree: ast.AST, lines: List[str], file_path: Path) -> List[PerformanceIssue]:
        """Analyze I/O operations."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for I/O-intensive operations
                if isinstance(node.func, ast.Attribute):
                    func_name = f"{node.func.value.id if isinstance(node.func.value, ast.Name) else ''}.{node.func.attr}" if hasattr(node.func, 'value') else node.func.attr

                    for io_op in self.performance_rules['io_operations']['io_intensive_operations']:
                        if io_op in func_name.lower():
                            issues.append(PerformanceIssue(
                                id=f"io_intensive_{node.lineno}_{node.col_offset}",
                                file_path=str(file_path),
                                line_number=node.lineno,
                                issue_type="io_operations",
                                severity="medium",
                                title="I/O-Intensive Operation",
                                description=f"I/O-intensive operation '{func_name}' detected",
                                performance_impact="Blocking I/O operations can cause performance bottlenecks",
                                optimization_suggestion="Consider async/await, threading, or batching",
                                code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                                estimated_improvement="20-60% latency reduction",
                                complexity_score=1.0,
                                tags=["io", "async", "performance"]
                            ))

                elif isinstance(node.func, ast.Name) and node.func.id == 'open':
                    # Check file operations
                    issues.append(PerformanceIssue(
                        id=f"file_operation_{node.lineno}_{node.col_offset}",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        issue_type="io_operations",
                        severity="low",
                        title="File Operation",
                        description="File I/O operation detected",
                        performance_impact="File I/O can be slow, especially for large files",
                        optimization_suggestion="Use buffered I/O, consider streaming for large files",
                        code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                        estimated_improvement="10-30% I/O performance improvement",
                        complexity_score=0.5,
                        tags=["io", "file", "buffering"]
                    ))

        return issues

    def _analyze_database_operations(self, tree: ast.AST, lines: List[str], file_path: Path) -> List[PerformanceIssue]:
        """Analyze database operations."""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for database operations
                call_str = ast.unparse(node) if hasattr(ast, 'unparse') else ""

                for db_pattern in self.performance_rules['database_operations']['query_patterns']:
                    if db_pattern.lower() in call_str.lower():
                        issues.append(PerformanceIssue(
                            id=f"db_operation_{node.lineno}_{node.col_offset}",
                            file_path=str(file_path),
                            line_number=node.lineno,
                            issue_type="database_operations",
                            severity="medium",
                            title="Database Operation",
                            description=f"Database operation '{db_pattern}' detected",
                            performance_impact="Database queries can be significant performance bottlenecks",
                            optimization_suggestion="Use indexing, query optimization, connection pooling, or caching",
                            code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                            estimated_improvement="40-80% query time reduction",
                            complexity_score=1.5,
                            tags=["database", "query", "optimization"]
                        ))
                        break

        # Check for N+1 query pattern
        n_plus_one_issues = self._detect_n_plus_one_queries(tree, lines, file_path)
        issues.extend(n_plus_one_issues)

        return issues

    def _analyze_caching_opportunities(self, tree: ast.AST, lines: List[str], file_path: Path) -> List[PerformanceIssue]:
        """Analyze caching opportunities."""
        issues = []

        # Look for repeated expensive operations
        expensive_calls = defaultdict(list)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    call_signature = f"{node.func.attr}"
                    expensive_calls[call_signature].append((node.lineno, lines[node.lineno - 1].strip() if node.lineno <= len(lines) else ""))

        for call_sig, occurrences in expensive_calls.items():
            if len(occurrences) > 3:  # Called more than 3 times
                issues.append(PerformanceIssue(
                    id=f"cache_opportunity_{hash(call_sig)}",
                    file_path=str(file_path),
                    line_number=occurrences[0][0],
                    issue_type="caching_opportunity",
                    severity="low",
                    title="Caching Opportunity",
                    description=f"Expensive operation '{call_sig}' called {len(occurrences)} times",
                    performance_impact="Repeated expensive calculations",
                    optimization_suggestion="Consider caching results using functools.lru_cache or custom cache",
                    code_snippet=occurrences[0][1],
                    estimated_improvement="50-90% execution time reduction for repeated calls",
                    complexity_score=0.8,
                    tags=["caching", "optimization", "memoization"]
                ))

        return issues

    def _analyze_concurrency_opportunities(self, tree: ast.AST, lines: List[str], file_path: Path) -> List[PerformanceIssue]:
        """Analyze concurrency opportunities."""
        issues = []

        # Look for independent operations that could be parallelized
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                # Check if loop contains I/O operations
                has_io = self._has_io_operations(node)
                if has_io:
                    issues.append(PerformanceIssue(
                        id=f"concurrency_opportunity_{node.lineno}",
                        file_path=str(file_path),
                        line_number=node.lineno,
                        issue_type="concurrency_opportunity",
                        severity="medium",
                        title="Concurrency Opportunity",
                        description="Loop with I/O operations detected",
                        performance_impact="Sequential I/O operations can be slow",
                        optimization_suggestion="Consider using threading, asyncio, or concurrent.futures",
                        code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                        estimated_improvement="60-90% execution time reduction for I/O bound workloads",
                        complexity_score=1.2,
                        tags=["concurrency", "parallel", "async"]
                    ))

        return issues

    def _analyze_string_operations(self, tree: ast.AST, lines: List[str], file_path: Path) -> List[PerformanceIssue]:
        """Analyze string operations."""
        issues = []

        for line_num, line in enumerate(lines, 1):
            # Check for string concatenation in loops
            if re.search(r'\+\s*=.*["\']', line) or re.search(r'["\']\s*\+.*["\']', line):
                # Check if this might be in a loop by looking at surrounding lines
                context_lines = lines[max(0, line_num-10):line_num+5]
                loop_indicators = ['for ', 'while ', 'for:', 'while:']

                if any(indicator in context_line for context_line in context_lines for indicator in loop_indicators):
                    issues.append(PerformanceIssue(
                        id=f"string_concat_{line_num}",
                        file_path=str(file_path),
                        line_number=line_num,
                        issue_type="string_operations",
                        severity="low",
                        title="String Concatenation in Loop",
                        description="String concatenation detected, possibly in a loop",
                        performance_impact="Inefficient string building in loops",
                        optimization_suggestion="Use list of strings with join() or f-strings",
                        code_snippet=line.strip(),
                        estimated_improvement="30-70% string operation speedup",
                        complexity_score=0.6,
                        tags=["string", "concatenation", "optimization"]
                    ))

        return issues

    def _count_nested_loops(self, node: ast.AST) -> int:
        """Count maximum nesting level of loops in a function."""
        max_depth = 0
        current_depth = 0

        def count_loops(n):
            nonlocal max_depth, current_depth

            if isinstance(n, (ast.For, ast.While)):
                current_depth += 1
                max_depth = max(max_depth, current_depth)

                for child in ast.walk(n):
                    if isinstance(child, (ast.For, ast.While)):
                        count_loops(child)

                current_depth -= 1

        count_loops(node)
        return max_depth

    def _find_expensive_operations_in_loops(self, func_node: ast.FunctionDef) -> List[Dict[str, Any]]:
        """Find expensive operations inside loops."""
        expensive_ops = []

        for node in ast.walk(func_node):
            if isinstance(node, (ast.For, ast.While)):
                # Look for expensive operations inside this loop
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Attribute):
                            if child.func.attr in self.performance_rules['algorithmic_complexity']['expensive_operations']:
                                expensive_ops.append({
                                    'line': child.lineno,
                                    'operation': child.func.attr,
                                    'code': ast.unparse(child) if hasattr(ast, 'unparse') else str(child)
                                })

        return expensive_ops

    def _estimate_recursion_depth(self, func_node: ast.FunctionDef) -> int:
        """Estimate maximum recursion depth of a function."""
        recursive_calls = 0

        for node in ast.walk(func_node):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == func_node.name:
                    recursive_calls += 1

        # Simple heuristic: base case plus recursive calls
        return recursive_calls + 1

    def _estimate_list_comprehension_size(self, node: ast.ListComp) -> int:
        """Estimate the size of list comprehension result."""
        # This is a simplified estimation
        # In real implementation, we'd analyze the input ranges
        return 1000  # Conservative estimate

    def _detect_n_plus_one_queries(self, tree: ast.AST, lines: List[str], file_path: Path) -> List[PerformanceIssue]:
        """Detect N+1 query patterns."""
        issues = []

        # Look for database queries inside loops
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                # Check if loop contains database operations
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        call_str = ast.unparse(child) if hasattr(ast, 'unparse') else ""
                        for db_pattern in self.performance_rules['database_operations']['query_patterns']:
                            if db_pattern.lower() in call_str.lower():
                                issues.append(PerformanceIssue(
                                    id=f"n_plus_one_{node.lineno}",
                                    file_path=str(file_path),
                                    line_number=node.lineno,
                                    issue_type="database_operations",
                                    severity="high",
                                    title="Potential N+1 Query Pattern",
                                    description="Database query found inside loop - potential N+1 query problem",
                                    performance_impact="Multiple database queries instead of batch operations",
                                    optimization_suggestion="Use eager loading, select_related, prefetch_related, or batch queries",
                                    code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                                    estimated_improvement="80-95% query time reduction",
                                    complexity_score=2.0,
                                    tags=["database", "n_plus_one", "optimization"]
                                ))
                                break

        return issues

    def _has_io_operations(self, node: ast.AST) -> bool:
        """Check if AST node contains I/O operations."""
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    func_name = f"{child.func.attr}"
                    for io_op in self.performance_rules['io_operations']['io_intensive_operations']:
                        if io_op in func_name.lower():
                            return True
        return False

    def run_benchmark_suite(self, test_files: List[Path] = None) -> Dict[str, Any]:
        """Run performance benchmark suite."""
        if test_files is None:
            # Find test files automatically
            test_files = []
            for root, dirs, files in os.walk(self.project_root):
                dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.venv', 'venv', 'node_modules'}]
                for file in files:
                    if file.endswith('.py') and ('test' in file or 'bench' in file):
                        test_files.append(Path(root) / file)

        benchmark_results = []

        for test_file in test_files:
            print(f"Benchmarking {test_file}...")
            result = self._benchmark_file(test_file)
            if result:
                benchmark_results.append(result)

        return {
            'benchmark_results': benchmark_results,
            'total_benchmarks': len(benchmark_results),
            'analysis_timestamp': time.time()
        }

    def _benchmark_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Benchmark a single file."""
        try:
            # Create a profiler
            profiler = cProfile.Profile()

            # Read and execute the file in a safe way
            with open(file_path, 'r') as f:
                code = f.read()

            # Profile the code execution
            start_time = time.time()
            profiler.enable()

            try:
                # Execute the code in a controlled environment
                exec_globals = {'__name__': '__main__'}
                exec(code, exec_globals)
            except Exception as e:
                print(f"Error executing {file_path}: {e}")
                return None

            profiler.disable()
            end_time = time.time()

            # Get profiling stats
            s = io.StringIO()
            ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
            ps.print_stats(20)  # Top 20 functions

            # Parse results
            stats_str = s.getvalue()

            return {
                'file_path': str(file_path),
                'execution_time': end_time - start_time,
                'profile_stats': stats_str,
                'top_functions': self._parse_top_functions(stats_str)
            }

        except Exception as e:
            print(f"Error benchmarking {file_path}: {e}")
            return None

    def _parse_top_functions(self, stats_str: str) -> List[Dict[str, Any]]:
        """Parse top functions from profiling stats."""
        functions = []
        lines = stats_str.split('\n')

        # Skip header lines
        start_index = 0
        for i, line in enumerate(lines):
            if 'ncalls' in line and 'tottime' in line:
                start_index = i + 1
                break

        # Parse function data
        for line in lines[start_index:start_index + 10]:  # Top 10 functions
            if line.strip() and not line.startswith(' '):
                parts = line.split()
                if len(parts) >= 6:
                    try:
                        functions.append({
                            'ncalls': parts[0],
                            'tottime': float(parts[1]),
                            'percall': float(parts[2]),
                            'cumtime': float(parts[3]),
                            'percall_cum': float(parts[4]),
                            'function': ' '.join(parts[5:])
                        })
                    except (ValueError, IndexError):
                        continue

        return functions

    def analyze_project(self) -> Dict[str, Any]:
        """Analyze entire project for performance issues."""
        print("Scanning project for performance analysis...")

        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.venv', 'venv', 'node_modules'}]

            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)

        print(f"Found {len(python_files)} Python files")

        # Analyze each file
        all_issues = []
        for file_path in python_files:
            print(f"Analyzing {file_path}...")
            issues = self.profile_file(file_path)
            all_issues.extend(issues)

        # Run benchmark suite
        benchmark_results = self.run_benchmark_suite()

        # Calculate metrics
        metrics = self._calculate_performance_metrics(all_issues)

        return {
            'performance_summary': asdict(metrics),
            'performance_issues': [asdict(issue) for issue in all_issues],
            'benchmark_results': benchmark_results,
            'optimization_recommendations': self._generate_optimization_recommendations(all_issues),
            'analysis_timestamp': time.time()
        }

    def _calculate_performance_metrics(self, issues: List[PerformanceIssue]) -> PerformanceMetrics:
        """Calculate performance analysis metrics."""
        # Group issues by type
        slow_functions = [issue for issue in issues if issue.issue_type == 'algorithmic_complexity']
        memory_intensive = [issue for issue in issues if issue.issue_type == 'memory_usage']
        io_intensive = [issue for issue in issues if issue.issue_type == 'io_operations']
        database_issues = [issue for issue in issues if issue.issue_type == 'database_operations']
        cache_opportunities = [issue for issue in issues if issue.issue_type == 'caching_opportunity']
        concurrency_opportunities = [issue for issue in issues if issue.issue_type == 'concurrency_opportunity']

        # Calculate overall performance score (0-100, higher is better)
        severity_weights = {'critical': 10, 'high': 5, 'medium': 2, 'low': 1}
        weighted_issues = sum(severity_weights.get(issue.severity, 1) for issue in issues)
        performance_score = max(0, 100 - weighted_issues * 2)

        return PerformanceMetrics(
            total_functions_analyzed=len(set(issue.file_path for issue in issues)),
            slow_functions=[{'function': issue.title, 'impact': issue.performance_impact} for issue in slow_functions],
            memory_intensive_functions=[{'function': issue.title, 'impact': issue.performance_impact} for issue in memory_intensive],
            io_intensive_operations=[{'operation': issue.title, 'impact': issue.performance_impact} for issue in io_intensive],
            algorithmic_complexity_issues=[{'issue': issue.title, 'complexity': issue.complexity_score} for issue in slow_functions],
            cache_opportunities=[{'opportunity': issue.title, 'improvement': issue.estimated_improvement} for issue in cache_opportunities],
            concurrency_opportunities=[{'opportunity': issue.title, 'improvement': issue.estimated_improvement} for issue in concurrency_opportunities],
            database_query_issues=[{'issue': issue.title, 'impact': issue.performance_impact} for issue in database_issues],
            overall_performance_score=performance_score
        )

    def _generate_optimization_recommendations(self, issues: List[PerformanceIssue]) -> List[Dict[str, Any]]:
        """Generate optimization recommendations."""
        recommendations = []

        # Count issues by type and severity
        issue_counts = defaultdict(lambda: defaultdict(int))
        for issue in issues:
            issue_counts[issue.issue_type][issue.severity] += 1

        # Generate recommendations based on issue patterns
        if issue_counts['algorithmic_complexity']['high'] > 0 or issue_counts['algorithmic_complexity']['critical'] > 0:
            recommendations.append({
                'priority': 'high',
                'category': 'algorithmic_optimization',
                'title': 'Optimize Algorithmic Complexity',
                'description': 'Critical algorithmic performance issues detected',
                'suggestions': [
                    'Reduce nested loops',
                    'Use more efficient data structures',
                    'Implement memoization for repeated calculations',
                    'Consider divide-and-conquer approaches'
                ],
                'estimated_impact': '50-90% performance improvement'
            })

        if issue_counts['database_operations']['high'] > 0:
            recommendations.append({
                'priority': 'high',
                'category': 'database_optimization',
                'title': 'Optimize Database Operations',
                'description': 'Database performance bottlenecks detected',
                'suggestions': [
                    'Fix N+1 query problems',
                    'Add appropriate indexes',
                    'Use connection pooling',
                    'Implement query result caching'
                ],
                'estimated_impact': '40-80% query time reduction'
            })

        if len([issue for issue in issues if 'concurrency' in issue.tags]) > 2:
            recommendations.append({
                'priority': 'medium',
                'category': 'concurrency',
                'title': 'Implement Concurrency',
                'description': 'Multiple opportunities for parallel execution detected',
                'suggestions': [
                    'Use asyncio for I/O-bound operations',
                    'Use multiprocessing for CPU-bound tasks',
                    'Implement thread pools for concurrent processing'
                ],
                'estimated_impact': '60-90% execution time reduction'
            })

        if len([issue for issue in issues if 'caching' in issue.tags]) > 3:
            recommendations.append({
                'priority': 'medium',
                'category': 'caching',
                'title': 'Implement Caching Strategy',
                'description': 'Multiple caching opportunities identified',
                'suggestions': [
                    'Use functools.lru_cache for function results',
                    'Implement Redis or Memcached for data caching',
                    'Cache expensive database query results'
                ],
                'estimated_impact': '50-90% reduction in repeated operations'
            })

        return recommendations

    def generate_report(self, analysis_results: Dict[str, Any], output_path: str = None) -> str:
        """Generate performance analysis report."""
        if output_path is None:
            output_path = '/home/activeloguser/DMLogn8n/quality/reports/performance_analysis_report.json'

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)

        return output_path


def main():
    """Main function for standalone usage."""
    project_root = '/home/activeloguser/DMLogn8n'
    profiler = PerformanceProfiler(project_root)

    print("Starting performance analysis...")
    results = profiler.analyze_project()

    # Generate report
    report_path = profiler.generate_report(results)
    print(f"Analysis complete. Report saved to: {report_path}")

    # Print summary
    summary = results['performance_summary']
    print(f"\n=== Performance Analysis Summary ===")
    print(f"Functions analyzed: {summary['total_functions_analyzed']}")
    print(f"Overall performance score: {summary['overall_performance_score']:.1f}/100")
    print(f"Algorithmic issues: {len(summary['algorithmic_complexity_issues'])}")
    print(f"Memory-intensive functions: {len(summary['memory_intensive_functions'])}")
    print(f"I/O-intensive operations: {len(summary['io_intensive_operations'])}")
    print(f"Database issues: {len(summary['database_query_issues'])}")
    print(f"Caching opportunities: {len(summary['cache_opportunities'])}")
    print(f"Concurrency opportunities: {len(summary['concurrency_opportunities'])}")

    print(f"\n=== Top Optimization Recommendations ===")
    for rec in results['optimization_recommendations'][:3]:
        print(f"{rec['priority'].upper()}: {rec['title']}")
        print(f"  {rec['description']}")
        print(f"  Estimated impact: {rec['estimated_impact']}")
        print()


if __name__ == "__main__":
    main()