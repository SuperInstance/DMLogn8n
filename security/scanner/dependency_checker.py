#!/usr/bin/env python3
"""
DMLogn8n Advanced Dependency Security Checker
Comprehensive dependency vulnerability detection and management system
"""

import asyncio
import aiohttp
import json
import logging
import os
import re
import sys
import time
import hashlib
import sqlite3
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/activeloguser/DMLogn8n/security/logs/dependency_checker.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Dependency:
    name: str
    version: str
    ecosystem: str
    file_path: str
    dev_dependency: bool = False
    vulnerabilities: List[Dict] = None
    license_info: Dict = None
    repository_url: Optional[str] = None
    download_count: Optional[int] = None
    last_updated: Optional[datetime] = None
    security_advisories: List[Dict] = None

@dataclass
class VulnerabilityInfo:
    id: str
    title: str
    description: str
    severity: str
    cvss_score: Optional[float]
    cwe_id: Optional[str]
    published_at: datetime
    updated_at: datetime
    patched_versions: List[str]
    unaffected_versions: List[str]
    references: List[str]
    advisory_url: Optional[str]

@dataclass
class DependencyReport:
    scan_id: str
    project_path: str
    scanned_at: datetime
    total_dependencies: int
    vulnerable_dependencies: int
    critical_vulnerabilities: int
    high_vulnerabilities: int
    dependencies: List[Dependency]
    summary_statistics: Dict[str, Any]
    recommendations: List[str]

class DependencyChecker:
    """Advanced dependency vulnerability checker"""

    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.db_path = self.config.get('database_path', '/home/activeloguser/DMLogn8n/security/data/dependencies.db')
        self.cache_path = self.config.get('cache_path', '/home/activeloguser/DMLogn8n/security/cache/')
        self.scanner_version = "2.0.0"

        # API configurations
        self.nvd_api_key = self.config.get('nvd_api_key')
        self.github_token = self.config.get('github_token')
        self.osv_api_url = "https://api.osv.dev/v1/query"
        self.nvd_api_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        self.deps_dev_api_url = "https://api.deps.dev/v3alpha"

        # Initialize cache
        os.makedirs(self.cache_path, exist_ok=True)
        self._init_database()

        # Supported ecosystems
        self.supported_ecosystems = {
            'npm': ['package.json', 'package-lock.json', 'yarn.lock'],
            'pip': ['requirements.txt', 'Pipfile', 'Pipfile.lock', 'pyproject.toml'],
            'maven': ['pom.xml'],
            'gradle': ['build.gradle', 'build.gradle.kts'],
            'composer': ['composer.json', 'composer.lock'],
            'nuget': ['packages.config', '*.csproj', 'packages.lock.json'],
            'go': ['go.mod', 'go.sum'],
            'ruby': ['Gemfile', 'Gemfile.lock'],
            'cargo': ['Cargo.toml', 'Cargo.lock']
        }

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration"""
        default_config = {
            'database_path': '/home/activeloguser/DMLogn8n/security/data/dependencies.db',
            'cache_path': '/home/activeloguser/DMLogn8n/security/cache/',
            'nvd_api_key': None,
            'github_token': None,
            'scan_timeout': 300,
            'max_concurrent_requests': 10,
            'cache_expiry_hours': 24,
            'include_dev_dependencies': False,
            'license_check': True,
            'outdated_check': True,
            'security_advisory_sources': ['nvd', 'osv', 'github'],
            'auto_update_threshold': 7  # days
        }

        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")

        return default_config

    def _init_database(self):
        """Initialize database for dependency storage"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create dependencies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                ecosystem TEXT NOT NULL,
                file_path TEXT,
                dev_dependency BOOLEAN,
                vulnerabilities TEXT,
                license_info TEXT,
                repository_url TEXT,
                last_updated TIMESTAMP,
                scan_id TEXT,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create vulnerability cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vulnerability_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                package_name TEXT NOT NULL,
                ecosystem TEXT NOT NULL,
                vulnerability_id TEXT,
                severity TEXT,
                cvss_score REAL,
                data TEXT,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                UNIQUE(package_name, ecosystem, vulnerability_id)
            )
        ''')

        # Create scans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dependency_scans (
                scan_id TEXT PRIMARY KEY,
                project_path TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                total_dependencies INTEGER,
                vulnerable_dependencies INTEGER,
                critical_vulnerabilities INTEGER,
                status TEXT
            )
        ''')

        conn.commit()
        conn.close()

    async def scan_project_dependencies(self, project_path: str) -> DependencyReport:
        """Scan all dependencies in a project"""
        scan_id = self._generate_scan_id()
        logger.info(f"Starting dependency scan {scan_id} for {project_path}")

        # Record scan start
        self._record_scan_start(scan_id, project_path)

        try:
            dependencies = []
            project_path = Path(project_path)

            # Scan each supported ecosystem
            for ecosystem, config_files in self.supported_ecosystems.items():
                deps = await self._scan_ecosystem(project_path, ecosystem, config_files, scan_id)
                dependencies.extend(deps)

            # Analyze dependencies for vulnerabilities
            await self._analyze_dependencies_vulnerabilities(dependencies)

            # Generate statistics and recommendations
            report = self._generate_dependency_report(scan_id, project_path, dependencies)

            # Store results
            self._store_scan_results(scan_id, dependencies, report)

            logger.info(f"Dependency scan {scan_id} completed. Found {report.vulnerable_dependencies} vulnerable dependencies")
            return report

        except Exception as e:
            logger.error(f"Dependency scan {scan_id} failed: {e}")
            self._update_scan_status(scan_id, 'failed')
            raise

    async def _scan_ecosystem(self, project_path: Path, ecosystem: str, config_files: List[str], scan_id: str) -> List[Dependency]:
        """Scan dependencies for a specific ecosystem"""
        dependencies = []

        for config_file in config_files:
            # Handle glob patterns
            if '*' in config_file:
                files = list(project_path.rglob(config_file))
            else:
                files = list(project_path.rglob(config_file))

            for file_path in files:
                try:
                    deps = await self._parse_dependency_file(file_path, ecosystem)
                    for dep in deps:
                        dep.scan_id = scan_id
                    dependencies.extend(deps)
                except Exception as e:
                    logger.warning(f"Failed to scan {file_path} for {ecosystem}: {e}")

        return dependencies

    async def _parse_dependency_file(self, file_path: Path, ecosystem: str) -> List[Dependency]:
        """Parse dependency file and extract dependencies"""
        dependencies = []

        if ecosystem == 'npm':
            dependencies = await self._parse_npm_dependencies(file_path)
        elif ecosystem == 'pip':
            dependencies = await self._parse_pip_dependencies(file_path)
        elif ecosystem == 'maven':
            dependencies = await self._parse_maven_dependencies(file_path)
        elif ecosystem == 'gradle':
            dependencies = await self._parse_gradle_dependencies(file_path)
        elif ecosystem == 'composer':
            dependencies = await self._parse_composer_dependencies(file_path)
        elif ecosystem == 'nuget':
            dependencies = await self._parse_nuget_dependencies(file_path)
        elif ecosystem == 'go':
            dependencies = await self._parse_go_dependencies(file_path)
        elif ecosystem == 'ruby':
            dependencies = await self._parse_ruby_dependencies(file_path)
        elif ecosystem == 'cargo':
            dependencies = await self._parse_cargo_dependencies(file_path)

        # Set common properties
        for dep in dependencies:
            dep.ecosystem = ecosystem
            dep.file_path = str(file_path)

        return dependencies

    async def _parse_npm_dependencies(self, file_path: Path) -> List[Dependency]:
        """Parse npm package.json or package-lock.json"""
        dependencies = []

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            if file_path.name == 'package.json':
                deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                dev_deps = set(data.get('devDependencies', {}).keys())

                for name, version in deps.items():
                    dep = Dependency(
                        name=name,
                        version=self._normalize_npm_version(version),
                        ecosystem='npm',
                        file_path=str(file_path),
                        dev_dependency=name in dev_deps
                    )
                    dependencies.append(dep)

            elif file_path.name == 'package-lock.json' or file_path.name == 'yarn.lock':
                # Parse lock file for exact versions
                if file_path.name == 'package-lock.json':
                    packages = data.get('packages', {})
                    for pkg_path, pkg_info in packages.items():
                        if pkg_path.startswith('node_modules/'):
                            name = pkg_path.replace('node_modules/', '')
                            if name:
                                dep = Dependency(
                                    name=name,
                                    version=pkg_info.get('version', ''),
                                    ecosystem='npm',
                                    file_path=str(file_path),
                                    dev_dependency=pkg_info.get('dev', False)
                                )
                                dependencies.append(dep)

        except Exception as e:
            logger.warning(f"Failed to parse npm file {file_path}: {e}")

        return dependencies

    async def _parse_pip_dependencies(self, file_path: Path) -> List[Dependency]:
        """Parse Python requirements.txt or Pipfile"""
        dependencies = []

        try:
            if file_path.name == 'requirements.txt':
                with open(file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Parse package requirement
                            match = re.match(r'^([a-zA-Z0-9\-_.]+)([><=!]+)(.+)$', line)
                            if match:
                                name, operator, version = match.groups()
                            else:
                                name = line
                                version = 'latest'

                            dep = Dependency(
                                name=name,
                                version=version,
                                ecosystem='pip',
                                file_path=str(file_path)
                            )
                            dependencies.append(dep)

            elif file_path.name == 'Pipfile':
                with open(file_path, 'r') as f:
                    data = json.load(f)

                # Parse packages and dev-packages
                packages = {**data.get('packages', {}), **data.get('dev-packages', {})}
                dev_packages = set(data.get('dev-packages', {}).keys())

                for name, version in packages.items():
                    dep = Dependency(
                        name=name,
                        version=version if version != '*' else 'latest',
                        ecosystem='pip',
                        file_path=str(file_path),
                        dev_dependency=name in dev_packages
                    )
                    dependencies.append(dep)

            elif file_path.name == 'pyproject.toml':
                # Parse pyproject.toml (basic implementation)
                with open(file_path, 'r') as f:
                    content = f.read()

                # Simple regex to extract dependencies
                deps_pattern = r'\[tool\.poetry\.dependencies\](.*?)(?=\[|\Z)'
                match = re.search(deps_pattern, content, re.DOTALL)
                if match:
                    deps_section = match.group(1)
                    for line in deps_section.split('\n'):
                        line = line.strip()
                        if '=' in line and not line.startswith('#'):
                            parts = line.split('=', 1)
                            if len(parts) == 2:
                                name = parts[0].strip()
                                version = parts[1].strip().strip('"\'')
                                dep = Dependency(
                                    name=name,
                                    version=version,
                                    ecosystem='pip',
                                    file_path=str(file_path)
                                )
                                dependencies.append(dep)

        except Exception as e:
            logger.warning(f"Failed to parse pip file {file_path}: {e}")

        return dependencies

    async def _parse_maven_dependencies(self, file_path: Path) -> List[Dependency]:
        """Parse Maven pom.xml"""
        dependencies = []

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Handle namespace
            namespace = ''
            if root.tag.startswith('{'):
                namespace = root.tag.split('}')[0] + '}'

            deps_elements = root.findall(f'.//{namespace}dependency')
            for dep_elem in deps_elements:
                group_id = dep_elem.find(f'{namespace}groupId')
                artifact_id = dep_elem.find(f'{namespace}artifactId')
                version = dep_elem.find(f'{namespace}version')

                if group_id is not None and artifact_id is not None:
                    name = f"{group_id.text}:{artifact_id.text}"
                    version_text = version.text if version is not None else 'latest'

                    dep = Dependency(
                        name=name,
                        version=version_text,
                        ecosystem='maven',
                        file_path=str(file_path)
                    )
                    dependencies.append(dep)

        except Exception as e:
            logger.warning(f"Failed to parse Maven file {file_path}: {e}")

        return dependencies

    async def _parse_gradle_dependencies(self, file_path: Path) -> List[Dependency]:
        """Parse Gradle build.gradle"""
        dependencies = []

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Parse dependency declarations
            # Patterns for different dependency formats
            patterns = [
                r"implementation\s+['\"]([^:]+):([^:]+):([^'\"]+)['\"]",
                r"api\s+['\"]([^:]+):([^:]+):([^'\"]+)['\"]",
                r"compile\s+['\"]([^:]+):([^:]+):([^'\"]+)['\"]",
                r"testImplementation\s+['\"]([^:]+):([^:]+):([^'\"]+)['\"]"
            ]

            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    group_id, artifact_id, version = match.groups()
                    name = f"{group_id}:{artifact_id}"

                    dep = Dependency(
                        name=name,
                        version=version,
                        ecosystem='gradle',
                        file_path=str(file_path),
                        dev_dependency='test' in pattern
                    )
                    dependencies.append(dep)

        except Exception as e:
            logger.warning(f"Failed to parse Gradle file {file_path}: {e}")

        return dependencies

    async def _parse_composer_dependencies(self, file_path: Path) -> List[Dependency]:
        """Parse PHP composer.json"""
        dependencies = []

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            deps = {**data.get('require', {}), **data.get('require-dev', {})}
            dev_deps = set(data.get('require-dev', {}).keys())

            for name, version in deps.items():
                dep = Dependency(
                    name=name,
                    version=version,
                    ecosystem='composer',
                    file_path=str(file_path),
                    dev_dependency=name in dev_deps
                )
                dependencies.append(dep)

        except Exception as e:
            logger.warning(f"Failed to parse Composer file {file_path}: {e}")

        return dependencies

    async def _parse_nuget_dependencies(self, file_path: Path) -> List[Dependency]:
        """Parse NuGet packages.config or .csproj"""
        dependencies = []

        try:
            if file_path.name == 'packages.config':
                tree = ET.parse(file_path)
                root = tree.getroot()

                for package in root.findall('package'):
                    name = package.get('id')
                    version = package.get('version')

                    if name and version:
                        dep = Dependency(
                            name=name,
                            version=version,
                            ecosystem='nuget',
                            file_path=str(file_path)
                        )
                        dependencies.append(dep)

            elif file_path.suffix == '.csproj':
                tree = ET.parse(file_path)
                root = tree.getroot()

                # Handle namespace
                namespace = ''
                if root.tag.startswith('{'):
                    namespace = root.tag.split('}')[0] + '}'

                package_refs = root.findall(f'.//{namespace}PackageReference')
                for package_ref in package_refs:
                    name = package_ref.get('Include')
                    version = package_ref.get('Version')

                    if name and version:
                        dep = Dependency(
                            name=name,
                            version=version,
                            ecosystem='nuget',
                            file_path=str(file_path)
                        )
                        dependencies.append(dep)

        except Exception as e:
            logger.warning(f"Failed to parse NuGet file {file_path}: {e}")

        return dependencies

    async def _parse_go_dependencies(self, file_path: Path) -> List[Dependency]:
        """Parse Go go.mod"""
        dependencies = []

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Parse require blocks
            require_pattern = r'require\s*\((.*?)\)'
            require_matches = re.finditer(require_pattern, content, re.DOTALL)

            for match in require_matches:
                require_block = match.group(1)
                for line in require_block.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('//'):
                        parts = line.split()
                        if len(parts) >= 2:
                            name = parts[0]
                            version = parts[1]

                            dep = Dependency(
                                name=name,
                                version=version,
                                ecosystem='go',
                                file_path=str(file_path)
                            )
                            dependencies.append(dep)

            # Also parse single require lines
            single_require_pattern = r'require\s+([^\s]+)\s+([^\s]+)'
            single_matches = re.finditer(single_require_pattern, content)
            for match in single_matches:
                name, version = match.groups()
                dep = Dependency(
                    name=name,
                    version=version,
                    ecosystem='go',
                    file_path=str(file_path)
                )
                dependencies.append(dep)

        except Exception as e:
            logger.warning(f"Failed to parse Go file {file_path}: {e}")

        return dependencies

    async def _parse_ruby_dependencies(self, file_path: Path) -> List[Dependency]:
        """Parse Ruby Gemfile"""
        dependencies = []

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Parse gem declarations
            gem_pattern = r"gem\s+['\"]([^'\"]+)['\"](?:,\s*['\"]([^'\"]+)['\'])?|gem\s+['\"]([^'\"]+)['\"],\s*:\s*branch\s*=>\s*['\"]([^'\"]+)['\"]"
            matches = re.finditer(gem_pattern, content)

            for match in matches:
                if match.group(1):  # Standard gem with version
                    name = match.group(1)
                    version = match.group(2) or 'latest'
                elif match.group(3):  # Git branch
                    name = match.group(3)
                    version = f"branch:{match.group(4)}"
                else:
                    continue

                dep = Dependency(
                    name=name,
                    version=version,
                    ecosystem='ruby',
                    file_path=str(file_path)
                )
                dependencies.append(dep)

        except Exception as e:
            logger.warning(f"Failed to parse Ruby file {file_path}: {e}")

        return dependencies

    async def _parse_cargo_dependencies(self, file_path: Path) -> List[Dependency]:
        """Parse Rust Cargo.toml"""
        dependencies = []

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Parse [dependencies] section
            deps_pattern = r'\[dependencies\](.*?)(?=\[|\Z)'
            deps_match = re.search(deps_pattern, content, re.DOTALL)
            if deps_match:
                deps_section = deps_match.group(1)
                for line in deps_section.split('\n'):
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        name_version = line.split('=', 1)
                        if len(name_version) == 2:
                            name = name_version[0].strip()
                            version = name_version[1].strip().strip('"\'')
                            dep = Dependency(
                                name=name,
                                version=version,
                                ecosystem='cargo',
                                file_path=str(file_path)
                            )
                            dependencies.append(dep)

            # Parse [dev-dependencies] section
            dev_deps_pattern = r'\[dev-dependencies\](.*?)(?=\[|\Z)'
            dev_deps_match = re.search(dev_deps_pattern, content, re.DOTALL)
            if dev_deps_match:
                dev_deps_section = dev_deps_match.group(1)
                for line in dev_deps_section.split('\n'):
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        name_version = line.split('=', 1)
                        if len(name_version) == 2:
                            name = name_version[0].strip()
                            version = name_version[1].strip().strip('"\'')
                            dep = Dependency(
                                name=name,
                                version=version,
                                ecosystem='cargo',
                                file_path=str(file_path),
                                dev_dependency=True
                            )
                            dependencies.append(dep)

        except Exception as e:
            logger.warning(f"Failed to parse Cargo file {file_path}: {e}")

        return dependencies

    async def _analyze_dependencies_vulnerabilities(self, dependencies: List[Dependency]):
        """Analyze dependencies for security vulnerabilities"""
        logger.info(f"Analyzing {len(dependencies)} dependencies for vulnerabilities")

        # Group dependencies by ecosystem for batch processing
        by_ecosystem = {}
        for dep in dependencies:
            if dep.ecosystem not in by_ecosystem:
                by_ecosystem[dep.ecosystem] = []
            by_ecosystem[dep.ecosystem].append(dep)

        # Process each ecosystem
        tasks = []
        for ecosystem, deps in by_ecosystem.items():
            if self.config.get('include_dev_dependencies') or not all(dep.dev_dependency for dep in deps):
                tasks.append(self._check_ecosystem_vulnerabilities(ecosystem, deps))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_ecosystem_vulnerabilities(self, ecosystem: str, dependencies: List[Dependency]):
        """Check vulnerabilities for dependencies in an ecosystem"""
        # Use appropriate API for each ecosystem
        if ecosystem in ['npm', 'pip', 'maven', 'gradle']:
            await self._check_osv_vulnerabilities(dependencies)
        elif ecosystem == 'npm':
            await self._check_npm_advisories(dependencies)
        elif ecosystem == 'pip':
            await self._check_pip_vulnerabilities(dependencies)

    async def _check_osv_vulnerabilities(self, dependencies: List[Dependency]):
        """Check vulnerabilities using OSV.dev API"""
        batch_size = 100  # OSV API allows batch queries

        for i in range(0, len(dependencies), batch_size):
            batch = dependencies[i:i + batch_size]
            await self._query_osv_batch(batch)

    async def _query_osv_batch(self, dependencies: List[Dependency]):
        """Query OSV API for a batch of dependencies"""
        try:
            async with aiohttp.ClientSession() as session:
                tasks = []
                for dep in dependencies:
                    # Check cache first
                    cached_vulns = self._get_cached_vulnerabilities(dep.name, dep.ecosystem)
                    if cached_vulns:
                        dep.vulnerabilities = cached_vulns
                    else:
                        tasks.append(self._query_osv_single(dep, session))

                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"Failed to query OSV API: {e}")

    async def _query_osv_single(self, dependency: Dependency, session: aiohttp.ClientSession):
        """Query OSV API for a single dependency"""
        try:
            payload = {
                "package": {
                    "name": dependency.name,
                    "ecosystem": dependency.ecosystem.upper()
                },
                "version": dependency.version
            }

            async with session.post(self.osv_api_url, json=payload, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    vulns = data.get('vulns', [])

                    if vulns:
                        dependency.vulnerabilities = []
                        for vuln in vulns:
                            vuln_info = {
                                'id': vuln.get('id', ''),
                                'title': vuln.get('summary', ''),
                                'description': vuln.get('details', ''),
                                'severity': self._extract_severity_from_osv(vuln),
                                'cvss_score': self._extract_cvss_from_osv(vuln),
                                'published_at': vuln.get('published', ''),
                                'references': [ref.get('url', '') for ref in vuln.get('references', [])]
                            }
                            dependency.vulnerabilities.append(vuln_info)

                        # Cache results
                        self._cache_vulnerabilities(dependency.name, dependency.ecosystem, dependency.vulnerabilities)

        except Exception as e:
            logger.warning(f"Failed to query OSV for {dependency.name}: {e}")

    async def _check_npm_advisories(self, dependencies: List[Dependency]):
        """Check npm advisories for Node.js dependencies"""
        try:
            async with aiohttp.ClientSession() as session:
                for dep in dependencies:
                    if dep.ecosystem == 'npm':
                        await self._query_npm_advisory(dep, session)

        except Exception as e:
            logger.error(f"Failed to check npm advisories: {e}")

    async def _query_npm_advisory(self, dependency: Dependency, session: aiohttp.ClientSession):
        """Query npm advisory database"""
        try:
            url = f"https://registry.npmjs.org/-/v1/advisories"
            params = {
                'package': dependency.name,
                'version': dependency.version
            }

            async with session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    advisories = data.get('objects', [])

                    if advisories:
                        if not dependency.vulnerabilities:
                            dependency.vulnerabilities = []

                        for advisory in advisories:
                            vuln_info = {
                                'id': f"NPM-{advisory.get('id', '')}",
                                'title': advisory.get('title', ''),
                                'description': advisory.get('overview', ''),
                                'severity': advisory.get('severity', 'moderate'),
                                'cvss_score': advisory.get('cvss_score'),
                                'published_at': advisory.get('created', ''),
                                'references': [advisory.get('url', '')]
                            }
                            dependency.vulnerabilities.append(vuln_info)

        except Exception as e:
            logger.warning(f"Failed to query npm advisory for {dependency.name}: {e}")

    async def _check_pip_vulnerabilities(self, dependencies: List[Dependency]):
        """Check Python package vulnerabilities"""
        try:
            # Use Safety or PyUp API for Python packages
            async with aiohttp.ClientSession() as session:
                for dep in dependencies:
                    if dep.ecosystem == 'pip':
                        await self._query_pip_vulnerability(dep, session)

        except Exception as e:
            logger.error(f"Failed to check pip vulnerabilities: {e}")

    async def _query_pip_vulnerability(self, dependency: Dependency, session: aiohttp.ClientSession):
        """Query Python package vulnerability"""
        try:
            # Use PyUp Safety API (or check for local safety DB)
            url = f"https://pyup.io/api/v1/safety/"
            payload = {
                "packages": [{
                    "package": dependency.name,
                    "version": dependency.version
                }]
            }

            async with session.post(url, json=payload, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    vulns = data.get('vulnerabilities', [])

                    if vulns:
                        if not dependency.vulnerabilities:
                            dependency.vulnerabilities = []

                        for vuln in vulns:
                            vuln_info = {
                                'id': vuln.get('id', ''),
                                'title': vuln.get('advisory', ''),
                                'description': vuln.get('advisory', ''),
                                'severity': self._map_safety_severity(vuln.get('v', 'medium')),
                                'cvss_score': None,
                                'published_at': vuln.get('cve', ''),
                                'references': [f"https://nvd.nist.gov/vuln/detail/{vuln.get('cve', '')}"]
                            }
                            dependency.vulnerabilities.append(vuln_info)

        except Exception as e:
            logger.warning(f"Failed to query pip vulnerability for {dependency.name}: {e}")

    def _get_cached_vulnerabilities(self, package_name: str, ecosystem: str) -> Optional[List[Dict]]:
        """Get cached vulnerabilities for a package"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT data FROM vulnerability_cache
                WHERE package_name = ? AND ecosystem = ? AND expires_at > ?
            ''', (package_name, ecosystem, datetime.now()))

            row = cursor.fetchone()
            conn.close()

            if row:
                return json.loads(row[0])

        except Exception as e:
            logger.warning(f"Failed to get cached vulnerabilities: {e}")

        return None

    def _cache_vulnerabilities(self, package_name: str, ecosystem: str, vulnerabilities: List[Dict]):
        """Cache vulnerabilities for a package"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            expires_at = datetime.now() + timedelta(hours=self.config.get('cache_expiry_hours', 24))

            for vuln in vulnerabilities:
                cursor.execute('''
                    INSERT OR REPLACE INTO vulnerability_cache
                    (package_name, ecosystem, vulnerability_id, severity, cvss_score, data, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    package_name,
                    ecosystem,
                    vuln.get('id', ''),
                    vuln.get('severity', ''),
                    vuln.get('cvss_score'),
                    json.dumps(vuln),
                    expires_at
                ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.warning(f"Failed to cache vulnerabilities: {e}")

    def _extract_severity_from_osv(self, vuln: Dict) -> str:
        """Extract severity from OSV vulnerability data"""
        severity = vuln.get('severity', [])
        if severity:
            return severity[0].get('score', 'UNKNOWN')
        return 'UNKNOWN'

    def _extract_cvss_from_osv(self, vuln: Dict) -> Optional[float]:
        """Extract CVSS score from OSV vulnerability data"""
        severity = vuln.get('severity', [])
        if severity:
            score = severity[0].get('score')
            if isinstance(score, (int, float)):
                return float(score)
        return None

    def _map_safety_severity(self, safety_severity: str) -> str:
        """Map Safety severity to standard severity levels"""
        mapping = {
            'critical': 'CRITICAL',
            'high': 'HIGH',
            'medium': 'MEDIUM',
            'low': 'LOW'
        }
        return mapping.get(safety_severity.lower(), 'MEDIUM')

    def _normalize_npm_version(self, version: str) -> str:
        """Normalize npm version specification"""
        # Remove ^, ~, >=, <= operators for vulnerability checking
        return re.sub(r'^[\^~><=]+\s*', '', version)

    def _generate_dependency_report(self, scan_id: str, project_path: Path, dependencies: List[Dependency]) -> DependencyReport:
        """Generate dependency security report"""
        total_deps = len(dependencies)
        vulnerable_deps = len([dep for dep in dependencies if dep.vulnerabilities])
        critical_vulns = sum(len([v for v in (dep.vulnerabilities or []) if v.get('severity') == 'CRITICAL']) for dep in dependencies)
        high_vulns = sum(len([v for v in (dep.vulnerabilities or []) if v.get('severity') == 'HIGH']) for dep in dependencies)

        # Generate summary statistics
        stats = self._generate_dependency_statistics(dependencies)

        # Generate recommendations
        recommendations = self._generate_recommendations(dependencies)

        return DependencyReport(
            scan_id=scan_id,
            project_path=str(project_path),
            scanned_at=datetime.now(),
            total_dependencies=total_deps,
            vulnerable_dependencies=vulnerable_deps,
            critical_vulnerabilities=critical_vulns,
            high_vulnerabilities=high_vulns,
            dependencies=dependencies,
            summary_statistics=stats,
            recommendations=recommendations
        )

    def _generate_dependency_statistics(self, dependencies: List[Dependency]) -> Dict[str, Any]:
        """Generate dependency statistics"""
        stats = {
            'by_ecosystem': {},
            'by_severity': {
                'CRITICAL': 0,
                'HIGH': 0,
                'MEDIUM': 0,
                'LOW': 0
            },
            'dev_vs_prod': {
                'production': 0,
                'development': 0
            },
            'most_vulnerable': [],
            'vulnerability_trends': {}
        }

        # Count by ecosystem
        for dep in dependencies:
            ecosystem = dep.ecosystem
            stats['by_ecosystem'][ecosystem] = stats['by_ecosystem'].get(ecosystem, 0) + 1

            # Count dev vs prod
            if dep.dev_dependency:
                stats['dev_vs_prod']['development'] += 1
            else:
                stats['dev_vs_prod']['production'] += 1

            # Count vulnerabilities by severity
            if dep.vulnerabilities:
                for vuln in dep.vulnerabilities:
                    severity = vuln.get('severity', 'UNKNOWN')
                    if severity in stats['by_severity']:
                        stats['by_severity'][severity] += 1

        # Find most vulnerable packages
        dep_vuln_counts = [(dep.name, len(dep.vulnerabilities or [])) for dep in dependencies if dep.vulnerabilities]
        dep_vuln_counts.sort(key=lambda x: x[1], reverse=True)
        stats['most_vulnerable'] = dep_vuln_counts[:10]

        return stats

    def _generate_recommendations(self, dependencies: List[Dependency]) -> List[str]:
        """Generate security recommendations"""
        recommendations = []

        vulnerable_deps = [dep for dep in dependencies if dep.vulnerabilities]
        if vulnerable_deps:
            recommendations.append(f"Update {len(vulnerable_deps)} vulnerable dependencies to their latest secure versions")

        critical_vulns = [dep for dep in dependencies if dep.vulnerabilities and
                         any(v.get('severity') == 'CRITICAL' for v in dep.vulnerabilities)]
        if critical_vulns:
            recommendations.append(f"URGENT: Fix {len(critical_vulns)} packages with CRITICAL vulnerabilities")

        # Check for outdated dependencies
        outdated_recs = self._check_outdated_dependencies(dependencies)
        recommendations.extend(outdated_recs)

        # Check for unused dependencies
        unused_recs = self._check_unused_dependencies(dependencies)
        recommendations.extend(unused_recs)

        # Check for license issues
        if self.config.get('license_check'):
            license_recs = self._check_license_compliance(dependencies)
            recommendations.extend(license_recs)

        return recommendations

    def _check_outdated_dependencies(self, dependencies: List[Dependency]) -> List[str]:
        """Check for outdated dependencies"""
        recommendations = []

        # This would involve checking latest versions
        # For now, return a placeholder recommendation
        if len(dependencies) > 50:
            recommendations.append("Consider regularly updating dependencies to patch security vulnerabilities")

        return recommendations

    def _check_unused_dependencies(self, dependencies: List[Dependency]) -> List[str]:
        """Check for potentially unused dependencies"""
        recommendations = []

        dev_deps = [dep for dep in dependencies if dep.dev_dependency]
        if len(dev_deps) > len(dependencies) * 0.5:
            recommendations.append("Review development dependencies - consider removing unused packages")

        return recommendations

    def _check_license_compliance(self, dependencies: List[Dependency]) -> List[str]:
        """Check dependency license compliance"""
        recommendations = []

        # This would involve checking license compatibility
        # For now, return a placeholder recommendation
        recommendations.append("Review dependency licenses for compliance with project requirements")

        return recommendations

    def _generate_scan_id(self) -> str:
        """Generate unique scan ID"""
        return f"dep_scan_{int(time.time())}_{hashlib.md5(os.urandom(16)).hexdigest()[:8]}"

    def _record_scan_start(self, scan_id: str, project_path: str):
        """Record scan start in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO dependency_scans
            (scan_id, project_path, started_at, status)
            VALUES (?, ?, ?, ?)
        ''', (scan_id, project_path, datetime.now(), 'running'))

        conn.commit()
        conn.close()

    def _store_scan_results(self, scan_id: str, dependencies: List[Dependency], report: DependencyReport):
        """Store scan results in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Update scan record
        cursor.execute('''
            UPDATE dependency_scans
            SET completed_at = ?, total_dependencies = ?, vulnerable_dependencies = ?,
                critical_vulnerabilities = ?, status = ?
            WHERE scan_id = ?
        ''', (
            report.scanned_at,
            report.total_dependencies,
            report.vulnerable_dependencies,
            report.critical_vulnerabilities,
            'completed',
            scan_id
        ))

        # Store dependencies
        for dep in dependencies:
            cursor.execute('''
                INSERT INTO dependencies
                (name, version, ecosystem, file_path, dev_dependency, vulnerabilities,
                 license_info, repository_url, scan_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                dep.name,
                dep.version,
                dep.ecosystem,
                dep.file_path,
                dep.dev_dependency,
                json.dumps(dep.vulnerabilities) if dep.vulnerabilities else None,
                json.dumps(dep.license_info) if dep.license_info else None,
                dep.repository_url,
                scan_id
            ))

        conn.commit()
        conn.close()

    def _update_scan_status(self, scan_id: str, status: str):
        """Update scan status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE dependency_scans
            SET completed_at = ?, status = ?
            WHERE scan_id = ?
        ''', (datetime.now(), status, scan_id))

        conn.commit()
        conn.close()

    async def generate_dependency_report(self, scan_id: str, format: str = 'json') -> Dict:
        """Generate dependency security report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get scan details
        cursor.execute('''
            SELECT * FROM dependency_scans WHERE scan_id = ?
        ''', (scan_id,))

        scan_row = cursor.fetchone()
        if not scan_row:
            conn.close()
            return {'error': 'Scan not found'}

        # Get dependencies for this scan
        cursor.execute('''
            SELECT * FROM dependencies WHERE scan_id = ?
            ORDER BY name
        ''', (scan_id,))

        dep_rows = cursor.fetchall()
        conn.close()

        # Format report
        report = {
            'scan_id': scan_id,
            'project_path': scan_row[1],
            'started_at': scan_row[2],
            'completed_at': scan_row[3],
            'total_dependencies': scan_row[4],
            'vulnerable_dependencies': scan_row[5],
            'critical_vulnerabilities': scan_row[6],
            'dependencies': []
        }

        for row in dep_rows:
            dep = {
                'name': row[1],
                'version': row[2],
                'ecosystem': row[3],
                'file_path': row[4],
                'dev_dependency': bool(row[5]),
                'vulnerabilities': json.loads(row[6]) if row[6] else [],
                'license_info': json.loads(row[7]) if row[7] else None,
                'repository_url': row[8]
            }
            report['dependencies'].append(dep)

        # Generate statistics
        report['statistics'] = self._generate_dependency_statistics(
            [Dependency(**dep) for dep in report['dependencies']]
        )

        # Generate recommendations
        report['recommendations'] = self._generate_recommendations(
            [Dependency(**dep) for dep in report['dependencies']]
        )

        return report

async def main():
    """Main function for running dependency checker"""
    checker = DependencyChecker()

    # Example usage
    project_path = "/home/activeloguser/DMLogn8n"

    logger.info("Starting dependency security scan...")
    report = await checker.scan_project_dependencies(project_path)

    # Save report to file
    report_path = f"/home/activeloguser/DMLogn8n/security/reports/dependency_report_{report.scan_id}.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, 'w') as f:
        json.dump(report.__dict__, f, indent=2, default=str)

    logger.info(f"Dependency scan completed. Report saved to: {report_path}")
    logger.info(f"Found {report.vulnerable_dependencies} vulnerable dependencies out of {report.total_dependencies} total")

    # Print summary
    print("\n=== DEPENDENCY SECURITY SUMMARY ===")
    print(f"Total dependencies: {report.total_dependencies}")
    print(f"Vulnerable dependencies: {report.vulnerable_dependencies}")
    print(f"Critical vulnerabilities: {report.critical_vulnerabilities}")
    print(f"High vulnerabilities: {report.high_vulnerabilities}")

    if report.recommendations:
        print("\n=== RECOMMENDATIONS ===")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"{i}. {rec}")

    return report

if __name__ == "__main__":
    asyncio.run(main())