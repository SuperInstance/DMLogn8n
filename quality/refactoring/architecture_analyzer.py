#!/usr/bin/env python3
"""
Software Architecture Analyzer
Analyzes software architecture, design patterns, and structural quality.
"""

import ast
import os
import re
import json
import time
import networkx as nx
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
from enum import Enum


class ArchitecturalPattern(Enum):
    """Common architectural patterns."""
    LAYERED = "layered"
    MICROSERVICES = "microservices"
    EVENT_DRIVEN = "event_driven"
    MVC = "mvc"
    MVP = "mvp"
    MVVM = "mvvm"
    HEXAGONAL = "hexagonal"
    CLEAN_ARCHITECTURE = "clean_architecture"
    PLUGIN = "plugin"
    REPOSITORY = "repository"
    FACTORY = "factory"
    OBSERVER = "observer"
    STRATEGY = "strategy"
    COMMAND = "command"
    DECORATOR = "decorator"
    ADAPTER = "adapter"
    FACADE = "facade"
    PROXY = "proxy"


class ArchitecturalIssue(Enum):
    """Types of architectural issues."""
    ARCHITECTURAL_VIOLATION = "architectural_violation"
    DESIGN_PATTERN_VIOLATION = "design_pattern_violation"
    SOLID_VIOLATION = "solid_violation"
    COUPLING_ISSUE = "coupling_issue"
    COHESION_ISSUE = "cohesion_issue"
    LAYER_VIOLATION = "layer_violation"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    GOD_OBJECT = "god_object"
    SPAGHETTI_CODE = "spaghetti_code"
    REINVENTED_WHEEL = "reinvented_wheel"


@dataclass
class ArchitectureMetrics:
    """Metrics for architectural analysis."""
    total_modules: int
    total_classes: int
    total_interfaces: int
    inheritance_depth: float
    fan_in: float
    fan_out: float
    coupling_between_objects: float
    cohesion_of_methods: float
    lack_of_cohesion_of_methods: float
    response_for_class: float
    weighted_methods_per_class: float


@dataclass
class DesignPatternInstance:
    """Instance of a detected design pattern."""
    pattern_type: ArchitecturalPattern
    confidence: float
    participants: List[str]
    location: str
    description: str


@dataclass
class ArchitectureViolation:
    """Architecture violation or issue."""
    violation_type: ArchitecturalIssue
    severity: str
    file_path: str
    line_number: int
    description: str
    suggestion: str
    affected_components: List[str]


class ArchitectureAnalyzer:
    """Comprehensive software architecture analysis system."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.dependency_graph = nx.DiGraph()
        self.module_hierarchy = defaultdict(list)
        self.detected_patterns = []
        self.architecture_violations = []
        self.solid_violations = []
        self.design_patterns = self._initialize_design_patterns()
        self.architecture_principles = self._initialize_architecture_principles()

    def _initialize_design_patterns(self) -> Dict[ArchitecturalPattern, Dict[str, Any]]:
        """Initialize design pattern detection rules."""
        return {
            ArchitecturalPattern.FACTORY: {
                'class_suffixes': ['Factory', 'Creator'],
                'method_names': ['create', 'build', 'make', 'factory'],
                'characteristics': ['static_creation_method', 'abstract_factory']
            },
            ArchitecturalPattern.SINGLETON: {
                'method_names': ['getInstance', 'instance', '__new__'],
                'characteristics': ['private_constructor', 'static_instance']
            },
            ArchitecturalPattern.OBSERVER: {
                'method_names': ['notify', 'update', 'attach', 'detach', 'subscribe', 'unsubscribe'],
                'class_suffixes': ['Observer', 'Subject', 'Publisher', 'Subscriber'],
                'characteristics': ['notification_method', 'observer_list']
            },
            ArchitecturalPattern.STRATEGY: {
                'method_names': ['execute', 'algorithm', 'strategy'],
                'class_suffixes': ['Strategy', 'Algorithm'],
                'characteristics': ['interface_implementation', 'algorithm_variation']
            },
            ArchitecturalPattern.COMMAND: {
                'method_names': ['execute', 'undo', 'redo'],
                'class_suffixes': ['Command', 'Action'],
                'characteristics': ['command_interface', 'invoker']
            },
            ArchitecturalPattern.ADAPTER: {
                'class_suffixes': ['Adapter', 'Wrapper'],
                'characteristics': ['interface_conversion', 'legacy_integration']
            },
            ArchitecturalPattern.FACADE: {
                'class_suffixes': ['Facade', 'Manager'],
                'characteristics': ['simplified_interface', 'subsystem_encapsulation']
            },
            ArchitecturalPattern.REPOSITORY: {
                'class_suffixes': ['Repository', 'Dao', 'Storage'],
                'method_names': ['save', 'find', 'delete', 'update', 'query'],
                'characteristics': ['data_access_abstraction', 'collection_like_interface']
            },
            ArchitecturalPattern.DECORATOR: {
                'class_suffixes': ['Decorator', 'Wrapper'],
                'characteristics': ['same_interface', 'runtime_addition']
            },
            ArchitecturalPattern.PROXY: {
                'class_suffixes': ['Proxy', 'Surrogate'],
                'characteristics': ['same_interface', 'access_control']
            }
        }

    def _initialize_architecture_principles(self) -> Dict[str, Any]:
        """Initialize architecture principles to check."""
        return {
            'solid_principles': {
                'single_responsibility': {
                    'description': 'A class should have only one reason to change',
                    'indicators': ['multiple_responsibilities', 'too_many_methods', 'diverse_functionality']
                },
                'open_closed': {
                    'description': 'Software entities should be open for extension, closed for modification',
                    'indicators': ['frequent_modification', 'extension_points_missing']
                },
                'liskov_substitution': {
                    'description': 'Subtypes must be substitutable for their base types',
                    'indicators': ['subtype_violation', 'contract_broken']
                },
                'interface_segregation': {
                    'description': 'Clients should not be forced to depend on interfaces they do not use',
                    'indicators': ['fat_interface', 'unused_methods']
                },
                'dependency_inversion': {
                    'description': 'Depend on abstractions, not concretions',
                    'indicators': ['concrete_dependencies', 'tight_coupling']
                }
            },
            'quality_attributes': {
                'modularity': ['high_cohesion', 'low_coupling', 'encapsulation'],
                'maintainability': ['clear_structure', 'separation_of_concerns', 'testability'],
                'scalability': ['loose_coupling', 'statelessness', 'horizontal_scaling'],
                'reliability': ['error_handling', 'fault_tolerance', 'recovery']
            }
        }

    def analyze_architecture(self) -> Dict[str, Any]:
        """Analyze the overall architecture of the project."""
        print("Analyzing software architecture...")

        # Scan and parse all Python files
        python_files = self._scan_python_files()
        print(f"Found {len(python_files)} Python files")

        # Analyze each file
        all_classes = []
        all_modules = []
        for file_path in python_files:
            print(f"Analyzing {file_path}")
            classes, module_info = self._analyze_file_architecture(file_path)
            all_classes.extend(classes)
            all_modules.append(module_info)

        # Build dependency graph
        self._build_dependency_graph(all_classes, all_modules)

        # Detect design patterns
        self._detect_design_patterns(all_classes)

        # Analyze SOLID principles violations
        self._analyze_solid_violations(all_classes)

        # Analyze architectural layers
        layers = self._analyze_architectural_layers(all_classes, all_modules)

        # Calculate architectural metrics
        metrics = self._calculate_architectural_metrics(all_classes, all_modules)

        # Identify architectural issues
        self._identify_architectural_issues(all_classes, all_modules)

        # Generate recommendations
        recommendations = self._generate_architecture_recommendations()

        return {
            'architecture_summary': {
                'total_classes': len(all_classes),
                'total_modules': len(all_modules),
                'detected_patterns': len(self.detected_patterns),
                'violations_count': len(self.architecture_violations),
                'solid_violations': len(self.solid_violations),
                'layers': layers
            },
            'design_patterns': [asdict(pattern) for pattern in self.detected_patterns],
            'architectural_metrics': asdict(metrics),
            'violations': [asdict(violation) for violation in self.architecture_violations],
            'solid_violations': [asdict(violation) for violation in self.solid_violations],
            'recommendations': recommendations,
            'analysis_timestamp': time.time()
        }

    def _scan_python_files(self) -> List[Path]:
        """Scan project for Python files."""
        python_files = []

        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.venv', 'venv', 'node_modules'}]

            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)

        return python_files

    def _analyze_file_architecture(self, file_path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Analyze architecture of a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            # Extract class information
            classes = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = self._analyze_class_architecture(node, file_path)
                    classes.append(class_info)

            # Extract module information
            module_info = self._analyze_module_architecture(tree, file_path)

            return classes, module_info

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return [], {}

    def _analyze_class_architecture(self, class_node: ast.ClassDef, file_path: Path) -> Dict[str, Any]:
        """Analyze architecture of a single class."""
        # Extract methods
        methods = []
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                method_info = {
                    'name': node.name,
                    'is_abstract': any(isinstance(d, ast.Name) and d.id == 'abstractmethod' for d in node.decorator_list),
                    'is_static': any(isinstance(d, ast.Name) and d.id == 'staticmethod' for d in node.decorator_list),
                    'is_class_method': any(isinstance(d, ast.Name) and d.id == 'classmethod' for d in node.decorator_list),
                    'parameters': len(node.args.args),
                    'line_number': node.lineno,
                    'complexity': self._calculate_method_complexity(node)
                }
                methods.append(method_info)

        # Extract attributes
        attributes = []
        for node in class_node.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        attributes.append({
                            'name': target.id,
                            'is_private': target.id.startswith('_'),
                            'line_number': node.lineno
                        })

        # Extract inheritance information
        base_classes = []
        for base in class_node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)

        # Calculate class metrics
        class_metrics = self._calculate_class_metrics(class_node, methods, attributes)

        return {
            'name': class_node.name,
            'file_path': str(file_path),
            'line_number': class_node.lineno,
            'methods': methods,
            'attributes': attributes,
            'base_classes': base_classes,
            'metrics': class_metrics,
            'is_interface': self._is_interface_class(class_node),
            'is_abstract': self._is_abstract_class(class_node),
            'design_patterns': []  # Will be filled later
        }

    def _analyze_module_architecture(self, tree: ast.AST, file_path: Path) -> Dict[str, Any]:
        """Analyze architecture of a module."""
        # Extract imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}" if module else alias.name)

        # Extract top-level functions
        functions = []
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    'name': node.name,
                    'line_number': node.lineno,
                    'complexity': self._calculate_method_complexity(node)
                })

        # Determine module layer
        layer = self._determine_module_layer(file_path, imports, functions)

        return {
            'file_path': str(file_path),
            'imports': imports,
            'functions': functions,
            'layer': layer,
            'is_test_module': 'test' in file_path.name.lower()
        }

    def _calculate_method_complexity(self, method_node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a method."""
        complexity = 1  # Base complexity

        for node in ast.walk(method_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.With)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1

        return complexity

    def _calculate_class_metrics(self, class_node: ast.ClassDef, methods: List[Dict], attributes: List[Dict]) -> Dict[str, Any]:
        """Calculate various class-level metrics."""
        # Weighted Methods per Class (WMC)
        wmc = sum(method['complexity'] for method in methods)

        # Response for a Class (RFC)
        rfc = len(methods) + sum(len(method['parameters']) for method in methods)

        # Lack of Cohesion of Methods (LCOM)
        lcom = self._calculate_lcom(methods, attributes)

        # Coupling between objects (CBO) - will be calculated later
        cbo = 0

        # Depth of Inheritance Tree (DIT)
        dit = len(class_node.bases)

        # Number of Children (NOC) - will be calculated later
        noc = 0

        return {
            'wmc': wmc,
            'rfc': rfc,
            'lcom': lcom,
            'cbo': cbo,
            'dit': dit,
            'noc': noc,
            'method_count': len(methods),
            'attribute_count': len(attributes),
            'public_methods': len([m for m in methods if not m['name'].startswith('_')]),
            'private_methods': len([m for m in methods if m['name'].startswith('_')])
        }

    def _calculate_lcom(self, methods: List[Dict], attributes: List[Dict]) -> float:
        """Calculate Lack of Cohesion of Methods."""
        if not methods or not attributes:
            return 0.0

        # Simplified LCOM calculation
        # Count methods that use each attribute
        attribute_usage = defaultdict(int)
        for method in methods:
            method_name = method['name']
            # This is simplified - in real implementation, we'd analyze method bodies
            for attr in attributes:
                # Assume some attribute usage based on naming
                if attr['name'].replace('_', '') in method_name.replace('_', ''):
                    attribute_usage[attr['name']] += 1

        # Calculate LCOM based on attribute usage
        used_attributes = len([attr for attr in attributes if attribute_usage[attr['name']] > 0])
        total_attributes = len(attributes)

        if total_attributes == 0:
            return 0.0

        # LCOM = (methods_using_no_attributes - methods_using_all_attributes) / total_methods
        methods_using_no_attributes = len([m for m in methods if all(attribute_usage[attr['name']] == 0 for attr in attributes)])
        methods_using_all_attributes = len([m for m in methods if all(attribute_usage[attr['name']] > 0 for attr in attributes)])

        lcom = (methods_using_no_attributes - methods_using_all_attributes) / len(methods) if methods else 0
        return max(0, lcom)

    def _is_interface_class(self, class_node: ast.ClassDef) -> bool:
        """Check if a class is an interface."""
        # Check if all methods are abstract
        methods = [node for node in class_node.body if isinstance(node, ast.FunctionDef)]
        if not methods:
            return False

        abstract_methods = 0
        for method in methods:
            if any(isinstance(d, ast.Name) and d.id == 'abstractmethod' for d in method.decorator_list):
                abstract_methods += 1

        return abstract_methods == len(methods)

    def _is_abstract_class(self, class_node: ast.ClassDef) -> bool:
        """Check if a class is abstract."""
        return any(isinstance(d, ast.Name) and d.id == 'abstractmethod' for d in class_node.body
                  if hasattr(d, 'decorator_list') for d in class_node.body
                  if isinstance(d, ast.FunctionDef) for d in d.decorator_list)

    def _determine_module_layer(self, file_path: Path, imports: List[str], functions: List[Dict]) -> str:
        """Determine the architectural layer of a module."""
        path_parts = file_path.parts
        file_name = file_path.name.lower()

        # Check for common layer indicators
        if any(part in ['models', 'entities', 'domain'] for part in path_parts):
            return 'domain'
        elif any(part in ['controllers', 'handlers', 'views'] for part in path_parts):
            return 'presentation'
        elif any(part in ['services', 'business', 'logic'] for part in path_parts):
            return 'business'
        elif any(part in ['repositories', 'dao', 'storage', 'database'] for part in path_parts):
            return 'data'
        elif any(part in ['utils', 'helpers', 'common', 'shared'] for part in path_parts):
            return 'infrastructure'
        elif 'test' in file_name:
            return 'test'
        elif any(imp in ['django', 'flask', 'fastapi'] for imp in imports):
            return 'presentation'
        elif any(imp in ['sqlalchemy', 'psycopg2', 'pymongo'] for imp in imports):
            return 'data'

        return 'unknown'

    def _build_dependency_graph(self, classes: List[Dict], modules: List[Dict]):
        """Build dependency graph from classes and modules."""
        # Add nodes
        for class_info in classes:
            self.dependency_graph.add_node(class_info['name'], **class_info)

        # Add edges based on inheritance
        for class_info in classes:
            for base_class in class_info['base_classes']:
                if base_class in [c['name'] for c in classes]:
                    self.dependency_graph.add_edge(class_info['name'], base_class, type='inheritance')

        # Add edges based on module imports
        for module_info in modules:
            for import_name in module_info['imports']:
                # Find if this import corresponds to a class in our project
                for class_info in classes:
                    if import_name.split('.')[-1] == class_info['name']:
                        module_name = Path(module_info['file_path']).stem
                        self.dependency_graph.add_edge(module_name, class_info['name'], type='import')

    def _detect_design_patterns(self, classes: List[Dict]):
        """Detect design patterns in the codebase."""
        for class_info in classes:
            for pattern_type, pattern_rules in self.design_patterns.items():
                confidence = self._calculate_pattern_confidence(class_info, pattern_rules)
                if confidence > 0.6:  # Threshold for pattern detection
                    pattern_instance = DesignPatternInstance(
                        pattern_type=pattern_type,
                        confidence=confidence,
                        participants=[class_info['name']],
                        location=class_info['file_path'],
                        description=self._generate_pattern_description(pattern_type, class_info)
                    )
                    self.detected_patterns.append(pattern_instance)

    def _calculate_pattern_confidence(self, class_info: Dict, pattern_rules: Dict[str, Any]) -> float:
        """Calculate confidence score for a pattern match."""
        confidence = 0.0
        indicators = 0

        class_name = class_info['name']
        method_names = [method['name'] for method in class_info['methods']]

        # Check class suffixes
        if 'class_suffixes' in pattern_rules:
            for suffix in pattern_rules['class_suffixes']:
                if class_name.endswith(suffix):
                    confidence += 0.3
                    indicators += 1

        # Check method names
        if 'method_names' in pattern_rules:
            for method_name in pattern_rules['method_names']:
                if any(method_name.lower() in name.lower() for name in method_names):
                    confidence += 0.2
                    indicators += 1

        # Check characteristics
        if 'characteristics' in pattern_rules:
            for characteristic in pattern_rules['characteristics']:
                if self._check_pattern_characteristic(class_info, characteristic):
                    confidence += 0.2
                    indicators += 1

        # Normalize confidence
        max_possible_confidence = len(pattern_rules.get('class_suffixes', [])) * 0.3 + \
                                  len(pattern_rules.get('method_names', [])) * 0.2 + \
                                  len(pattern_rules.get('characteristics', [])) * 0.2

        if max_possible_confidence > 0:
            confidence = min(confidence / max_possible_confidence, 1.0)

        return confidence

    def _check_pattern_characteristic(self, class_info: Dict, characteristic: str) -> bool:
        """Check if a class exhibits a specific pattern characteristic."""
        if characteristic == 'static_creation_method':
            return any(method['is_static'] and any(create in method['name'].lower()
                       for create in ['create', 'build', 'make', 'factory'])
                   for method in class_info['methods'])
        elif characteristic == 'interface_implementation':
            return len(class_info['base_classes']) > 0
        elif characteristic == 'notification_method':
            return any('notify' in method['name'].lower() or 'update' in method['name'].lower()
                      for method in class_info['methods'])
        elif characteristic == 'command_interface':
            return any(method['name'] == 'execute' for method in class_info['methods'])
        elif characteristic == 'same_interface':
            # Would need more sophisticated analysis
            return len(class_info['base_classes']) > 0

        return False

    def _generate_pattern_description(self, pattern_type: ArchitecturalPattern, class_info: Dict) -> str:
        """Generate description for detected pattern."""
        descriptions = {
            ArchitecturalPattern.FACTORY: f"Factory pattern detected in {class_info['name']} for object creation",
            ArchitecturalPattern.SINGLETON: f"Singleton pattern detected in {class_info['name']} ensuring single instance",
            ArchitecturalPattern.OBSERVER: f"Observer pattern detected in {class_info['name']} for event notification",
            ArchitecturalPattern.STRATEGY: f"Strategy pattern detected in {class_info['name']} for algorithm variation",
            ArchitecturalPattern.REPOSITORY: f"Repository pattern detected in {class_info['name']} for data access abstraction",
        }
        return descriptions.get(pattern_type, f"{pattern_type.value} pattern detected in {class_info['name']}")

    def _analyze_solid_violations(self, classes: List[Dict]):
        """Analyze SOLID principle violations."""
        for class_info in classes:
            # Single Responsibility Principle violations
            if self._violates_srp(class_info):
                violation = ArchitectureViolation(
                    violation_type=ArchitecturalIssue.SOLID_VIOLATION,
                    severity='medium',
                    file_path=class_info['file_path'],
                    line_number=class_info['line_number'],
                    description=f"Class {class_info['name']} may violate Single Responsibility Principle",
                    suggestion="Consider splitting this class into smaller, more focused classes",
                    affected_components=[class_info['name']]
                )
                self.solid_violations.append(violation)

            # Open/Closed Principle violations
            if self._violates_ocp(class_info):
                violation = ArchitectureViolation(
                    violation_type=ArchitecturalIssue.SOLID_VIOLATION,
                    severity='medium',
                    file_path=class_info['file_path'],
                    line_number=class_info['line_number'],
                    description=f"Class {class_info['name']} may violate Open/Closed Principle",
                    suggestion="Consider using abstraction and composition instead of modification",
                    affected_components=[class_info['name']]
                )
                self.solid_violations.append(violation)

            # Dependency Inversion Principle violations
            if self._violates_dip(class_info):
                violation = ArchitectureViolation(
                    violation_type=ArchitecturalIssue.SOLID_VIOLATION,
                    severity='high',
                    file_path=class_info['file_path'],
                    line_number=class_info['line_number'],
                    description=f"Class {class_info['name']} may violate Dependency Inversion Principle",
                    suggestion="Depend on abstractions rather than concrete implementations",
                    affected_components=[class_info['name']]
                )
                self.solid_violations.append(violation)

    def _violates_srp(self, class_info: Dict) -> bool:
        """Check if class violates Single Responsibility Principle."""
        # Heuristics for SRP violations
        metrics = class_info['metrics']

        # Too many methods might indicate multiple responsibilities
        if metrics['method_count'] > 15:
            return True

        # High WMC (Weighted Methods per Class) might indicate complexity
        if metrics['wmc'] > 20:
            return True

        # High LCOM indicates lack of cohesion
        if metrics['lcom'] > 0.8:
            return True

        return False

    def _violates_ocp(self, class_info: Dict) -> bool:
        """Check if class violates Open/Closed Principle."""
        # Heuristics for OCP violations
        methods = class_info['methods']

        # Many conditional statements might indicate the class is not closed for modification
        complex_methods = [m for m in methods if m['complexity'] > 5]
        if len(complex_methods) > len(methods) * 0.3:
            return True

        return False

    def _violates_dip(self, class_info: Dict) -> bool:
        """Check if class violates Dependency Inversion Principle."""
        # Check if class depends on concrete classes rather than abstractions
        base_classes = class_info['base_classes']

        # If class has no abstract base classes but has methods, it might violate DIP
        if len(base_classes) == 0 and len(class_info['methods']) > 0:
            return True

        return False

    def _analyze_architectural_layers(self, classes: List[Dict], modules: List[Dict]) -> Dict[str, Any]:
        """Analyze architectural layers and their relationships."""
        layers = defaultdict(list)

        # Group classes by layer
        for class_info in classes:
            module_info = next((m for m in modules if m['file_path'] == class_info['file_path']), None)
            if module_info:
                layer = module_info['layer']
                layers[layer].append(class_info['name'])

        # Check for layer violations
        layer_violations = []
        for module_info in modules:
            violations = self._check_layer_violations(module_info, modules)
            layer_violations.extend(violations)

        return {
            'layers': dict(layers),
            'layer_count': len(layers),
            'violations': layer_violations
        }

    def _check_layer_violations(self, module_info: Dict, all_modules: List[Dict]) -> List[Dict]:
        """Check for architectural layer violations."""
        violations = []
        current_layer = module_info['layer']

        # Define allowed dependencies between layers
        allowed_dependencies = {
            'presentation': ['business'],
            'business': ['domain', 'data'],
            'data': ['domain'],
            'domain': [],
            'infrastructure': ['domain', 'data', 'business'],
            'test': ['*']  # Tests can depend on anything
        }

        if current_layer in allowed_dependencies:
            allowed_layers = allowed_dependencies[current_layer]

            for import_name in module_info['imports']:
                # Find which layer this import belongs to
                import_layer = self._get_import_layer(import_name, all_modules)

                if import_layer and import_layer not in allowed_layers and '*' not in allowed_layers:
                    violations.append({
                        'type': 'layer_violation',
                        'from_layer': current_layer,
                        'to_layer': import_layer,
                        'import': import_name,
                        'file': module_info['file_path']
                    })

        return violations

    def _get_import_layer(self, import_name: str, all_modules: List[Dict]) -> Optional[str]:
        """Determine which layer an import belongs to."""
        for module_info in all_modules:
            if import_name in module_info['imports'] or import_name.split('.')[-1] in Path(module_info['file_path']).stem:
                return module_info['layer']
        return None

    def _calculate_architectural_metrics(self, classes: List[Dict], modules: List[Dict]) -> ArchitectureMetrics:
        """Calculate comprehensive architectural metrics."""
        if not classes:
            return ArchitectureMetrics(
                total_modules=0, total_classes=0, total_interfaces=0,
                inheritance_depth=0, fan_in=0, fan_out=0,
                coupling_between_objects=0, cohesion_of_methods=0,
                lack_of_cohesion_of_methods=0, response_for_class=0,
                weighted_methods_per_class=0
            )

        # Calculate average metrics
        total_modules = len(modules)
        total_classes = len(classes)
        total_interfaces = len([c for c in classes if c['is_interface']])

        # Inheritance depth
        inheritance_depths = [c['metrics']['dit'] for c in classes]
        avg_inheritance_depth = sum(inheritance_depths) / len(inheritance_depths) if inheritance_depths else 0

        # Weighted Methods per Class
        wmc_values = [c['metrics']['wmc'] for c in classes]
        avg_wmc = sum(wmc_values) / len(wmc_values) if wmc_values else 0

        # Response for a Class
        rfc_values = [c['metrics']['rfc'] for c in classes]
        avg_rfc = sum(rfc_values) / len(rfc_values) if rfc_values else 0

        # Lack of Cohesion of Methods
        lcom_values = [c['metrics']['lcom'] for c in classes]
        avg_lcom = sum(lcom_values) / len(lcom_values) if lcom_values else 0

        # Fan-in and Fan-out (simplified calculation based on dependency graph)
        fan_in_values = []
        fan_out_values = []

        for class_info in classes:
            # Simplified calculation - in real implementation, use dependency graph
            fan_in = len([c for c in classes if class_info['name'] in c['base_classes']])
            fan_out = len(class_info['base_classes'])

            fan_in_values.append(fan_in)
            fan_out_values.append(fan_out)

        avg_fan_in = sum(fan_in_values) / len(fan_in_values) if fan_in_values else 0
        avg_fan_out = sum(fan_out_values) / len(fan_out_values) if fan_out_values else 0

        # Coupling Between Objects (CBO)
        cbo_values = [c['metrics']['cbo'] for c in classes]
        avg_cbo = sum(cbo_values) / len(cbo_values) if cbo_values else 0

        # Cohesion of Methods (inverse of LCOM)
        avg_cohesion = 1 - avg_lcom

        return ArchitectureMetrics(
            total_modules=total_modules,
            total_classes=total_classes,
            total_interfaces=total_interfaces,
            inheritance_depth=avg_inheritance_depth,
            fan_in=avg_fan_in,
            fan_out=avg_fan_out,
            coupling_between_objects=avg_cbo,
            cohesion_of_methods=avg_cohesion,
            lack_of_cohesion_of_methods=avg_lcom,
            response_for_class=avg_rfc,
            weighted_methods_per_class=avg_wmc
        )

    def _identify_architectural_issues(self, classes: List[Dict], modules: List[Dict]):
        """Identify various architectural issues."""
        # God objects
        for class_info in classes:
            if class_info['metrics']['method_count'] > 20 or class_info['metrics']['attribute_count'] > 15:
                violation = ArchitectureViolation(
                    violation_type=ArchitecturalIssue.GOD_OBJECT,
                    severity='high',
                    file_path=class_info['file_path'],
                    line_number=class_info['line_number'],
                    description=f"Class {class_info['name']} appears to be a God object with {class_info['metrics']['method_count']} methods and {class_info['metrics']['attribute_count']} attributes",
                    suggestion="Consider breaking this class into smaller, more focused classes",
                    affected_components=[class_info['name']]
                )
                self.architecture_violations.append(violation)

        # High coupling
        for class_info in classes:
            if class_info['metrics']['wmc'] > 25:
                violation = ArchitectureViolation(
                    violation_type=ArchitecturalIssue.COUPLING_ISSUE,
                    severity='medium',
                    file_path=class_info['file_path'],
                    line_number=class_info['line_number'],
                    description=f"Class {class_info['name']} has high coupling (WMC: {class_info['metrics']['wmc']})",
                    suggestion="Consider reducing complexity and dependencies",
                    affected_components=[class_info['name']]
                )
                self.architecture_violations.append(violation)

    def _generate_architecture_recommendations(self) -> List[Dict[str, Any]]:
        """Generate architectural improvement recommendations."""
        recommendations = []

        # Pattern recommendations
        if len(self.detected_patterns) < 5:
            recommendations.append({
                'type': 'design_patterns',
                'priority': 'medium',
                'title': 'Increase Use of Design Patterns',
                'description': 'Consider implementing more design patterns to improve code structure',
                'suggestion': 'Review opportunities for Factory, Strategy, Observer, and Repository patterns',
                'estimated_effort': '2-4 days'
            })

        # SOLID principle recommendations
        if len(self.solid_violations) > 0:
            recommendations.append({
                'type': 'solid_principles',
                'priority': 'high',
                'title': 'Address SOLID Principle Violations',
                'description': f'Found {len(self.solid_violations)} SOLID principle violations',
                'suggestion': 'Refactor classes to better adhere to SOLID principles',
                'estimated_effort': '1-2 weeks'
            })

        # Layer architecture recommendations
        recommendations.append({
            'type': 'layer_architecture',
            'priority': 'medium',
            'title': 'Improve Layer Architecture',
            'description': 'Strengthen separation of concerns between architectural layers',
            'suggestion': 'Clearly define layer responsibilities and enforce dependency rules',
            'estimated_effort': '3-5 days'
        })

        return recommendations

    def generate_report(self, analysis_results: Dict[str, Any], output_path: str = None) -> str:
        """Generate architecture analysis report."""
        if output_path is None:
            output_path = '/home/activeloguser/DMLogn8n/quality/reports/architecture_analysis_report.json'

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)

        return output_path


def main():
    """Main function for standalone usage."""
    project_root = '/home/activeloguser/DMLogn8n'
    analyzer = ArchitectureAnalyzer(project_root)

    print("Starting architecture analysis...")
    results = analyzer.analyze_architecture()

    # Generate report
    report_path = analyzer.generate_report(results)
    print(f"Analysis complete. Report saved to: {report_path}")

    # Print summary
    summary = results['architecture_summary']
    print(f"\n=== Architecture Analysis Summary ===")
    print(f"Total classes: {summary['total_classes']}")
    print(f"Total modules: {summary['total_modules']}")
    print(f"Design patterns detected: {summary['detected_patterns']}")
    print(f"Architectural violations: {summary['violations_count']}")
    print(f"SOLID principle violations: {summary['solid_violations']}")

    metrics = results['architectural_metrics']
    print(f"\n=== Architectural Metrics ===")
    print(f"Average inheritance depth: {metrics['inheritance_depth']:.2f}")
    print(f"Average weighted methods per class: {metrics['weighted_methods_per_class']:.2f}")
    print(f"Average response for class: {metrics['response_for_class']:.2f}")
    print(f"Average coupling between objects: {metrics['coupling_between_objects']:.2f}")
    print(f"Average cohesion of methods: {metrics['cohesion_of_methods']:.2f}")

    print(f"\n=== Detected Design Patterns ===")
    for pattern in results['design_patterns']:
        print(f"{pattern['pattern_type']}: {pattern['participants'][0]} (confidence: {pattern['confidence']:.2f})")

    print(f"\n=== Top Recommendations ===")
    for rec in results['recommendations'][:3]:
        print(f"- {rec['title']}")
        print(f"  {rec['description']}")
        print(f"  Priority: {rec['priority']}")
        print()


if __name__ == "__main__":
    main()