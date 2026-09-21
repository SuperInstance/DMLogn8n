#!/usr/bin/env python3
"""
Setup script for LoRA-based Strategic Adaptation System
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = requirements_file.read_text(encoding="utf-8").strip().split('\n')
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

setup(
    name="lora-adaptation-system",
    version="1.0.0",
    author="DMlogn8n Development Team",
    author_email="dev@dmlogn8n.com",
    description="LoRA-based Strategic Adaptation System for D&D Agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dmlogn8n/agent-intelligence-system",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Games/Entertainment :: Role-Playing",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
        ],
        "gpu": [
            "bitsandbytes>=0.35.0",
            "flash-attn>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "lora-adaptation-test=integration_tests:run_integration_tests",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.md", "*.txt"],
    },
    zip_safe=False,
    keywords="lora adaptation dnd agents machine learning strategic",
    project_urls={
        "Bug Reports": "https://github.com/dmlogn8n/agent-intelligence-system/issues",
        "Source": "https://github.com/dmlogn8n/agent-intelligence-system",
        "Documentation": "https://github.com/dmlogn8n/agent-intelligence-system/blob/main/lora-adaptation/README.md",
    },
)