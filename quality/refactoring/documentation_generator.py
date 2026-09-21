#!/usr/bin/env python3
"""
Automatic Documentation Generator
Generates comprehensive documentation from code analysis and metadata.
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
import inspect
from datetime import datetime


@dataclass
class DocumentationSection:
    """Data class for documentation sections."""
    title: str
    content: str
    subsections: List['DocumentationSection']
    metadata: Dict[str, Any]
    code_examples: List[str]
    diagrams: List[str]


@dataclass
class APIDocumentation:
    """Data class for API documentation."""
    module_name: str
    file_path: str
    description: str
    functions: List[Dict[str, Any]]
    classes: List[Dict[str, Any]]
    constants: List[Dict[str, Any]]
    examples: List[str]
    dependencies: List[str]
    usage_notes: List[str]


class DocumentationGenerator:
    """Automatic documentation generation system."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.documentation_config = self._initialize_documentation_config()
        self.templates = self._initialize_templates()
        self.project_structure = self._analyze_project_structure()

    def _initialize_documentation_config(self) -> Dict[str, Any]:
        """Initialize documentation configuration."""
        return {
            'output_format': 'markdown',  # markdown, html, rst
            'include_private': False,
            'include_magic_methods': False,
            'include_type_hints': True,
            'include_examples': True,
            'include_diagrams': True,
            'max_line_length': 88,
            'toc_depth': 3,
            'sections': [
                'introduction',
                'installation',
                'quick_start',
                'api_reference',
                'examples',
                'architecture',
                'contributing',
                'changelog'
            ],
            'ignore_patterns': [
                'test_*.py',
                '*_test.py',
                '__pycache__',
                '.venv',
                'venv'
            ]
        }

    def _initialize_templates(self) -> Dict[str, str]:
        """Initialize documentation templates."""
        return {
            'module_template': """# {module_name}

{description}

## Functions

{functions}

## Classes

{classes}

## Constants

{constants}

## Examples

{examples}
""",
            'function_template': """### {function_name}

{description}

**Parameters:**
{parameters}

**Returns:**
{return_type}

**Raises:**
{raises}

**Example:**
```python
{example}
```
""",
            'class_template': """### {class_name}

{description}

**Inheritance:** {inheritance}

**Methods:**
{methods}

**Attributes:**
{attributes}

**Example:**
```python
{example}
```
""",
            'readme_template': """# {project_name}

{description}

## Installation

```bash
{install_command}
```

## Quick Start

{quick_start}

## Features

{features}

## Documentation

{documentation_link}

## Contributing

{contributing}

## License

{license}
"""
        }

    def _analyze_project_structure(self) -> Dict[str, Any]:
        """Analyze the project structure."""
        structure = {
            'modules': [],
            'packages': [],
            'main_files': [],
            'config_files': [],
            'test_files': []
        }

        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', '.venv']]

            rel_path = Path(root).relative_to(self.project_root)

            # Check if it's a package (has __init__.py)
            if '__init__.py' in files:
                structure['packages'].append(str(rel_path))

            for file in files:
                file_path = Path(root) / file
                rel_file_path = file_path.relative_to(self.project_root)

                if file.endswith('.py'):
                    if any(pattern in file for pattern in ['test_', '_test']):
                        structure['test_files'].append(str(rel_file_path))
                    elif file in ['main.py', 'app.py', 'run.py', 'server.py']:
                        structure['main_files'].append(str(rel_file_path))
                    else:
                        structure['modules'].append(str(rel_file_path))
                elif file in ['requirements.txt', 'setup.py', 'pyproject.toml', 'environment.yml']:
                    structure['config_files'].append(str(rel_file_path))

        return structure

    def generate_documentation(self, output_dir: str = None) -> Dict[str, Any]:
        """Generate comprehensive documentation."""
        if output_dir is None:
            output_dir = self.project_root / 'docs'

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        print(f"Generating documentation in {output_path}")

        # Generate different types of documentation
        docs_generated = {}

        # Generate README
        readme_path = self._generate_readme(output_path)
        docs_generated['readme'] = str(readme_path)

        # Generate API documentation
        api_docs = self._generate_api_docs(output_path)
        docs_generated['api_docs'] = api_docs

        # Generate architecture documentation
        arch_docs = self._generate_architecture_docs(output_path)
        docs_generated['architecture'] = str(arch_docs)

        # Generate examples documentation
        examples_docs = self._generate_examples_docs(output_path)
        docs_generated['examples'] = str(examples_docs)

        # Generate contributing guide
        contributing_docs = self._generate_contributing_guide(output_path)
        docs_generated['contributing'] = str(contributing_docs)

        # Generate changelog
        changelog_docs = self._generate_changelog(output_path)
        docs_generated['changelog'] = str(changelog_docs)

        # Generate documentation index
        index_docs = self._generate_documentation_index(output_path, docs_generated)
        docs_generated['index'] = str(index_docs)

        return {
            'output_directory': str(output_path),
            'generated_files': docs_generated,
            'generation_timestamp': time.time()
        }

    def _generate_readme(self, output_path: Path) -> Path:
        """Generate README.md file."""
        readme_path = output_path / 'README.md'

        # Extract project information
        project_name = self.project_root.name
        description = self._extract_project_description()
        install_command = self._generate_install_command()
        quick_start = self._generate_quick_start()
        features = self._extract_project_features()

        # Generate README content
        readme_content = self.templates['readme_template'].format(
            project_name=project_name,
            description=description,
            install_command=install_command,
            quick_start=quick_start,
            features=features,
            documentation_link="[View Full Documentation](docs/index.md)",
            contributing="[Contributing Guide](contributing.md)",
            license="MIT License"
        )

        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)

        return readme_path

    def _generate_api_docs(self, output_path: Path) -> Dict[str, str]:
        """Generate API documentation."""
        api_dir = output_path / 'api'
        api_dir.mkdir(exist_ok=True)

        api_docs = {}

        # Generate documentation for each module
        for module_path in self.project_structure['modules']:
            if not self._should_ignore_file(module_path):
                module_doc = self._generate_module_documentation(module_path)
                if module_doc:
                    # Create file name from module path
                    file_name = module_path.replace('.py', '.md').replace('/', '_')
                    doc_path = api_dir / file_name

                    with open(doc_path, 'w', encoding='utf-8') as f:
                        f.write(module_doc)

                    api_docs[module_path] = str(doc_path)

        # Generate API index
        api_index = self._generate_api_index(api_docs)
        index_path = api_dir / 'index.md'
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(api_index)

        api_docs['index'] = str(index_path)

        return api_docs

    def _generate_module_documentation(self, module_path: str) -> Optional[str]:
        """Generate documentation for a specific module."""
        try:
            full_path = self.project_root / module_path
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            # Extract module information
            module_doc = self._extract_module_info(tree, module_path)
            if not module_doc:
                return None

            # Generate functions documentation
            functions_doc = self._generate_functions_documentation(tree, module_path)

            # Generate classes documentation
            classes_doc = self._generate_classes_documentation(tree, module_path)

            # Generate constants documentation
            constants_doc = self._generate_constants_documentation(tree, module_path)

            # Generate examples
            examples_doc = self._generate_module_examples(tree, module_path)

            # Combine all sections
            full_doc = self.templates['module_template'].format(
                module_name=module_doc['name'],
                description=module_doc['description'],
                functions=functions_doc,
                classes=classes_doc,
                constants=constants_doc,
                examples=examples_doc
            )

            return full_doc

        except Exception as e:
            print(f"Error generating documentation for {module_path}: {e}")
            return None

    def _extract_module_info(self, tree: ast.AST, module_path: str) -> Optional[Dict[str, Any]]:
        """Extract module information from AST."""
        docstring = ast.get_docstring(tree)
        if not docstring:
            return None

        module_name = Path(module_path).stem

        return {
            'name': module_name,
            'description': docstring,
            'file_path': module_path
        }

    def _generate_functions_documentation(self, tree: ast.AST, module_path: str) -> str:
        """Generate documentation for all functions in a module."""
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if self._should_include_function(node):
                    func_doc = self._extract_function_info(node)
                    if func_doc:
                        functions.append(self._generate_function_documentation(func_doc))

        return '\n\n'.join(functions)

    def _generate_classes_documentation(self, tree: ast.AST, module_path: str) -> str:
        """Generate documentation for all classes in a module."""
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_doc = self._extract_class_info(node)
                if class_doc:
                    classes.append(self._generate_class_documentation(class_doc))

        return '\n\n'.join(classes)

    def _generate_constants_documentation(self, tree: ast.AST, module_path: str) -> str:
        """Generate documentation for module constants."""
        constants = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        constant_doc = self._extract_constant_info(node, target.id)
                        if constant_doc:
                            constants.append(f"**{target.id}**: {constant_doc}")

        return '\n'.join(constants) if constants else "No constants defined."

    def _extract_function_info(self, node: ast.FunctionDef) -> Optional[Dict[str, Any]]:
        """Extract function information from AST node."""
        docstring = ast.get_docstring(node)
        if not docstring:
            docstring = "No description available."

        # Extract parameters
        parameters = []
        for arg in node.args.args:
            param_info = arg.arg
            if node.args.defaults:
                # Check if this parameter has a default value
                default_index = len(node.args.args) - len(node.args.defaults)
                if len(node.args.args) - len(node.args.defaults) <= list(node.args.args).index(arg) < len(node.args.args):
                    param_info += f" = (default value)"
            parameters.append(param_info)

        # Extract return type
        return_type = "Any"
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return_type = node.returns.id
            elif isinstance(node.returns, ast.Constant):
                return_type = str(node.returns.value)

        # Extract exceptions
        raises = self._extract_function_exceptions(node)

        return {
            'name': node.name,
            'description': docstring,
            'parameters': parameters,
            'return_type': return_type,
            'raises': raises,
            'line_number': node.lineno
        }

    def _extract_class_info(self, node: ast.ClassDef) -> Optional[Dict[str, Any]]:
        """Extract class information from AST node."""
        docstring = ast.get_docstring(node)
        if not docstring:
            docstring = "No description available."

        # Extract inheritance
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)

        # Extract methods
        methods = []
        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                if self._should_include_function(child):
                    method_info = self._extract_function_info(child)
                    if method_info:
                        methods.append(method_info['name'])

        # Extract attributes
        attributes = []
        for child in node.body:
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)

        return {
            'name': node.name,
            'description': docstring,
            'inheritance': ' -> '.join(base_classes) if base_classes else 'None',
            'methods': methods,
            'attributes': attributes,
            'line_number': node.lineno
        }

    def _extract_constant_info(self, node: ast.Assign, name: str) -> Optional[str]:
        """Extract constant information."""
        if isinstance(node.value, ast.Constant):
            return f"`{node.value.value}`"
        elif isinstance(node.value, ast.Str):  # Python < 3.8
            return f"`{node.value.s}`"
        elif isinstance(node.value, ast.Num):  # Python < 3.8
            return f"`{node.value.n}`"
        else:
            return "Complex value"

    def _extract_function_exceptions(self, node: ast.FunctionDef) -> List[str]:
        """Extract exceptions raised by function."""
        exceptions = []

        for child in ast.walk(node):
            if isinstance(child, ast.Raise):
                if child.exc:
                    if isinstance(child.exc, ast.Name):
                        exceptions.append(child.exc.id)
                    elif isinstance(child.exc, ast.Call) and isinstance(child.exc.func, ast.Name):
                        exceptions.append(child.exc.func.id)

        return list(set(exceptions)) if exceptions else ["None documented"]

    def _generate_function_documentation(self, func_info: Dict[str, Any]) -> str:
        """Generate documentation for a single function."""
        parameters_doc = '\n'.join([f"- {param}" for param in func_info['parameters']])
        raises_doc = '\n'.join([f"- {exc}" for exc in func_info['raises']])

        # Generate example if not in docstring
        example = self._generate_function_example(func_info['name'], func_info['parameters'])

        return self.templates['function_template'].format(
            function_name=func_info['name'],
            description=func_info['description'],
            parameters=parameters_doc,
            return_type=func_info['return_type'],
            raises=raises_doc,
            example=example
        )

    def _generate_class_documentation(self, class_info: Dict[str, Any]) -> str:
        """Generate documentation for a single class."""
        methods_doc = '\n'.join([f"- {method}" for method in class_info['methods']])
        attributes_doc = '\n'.join([f"- {attr}" for attr in class_info['attributes']])

        # Generate example
        example = self._generate_class_example(class_info['name'], class_info['methods'])

        return self.templates['class_template'].format(
            class_name=class_info['name'],
            description=class_info['description'],
            inheritance=class_info['inheritance'],
            methods=methods_doc,
            attributes=attributes_doc,
            example=example
        )

    def _generate_function_example(self, func_name: str, parameters: List[str]) -> str:
        """Generate example usage for a function."""
        # Simple example generation
        param_str = ', '.join([p.split('=')[0].strip() for p in parameters if p != 'self'])
        if param_str:
            return f"result = {func_name}({param_str})"
        else:
            return f"result = {func_name}()"

    def _generate_class_example(self, class_name: str, methods: List[str]) -> str:
        """Generate example usage for a class."""
        example = f"# Create instance\ninstance = {class_name}()\n\n"

        if methods:
            # Add example method call
            public_methods = [m for m in methods if not m.startswith('_') and m != '__init__']
            if public_methods:
                method = public_methods[0]
                example += f"# Call method\nresult = instance.{method}()\n"

        return example

    def _generate_module_examples(self, tree: ast.AST, module_path: str) -> str:
        """Generate examples for module usage."""
        # Look for if __name__ == "__main__" blocks for examples
        examples = []

        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                if (isinstance(node.test, ast.Compare) and
                    len(node.test.ops) == 1 and
                    isinstance(node.test.ops[0], ast.Eq) and
                    len(node.test.comparators) == 1 and
                    isinstance(node.test.comparators[0], ast.Constant) and
                    node.test.comparators[0].value == "__main__"):

                    # Extract example code
                    example_code = ast.unparse(node.body[0]) if hasattr(ast, 'unparse') else "# Example code"
                    examples.append(f"```python\n{example_code}\n```")

        return '\n\n'.join(examples) if examples else "No examples found."

    def _generate_architecture_docs(self, output_path: Path) -> Path:
        """Generate architecture documentation."""
        arch_path = output_path / 'architecture.md'

        # Extract architecture information
        packages = self.project_structure['packages']
        modules = self.project_structure['modules']
        main_files = self.project_structure['main_files']

        # Generate architecture content
        content = f"""# Architecture Documentation

## Project Structure

This project is organized into the following components:

### Packages
{self._format_package_list(packages)}

### Modules
{self._format_module_list(modules)}

### Main Entry Points
{self._format_main_files(main_files)}

## Design Patterns

The project follows these design principles:

- **Modularity**: Clear separation of concerns between modules
- **Maintainability**: Well-documented code with comprehensive tests
- **Scalability**: Designed to handle growth in data and users

## Component Interaction

```
[Diagram placeholder - consider using tools like PlantUML or Mermaid]
```

## Data Flow

1. Input processing
2. Business logic execution
3. Output generation

## Technology Stack

- **Language**: Python
- **Framework**: [Add framework info]
- **Database**: [Add database info]
- **Testing**: [Add testing framework info]

## Deployment Architecture

[Add deployment architecture information]
"""

        with open(arch_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return arch_path

    def _generate_examples_docs(self, output_path: Path) -> Path:
        """Generate examples documentation."""
        examples_path = output_path / 'examples.md'

        content = """# Examples

This section provides practical examples of how to use the project.

## Basic Usage

[Add basic usage examples]

## Advanced Usage

[Add advanced usage examples]

## Common Patterns

[Add common usage patterns]

## Troubleshooting

[Add troubleshooting examples]
"""

        with open(examples_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return examples_path

    def _generate_contributing_guide(self, output_path: Path) -> Path:
        """Generate contributing guide."""
        contributing_path = output_path / 'contributing.md'

        content = """# Contributing

We welcome contributions! This guide will help you get started.

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make your changes
5. Submit a pull request

## Development Setup

```bash
# Clone the repository
git clone <your-fork-url>

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_module.py
```

## Code Style

This project follows standard Python style guidelines:

- Use `black` for code formatting
- Follow PEP 8 guidelines
- Write comprehensive docstrings
- Include type hints where appropriate

## Submitting Changes

1. Ensure all tests pass
2. Update documentation if needed
3. Add tests for new functionality
4. Submit a pull request with a clear description

## Reporting Issues

Please use the GitHub issue tracker to report bugs or request features.
"""

        with open(contributing_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return contributing_path

    def _generate_changelog(self, output_path: Path) -> Path:
        """Generate changelog."""
        changelog_path = output_path / 'changelog.md'

        content = f"""# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Initial documentation generation
- Code quality analysis tools

### Changed
- Improved project structure

### Deprecated

### Removed

### Fixed

### Security

## [1.0.0] - {datetime.now().strftime('%Y-%m-%d')}

### Added
- Initial release
- Core functionality
- Basic documentation

## Development Guidelines

- Version numbers follow Semantic Versioning
- All changes should be documented
- Breaking changes should be clearly marked
"""

        with open(changelog_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return changelog_path

    def _generate_documentation_index(self, output_path: Path, docs_generated: Dict[str, str]) -> Path:
        """Generate main documentation index."""
        index_path = output_path / 'index.md'

        content = f"""# Documentation

Welcome to the {self.project_root.name} documentation!

## Table of Contents

- [Getting Started](#getting-started)
  - [Installation](installation.md)
  - [Quick Start](quick_start.md)
- [API Reference](api/index.md)
- [Architecture](architecture.md)
- [Examples](examples.md)
- [Contributing](contributing.md)
- [Changelog](changelog.md)

## Getting Started

### Installation

See the [installation guide](installation.md) for detailed setup instructions.

### Quick Start

Check out our [quick start guide](quick_start.md) to get up and running quickly.

## API Reference

Comprehensive API documentation is available in the [API reference section](api/index.md).

## Architecture

Learn about the project's [architecture and design](architecture.md).

## Examples

Browse our [examples](examples.md) to see the project in action.

## Contributing

Interested in contributing? See our [contributing guide](contributing.md).

---

*Documentation generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return index_path

    def _generate_api_index(self, api_docs: Dict[str, str]) -> str:
        """Generate API documentation index."""
        content = "# API Reference\n\n"

        for module_path, doc_path in api_docs.items():
            if module_path != 'index':
                module_name = Path(module_path).stem
                relative_path = Path(doc_path).name
                content += f"- [{module_name}]({relative_path})\n"

        return content

    def _should_ignore_file(self, file_path: str) -> bool:
        """Check if file should be ignored."""
        for pattern in self.documentation_config['ignore_patterns']:
            if pattern.replace('*', '') in file_path:
                return True
        return False

    def _should_include_function(self, node: ast.FunctionDef) -> bool:
        """Check if function should be included in documentation."""
        # Skip private functions unless explicitly requested
        if not self.documentation_config['include_private'] and node.name.startswith('_'):
            return False

        # Skip magic methods unless explicitly requested
        if not self.documentation_config['include_magic_methods'] and (
            node.name.startswith('__') and node.name.endswith('__')
        ):
            return False

        return True

    def _extract_project_description(self) -> str:
        """Extract project description from various sources."""
        # Try to get description from setup.py or pyproject.toml
        setup_files = ['setup.py', 'pyproject.toml', 'README.md']

        for setup_file in setup_files:
            file_path = self.project_root / setup_file
            if file_path.exists():
                if setup_file == 'README.md':
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        # Look for first non-empty, non-header line
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                return line
                else:
                    # Parse setup.py or pyproject.toml for description
                    # This is simplified - real implementation would parse these files
                    return f"Documentation for {self.project_root.name}"

        return f"Documentation for {self.project_root.name}"

    def _generate_install_command(self) -> str:
        """Generate installation command."""
        if (self.project_root / 'requirements.txt').exists():
            return "pip install -r requirements.txt"
        elif (self.project_root / 'setup.py').exists():
            return "pip install ."
        elif (self.project_root / 'pyproject.toml').exists():
            return "pip install ."
        else:
            return "pip install -e ."

    def _generate_quick_start(self) -> str:
        """Generate quick start guide."""
        # Look for main files to determine entry point
        main_files = self.project_structure['main_files']

        if main_files:
            main_file = main_files[0]
            module_name = Path(main_file).stem
            return f"""
```python
# Import the main module
import {module_name}

# Basic usage
result = {module_name}.main_function()
print(result)
```
"""
        else:
            return """
```python
# Import the module
import module_name

# Start using the project
# Add your code here
```
"""

    def _extract_project_features(self) -> str:
        """Extract project features."""
        # This is a simplified implementation
        # Real implementation would analyze code for features
        features = [
            "Comprehensive code analysis",
            "Performance profiling",
            "Documentation generation",
            "Quality metrics"
        ]

        return '\n'.join([f"- {feature}" for feature in features])

    def _format_package_list(self, packages: List[str]) -> str:
        """Format package list for documentation."""
        if not packages:
            return "No packages found."

        return '\n'.join([f"- `{pkg}`" for pkg in packages])

    def _format_module_list(self, modules: List[str]) -> str:
        """Format module list for documentation."""
        if not modules:
            return "No modules found."

        return '\n'.join([f"- `{Path(module).stem}`" for module in modules])

    def _format_main_files(self, main_files: List[str]) -> str:
        """Format main files list for documentation."""
        if not main_files:
            return "No main entry points found."

        return '\n'.join([f"- `{file}`" for file in main_files])


def main():
    """Main function for standalone usage."""
    project_root = '/home/activeloguser/DMLogn8n'
    generator = DocumentationGenerator(project_root)

    print("Starting documentation generation...")
    results = generator.generate_documentation()

    print(f"Documentation generated successfully!")
    print(f"Output directory: {results['output_directory']}")
    print(f"Generated files: {len(results['generated_files'])}")

    for doc_type, file_path in results['generated_files'].items():
        print(f"  {doc_type}: {file_path}")


if __name__ == "__main__":
    main()