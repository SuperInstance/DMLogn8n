#!/usr/bin/env python3
"""
DMLogn8n Dependency Vulnerability Scanner
Scans dependencies for known vulnerabilities and security issues
"""

import json
import logging
import asyncio
import aiofiles
import aiohttp
import subprocess
import hashlib
import re
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict
import redis.asyncio as redis
import yaml
import os
import tempfile

logger = logging.getLogger(__name__)

class VulnerabilitySeverity(Enum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class PackageManager(Enum):
    NPM = "npm"
    PYPI = "pypi"
    MAVEN = "maven"
    GRADLE = "gradle"
    COMPOSER = "composer"
    GEM = "gem"
    CARGO = "cargo"
    GO = "go"
    DOCKER = "docker"

@dataclass
class Dependency:
    name: str
    version: str
    package_manager: PackageManager
    file_path: str
    installed_at: Optional[datetime] = None
    license: Optional[str] = None
    repository: Optional[str] = None

@dataclass
class DependencyVulnerability:
    vuln_id: str
    cve_id: Optional[str]
    dependency_name: str
    affected_versions: List[str]
    fixed_version: Optional[str]
    severity: VulnerabilitySeverity
    description: str
    references: List[str]
    published_at: datetime
    cvss_score: Optional[float] = None
    exploit_available: bool = False

@dataclass
class DependencyScanReport:
    scan_id: str
    scan_date: datetime
    project_path: str
    dependencies: List[Dependency]
    vulnerabilities: List[DependencyVulnerability]
    risk_score: float
    recommendations: List[str]
    statistics: Dict[str, Any]

class DependencyScanner:
    """
    Dependency vulnerability scanner for software supply chain security
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.redis_client = None
        self.scan_cache = {}
        self.vulnerability_cache = {}
        self.dependency_cache = {}

        # Scanner configuration
        self.enable_scanning = self.config.get('enable_scanning', True)
        self.cache_ttl_hours = self.config.get('cache_ttl_hours', 24)
        self.max_scan_depth = self.config.get('max_scan_depth', 5)
        self.cve_api_key = self.config.get('cve_api_key', None)
        self.github_token = self.config.get('github_token', None)
        self.scan_timeout_seconds = self.config.get('scan_timeout_seconds', 300)

        # Package manager configurations
        self.npm_registry = self.config.get('npm_registry', 'https://registry.npmjs.org')
        self.pypi_registry = self.config.get('pypi_registry', 'https://pypi.org/pypi')
        self.maven_registry = self.config.get('maven_registry', 'https://search.maven.org')

    async def initialize(self):
        """Initialize dependency scanner components"""
        try:
            # Initialize Redis
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=10,  # Dependency scanner specific DB
                decode_responses=True
            )

            # Load vulnerability database
            await self._load_vulnerability_database()

            # Start background tasks
            await self._start_background_tasks()

            logger.info("Dependency Scanner initialized")

        except Exception as e:
            logger.error(f"Dependency Scanner initialization failed: {e}")
            raise

    async def scan_project(self, project_path: str) -> DependencyScanReport:
        """
        Scan project for dependency vulnerabilities
        """
        try:
            scan_id = hashlib.md5(f"{project_path}_{datetime.now()}".encode()).hexdigest()[:16]
            scan_start = datetime.now()

            logger.info(f"Starting dependency scan for project: {project_path}")

            # Discover dependencies
            dependencies = await self._discover_dependencies(project_path)

            # Check for vulnerabilities
            vulnerabilities = []
            for dependency in dependencies:
                dep_vulns = await self._check_dependency_vulnerabilities(dependency)
                vulnerabilities.extend(dep_vulns)

            # Calculate risk score
            risk_score = self._calculate_risk_score(vulnerabilities, dependencies)

            # Generate recommendations
            recommendations = self._generate_recommendations(vulnerabilities, dependencies)

            # Create scan report
            report = DependencyScanReport(
                scan_id=scan_id,
                scan_date=scan_start,
                project_path=project_path,
                dependencies=dependencies,
                vulnerabilities=vulnerabilities,
                risk_score=risk_score,
                recommendations=recommendations,
                statistics=self._generate_statistics(dependencies, vulnerabilities)
            )

            # Store scan results
            await self._store_scan_report(report)

            logger.info(f"Dependency scan completed. Found {len(dependencies)} dependencies and {len(vulnerabilities)} vulnerabilities")
            return report

        except Exception as e:
            logger.error(f"Project dependency scan error: {e}")
            raise

    async def scan_dependency(self, package_name: str, version: str,
                           package_manager: PackageManager) -> List[DependencyVulnerability]:
        """
        Scan specific dependency for vulnerabilities
        """
        try:
            dependency = Dependency(
                name=package_name,
                version=version,
                package_manager=package_manager,
                file_path="manual_scan"
            )

            return await self._check_dependency_vulnerabilities(dependency)

        except Exception as e:
            logger.error(f"Dependency scan error: {e}")
            return []

    async def update_vulnerability_database(self):
        """
        Update vulnerability database from external sources
        """
        try:
            logger.info("Updating dependency vulnerability database...")

            # Update npm advisory database
            await self._update_npm_advisories()

            # Update PyPI vulnerability database
            await self._update_pypi_advisories()

            # Update Maven vulnerability database
            await self._update_maven_advisories()

            logger.info("Dependency vulnerability database updated successfully")

        except Exception as e:
            logger.error(f"Vulnerability database update error: {e}")

    async def get_scan_report(self, scan_id: str) -> Optional[DependencyScanReport]:
        """
        Get dependency scan report by ID
        """
        try:
            if self.redis_client:
                report_data = await self.redis_client.get(f"dependency_scan_report:{scan_id}")
                if report_data:
                    report_dict = json.loads(report_data)
                    return self._dict_to_scan_report(report_dict)

            return None

        except Exception as e:
            logger.error(f"Dependency scan report retrieval error: {e}")
            return None

    # Private methods
    async def _discover_dependencies(self, project_path: str) -> List[Dependency]:
        """Discover all dependencies in the project"""
        dependencies = []

        try:
            # Check for different package managers
            package_files = {
                PackageManager.NPM: ['package.json', 'package-lock.json'],
                PackageManager.PYPI: ['requirements.txt', 'Pipfile', 'pyproject.toml'],
                PackageManager.MAVEN: ['pom.xml', 'build.gradle'],
                PackageManager.GRADLE: ['build.gradle', 'settings.gradle'],
                PackageManager.COMPOSER: ['composer.json', 'composer.lock'],
                PackageManager.GEM: ['Gemfile', 'Gemfile.lock'],
                PackageManager.CARGO: ['Cargo.toml', 'Cargo.lock'],
                PackageManager.GO: ['go.mod', 'go.sum'],
                PackageManager.DOCKER: ['Dockerfile', 'docker-compose.yml']
            }

            for package_manager, files in package_files.items():
                for file_name in files:
                    file_path = os.path.join(project_path, file_name)
                    if os.path.exists(file_path):
                        try:
                            file_dependencies = await self._parse_dependency_file(file_path, package_manager)
                            dependencies.extend(file_dependencies)
                        except Exception as e:
                            logger.error(f"Error parsing {file_name}: {e}")

        except Exception as e:
            logger.error(f"Dependency discovery error: {e}")

        return dependencies

    async def _parse_dependency_file(self, file_path: str, package_manager: PackageManager) -> List[Dependency]:
        """Parse dependency file and extract dependencies"""
        dependencies = []

        try:
            if package_manager == PackageManager.NPM:
                dependencies = await self._parse_npm_file(file_path)
            elif package_manager == PackageManager.PYPI:
                dependencies = await self._parse_pypi_file(file_path)
            elif package_manager == PackageManager.MAVEN:
                dependencies = await self._parse_maven_file(file_path)
            elif package_manager == PackageManager.GRADLE:
                dependencies = await self._parse_gradle_file(file_path)
            elif package_manager == PackageManager.COMPOSER:
                dependencies = await self._parse_composer_file(file_path)
            elif package_manager == PackageManager.GEM:
                dependencies = await self._parse_gem_file(file_path)
            elif package_manager == PackageManager.CARGO:
                dependencies = await self._parse_cargo_file(file_path)
            elif package_manager == PackageManager.GO:
                dependencies = await self._parse_go_file(file_path)

        except Exception as e:
            logger.error(f"Error parsing dependency file {file_path}: {e}")

        return dependencies

    async def _parse_npm_file(self, file_path: str) -> List[Dependency]:
        """Parse npm package.json or package-lock.json"""
        dependencies = []

        try:
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                data = json.loads(content)

            # Parse dependencies
            dep_sections = ['dependencies', 'devDependencies', 'peerDependencies']
            for section in dep_sections:
                if section in data:
                    for name, version in data[section].items():
                        # Clean version string
                        version = re.sub(r'^[\^~]', '', version)
                        dependencies.append(Dependency(
                            name=name,
                            version=version,
                            package_manager=PackageManager.NPM,
                            file_path=file_path
                        ))

        except Exception as e:
            logger.error(f"NPM file parsing error: {e}")

        return dependencies

    async def _parse_pypi_file(self, file_path: str) -> List[Dependency]:
        """Parse Python requirements.txt, Pipfile, or pyproject.toml"""
        dependencies = []

        try:
            if file_path.endswith('.txt'):
                # Parse requirements.txt
                async with aiofiles.open(file_path, 'r') as f:
                    lines = await f.readlines()
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Parse requirement: package==version
                            if '==' in line:
                                name, version = line.split('==', 1)
                                dependencies.append(Dependency(
                                    name=name.strip(),
                                    version=version.strip(),
                                    package_manager=PackageManager.PYPI,
                                    file_path=file_path
                                ))

            elif file_path.endswith('Pipfile'):
                # Parse Pipfile
                async with aiofiles.open(file_path, 'r') as f:
                    content = await f.read()
                    # Parse TOML-like format
                    in_packages = False
                    for line in content.split('\n'):
                        line = line.strip()
                        if line == '[packages]':
                            in_packages = True
                            continue
                        elif line.startswith('['):
                            in_packages = False
                            continue
                        elif in_packages and line and '=' in line:
                            name, version = line.split('=', 1)
                            name = name.strip().strip('"\'')
                            version = version.strip().strip('"\'')
                            dependencies.append(Dependency(
                                name=name,
                                version=version,
                                package_manager=PackageManager.PYPI,
                                file_path=file_path
                            ))

        except Exception as e:
            logger.error(f"Python dependency file parsing error: {e}")

        return dependencies

    async def _parse_maven_file(self, file_path: str) -> List[Dependency]:
        """Parse Maven pom.xml"""
        dependencies = []

        try:
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()

            # Use regex to extract dependencies
            dependency_pattern = r'<dependency>.*?<groupId>(.*?)</groupId>.*?<artifactId>(.*?)</artifactId>.*?(?:<version>(.*?)</version>)?.*?</dependency>'
            matches = re.findall(dependency_pattern, content, re.DOTALL)

            for group_id, artifact_id, version in matches:
                if not version:
                    version = "unknown"
                dependencies.append(Dependency(
                    name=f"{group_id}:{artifact_id}",
                    version=version,
                    package_manager=PackageManager.MAVEN,
                    file_path=file_path
                ))

        except Exception as e:
            logger.error(f"Maven file parsing error: {e}")

        return dependencies

    async def _parse_gradle_file(self, file_path: str) -> List[Dependency]:
        """Parse Gradle build.gradle"""
        dependencies = []

        try:
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()

            # Parse implementation and compile dependencies
            dep_patterns = [
                r'implementation\s+[\'"](.*?)[\'"]',
                r'compile\s+[\'"](.*?)[\'"]',
                r'api\s+[\'"](.*?)[\'"]'
            ]

            for pattern in dep_patterns:
                matches = re.findall(pattern, content)
                for dep_string in matches:
                    # Parse dependency format: group:artifact:version
                    parts = dep_string.split(':')
                    if len(parts) >= 2:
                        name = dep_string
                        version = parts[2] if len(parts) > 2 else "unknown"
                        dependencies.append(Dependency(
                            name=name,
                            version=version,
                            package_manager=PackageManager.GRADLE,
                            file_path=file_path
                        ))

        except Exception as e:
            logger.error(f"Gradle file parsing error: {e}")

        return dependencies

    async def _parse_composer_file(self, file_path: str) -> List[Dependency]:
        """Parse Composer composer.json"""
        dependencies = []

        try:
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                data = json.loads(content)

            # Parse require and require-dev
            for section in ['require', 'require-dev']:
                if section in data:
                    for name, version in data[section].items():
                        dependencies.append(Dependency(
                            name=name,
                            version=version,
                            package_manager=PackageManager.COMPOSER,
                            file_path=file_path
                        ))

        except Exception as e:
            logger.error(f"Composer file parsing error: {e}")

        return dependencies

    async def _parse_gem_file(self, file_path: str) -> List[Dependency]:
        """Parse Ruby Gemfile"""
        dependencies = []

        try:
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()

            # Parse gem declarations
            gem_pattern = r"gem\s+['\"](.*?)['\"](?:,\s*['\"](.*?)['\"])?"
            matches = re.findall(gem_pattern, content)

            for name, version in matches:
                if not version:
                    version = "latest"
                dependencies.append(Dependency(
                    name=name,
                    version=version,
                    package_manager=PackageManager.GEM,
                    file_path=file_path
                ))

        except Exception as e:
            logger.error(f"Ruby Gemfile parsing error: {e}")

        return dependencies

    async def _parse_cargo_file(self, file_path: str) -> List[Dependency]:
        """Parse Rust Cargo.toml"""
        dependencies = []

        try:
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()

            # Parse [dependencies] section
            in_dependencies = False
            for line in content.split('\n'):
                line = line.strip()
                if line == '[dependencies]':
                    in_dependencies = True
                    continue
                elif line.startswith('['):
                    in_dependencies = False
                    continue
                elif in_dependencies and '=' in line:
                    name, version = line.split('=', 1)
                    name = name.strip()
                    version = version.strip().strip('"\'')
                    dependencies.append(Dependency(
                        name=name,
                        version=version,
                        package_manager=PackageManager.CARGO,
                        file_path=file_path
                    ))

        except Exception as e:
            logger.error(f"Cargo file parsing error: {e}")

        return dependencies

    async def _parse_go_file(self, file_path: str) -> List[Dependency]:
        """Parse Go go.mod"""
        dependencies = []

        try:
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()

            # Parse require statements
            require_pattern = r'require\s+([^\s]+)\s+(v[^\s]+)'
            matches = re.findall(require_pattern, content)

            for name, version in matches:
                dependencies.append(Dependency(
                    name=name,
                    version=version,
                    package_manager=PackageManager.GO,
                    file_path=file_path
                ))

        except Exception as e:
            logger.error(f"Go file parsing error: {e}")

        return dependencies

    async def _check_dependency_vulnerabilities(self, dependency: Dependency) -> List[DependencyVulnerability]:
        """Check dependency for known vulnerabilities"""
        vulnerabilities = []

        try:
            # Check cache first
            cache_key = f"{dependency.package_manager.value}:{dependency.name}:{dependency.version}"
            if cache_key in self.vulnerability_cache:
                return self.vulnerability_cache[cache_key]

            # Query vulnerability databases
            if dependency.package_manager == PackageManager.NPM:
                vulnerabilities = await self._check_npm_vulnerabilities(dependency)
            elif dependency.package_manager == PackageManager.PYPI:
                vulnerabilities = await self._check_pypi_vulnerabilities(dependency)
            elif dependency.package_manager == PackageManager.MAVEN:
                vulnerabilities = await self._check_maven_vulnerabilities(dependency)
            else:
                # Generic vulnerability check
                vulnerabilities = await self._check_generic_vulnerabilities(dependency)

            # Cache result
            self.vulnerability_cache[cache_key] = vulnerabilities

        except Exception as e:
            logger.error(f"Dependency vulnerability check error: {e}")

        return vulnerabilities

    async def _check_npm_vulnerabilities(self, dependency: Dependency) -> List[DependencyVulnerability]:
        """Check npm package for vulnerabilities"""
        vulnerabilities = []

        try:
            # Query npm advisory database
            url = f"{self.npm_registry}/-/v1/security-advisories"
            params = {
                'package': dependency.name,
                'version': dependency.version
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        for advisory in data:
                            vuln = DependencyVulnerability(
                                vuln_id=advisory.get('id', ''),
                                cve_id=advisory.get('cve'),
                                dependency_name=dependency.name,
                                affected_versions=advisory.get('vulnerable_versions', []),
                                fixed_version=advisory.get('patched_versions', [''])[0] if advisory.get('patched_versions') else None,
                                severity=self._map_severity(advisory.get('severity', 'moderate')),
                                description=advisory.get('overview', ''),
                                references=advisory.get('references', []),
                                published_at=datetime.fromisoformat(advisory.get('created_at', datetime.now().isoformat())),
                                cvss_score=advisory.get('cvss_score'),
                                exploit_available=advisory.get('exploit_available', False)
                            )
                            vulnerabilities.append(vuln)

        except Exception as e:
            logger.error(f"NPM vulnerability check error: {e}")

        return vulnerabilities

    async def _check_pypi_vulnerabilities(self, dependency: Dependency) -> List[DependencyVulnerability]:
        """Check PyPI package for vulnerabilities"""
        vulnerabilities = []

        try:
            # Query OSV API for Python vulnerabilities
            url = "https://api.osv.dev/v1/query"
            payload = {
                "package": {
                    "name": dependency.name,
                    "ecosystem": "PyPI"
                },
                "version": dependency.version
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        for vuln_data in data.get('vulns', []):
                            vuln = DependencyVulnerability(
                                vuln_id=vuln_data.get('id', ''),
                                cve_id=self._extract_cve(vuln_data.get('aliases', [])),
                                dependency_name=dependency.name,
                                affected_versions=vuln_data.get('affected', []),
                                fixed_version=vuln_data.get('fixed', [''])[0] if vuln_data.get('fixed') else None,
                                severity=self._map_severity(vuln_data.get('severity', 'moderate')),
                                description=vuln_data.get('summary', ''),
                                references=vuln_data.get('references', []),
                                published_at=datetime.fromisoformat(vuln_data.get('created_at', datetime.now().isoformat())),
                                cvss_score=vuln_data.get('severity_details', {}).get('score'),
                                exploit_available=vuln_data.get('exploit_available', False)
                            )
                            vulnerabilities.append(vuln)

        except Exception as e:
            logger.error(f"PyPI vulnerability check error: {e}")

        return vulnerabilities

    async def _check_maven_vulnerabilities(self, dependency: Dependency) -> List[DependencyVulnerability]:
        """Check Maven dependency for vulnerabilities"""
        vulnerabilities = []

        try:
            # Query OSV API for Java vulnerabilities
            url = "https://api.osv.dev/v1/query"
            payload = {
                "package": {
                    "name": dependency.name.split(':')[1] if ':' in dependency.name else dependency.name,
                    "ecosystem": "Maven"
                },
                "version": dependency.version
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        for vuln_data in data.get('vulns', []):
                            vuln = DependencyVulnerability(
                                vuln_id=vuln_data.get('id', ''),
                                cve_id=self._extract_cve(vuln_data.get('aliases', [])),
                                dependency_name=dependency.name,
                                affected_versions=vuln_data.get('affected', []),
                                fixed_version=vuln_data.get('fixed', [''])[0] if vuln_data.get('fixed') else None,
                                severity=self._map_severity(vuln_data.get('severity', 'moderate')),
                                description=vuln_data.get('summary', ''),
                                references=vuln_data.get('references', []),
                                published_at=datetime.fromisoformat(vuln_data.get('created_at', datetime.now().isoformat())),
                                cvss_score=vuln_data.get('severity_details', {}).get('score'),
                                exploit_available=vuln_data.get('exploit_available', False)
                            )
                            vulnerabilities.append(vuln)

        except Exception as e:
            logger.error(f"Maven vulnerability check error: {e}")

        return vulnerabilities

    async def _check_generic_vulnerabilities(self, dependency: Dependency) -> List[DependencyVulnerability]:
        """Generic vulnerability check for other package managers"""
        vulnerabilities = []

        try:
            # Query OSV API with generic ecosystem
            url = "https://api.osv.dev/v1/query"
            payload = {
                "package": {
                    "name": dependency.name,
                    "ecosystem": dependency.package_manager.value
                },
                "version": dependency.version
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        for vuln_data in data.get('vulns', []):
                            vuln = DependencyVulnerability(
                                vuln_id=vuln_data.get('id', ''),
                                cve_id=self._extract_cve(vuln_data.get('aliases', [])),
                                dependency_name=dependency.name,
                                affected_versions=vuln_data.get('affected', []),
                                fixed_version=vuln_data.get('fixed', [''])[0] if vuln_data.get('fixed') else None,
                                severity=self._map_severity(vuln_data.get('severity', 'moderate')),
                                description=vuln_data.get('summary', ''),
                                references=vuln_data.get('references', []),
                                published_at=datetime.fromisoformat(vuln_data.get('created_at', datetime.now().isoformat())),
                                cvss_score=vuln_data.get('severity_details', {}).get('score'),
                                exploit_available=vuln_data.get('exploit_available', False)
                            )
                            vulnerabilities.append(vuln)

        except Exception as e:
            logger.error(f"Generic vulnerability check error: {e}")

        return vulnerabilities

    def _map_severity(self, severity: str) -> VulnerabilitySeverity:
        """Map severity string to enum"""
        severity_mapping = {
            'low': VulnerabilitySeverity.LOW,
            'moderate': VulnerabilitySeverity.MEDIUM,
            'high': VulnerabilitySeverity.HIGH,
            'critical': VulnerabilitySeverity.CRITICAL
        }
        return severity_mapping.get(severity.lower(), VulnerabilitySeverity.MEDIUM)

    def _extract_cve(self, aliases: List[str]) -> Optional[str]:
        """Extract CVE ID from aliases"""
        for alias in aliases:
            if alias.startswith('CVE-'):
                return alias
        return None

    def _calculate_risk_score(self, vulnerabilities: List[DependencyVulnerability],
                             dependencies: List[Dependency]) -> float:
        """Calculate risk score from vulnerabilities"""
        if not vulnerabilities:
            return 0.0

        total_score = 0.0
        for vuln in vulnerabilities:
            severity_score = vuln.severity.value
            cvss_score = vuln.cvss_score or severity_score * 2.0
            if vuln.exploit_available:
                cvss_score += 1.0
            total_score += cvss_score

        # Normalize to 0-100 scale
        max_possible_score = len(vulnerabilities) * 11.0  # Max CVSS + exploit
        base_score = min(100.0, (total_score / max_possible_score) * 100)

        # Adjust for dependency count (more dependencies = slightly higher risk)
        dependency_factor = min(1.2, 1.0 + (len(dependencies) / 1000) * 0.2)

        return base_score * dependency_factor

    def _generate_recommendations(self, vulnerabilities: List[DependencyVulnerability],
                                dependencies: List[Dependency]) -> List[str]:
        """Generate security recommendations"""
        recommendations = []

        if not vulnerabilities:
            recommendations.append("No vulnerable dependencies found - continue monitoring")
            return recommendations

        # Count by severity
        severity_counts = defaultdict(int)
        for vuln in vulnerabilities:
            severity_counts[vuln.severity.name] += 1

        # Generate recommendations based on findings
        if severity_counts['CRITICAL'] > 0:
            recommendations.append("CRITICAL: Update packages with critical vulnerabilities immediately")

        if severity_counts['HIGH'] > 0:
            recommendations.append("HIGH: Update packages with high-severity vulnerabilities within 7 days")

        if severity_counts['MEDIUM'] > 5:
            recommendations.append("MEDIUM: Address multiple medium-severity vulnerabilities")

        # Update recommendations
        vulnerable_packages = set(vuln.dependency_name for vuln in vulnerabilities)
        recommendations.append(f"Update {len(vulnerable_packages)} vulnerable packages to latest secure versions")

        # License recommendations
        recommendations.extend([
            "Use package lock files to ensure consistent dependency versions",
            "Regularly scan for dependency vulnerabilities",
            "Consider using dependency vulnerability scanning in CI/CD pipelines",
            "Review and update indirect dependencies",
            "Monitor for newly disclosed vulnerabilities"
        ])

        return list(set(recommendations))  # Remove duplicates

    def _generate_statistics(self, dependencies: List[Dependency],
                            vulnerabilities: List[DependencyVulnerability]) -> Dict[str, Any]:
        """Generate scan statistics"""
        stats = {
            'total_dependencies': len(dependencies),
            'total_vulnerabilities': len(vulnerabilities),
            'vulnerable_dependencies': len(set(vuln.dependency_name for vuln in vulnerabilities)),
            'package_managers': defaultdict(int),
            'severity_counts': defaultdict(int),
            'exploitable_vulns': 0
        }

        for dep in dependencies:
            stats['package_managers'][dep.package_manager.value] += 1

        for vuln in vulnerabilities:
            stats['severity_counts'][vuln.severity.name] += 1
            if vuln.exploit_available:
                stats['exploitable_vulns'] += 1

        return {k: dict(v) if isinstance(v, defaultdict) else v for k, v in stats.items()}

    async def _store_scan_report(self, report: DependencyScanReport):
        """Store dependency scan report"""
        try:
            if self.redis_client:
                report_data = asdict(report)
                report_data['scan_date'] = report.scan_date.isoformat()
                report_data['dependencies'] = [asdict(dep) for dep in report.dependencies]
                report_data['vulnerabilities'] = [asdict(vuln) for vuln in report.vulnerabilities]

                await self.redis_client.setex(
                    f"dependency_scan_report:{report.scan_id}",
                    86400 * 30,  # 30 days
                    json.dumps(report_data)
                )

                # Add to scan history
                await self.redis_client.lpush(
                    "dependency_scan_history",
                    json.dumps({
                        'scan_id': report.scan_id,
                        'project_path': report.project_path,
                        'risk_score': report.risk_score,
                        'vulnerability_count': len(report.vulnerabilities),
                        'scan_date': report.scan_date.isoformat()
                    })
                )
                await self.redis_client.ltrim("dependency_scan_history", 0, 1000)

        except Exception as e:
            logger.error(f"Dependency scan report storage error: {e}")

    def _dict_to_scan_report(self, data: Dict) -> DependencyScanReport:
        """Convert dictionary to DependencyScanReport object"""
        dependencies = []
        for dep_data in data.get('dependencies', []):
            dep_data['package_manager'] = PackageManager(dep_data['package_manager'])
            if dep_data.get('installed_at'):
                dep_data['installed_at'] = datetime.fromisoformat(dep_data['installed_at'])
            dependencies.append(Dependency(**dep_data))

        vulnerabilities = []
        for vuln_data in data.get('vulnerabilities', []):
            vuln_data['severity'] = VulnerabilitySeverity(vuln_data['severity'])
            vuln_data['published_at'] = datetime.fromisoformat(vuln_data['published_at'])
            vulnerabilities.append(DependencyVulnerability(**vuln_data))

        return DependencyScanReport(
            scan_id=data['scan_id'],
            scan_date=datetime.fromisoformat(data['scan_date']),
            project_path=data['project_path'],
            dependencies=dependencies,
            vulnerabilities=vulnerabilities,
            risk_score=data['risk_score'],
            recommendations=data['recommendations'],
            statistics=data['statistics']
        )

    async def _load_vulnerability_database(self):
        """Load vulnerability database from cache"""
        try:
            if self.redis_client:
                # Load cached vulnerability data
                keys = await self.redis_client.keys("dependency_vuln:*")
                for key in keys:
                    vuln_data = await self.redis_client.get(key)
                    if vuln_data:
                        self.vulnerability_cache[key] = [DependencyVulnerability(**v) for v in json.loads(vuln_data)]

            logger.info(f"Loaded {len(self.vulnerability_cache)} cached vulnerability entries")

        except Exception as e:
            logger.error(f"Vulnerability database loading error: {e}")

    # Update methods
    async def _update_npm_advisories(self):
        """Update npm vulnerability database"""
        try:
            # Download npm advisories
            async with aiohttp.ClientSession() as session:
                url = "https://registry.npmjs.org/-/npm/v1/security/advisories"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Process and store advisories
                        pass

        except Exception as e:
            logger.error(f"NPM advisories update error: {e}")

    async def _update_pypi_advisories(self):
        """Update PyPI vulnerability database"""
        try:
            # PyPI doesn't have a direct advisory API, use OSV database
            pass

        except Exception as e:
            logger.error(f"PyPI advisories update error: {e}")

    async def _update_maven_advisories(self):
        """Update Maven vulnerability database"""
        try:
            # Use OSV database for Maven vulnerabilities
            pass

        except Exception as e:
            logger.error(f"Maven advisories update error: {e}")

    async def _start_background_tasks(self):
        """Start background tasks for dependency scanner"""
        try:
            # Periodic vulnerability database updates
            asyncio.create_task(self._periodic_database_updates())

            # Cache cleanup
            asyncio.create_task(self._periodic_cache_cleanup())

        except Exception as e:
            logger.error(f"Background tasks startup error: {e}")

    async def _periodic_database_updates(self):
        """Periodically update vulnerability databases"""
        while True:
            try:
                await asyncio.sleep(86400)  # Daily
                await self.update_vulnerability_database()

            except Exception as e:
                logger.error(f"Periodic database update error: {e}")
                await asyncio.sleep(3600)

    async def _periodic_cache_cleanup(self):
        """Clean up old cached data"""
        while True:
            try:
                await asyncio.sleep(3600 * 6)  # Every 6 hours

                # Clean up old cache entries
                if self.redis_client:
                    # Clean up old vulnerability cache entries
                    pass

            except Exception as e:
                logger.error(f"Periodic cache cleanup error: {e}")
                await asyncio.sleep(300)