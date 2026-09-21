#!/usr/bin/env python3
"""
Dependency Management System
Analyzes code dependencies, identifies circular dependencies, and optimizes module structure.
"""

import ast
import os
import sys
import importlib.util
import networkx as nx
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import json
import time


@dataclass
class DependencyInfo:
    """Data class for dependency information."""
    module_path: str
    imported_modules: List[str]
    imported_from: List[str]
    dependencies: List[str]
    dependents: List[str]
    circular_dependencies: List[str]
    dependency_depth: int
    coupling_metrics: Dict[str, float]
    cohesion_score: float
    stability_score: float


@dataclass
class ModuleMetrics:
    """Data class for module quality metrics."""
    module_path: str
    lines_of_code: int
    number_of_classes: int
    number_of_functions: int
    number_of_imports: int
    import_complexity: float
    fan_in: int  # Number of modules that depend on this module
    fan_out: int  # Number of modules this module depends on
    instability: float  # fan_out / (fan_in + fan_out)
    abstractness: float  # Number of abstract classes / total classes
    distance_from_main_sequence: float  # |abstractness + instability - 1|


class DependencyManager:
    """Advanced dependency analysis and management system."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.dependency_graph = nx.DiGraph()
        self.module_info = {}
        self.circular_dependencies = []
        self.module_metrics = {}
        self.excluded_modules = {'__pycache__', '.git', '.venv', 'venv', 'node_modules', 'site-packages'}

    def scan_project(self) -> List[Path]:
        """Scan project for Python modules."""
        python_files = []

        for root, dirs, files in os.walk(self.project_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.excluded_modules]

            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)

        return python_files

    def analyze_module(self, file_path: Path) -> DependencyInfo:
        """Analyze dependencies of a single module."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            # Extract imports
            imported_modules = self._extract_imports(tree)
            imported_from = self._extract_import_from(tree)

            # Filter local imports
            local_dependencies = self._filter_local_imports(imported_modules + imported_from)

            # Calculate dependency metrics
            dependency_depth = self._calculate_dependency_depth(file_path, local_dependencies)
            coupling_metrics = self._calculate_coupling_metrics(tree, local_dependencies)
            cohesion_score = self._calculate_cohesion_score(tree)
            stability_score = self._calculate_stability_score(file_path, local_dependencies)

            return DependencyInfo(
                module_path=str(file_path),
                imported_modules=imported_modules,
                imported_from=imported_from,
                dependencies=local_dependencies,
                dependents=[],  # Will be filled later
                circular_dependencies=[],  # Will be filled later
                dependency_depth=dependency_depth,
                coupling_metrics=coupling_metrics,
                cohesion_score=cohesion_score,
                stability_score=stability_score
            )

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements."""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)

        return imports

    def _extract_import_from(self, tree: ast.AST) -> List[str]:
        """Extract from...import statements."""
        imports_from = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    full_import = f"{module}.{alias.name}" if module else alias.name
                    imports_from.append(full_import)

        return imports_from

    def _filter_local_imports(self, imports: List[str]) -> List[str]:
        """Filter imports to include only local project modules."""
        local_imports = []

        for import_name in imports:
            # Remove relative import dots
            clean_import = import_name.lstrip('.')

            # Check if it's a local module
            if self._is_local_module(clean_import):
                local_imports.append(clean_import)

        return local_imports

    def _is_local_module(self, module_name: str) -> bool:
        """Check if a module is from the local project."""
        # Convert module name to potential file paths
        potential_paths = [
            self.project_root / f"{module_name.replace('.', '/')}.py",
            self.project_root / module_name.replace('.', '/') / "__init__.py"
        ]

        return any(path.exists() for path in potential_paths)

    def _calculate_dependency_depth(self, file_path: Path, dependencies: List[str]) -> int:
        """Calculate the maximum dependency depth."""
        if not dependencies:
            return 0

        max_depth = 0
        for dep in dependencies:
            dep_path = self._resolve_module_path(dep)
            if dep_path and dep_path in self.module_info:
                dep_depth = self.module_info[dep_path].dependency_depth
                max_depth = max(max_depth, dep_depth + 1)

        return max_depth

    def _resolve_module_path(self, module_name: str) -> Optional[Path]:
        """Resolve module name to file path."""
        potential_paths = [
            self.project_root / f"{module_name.replace('.', '/')}.py",
            self.project_root / module_name.replace('.', '/') / "__init__.py"
        ]

        for path in potential_paths:
            if path.exists():
                return path

        return None

    def _calculate_coupling_metrics(self, tree: ast.AST, dependencies: List[str]) -> Dict[str, float]:
        """Calculate coupling metrics."""
        # Afferent coupling (Ca) - number of classes that depend on this class
        # Efferent coupling (Ce) - number of classes this class depends on
        # Instability = Ce / (Ca + Ce)

        # Count different types of dependencies
        data_coupling = 0
        control_coupling = 0
        common_coupling = 0
        content_coupling = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    # Method call - could be data or control coupling
                    data_coupling += 1
                elif isinstance(node.func, ast.Name):
                    # Function call - likely control coupling
                    control_coupling += 1
            elif isinstance(node, ast.Attribute):
                # Attribute access - data coupling
                data_coupling += 1

        # Calculate coupling strength
        total_dependencies = len(dependencies)
        coupling_strength = (data_coupling + control_coupling + common_coupling + content_coupling)

        return {
            'afferent_coupling': 0,  # Will be calculated later
            'efferent_coupling': total_dependencies,
            'data_coupling': data_coupling,
            'control_coupling': control_coupling,
            'coupling_strength': coupling_strength,
            'instability': total_dependencies / (total_dependencies + 1) if total_dependencies > 0 else 0
        }

    def _calculate_cohesion_score(self, tree: ast.AST) -> float:
        """Calculate module cohesion score."""
        # Calculate how closely related the elements in a module are to each other
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

        if not classes and not functions:
            return 1.0  # Empty module has perfect cohesion

        # Count shared attributes and method calls
        shared_attributes = set()
        method_calls = defaultdict(set)

        for cls in classes:
            # Get all class attributes
            for node in ast.walk(cls):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    shared_attributes.add(node.id)

        # Count method calls between classes
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    method_name = node.func.attr
                    class_name = node.func.value.id if isinstance(node.func.value, ast.Name) else 'unknown'
                    method_calls[class_name].add(method_name)

        # Calculate cohesion based on shared elements
        total_elements = len(classes) + len(functions)
        shared_elements = len(shared_attributes) + sum(len(calls) for calls in method_calls.values())

        cohesion = shared_elements / total_elements if total_elements > 0 else 1.0
        return min(cohesion, 1.0)

    def _calculate_stability_score(self, file_path: Path, dependencies: List[str]) -> float:
        """Calculate module stability score."""
        # Stability = 1 - (number of outgoing dependencies / total dependencies)
        # Higher stability means module is less likely to change

        outgoing = len(dependencies)
        incoming = 0  # Will be calculated later when graph is built

        total = outgoing + incoming
        stability = 1 - (outgoing / total) if total > 0 else 1.0

        return stability

    def build_dependency_graph(self, module_info: Dict[str, DependencyInfo]) -> nx.DiGraph:
        """Build dependency graph from module information."""
        graph = nx.DiGraph()

        # Add nodes
        for module_path, info in module_info.items():
            graph.add_node(module_path, **asdict(info))

        # Add edges
        for module_path, info in module_info.items():
            for dependency in info.dependencies:
                dep_path = self._resolve_module_path(dependency)
                if dep_path and str(dep_path) in module_info:
                    graph.add_edge(module_path, str(dep_path))

        return graph

    def detect_circular_dependencies(self, graph: nx.DiGraph) -> List[List[str]]:
        """Detect circular dependencies in the graph."""
        try:
            cycles = list(nx.simple_cycles(graph))
            return cycles
        except Exception as e:
            print(f"Error detecting circular dependencies: {e}")
            return []

    def calculate_module_metrics(self, file_path: Path) -> ModuleMetrics:
        """Calculate detailed module metrics."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            # Basic metrics
            lines = len([line for line in content.split('\n') if line.strip()])
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]

            # Calculate abstractness
            abstract_classes = [cls for cls in classes if self._is_abstract_class(cls)]
            abstractness = len(abstract_classes) / len(classes) if classes else 0

            # Get dependency information
            module_path = str(file_path)
            dependencies = self.module_info[module_path].dependencies if module_path in self.module_info else []
            dependents = self.module_info[module_path].dependents if module_path in self.module_info else []

            # Calculate Martin's metrics
            fan_in = len(dependents)
            fan_out = len(dependencies)
            instability = fan_out / (fan_in + fan_out) if (fan_in + fan_out) > 0 else 0

            # Calculate distance from main sequence
            distance = abs(abstractness + instability - 1)

            return ModuleMetrics(
                module_path=module_path,
                lines_of_code=lines,
                number_of_classes=len(classes),
                number_of_functions=len(functions),
                number_of_imports=len(imports),
                import_complexity=self._calculate_import_complexity(tree),
                fan_in=fan_in,
                fan_out=fan_out,
                instability=instability,
                abstractness=abstractness,
                distance_from_main_sequence=distance
            )

        except Exception as e:
            print(f"Error calculating metrics for {file_path}: {e}")
            return None

    def _is_abstract_class(self, class_node: ast.ClassDef) -> bool:
        """Check if a class is abstract."""
        # Check if it has abstract methods or inherits from ABC
        for base in class_node.bases:
            if isinstance(base, ast.Name) and base.id in ['ABC', 'abstractmethod']:
                return True

        # Check for @abstractmethod decorator
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == 'abstractmethod':
                        return True

        return False

    def _calculate_import_complexity(self, tree: ast.AST) -> float:
        """Calculate import complexity based on types and depth."""
        complexity = 0.0

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                # From imports are slightly more complex
                if node.module:
                    complexity += 1.0 + (node.level * 0.5)  # Relative imports add complexity
            elif isinstance(node, ast.Import):
                # Simple imports
                complexity += 0.5

        return complexity

    def analyze_project(self) -> Dict[str, Any]:
        """Analyze entire project for dependencies."""
        print("Scanning project for dependency analysis...")

        python_files = self.scan_project()
        print(f"Found {len(python_files)} Python files")

        # Analyze each module
        for file_path in python_files:
            print(f"Analyzing {file_path}")
            module_info = self.analyze_module(file_path)
            if module_info:
                self.module_info[str(file_path)] = module_info

        # Fill in dependents information
        self._calculate_dependents()

        # Build dependency graph
        self.dependency_graph = self.build_dependency_graph(self.module_info)

        # Detect circular dependencies
        self.circular_dependencies = self.detect_circular_dependencies(self.dependency_graph)

        # Calculate module metrics
        for file_path in python_files:
            metrics = self.calculate_module_metrics(file_path)
            if metrics:
                self.module_metrics[str(file_path)] = metrics

        return self._generate_analysis_results()

    def _calculate_dependents(self):
        """Calculate which modules depend on each module."""
        for module_path, info in self.module_info.items():
            for dependency in info.dependencies:
                dep_path = self._resolve_module_path(dependency)
                if dep_path and str(dep_path) in self.module_info:
                    self.module_info[str(dep_path)].dependents.append(module_path)

    def _generate_analysis_results(self) -> Dict[str, Any]:
        """Generate comprehensive analysis results."""
        # Calculate overall metrics
        total_modules = len(self.module_info)
        total_dependencies = sum(len(info.dependencies) for info in self.module_info.values())
        avg_dependencies = total_dependencies / total_modules if total_modules > 0 else 0

        # Stability analysis
        stability_scores = [info.stability_score for info in self.module_info.values()]
        avg_stability = sum(stability_scores) / len(stability_scores) if stability_scores else 0

        # Cohesion analysis
        cohesion_scores = [info.cohesion_score for info in self.module_info.values()]
        avg_cohesion = sum(cohesion_scores) / len(cohesion_scores) if cohesion_scores else 0

        # Find modules with issues
        high_coupling_modules = []
        low_cohesion_modules = []
        unstable_modules = []

        for module_path, info in self.module_info.items():
            if info.coupling_metrics.get('efferent_coupling', 0) > 10:
                high_coupling_modules.append(module_path)
            if info.cohesion_score < 0.3:
                low_cohesion_modules.append(module_path)
            if info.stability_score < 0.3:
                unstable_modules.append(module_path)

        # Architecture quality metrics
        graph_metrics = self._calculate_graph_metrics()

        return {
            'project_summary': {
                'total_modules': total_modules,
                'total_dependencies': total_dependencies,
                'avg_dependencies_per_module': avg_dependencies,
                'avg_stability_score': avg_stability,
                'avg_cohesion_score': avg_cohesion,
                'circular_dependencies_count': len(self.circular_dependencies),
                'graph_metrics': graph_metrics
            },
            'module_dependencies': {path: asdict(info) for path, info in self.module_info.items()},
            'module_metrics': {path: asdict(metrics) for path, metrics in self.module_metrics.items()},
            'circular_dependencies': self.circular_dependencies,
            'problematic_modules': {
                'high_coupling': high_coupling_modules,
                'low_cohesion': low_cohesion_modules,
                'unstable': unstable_modules
            },
            'recommendations': self._generate_recommendations(),
            'analysis_timestamp': time.time()
        }

    def _calculate_graph_metrics(self) -> Dict[str, Any]:
        """Calculate dependency graph metrics."""
        if not self.dependency_graph:
            return {}

        try:
            return {
                'density': nx.density(self.dependency_graph),
                'is_dag': nx.is_directed_acyclic_graph(self.dependency_graph),
                'number_of_strongly_connected_components': nx.number_strongly_connected_components(self.dependency_graph),
                'average_clustering': nx.average_clustering(self.dependency_graph.to_undirected()),
                'diameter': nx.diameter(self.dependency_graph.to_undirected()) if nx.is_connected(self.dependency_graph.to_undirected()) else None
            }
        except Exception as e:
            print(f"Error calculating graph metrics: {e}")
            return {}

    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate optimization recommendations."""
        recommendations = []

        # Circular dependency recommendations
        if self.circular_dependencies:
            recommendations.append({
                'type': 'circular_dependencies',
                'severity': 'high',
                'description': f"Found {len(self.circular_dependencies)} circular dependencies",
                'suggestion': 'Refactor to break circular dependencies by extracting interfaces or using dependency injection',
                'affected_modules': [module for cycle in self.circular_dependencies for module in cycle]
            })

        # High coupling recommendations
        high_coupling = [(path, info) for path, info in self.module_info.items()
                        if info.coupling_metrics.get('efferent_coupling', 0) > 10]

        if high_coupling:
            recommendations.append({
                'type': 'high_coupling',
                'severity': 'medium',
                'description': f"Found {len(high_coupling)} modules with high coupling",
                'suggestion': 'Consider applying SOLID principles, especially Single Responsibility and Dependency Inversion',
                'affected_modules': [path for path, _ in high_coupling]
            })

        # Low cohesion recommendations
        low_cohesion = [(path, info) for path, info in self.module_info.items() if info.cohesion_score < 0.3]

        if low_cohesion:
            recommendations.append({
                'type': 'low_cohesion',
                'severity': 'medium',
                'description': f"Found {len(low_cohesion)} modules with low cohesion",
                'suggestion': 'Consider splitting modules into more focused components or grouping related functionality',
                'affected_modules': [path for path, _ in low_cohesion]
            })

        # Unstable modules recommendations
        unstable = [(path, info) for path, info in self.module_info.items() if info.stability_score < 0.3]

        if unstable:
            recommendations.append({
                'type': 'instability',
                'severity': 'low',
                'description': f"Found {len(unstable)} unstable modules",
                'suggestion': 'Consider making these modules more abstract or reducing their dependencies',
                'affected_modules': [path for path, _ in unstable]
            })

        return recommendations

    def generate_report(self, analysis_results: Dict[str, Any], output_path: str = None) -> str:
        """Generate dependency analysis report."""
        if output_path is None:
            output_path = '/home/activeloguser/DMLogn8n/quality/reports/dependency_analysis_report.json'

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)

        return output_path

    def visualize_dependencies(self, output_path: str = None) -> str:
        """Generate dependency graph visualization."""
        if output_path is None:
            output_path = '/home/activeloguser/DMLogn8n/quality/reports/dependency_graph.png'

        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches

            # Create visualization
            plt.figure(figsize=(20, 15))

            # Use spring layout for better visualization
            pos = nx.spring_layout(self.dependency_graph, k=1, iterations=50)

            # Draw nodes with different colors based on stability
            node_colors = []
            for node in self.dependency_graph.nodes():
                if node in self.module_info:
                    stability = self.module_info[node].stability_score
                    if stability > 0.7:
                        node_colors.append('green')  # Stable
                    elif stability > 0.4:
                        node_colors.append('yellow')  # Moderate
                    else:
                        node_colors.append('red')  # Unstable
                else:
                    node_colors.append('gray')

            nx.draw(self.dependency_graph, pos, with_labels=False, node_color=node_colors,
                   node_size=500, alpha=0.7, arrows=True, arrowsize=20)

            # Highlight circular dependencies
            for cycle in self.circular_dependencies:
                cycle_edges = [(cycle[i], cycle[i+1]) for i in range(len(cycle)-1)]
                cycle_edges.append((cycle[-1], cycle[0]))
                nx.draw_networkx_edges(self.dependency_graph, pos, edgelist=cycle_edges,
                                     edge_color='red', width=3, alpha=0.8)

            plt.title("Dependency Graph\n(Red nodes: unstable, Yellow: moderate, Green: stable)", fontsize=16)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

            return output_path

        except ImportError:
            print("Matplotlib not available for visualization")
            return None


def main():
    """Main function for standalone usage."""
    project_root = '/home/activeloguser/DMLogn8n'
    manager = DependencyManager(project_root)

    print("Starting dependency analysis...")
    results = manager.analyze_project()

    # Generate report
    report_path = manager.generate_report(results)
    print(f"Analysis complete. Report saved to: {report_path}")

    # Generate visualization
    viz_path = manager.visualize_dependencies()
    if viz_path:
        print(f"Dependency graph visualization saved to: {viz_path}")

    # Print summary
    summary = results['project_summary']
    print(f"\n=== Dependency Analysis Summary ===")
    print(f"Total modules: {summary['total_modules']}")
    print(f"Total dependencies: {summary['total_dependencies']}")
    print(f"Average dependencies per module: {summary['avg_dependencies_per_module']:.1f}")
    print(f"Average stability score: {summary['avg_stability_score']:.2f}")
    print(f"Average cohesion score: {summary['avg_cohesion_score']:.2f}")
    print(f"Circular dependencies: {summary['circular_dependencies_count']}")

    print(f"\n=== Recommendations ===")
    for rec in results['recommendations']:
        print(f"{rec['type'].upper()}: {rec['description']}")
        print(f"  Suggestion: {rec['suggestion']}")
        print(f"  Severity: {rec['severity']}")
        print()


if __name__ == "__main__":
    main()