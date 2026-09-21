#!/usr/bin/env python3
"""
DMLogn8n Documentation Generator - Automated Documentation Generation System
Comprehensive documentation generation with AI-powered content creation and multi-format output
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import yaml
import markdown
from jinja2 import Environment, FileSystemLoader, Template
import aiofiles
import aiohttp
from bs4 import BeautifulSoup
import git

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('documentation_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DocType(Enum):
    API_REFERENCE = "api_reference"
    USER_GUIDE = "user_guide"
    DEVELOPER_GUIDE = "developer_guide"
    TUTORIAL = "tutorial"
    QUICK_START = "quick_start"
    CHANGELOG = "changelog"
    FAQ = "faq"
    ARCHITECTURE = "architecture"
    DEPLOYMENT = "deployment"
    CONTRIBUTING = "contributing"

class OutputFormat(Enum):
    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"
    PDF_LATEX = "pdf_latex"
    EPUB = "epub"
    JSON = "json"
    YAML = "yaml"

@dataclass
class DocumentationSection:
    id: str
    title: str
    content: str
    subsections: List['DocumentationSection']
    metadata: Dict[str, Any]
    order: int

@dataclass
class DocumentationProject:
    id: str
    name: str
    description: str
    version: str
    sections: List[DocumentationSection]
    metadata: Dict[str, Any]
    output_formats: List[OutputFormat]
    created_at: datetime
    updated_at: datetime

class CodeAnalyzer:
    """Analyze source code to extract documentation information"""

    def __init__(self, source_path: str):
        self.source_path = Path(source_path)
        self.supported_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.go', '.rs', '.php'}

    async def analyze_project(self) -> Dict[str, Any]:
        """Analyze entire project structure and extract documentation info"""
        project_info = {
            "name": self.source_path.name,
            "structure": await self._analyze_structure(),
            "classes": await self._extract_classes(),
            "functions": await self._extract_functions(),
            "endpoints": await self._extract_api_endpoints(),
            "configurations": await self._extract_configurations(),
            "dependencies": await self._extract_dependencies(),
            "examples": await self._extract_examples()
        }

        return project_info

    async def _analyze_structure(self) -> Dict[str, Any]:
        """Analyze project directory structure"""
        structure = {"directories": [], "files": []}

        for item in self.source_path.rglob("*"):
            if item.is_dir():
                structure["directories"].append(str(item.relative_to(self.source_path)))
            elif item.is_file() and item.suffix in self.supported_extensions:
                structure["files"].append({
                    "path": str(item.relative_to(self.source_path)),
                    "size": item.stat().st_size,
                    "type": item.suffix[1:]  # Remove the dot
                })

        return structure

    async def _extract_classes(self) -> List[Dict[str, Any]]:
        """Extract class information from source code"""
        classes = []

        for file_path in self.source_path.rglob("*.py"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract class definitions
                class_pattern = r'class\s+(\w+)(?:\(([^)]+)\))?\s*:'
                matches = re.finditer(class_pattern, content)

                for match in matches:
                    class_name = match.group(1)
                    parent_class = match.group(2)
                    class_info = {
                        "name": class_name,
                        "file": str(file_path.relative_to(self.source_path)),
                        "parent": parent_class,
                        "methods": await self._extract_class_methods(content, class_name),
                        "docstring": self._extract_class_docstring(content, class_name),
                        "properties": await self._extract_class_properties(content, class_name)
                    }
                    classes.append(class_info)

            except Exception as e:
                logger.warning(f"Error analyzing {file_path}: {e}")

        return classes

    async def _extract_functions(self) -> List[Dict[str, Any]]:
        """Extract function information from source code"""
        functions = []

        for file_path in self.source_path.rglob("*.py"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract function definitions
                func_pattern = r'(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*([^\s:]+))?\s*:'
                matches = re.finditer(func_pattern, content)

                for match in matches:
                    func_name = match.group(1)
                    params = match.group(2)
                    return_type = match.group(3)
                    func_info = {
                        "name": func_name,
                        "file": str(file_path.relative_to(self.source_path)),
                        "parameters": self._parse_parameters(params),
                        "return_type": return_type,
                        "docstring": self._extract_function_docstring(content, func_name),
                        "decorators": self._extract_decorators(content, func_name)
                    }
                    functions.append(func_info)

            except Exception as e:
                logger.warning(f"Error analyzing functions in {file_path}: {e}")

        return functions

    async def _extract_api_endpoints(self) -> List[Dict[str, Any]]:
        """Extract API endpoint information"""
        endpoints = []

        for file_path in self.source_path.rglob("*.py"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Look for FastAPI endpoints
                if '@app.' in content or '@router.' in content:
                    endpoint_pattern = r'@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]'
                    matches = re.finditer(endpoint_pattern, content)

                    for match in matches:
                        method = match.group(1).upper()
                        path = match.group(2)
                        endpoint_info = {
                            "method": method,
                            "path": path,
                            "file": str(file_path.relative_to(self.source_path)),
                            "parameters": await self._extract_endpoint_parameters(content, path),
                            "responses": await self._extract_endpoint_responses(content, path),
                            "description": self._extract_endpoint_description(content, path)
                        }
                        endpoints.append(endpoint_info)

            except Exception as e:
                logger.warning(f"Error analyzing API endpoints in {file_path}: {e}")

        return endpoints

    async def _extract_class_methods(self, content: str, class_name: str) -> List[Dict[str, Any]]:
        """Extract methods from a class"""
        methods = []
        # Find class content
        class_pattern = rf'class\s+{class_name}[^:]*:.*?(?=\n\nclass|\Z)'
        class_match = re.search(class_pattern, content, re.DOTALL)

        if class_match:
            class_content = class_match.group(0)
            method_pattern = r'(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*([^\s:]+))?\s*:'

            for match in re.finditer(method_pattern, class_content):
                method_info = {
                    "name": match.group(1),
                    "parameters": self._parse_parameters(match.group(2)),
                    "return_type": match.group(3),
                    "docstring": self._extract_function_docstring(class_content, match.group(1))
                }
                methods.append(method_info)

        return methods

    async def _extract_class_properties(self, content: str, class_name: str) -> List[str]:
        """Extract properties from a class"""
        properties = []
        # This is a simplified implementation
        # In practice, you'd want more sophisticated parsing
        class_pattern = rf'class\s+{class_name}[^:]*:.*?(?=\n\nclass|\Z)'
        class_match = re.search(class_pattern, content, re.DOTALL)

        if class_match:
            class_content = class_match.group(0)
            # Look for property definitions
            property_pattern = r'@property\s+def\s+(\w+)'
            properties.extend(re.findall(property_pattern, class_content))

        return properties

    def _extract_class_docstring(self, content: str, class_name: str) -> str:
        """Extract docstring for a class"""
        pattern = rf'class\s+{class_name}[^:]*:\s*("""|\'\')(.*?)\1'
        match = re.search(pattern, content, re.DOTALL)
        return match.group(2).strip() if match else ""

    def _extract_function_docstring(self, content: str, func_name: str) -> str:
        """Extract docstring for a function"""
        pattern = rf'(?:async\s+)?def\s+{func_name}[^:]*:\s*("""|\'\')(.*?)\1'
        match = re.search(pattern, content, re.DOTALL)
        return match.group(2).strip() if match else ""

    def _extract_decorators(self, content: str, func_name: str) -> List[str]:
        """Extract decorators for a function"""
        # Find function definition and look backwards for decorators
        func_pattern = rf'(?:async\s+)?def\s+{func_name}'
        func_match = re.search(func_pattern, content)

        if func_match:
            # Get text before function definition
            before_func = content[:func_match.start()]
            lines = before_func.split('\n')

            decorators = []
            for line in reversed(lines[-5:]):  # Check last 5 lines before function
                if line.strip().startswith('@'):
                    decorators.append(line.strip())
                else:
                    break

            return list(reversed(decorators))

        return []

    def _parse_parameters(self, params_str: str) -> List[Dict[str, str]]:
        """Parse function parameters"""
        if not params_str.strip():
            return []

        params = []
        for param in params_str.split(','):
            param = param.strip()
            if ':' in param:
                name, type_hint = param.split(':', 1)
                params.append({"name": name.strip(), "type": type_hint.strip()})
            else:
                params.append({"name": param, "type": "Any"})

        return params

    async def _extract_endpoint_parameters(self, content: str, path: str) -> List[Dict[str, Any]]:
        """Extract parameters for API endpoints"""
        # This would need more sophisticated parsing in practice
        return []

    async def _extract_endpoint_responses(self, content: str, path: str) -> List[Dict[str, Any]]:
        """Extract response schemas for API endpoints"""
        # This would need more sophisticated parsing in practice
        return []

    def _extract_endpoint_description(self, content: str, path: str) -> str:
        """Extract description for API endpoint"""
        # Look for docstring near the endpoint definition
        return ""

    async def _extract_configurations(self) -> List[Dict[str, Any]]:
        """Extract configuration files and their contents"""
        configs = []
        config_files = ['config.yml', 'config.yaml', 'settings.py', '.env', 'docker-compose.yml']

        for config_file in config_files:
            config_path = self.source_path / config_file
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    configs.append({
                        "file": config_file,
                        "content": content,
                        "type": config_path.suffix[1:] if config_path.suffix else "env"
                    })
                except Exception as e:
                    logger.warning(f"Error reading config {config_file}: {e}")

        return configs

    async def _extract_dependencies(self) -> List[Dict[str, str]]:
        """Extract project dependencies"""
        dependencies = []

        # Check requirements.txt
        req_file = self.source_path / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '==' in line:
                                name, version = line.split('==', 1)
                                dependencies.append({"name": name, "version": version})
                            else:
                                dependencies.append({"name": line, "version": "latest"})
            except Exception as e:
                logger.warning(f"Error reading requirements.txt: {e}")

        # Check package.json
        package_file = self.source_path / "package.json"
        if package_file.exists():
            try:
                with open(package_file, 'r') as f:
                    package_data = json.load(f)
                    deps = package_data.get("dependencies", {})
                    for name, version in deps.items():
                        dependencies.append({"name": name, "version": version})
            except Exception as e:
                logger.warning(f"Error reading package.json: {e}")

        return dependencies

    async def _extract_examples(self) -> List[Dict[str, Any]]:
        """Extract code examples from the project"""
        examples = []
        example_dirs = ['examples', 'samples', 'docs/examples']

        for example_dir in example_dirs:
            example_path = self.source_path / example_dir
            if example_path.exists() and example_path.is_dir():
                for example_file in example_path.rglob("*.py"):
                    try:
                        with open(example_file, 'r', encoding='utf-8') as f:
                            content = f.read()

                        examples.append({
                            "file": str(example_file.relative_to(self.source_path)),
                            "content": content,
                            "description": self._extract_example_description(content)
                        })
                    except Exception as e:
                        logger.warning(f"Error reading example {example_file}: {e}")

        return examples

    def _extract_example_description(self, content: str) -> str:
        """Extract description from example code"""
        # Look for docstring at the beginning of the file
        docstring_pattern = r'^\s*(?:\'\'\'|\"\"\")(.*?)(?:\'\'\'|\"\"\")'
        match = re.search(docstring_pattern, content, re.DOTALL)
        return match.group(1).strip() if match else ""

class ContentGenerator:
    """AI-powered content generation for documentation"""

    def __init__(self):
        self.templates = self._load_templates()
        self.generation_rules = self._load_generation_rules()

    def _load_templates(self) -> Dict[str, Template]:
        """Load documentation templates"""
        template_dir = Path("templates/documentation")
        templates = {}

        if template_dir.exists():
            env = Environment(loader=FileSystemLoader(str(template_dir)))
            for template_file in template_dir.glob("*.j2"):
                template_name = template_file.stem
                templates[template_name] = env.get_template(template_file.name)

        return templates

    def _load_generation_rules(self) -> Dict[str, Any]:
        """Load content generation rules"""
        return {
            "api_reference": {
                "include_examples": True,
                "include_type_hints": True,
                "group_by_module": True,
                "sort_alphabetically": True
            },
            "user_guide": {
                "include_toc": True,
                "include_examples": True,
                "include_troubleshooting": True,
                "language_level": "beginner"
            },
            "developer_guide": {
                "include_architecture": True,
                "include_code_examples": True,
                "include_testing_guide": True,
                "include_contribution_guide": True
            }
        }

    async def generate_api_reference(self, project_info: Dict[str, Any]) -> DocumentationSection:
        """Generate API reference documentation"""
        content = "# API Reference\n\n"

        # Group functions by file/module
        functions_by_file = {}
        for func in project_info["functions"]:
            file_path = func["file"]
            if file_path not in functions_by_file:
                functions_by_file[file_path] = []
            functions_by_file[file_path].append(func)

        # Generate documentation for each module
        for file_path, functions in functions_by_file.items():
            content += f"## {file_path}\n\n"

            for func in functions:
                content += f"### {func['name']}\n\n"

                if func["docstring"]:
                    content += f"{func['docstring']}\n\n"

                content += "```python\n"
                content += f"def {func['name']}("
                content += ", ".join([f"{p['name']}: {p['type']}" for p in func['parameters']])
                content += ")"
                if func["return_type"]:
                    content += f" -> {func['return_type']}"
                content += "\n```\n\n"

                if func["parameters"]:
                    content += "**Parameters:**\n\n"
                    for param in func["parameters"]:
                        content += f"- `{param['name']}` ({param['type']})\n"
                    content += "\n"

                if func["return_type"]:
                    content += f"**Returns:** `{func['return_type']}`\n\n"

                if func["decorators"]:
                    content += "**Decorators:**\n\n"
                    for decorator in func["decorators"]:
                        content += f"- `{decorator}`\n"
                    content += "\n"

                content += "---\n\n"

        return DocumentationSection(
            id="api_reference",
            title="API Reference",
            content=content,
            subsections=[],
            metadata={"type": "api_reference", "generated_at": datetime.utcnow()},
            order=1
        )

    async def generate_user_guide(self, project_info: Dict[str, Any]) -> DocumentationSection:
        """Generate user guide documentation"""
        content = """# User Guide

## Getting Started

Welcome to the DMLogn8n platform! This guide will help you get started with using our multi-agent system.

### Prerequisites

Before you begin, make sure you have:

- Python 3.8 or higher installed
- Basic understanding of programming concepts
- Access to the DMLogn8n platform

### Installation

```bash
pip install dmlogn8n
```

### Quick Start

Here's a simple example to get you started:

```python
from dmlogn8n import Agent, Workflow

# Create your first agent
agent = Agent("my-agent")

# Define a simple task
async def my_task(input_data):
    return {"message": "Hello, World!"}

# Add the task to your agent
agent.add_task(my_task)

# Run the agent
result = await agent.run({"input": "test"})
print(result)
```

## Core Concepts

### Agents
Agents are autonomous programs that can perform tasks and interact with other agents.

### Workflows
Workflows define how agents collaborate and process data.

### Nodes
Nodes are individual processing units within workflows.

## Common Use Cases

### Data Processing
Process and transform data using agent workflows.

### API Integration
Connect to external APIs and services.

### Automation
Automate repetitive tasks and processes.

## Troubleshooting

### Common Issues

1. **Connection Errors**: Check your network configuration
2. **Authentication Issues**: Verify your API keys and credentials
3. **Performance Issues**: Monitor resource usage and optimize workflows

### Getting Help

- Check the [FAQ](#faq)
- Visit our [community forum](https://community.dmlogn8n.com)
- [Contact support](mailto:support@dmlogn8n.com)

## FAQ

**Q: How do I scale my workflows?**
A: Use our clustering features to distribute workloads across multiple instances.

**Q: Can I integrate with external services?**
A: Yes, we support integration with hundreds of popular services and APIs.

**Q: Is there a limit on the number of agents?**
A: Limits depend on your subscription plan. Contact us for enterprise requirements.
"""

        return DocumentationSection(
            id="user_guide",
            title="User Guide",
            content=content,
            subsections=[],
            metadata={"type": "user_guide", "generated_at": datetime.utcnow()},
            order=2
        )

    async def generate_architecture_doc(self, project_info: Dict[str, Any]) -> DocumentationSection:
        """Generate architecture documentation"""
        content = """# Architecture Overview

## System Architecture

The DMLogn8n platform is built on a microservices architecture with the following key components:

### Core Components

1. **Agent Engine**: Manages agent lifecycle and execution
2. **Workflow Orchestrator**: Coordinates agent interactions
3. **Message Broker**: Handles inter-service communication
4. **Storage Layer**: Persistent data storage
5. **API Gateway**: External interface and authentication

### Data Flow

```
User Request → API Gateway → Workflow Orchestrator → Agent Engine → Storage
```

## Technology Stack

- **Backend**: Python 3.8+, FastAPI, SQLAlchemy
- **Database**: PostgreSQL, Redis
- **Message Queue**: RabbitMQ, Apache Kafka
- **Containerization**: Docker, Kubernetes
- **Monitoring**: Prometheus, Grafana

## Scalability

### Horizontal Scaling
- Stateless services allow easy horizontal scaling
- Load balancers distribute traffic across instances
- Auto-scaling based on resource usage

### Performance Optimization
- Caching layers for frequently accessed data
- Connection pooling for database operations
- Asynchronous processing for I/O operations

## Security

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- API rate limiting

### Data Protection
- Encryption at rest and in transit
- Regular security audits
- Compliance with data protection regulations

## Deployment

### Production Deployment
- Containerized deployment with Docker
- Orchestration with Kubernetes
- CI/CD pipeline for automated deployments

### Development Environment
- Local development with Docker Compose
- Hot-reload for rapid development
- Integrated testing framework
"""

        return DocumentationSection(
            id="architecture",
            title="Architecture",
            content=content,
            subsections=[],
            metadata={"type": "architecture", "generated_at": datetime.utcnow()},
            order=3
        )

class DocumentRenderer:
    """Render documentation to various output formats"""

    def __init__(self):
        self.output_dir = Path("generated_docs")
        self.output_dir.mkdir(exist_ok=True)

    async def render_html(self, project: DocumentationProject) -> str:
        """Render documentation as HTML"""
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project.name} Documentation</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            border-bottom: 2px solid #e1e5e9;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .toc {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .toc ul {{
            list-style: none;
            padding-left: 0;
        }}
        .toc li {{
            margin: 5px 0;
        }}
        .toc a {{
            color: #0066cc;
            text-decoration: none;
        }}
        .toc a:hover {{
            text-decoration: underline;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .code {{
            background: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            font-family: 'Monaco', 'Menlo', monospace;
        }}
        .api-endpoint {{
            background: #e8f4fd;
            border-left: 4px solid #0066cc;
            padding: 15px;
            margin: 10px 0;
        }}
        .method-get {{ border-color: #28a745; }}
        .method-post {{ border-color: #007bff; }}
        .method-put {{ border-color: #ffc107; }}
        .method-delete {{ border-color: #dc3545; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{project.name}</h1>
        <p>{project.description}</p>
        <p><strong>Version:</strong> {project.version}</p>
        <p><strong>Last Updated:</strong> {project.updated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="toc">
        <h2>Table of Contents</h2>
        <ul>
            {self._generate_toc_html(project.sections)}
        </ul>
    </div>

    <div class="content">
        {self._render_sections_html(project.sections)}
    </div>
</body>
</html>
        """

        output_path = self.output_dir / f"{project.id}.html"
        async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
            await f.write(html_content)

        return str(output_path)

    def _generate_toc_html(self, sections: List[DocumentationSection]) -> str:
        """Generate table of contents HTML"""
        toc_html = ""
        for section in sorted(sections, key=lambda x: x.order):
            toc_html += f'<li><a href="#{section.id}">{section.title}</a></li>\n'
            if section.subsections:
                toc_html += '<ul>\n'
                for subsection in sorted(section.subsections, key=lambda x: x.order):
                    toc_html += f'<li><a href="#{subsection.id}">{subsection.title}</a></li>\n'
                toc_html += '</ul>\n'
        return toc_html

    def _render_sections_html(self, sections: List[DocumentationSection]) -> str:
        """Render sections as HTML"""
        content = ""
        for section in sorted(sections, key=lambda x: x.order):
            content += f'<div class="section" id="{section.id}">\n'
            content += f'<h1>{section.title}</h1>\n'

            # Convert markdown to HTML
            html_content = markdown.markdown(section.content, extensions=['codehilite', 'tables'])
            content += html_content + '\n'

            if section.subsections:
                for subsection in sorted(section.subsections, key=lambda x: x.order):
                    content += f'<div class="subsection" id="{subsection.id}">\n'
                    content += f'<h2>{subsection.title}</h2>\n'
                    content += markdown.markdown(subsection.content, extensions=['codehilite', 'tables'])
                    content += '</div>\n'

            content += '</div>\n'

        return content

    async def render_markdown(self, project: DocumentationProject) -> str:
        """Render documentation as Markdown"""
        markdown_content = f"""# {project.name}

{project.description}

**Version:** {project.version}
**Last Updated:** {project.updated_at.strftime('%Y-%m-%d %H:%M:%S')}

---

## Table of Contents

{self._generate_toc_markdown(project.sections)}

---

{self._render_sections_markdown(project.sections)}
"""

        output_path = self.output_dir / f"{project.id}.md"
        async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
            await f.write(markdown_content)

        return str(output_path)

    def _generate_toc_markdown(self, sections: List[DocumentationSection]) -> str:
        """Generate table of contents in Markdown"""
        toc = ""
        for section in sorted(sections, key=lambda x: x.order):
            toc += f"- [{section.title}](#{section.id.lower().replace(' ', '-')})\n"
            if section.subsections:
                for subsection in sorted(section.subsections, key=lambda x: x.order):
                    toc += f"  - [{subsection.title}](#{subsection.id.lower().replace(' ', '-')})\n"
        return toc

    def _render_sections_markdown(self, sections: List[DocumentationSection]) -> str:
        """Render sections as Markdown"""
        content = ""
        for section in sorted(sections, key=lambda x: x.order):
            content += f"# {section.title}\n\n"
            content += section.content + "\n\n"

            if section.subsections:
                for subsection in sorted(section.subsections, key=lambda x: x.order):
                    content += f"## {subsection.title}\n\n"
                    content += subsection.content + "\n\n"

        return content

    async def render_pdf(self, project: DocumentationProject) -> str:
        """Render documentation as PDF using LaTeX"""
        # Convert to LaTeX
        latex_content = self._generate_latex(project)

        # Write temporary LaTeX file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
            f.write(latex_content)
            tex_path = f.name

        try:
            # Compile LaTeX to PDF
            output_dir = str(self.output_dir)
            subprocess.run([
                'pdflatex',
                '-output-directory', output_dir,
                tex_path
            ], check=True, capture_output=True)

            pdf_path = self.output_dir / f"{project.id}.pdf"
            return str(pdf_path)

        except subprocess.CalledProcessError as e:
            logger.error(f"LaTeX compilation failed: {e}")
            # Fallback to markdown
            return await self.render_markdown(project)

        finally:
            # Clean up temporary files
            for ext in ['.tex', '.aux', '.log', '.out']:
                temp_file = Path(tex_path).with_suffix(ext)
                if temp_file.exists():
                    temp_file.unlink()

    def _generate_latex(self, project: DocumentationProject) -> str:
        """Generate LaTeX content for PDF rendering"""
        latex = r"""\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{hyperref}
\usepackage{listings}
\usepackage{xcolor}
\usepackage{geometry}

\geometry{a4paper, margin=1in}

\definecolor{codegreen}{rgb}{0,0.6,0}
\definecolor{codegray}{rgb}{0.5,0.5,0.5}
\definecolor{codepurple}{rgb}{0.58,0,0.82}
\definecolor{backcolour}{rgb}{0.95,0.95,0.92}

\lstdefinestyle{mystyle}{
    backgroundcolor=\color{backcolour},
    commentstyle=\color{codegreen},
    keywordstyle=\color{magenta},
    numberstyle=\tiny\color{codegray},
    stringstyle=\color{codepurple},
    basicstyle=\ttfamily\footnotesize,
    breakatwhitespace=false,
    breaklines=true,
    captionpos=b,
    keepspaces=true,
    numbers=left,
    numbersep=5pt,
    showspaces=false,
    showstringspaces=false,
    showtabs=false,
    tabsize=2
}

\lstset{style=mystyle}

\title{""" + project.name + r"""}
\author{DMLogn8n Documentation}
\date{""" + project.updated_at.strftime('%Y-%m-%d') + r"""}

\begin{document}

\maketitle

\section*{Version}
""" + project.version + r"""

\section*{Description}
""" + project.description + r"""

\tableofcontents
\newpage

"""

        # Add sections
        for section in sorted(project.sections, key=lambda x: x.order):
            latex += f"\\section{{{section.title}}}\n\n"

            # Convert markdown to LaTeX (simplified)
            section_latex = self._markdown_to_latex(section.content)
            latex += section_latex + "\n\n"

        latex += r"\end{document}"
        return latex

    def _markdown_to_latex(self, markdown_text: str) -> str:
        """Convert Markdown text to LaTeX (simplified implementation)"""
        # This is a simplified conversion
        # In practice, you'd want to use pandoc or a more comprehensive converter
        latex = markdown_text

        # Convert headers
        latex = re.sub(r'^### (.*)$', r'\\subsection{\1}', latex, flags=re.MULTILINE)
        latex = re.sub(r'^## (.*)$', r'\\section{\1}', latex, flags=re.MULTILINE)

        # Convert code blocks
        latex = re.sub(r'```(\w+)?\n(.*?)```', r'\\begin{lstlisting}[language=\1]\n\2\\end{lstlisting}',
                      latex, flags=re.DOTALL)

        # Convert inline code
        latex = re.sub(r'`([^`]+)`', r'\\texttt{\1}', latex)

        # Convert bold and italic
        latex = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', latex)
        latex = re.sub(r'\*(.*?)\*', r'\\textit{\1}', latex)

        return latex

class DocumentationGenerator:
    """Main documentation generation system"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.analyzer = CodeAnalyzer(self.config.get("source_path", "."))
        self.content_generator = ContentGenerator()
        self.renderer = DocumentRenderer()
        self.projects = {}

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            "source_path": ".",
            "output_formats": ["html", "markdown", "pdf"],
            "include_api_reference": True,
            "include_user_guide": True,
            "include_architecture": True,
            "template_dir": "templates/documentation",
            "output_dir": "generated_docs"
        }

        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)

        return default_config

    async def generate_documentation(self, project_name: str, doc_types: List[DocType] = None) -> str:
        """Generate complete documentation for a project"""
        if doc_types is None:
            doc_types = [DocType.API_REFERENCE, DocType.USER_GUIDE, DocType.ARCHITECTURE]

        logger.info(f"Starting documentation generation for {project_name}")

        # Analyze project
        project_info = await self.analyzer.analyze_project()
        logger.info(f"Analyzed project: {len(project_info['functions'])} functions, {len(project_info['classes'])} classes")

        # Generate documentation sections
        sections = []

        if DocType.API_REFERENCE in doc_types:
            api_section = await self.content_generator.generate_api_reference(project_info)
            sections.append(api_section)

        if DocType.USER_GUIDE in doc_types:
            user_guide = await self.content_generator.generate_user_guide(project_info)
            sections.append(user_guide)

        if DocType.ARCHITECTURE in doc_types:
            arch_doc = await self.content_generator.generate_architecture_doc(project_info)
            sections.append(arch_doc)

        # Create documentation project
        project_id = str(uuid.uuid4())
        project = DocumentationProject(
            id=project_id,
            name=project_name,
            description=project_info.get("description", f"Documentation for {project_name}"),
            version=self._extract_version(),
            sections=sections,
            metadata={
                "source_path": self.config["source_path"],
                "generation_time": datetime.utcnow().isoformat(),
                "doc_types": [dt.value for dt in doc_types]
            },
            output_formats=[OutputFormat(fmt) for fmt in self.config["output_formats"]],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.projects[project_id] = project

        # Render documentation in requested formats
        output_files = []
        for output_format in project.output_formats:
            try:
                if output_format == OutputFormat.HTML:
                    output_file = await self.renderer.render_html(project)
                elif output_format == OutputFormat.MARKDOWN:
                    output_file = await self.renderer.render_markdown(project)
                elif output_format == OutputFormat.PDF:
                    output_file = await self.renderer.render_pdf(project)
                else:
                    logger.warning(f"Unsupported output format: {output_format}")
                    continue

                output_files.append(output_file)
                logger.info(f"Generated {output_format.value} documentation: {output_file}")

            except Exception as e:
                logger.error(f"Error generating {output_format.value} documentation: {e}")

        logger.info(f"Documentation generation completed for {project_name}")
        return output_files[0] if output_files else ""

    def _extract_version(self) -> str:
        """Extract version from project"""
        # Try to get version from git
        try:
            repo = git.Repo(self.config["source_path"])
            return repo.head.commit.hexsha[:8]
        except:
            pass

        # Try to get version from package.json
        package_file = Path(self.config["source_path"]) / "package.json"
        if package_file.exists():
            with open(package_file, 'r') as f:
                package_data = json.load(f)
                return package_data.get("version", "1.0.0")

        # Default version
        return "1.0.0"

    async def update_documentation(self, project_id: str) -> str:
        """Update existing documentation"""
        if project_id not in self.projects:
            raise ValueError(f"Project {project_id} not found")

        project = self.projects[project_id]
        return await self.generate_documentation(project.name)

    async def schedule_auto_generation(self, interval_minutes: int = 60):
        """Schedule automatic documentation generation"""
        while True:
            try:
                logger.info("Starting scheduled documentation generation")
                await self.generate_documentation("DMLogn8n")
                logger.info("Scheduled documentation generation completed")
            except Exception as e:
                logger.error(f"Error in scheduled documentation generation: {e}")

            await asyncio.sleep(interval_minutes * 60)

    def get_project(self, project_id: str) -> Optional[DocumentationProject]:
        """Get documentation project by ID"""
        return self.projects.get(project_id)

    def list_projects(self) -> List[Dict[str, Any]]:
        """List all documentation projects"""
        return [
            {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "version": project.version,
                "created_at": project.created_at,
                "updated_at": project.updated_at,
                "sections_count": len(project.sections)
            }
            for project in self.projects.values()
        ]

# Main execution
if __name__ == "__main__":
    async def main():
        generator = DocumentationGenerator()

        # Generate documentation
        output_file = await generator.generate_documentation("DMLogn8n Platform")
        print(f"Documentation generated: {output_file}")

        # List projects
        projects = generator.list_projects()
        print(f"Generated {len(projects)} documentation projects")

    asyncio.run(main())