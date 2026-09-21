#!/usr/bin/env python3
"""
DMLogn8n Automated Vulnerability Patch Manager
Intelligent vulnerability patching system with rollback capabilities
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
import shutil
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
import git
import docker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/activeloguser/DMLogn8n/security/logs/patch_manager.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PatchStatus(Enum):
    PENDING = "PENDING"
    DOWNLOADING = "DOWNLOADING"
    TESTING = "TESTING"
    APPLYING = "APPLYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"
    SKIPPED = "SKIPPED"

class PatchType(Enum):
    SECURITY_UPDATE = "Security Update"
    DEPENDENCY_UPDATE = "Dependency Update"
    CODE_FIX = "Code Fix"
    CONFIGURATION_CHANGE = "Configuration Change"
    SYSTEM_UPDATE = "System Update"
    DOCKER_UPDATE = "Docker Update"
    LIBRARY_UPDATE = "Library Update"

class PatchPriority(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

@dataclass
class VulnerabilityPatch:
    id: str
    vulnerability_id: str
    title: str
    description: str
    patch_type: PatchType
    priority: PatchPriority
    affected_files: List[str]
    patch_commands: List[str]
    rollback_commands: List[str]
    dependencies: List[str]
    test_commands: List[str]
    estimated_downtime: int  # in minutes
    prerequisites: List[str]
    references: List[str]
    auto_applicable: bool
    requires_restart: bool
    backup_required: bool

@dataclass
class PatchOperation:
    id: str
    patch_id: str
    vulnerability_id: str
    status: PatchStatus
    started_at: datetime
    completed_at: Optional[datetime]
    target_path: str
    backup_location: Optional[str]
    test_results: Dict[str, Any]
    error_message: Optional[str]
    rollback_available: bool
    patch_version: str

@dataclass
class PatchReport:
    operation_id: str
    patch_id: str
    vulnerability_id: str
    patch_type: PatchType
    status: PatchStatus
    started_at: datetime
    completed_at: Optional[datetime]
    success: bool
    files_modified: List[str]
    test_results: Dict[str, Any]
    rollback_info: Dict[str, Any]
    error_details: Optional[str]

class PatchManager:
    """Advanced automated vulnerability patching system"""

    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.db_path = self.config.get('database_path', '/home/activeloguser/DMLogn8n/security/data/patch_manager.db')
        self.backup_path = self.config.get('backup_path', '/home/activeloguser/DMLogn8n/security/backups/')
        self.patches_path = self.config.get('patches_path', '/home/activeloguser/DMLogn8n/security/patches/')
        self.scanner_version = "2.0.0"

        # Initialize directories
        os.makedirs(self.backup_path, exist_ok=True)
        os.makedirs(self.patches_path, exist_ok=True)

        # Initialize database
        self._init_database()

        # Initialize Git repository for version control
        self._init_git_repository()

        # Docker client for container patching
        try:
            self.docker_client = docker.from_env()
            self.docker_available = True
        except Exception as e:
            logger.warning(f"Docker not available: {e}")
            self.docker_available = False

        # Patch registry with known vulnerability patches
        self.patch_registry = self._initialize_patch_registry()

        # Auto-patch configuration
        self.auto_patch_enabled = self.config.get('auto_patch_enabled', False)
        self.auto_patch_critical = self.config.get('auto_patch_critical', True)
        self.auto_patch_high = self.config.get('auto_patch_high', False)
        self.test_before_apply = self.config.get('test_before_apply', True)
        self.backup_before_patch = self.config.get('backup_before_patch', True)

    def _load_config(self, config_path: str) -> Dict:
        """Load patch manager configuration"""
        default_config = {
            'database_path': '/home/activeloguser/DMLogn8n/security/data/patch_manager.db',
            'backup_path': '/home/activeloguser/DMLogn8n/security/backups/',
            'patches_path': '/home/activeloguser/DMLogn8n/security/patches/',
            'auto_patch_enabled': False,
            'auto_patch_critical': True,
            'auto_patch_high': False,
            'auto_patch_medium': False,
            'test_before_apply': True,
            'backup_before_patch': True,
            'max_concurrent_patches': 3,
            'patch_timeout': 1800,  # 30 minutes
            'test_timeout': 600,     # 10 minutes
            'backup_retention_days': 30,
            'rollback_timeout': 300, # 5 minutes
            'notification_enabled': True,
            'maintenance_window': {
                'start': '02:00',
                'end': '04:00',
                'timezone': 'UTC'
            },
            'excluded_paths': [
                '/home/activeloguser/DMLogn8n/security/scanner/',
                '/home/activeloguser/DMLogn8n/security/logs/',
                '/home/activeloguser/DMLogn8n/security/backups/'
            ]
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
        """Initialize database for patch management"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create patches table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patches (
                id TEXT PRIMARY KEY,
                vulnerability_id TEXT,
                title TEXT NOT NULL,
                description TEXT,
                patch_type TEXT,
                priority TEXT,
                affected_files TEXT,
                patch_commands TEXT,
                rollback_commands TEXT,
                dependencies TEXT,
                test_commands TEXT,
                estimated_downtime INTEGER,
                prerequisites TEXT,
                references TEXT,
                auto_applicable BOOLEAN,
                requires_restart BOOLEAN,
                backup_required BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create patch_operations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patch_operations (
                id TEXT PRIMARY KEY,
                patch_id TEXT,
                vulnerability_id TEXT,
                status TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                target_path TEXT,
                backup_location TEXT,
                test_results TEXT,
                error_message TEXT,
                rollback_available BOOLEAN,
                patch_version TEXT,
                FOREIGN KEY (patch_id) REFERENCES patches (id)
            )
        ''')

        # Create patch_schedule table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patch_schedule (
                id TEXT PRIMARY KEY,
                patch_id TEXT,
                scheduled_time TIMESTAMP,
                priority TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patch_id) REFERENCES patches (id)
            )
        ''')

        conn.commit()
        conn.close()

    def _init_git_repository(self):
        """Initialize Git repository for version control"""
        try:
            repo_path = self.config.get('git_repo_path', '/home/activeloguser/DMLogn8n')

            if not os.path.exists(os.path.join(repo_path, '.git')):
                repo = git.Repo.init(repo_path)
                repo.config_writer().set_value("user", "name", "DMLogn8n Security Bot").release()
                repo.config_writer().set_value("user", "email", "security@dmlogn8n.local").release()

                # Create initial commit
                repo.index.add([repo_path])
                repo.index.commit("Initial commit - DMLogn8n Security Repository")

                logger.info(f"Initialized Git repository at {repo_path}")
            else:
                self.git_repo = git.Repo(repo_path)
                logger.info(f"Using existing Git repository at {repo_path}")

        except Exception as e:
            logger.warning(f"Failed to initialize Git repository: {e}")
            self.git_repo = None

    def _initialize_patch_registry(self) -> Dict[str, VulnerabilityPatch]:
        """Initialize registry of known vulnerability patches"""
        registry = {}

        # Node.js security patches
        registry.update({
            'CVE-2021-22939': VulnerabilityPatch(
                id='patch-nodejs-22939',
                vulnerability_id='CVE-2021-22939',
                title='Node.js HTTP/2 DoS Vulnerability Patch',
                description='Updates Node.js to version 14.18.1+ to fix HTTP/2 DoS vulnerability',
                patch_type=PatchType.DEPENDENCY_UPDATE,
                priority=PatchPriority.HIGH,
                affected_files=['package.json', 'package-lock.json'],
                patch_commands=[
                    'npm update node',
                    'npm audit fix --force'
                ],
                rollback_commands=[
                    'git checkout HEAD~1 -- package.json package-lock.json',
                    'npm install'
                ],
                dependencies=['npm'],
                test_commands=[
                    'node --version',
                    'npm test'
                ],
                estimated_downtime=5,
                prerequisites=['Node.js >= 14.0.0'],
                references=['https://nodejs.org/en/vulnerabilities'],
                auto_applicable=True,
                requires_restart=True,
                backup_required=True
            )
        })

        # Python security patches
        registry.update({
            'CVE-2021-3737': VulnerabilityPatch(
                id='patch-python-3737',
                vulnerability_id='CVE-2021-3737',
                title='Python urllib3 Regular Expression DoS Patch',
                description='Updates urllib3 to version 1.26.5+ to fix ReDoS vulnerability',
                patch_type=PatchType.DEPENDENCY_UPDATE,
                priority=PatchPriority.HIGH,
                affected_files=['requirements.txt', 'Pipfile.lock'],
                patch_commands=[
                    'pip install --upgrade urllib3>=1.26.5',
                    'pip freeze > requirements.txt'
                ],
                rollback_commands=[
                    'git checkout HEAD~1 -- requirements.txt',
                    'pip install -r requirements.txt'
                ],
                dependencies=['pip'],
                test_commands=[
                    'python -c "import urllib3; print(urllib3.__version__)"',
                    'python -m pytest tests/'
                ],
                estimated_downtime=2,
                prerequisites=['Python >= 3.6'],
                references=['https://nvd.nist.gov/vuln/detail/CVE-2021-3737'],
                auto_applicable=True,
                requires_restart=False,
                backup_required=True
            )
        })

        # OpenSSL security patches
        registry.update({
            'CVE-2021-3711': VulnerabilityPatch(
                id='patch-openssl-3711',
                vulnerability_id='CVE-2021-3711',
                title='OpenSSL SM2 DoS Vulnerability Patch',
                description='Updates OpenSSL to version 1.1.1l+ to fix SM2 signature vulnerability',
                patch_type=PatchType.SYSTEM_UPDATE,
                priority=PatchPriority.CRITICAL,
                affected_files=['/etc/ssl/', '/usr/lib/ssl/'],
                patch_commands=[
                    'apt-get update',
                    'apt-get install --only-upgrade openssl libssl-dev',
                    'systemctl restart apache2 nginx'
                ],
                rollback_commands=[
                    'apt-get install openssl=1.1.1k-1',
                    'systemctl restart apache2 nginx'
                ],
                dependencies=['apt-get'],
                test_commands=[
                    'openssl version',
                    'systemctl status apache2 nginx'
                ],
                estimated_downtime=10,
                prerequisites=['root access'],
                references=['https://www.openssl.org/news/secadv/20210824.txt'],
                auto_applicable=False,
                requires_restart=True,
                backup_required=True
            )
        })

        # Log4j security patches
        registry.update({
            'CVE-2021-44228': VulnerabilityPatch(
                id='patch-log4j-44228',
                vulnerability_id='CVE-2021-44228',
                title='Apache Log4j Remote Code Execution Patch',
                description='Updates Log4j to version 2.17.0+ to fix critical RCE vulnerability',
                patch_type=PatchType.DEPENDENCY_UPDATE,
                priority=PatchPriority.CRITICAL,
                affected_files=['pom.xml', 'build.gradle', 'package.json'],
                patch_commands=[
                    'mvn versions:use-latest-releases -Dincludes=org.apache.logging.log4j',
                    'gradle useLatestVersions',
                    'npm audit fix --force'
                ],
                rollback_commands=[
                    'git checkout HEAD~1 -- pom.xml build.gradle package.json',
                    'mvn clean install',
                    'gradle build',
                    'npm install'
                ],
                dependencies=['mvn', 'gradle', 'npm'],
                test_commands=[
                    'mvn test',
                    'gradle test',
                    'npm test'
                ],
                estimated_downtime=15,
                prerequisites=['Java >= 8'],
                references=['https://logging.apache.org/log4j/2.x/security.html'],
                auto_applicable=True,
                requires_restart=True,
                backup_required=True
            )
        })

        return registry

    async def create_patch(self, vulnerability_data: Dict, custom_commands: List[str] = None) -> VulnerabilityPatch:
        """Create a new vulnerability patch"""
        patch_id = f"patch_{vulnerability_data.get('id', 'unknown')}_{int(time.time())}"

        # Determine patch type and priority based on vulnerability
        severity = vulnerability_data.get('severity', 'MEDIUM')
        priority = self._map_severity_to_priority(severity)
        patch_type = self._determine_patch_type(vulnerability_data)

        # Generate patch commands based on vulnerability type
        if custom_commands:
            patch_commands = custom_commands
        else:
            patch_commands = self._generate_patch_commands(vulnerability_data)

        # Generate rollback commands
        rollback_commands = self._generate_rollback_commands(patch_commands)

        patch = VulnerabilityPatch(
            id=patch_id,
            vulnerability_id=vulnerability_data.get('id', ''),
            title=vulnerability_data.get('title', ''),
            description=vulnerability_data.get('description', ''),
            patch_type=patch_type,
            priority=priority,
            affected_files=vulnerability_data.get('affected_files', []),
            patch_commands=patch_commands,
            rollback_commands=rollback_commands,
            dependencies=vulnerability_data.get('dependencies', []),
            test_commands=vulnerability_data.get('test_commands', []),
            estimated_downtime=vulnerability_data.get('estimated_downtime', 5),
            prerequisites=vulnerability_data.get('prerequisites', []),
            references=vulnerability_data.get('references', []),
            auto_applicable=vulnerability_data.get('auto_applicable', False),
            requires_restart=vulnerability_data.get('requires_restart', False),
            backup_required=vulnerability_data.get('backup_required', True)
        )

        # Store patch in database
        self._store_patch(patch)

        logger.info(f"Created patch {patch_id} for vulnerability {vulnerability_data.get('id', 'unknown')}")
        return patch

    def _map_severity_to_priority(self, severity: str) -> PatchPriority:
        """Map vulnerability severity to patch priority"""
        mapping = {
            'CRITICAL': PatchPriority.CRITICAL,
            'HIGH': PatchPriority.HIGH,
            'MEDIUM': PatchPriority.MEDIUM,
            'LOW': PatchPriority.LOW
        }
        return mapping.get(severity.upper(), PatchPriority.MEDIUM)

    def _determine_patch_type(self, vulnerability_data: Dict) -> PatchType:
        """Determine patch type based on vulnerability characteristics"""
        category = vulnerability_data.get('category', '').lower()
        affected_component = vulnerability_data.get('affected_component', '').lower()

        if 'dependency' in category or 'package' in affected_component:
            return PatchType.DEPENDENCY_UPDATE
        elif 'system' in category or 'os' in affected_component:
            return PatchType.SYSTEM_UPDATE
        elif 'docker' in affected_component or 'container' in affected_component:
            return PatchType.DOCKER_UPDATE
        elif 'config' in category or 'configuration' in affected_component:
            return PatchType.CONFIGURATION_CHANGE
        elif 'library' in affected_component:
            return PatchType.LIBRARY_UPDATE
        else:
            return PatchType.CODE_FIX

    def _generate_patch_commands(self, vulnerability_data: Dict) -> List[str]:
        """Generate patch commands based on vulnerability type"""
        commands = []
        category = vulnerability_data.get('category', '').lower()
        affected_component = vulnerability_data.get('affected_component', '').lower()

        if 'sql injection' in category:
            commands.extend([
                '# Apply parameterized query fix',
                'find . -name "*.py" -exec sed -i "s/execute(.*\\+/execute(?, /g" {} \\;',
                'find . -name "*.js" -exec sed -i "s/db\\.query.*\\+/db\\.query(?, /g" {} \\;'
            ])
        elif 'xss' in category:
            commands.extend([
                '# Apply XSS protection',
                'find . -name "*.html" -exec sed -i "s/innerHTML/textContent/g" {} \\;',
                'find . -name "*.js" -exec sed -i "s/\\.html/\\.text/g" {} \\;'
            ])
        elif 'dependency' in category:
            affected_package = vulnerability_data.get('affected_component', '')
            if 'npm' in affected_component or 'package.json' in affected_component:
                commands.extend([
                    'npm audit fix --force',
                    'npm update'
                ])
            elif 'pip' in affected_component or 'requirements.txt' in affected_component:
                commands.extend([
                    'pip install --upgrade -r requirements.txt',
                    'pip freeze > requirements.txt'
                ])
        elif 'weak crypto' in category:
            commands.extend([
                '# Update cryptography libraries',
                'pip install --upgrade cryptography',
                'npm install crypto-js --save'
            ])

        return commands

    def _generate_rollback_commands(self, patch_commands: List[str]) -> List[str]:
        """Generate rollback commands based on patch commands"""
        rollback_commands = []

        # Git-based rollback
        rollback_commands.extend([
            '# Git rollback commands',
            'git checkout HEAD~1 -- .',
            'git status'
        ])

        # Package-specific rollback
        if any('npm' in cmd for cmd in patch_commands):
            rollback_commands.append('npm install')

        if any('pip' in cmd for cmd in patch_commands):
            rollback_commands.append('pip install -r requirements.txt')

        if any('apt-get' in cmd for cmd in patch_commands):
            rollback_commands.append('apt-get install --reinstall <package_name>')

        return rollback_commands

    def _store_patch(self, patch: VulnerabilityPatch):
        """Store patch in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO patches
            (id, vulnerability_id, title, description, patch_type, priority,
             affected_files, patch_commands, rollback_commands, dependencies,
             test_commands, estimated_downtime, prerequisites, references,
             auto_applicable, requires_restart, backup_required, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            patch.id,
            patch.vulnerability_id,
            patch.title,
            patch.description,
            patch.patch_type.value,
            patch.priority.value,
            json.dumps(patch.affected_files),
            json.dumps(patch.patch_commands),
            json.dumps(patch.rollback_commands),
            json.dumps(patch.dependencies),
            json.dumps(patch.test_commands),
            patch.estimated_downtime,
            json.dumps(patch.prerequisites),
            json.dumps(patch.references),
            patch.auto_applicable,
            patch.requires_restart,
            patch.backup_required,
            datetime.now()
        ))

        conn.commit()
        conn.close()

    async def apply_patch(self, patch_id: str, target_path: str = None,
                        force: bool = False, test_before: bool = None) -> PatchOperation:
        """Apply a vulnerability patch"""
        operation_id = f"op_{patch_id}_{int(time.time())}"

        logger.info(f"Starting patch operation {operation_id} for patch {patch_id}")

        # Get patch details
        patch = self._get_patch(patch_id)
        if not patch:
            raise ValueError(f"Patch {patch_id} not found")

        # Create patch operation record
        operation = PatchOperation(
            id=operation_id,
            patch_id=patch_id,
            vulnerability_id=patch.vulnerability_id,
            status=PatchStatus.PENDING,
            started_at=datetime.now(),
            completed_at=None,
            target_path=target_path or self.config.get('default_target_path', '/home/activeloguser/DMLogn8n'),
            backup_location=None,
            test_results={},
            error_message=None,
            rollback_available=False,
            patch_version=self._get_current_version()
        )

        self._store_operation(operation)

        try:
            # Check if patch should be applied
            if not force and not self._should_apply_patch(patch):
                operation.status = PatchStatus.SKIPPED
                operation.completed_at = datetime.now()
                operation.error_message = "Patch does not meet application criteria"
                self._update_operation(operation)
                return operation

            # Create backup if required
            if patch.backup_required and self.backup_before_patch:
                backup_location = await self._create_backup(operation.target_path, operation_id)
                operation.backup_location = backup_location

            # Create Git commit for patch application
            if self.git_repo:
                await self._create_git_commit("pre-patch", operation.target_path, operation_id)

            # Run tests before applying if enabled
            if test_before or (test_before is None and self.test_before_apply):
                test_results = await self._run_tests(patch.test_commands, operation.target_path)
                operation.test_results['pre_patch'] = test_results

                if not test_results.get('success', False):
                    operation.status = PatchStatus.FAILED
                    operation.error_message = "Pre-patch tests failed"
                    operation.completed_at = datetime.now()
                    self._update_operation(operation)
                    return operation

            # Apply patch
            operation.status = PatchStatus.APPLYING
            self._update_operation(operation)

            apply_results = await self._execute_patch_commands(
                patch.patch_commands, operation.target_path, operation_id
            )

            if not apply_results.get('success', False):
                operation.status = PatchStatus.FAILED
                operation.error_message = apply_results.get('error', 'Patch application failed')
                operation.completed_at = datetime.now()
                self._update_operation(operation)
                return operation

            # Run post-patch tests
            test_results = await self._run_tests(patch.test_commands, operation.target_path)
            operation.test_results['post_patch'] = test_results

            if not test_results.get('success', False):
                # Rollback if post-patch tests fail
                logger.warning("Post-patch tests failed, initiating rollback")
                await self._rollback_patch(operation)
                operation.status = PatchStatus.ROLLED_BACK
                operation.error_message = "Post-patch tests failed, patch rolled back"
            else:
                operation.status = PatchStatus.COMPLETED
                operation.rollback_available = True

                # Create Git commit for successful patch
                if self.git_repo:
                    await self._create_git_commit("post-patch", operation.target_path, operation_id)

            operation.completed_at = datetime.now()
            self._update_operation(operation)

            logger.info(f"Patch operation {operation_id} completed with status: {operation.status.value}")

        except Exception as e:
            logger.error(f"Patch operation {operation_id} failed: {e}")
            operation.status = PatchStatus.FAILED
            operation.error_message = str(e)
            operation.completed_at = datetime.now()
            self._update_operation(operation)

            # Attempt rollback if enabled
            if patch.backup_required:
                try:
                    await self._rollback_patch(operation)
                except Exception as rollback_error:
                    logger.error(f"Rollback failed for operation {operation_id}: {rollback_error}")

        return operation

    def _get_patch(self, patch_id: str) -> Optional[VulnerabilityPatch]:
        """Get patch from database or registry"""
        # Check patch registry first
        if patch_id in self.patch_registry:
            return self.patch_registry[patch_id]

        # Check database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM patches WHERE id = ?
        ''', (patch_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return VulnerabilityPatch(
                id=row[0],
                vulnerability_id=row[1],
                title=row[2],
                description=row[3],
                patch_type=PatchType(row[4]),
                priority=PatchPriority(row[5]),
                affected_files=json.loads(row[6]) if row[6] else [],
                patch_commands=json.loads(row[7]) if row[7] else [],
                rollback_commands=json.loads(row[8]) if row[8] else [],
                dependencies=json.loads(row[9]) if row[9] else [],
                test_commands=json.loads(row[10]) if row[10] else [],
                estimated_downtime=row[11],
                prerequisites=json.loads(row[12]) if row[12] else [],
                references=json.loads(row[13]) if row[13] else [],
                auto_applicable=bool(row[14]),
                requires_restart=bool(row[15]),
                backup_required=bool(row[16])
            )

        return None

    def _should_apply_patch(self, patch: VulnerabilityPatch) -> bool:
        """Determine if patch should be applied automatically"""
        if not patch.auto_applicable:
            return False

        if not self.auto_patch_enabled:
            return False

        # Check priority-based auto-patch settings
        if patch.priority == PatchPriority.CRITICAL and self.auto_patch_critical:
            return True

        if patch.priority == PatchPriority.HIGH and self.auto_patch_high:
            return True

        # Check maintenance window
        if not self._is_in_maintenance_window():
            return False

        # Check prerequisites
        if not self._check_prerequisites(patch.prerequisites):
            return False

        return True

    def _is_in_maintenance_window(self) -> bool:
        """Check if current time is within maintenance window"""
        try:
            from datetime import datetime
            import pytz

            maintenance = self.config.get('maintenance_window', {})
            if not maintenance:
                return True

            timezone = pytz.timezone(maintenance.get('timezone', 'UTC'))
            now = datetime.now(timezone)
            current_time = now.time()

            start_time = datetime.strptime(maintenance.get('start', '02:00'), '%H:%M').time()
            end_time = datetime.strptime(maintenance.get('end', '04:00'), '%H:%M').time()

            if start_time <= end_time:
                return start_time <= current_time <= end_time
            else:  # Overnight window
                return current_time >= start_time or current_time <= end_time

        except Exception as e:
            logger.warning(f"Failed to check maintenance window: {e}")
            return True

    def _check_prerequisites(self, prerequisites: List[str]) -> bool:
        """Check if prerequisites for patch are met"""
        for prereq in prerequisites:
            try:
                if prereq.startswith('Python >='):
                    version_required = prereq.split('>=')[1].strip()
                    result = subprocess.run(['python', '--version'], capture_output=True, text=True)
                    if result.returncode != 0:
                        return False
                    current_version = result.stdout.split()[1]
                    if not self._version_satisfies(current_version, version_required):
                        return False

                elif prereq.startswith('Node.js >='):
                    version_required = prereq.split('>=')[1].strip()
                    result = subprocess.run(['node', '--version'], capture_output=True, text=True)
                    if result.returncode != 0:
                        return False
                    current_version = result.stdout[1:]  # Remove 'v' prefix
                    if not self._version_satisfies(current_version, version_required):
                        return False

                elif prereq == 'root access':
                    if os.geteuid() != 0:
                        return False

                elif 'command exists' in prereq:
                    command = prereq.split('exists')[1].strip()
                    result = subprocess.run(['which', command], capture_output=True)
                    if result.returncode != 0:
                        return False

            except Exception as e:
                logger.warning(f"Failed to check prerequisite {prereq}: {e}")
                return False

        return True

    def _version_satisfies(self, current: str, required: str) -> bool:
        """Check if current version satisfies required version"""
        try:
            from packaging import version
            return version.parse(current) >= version.parse(required)
        except ImportError:
            # Fallback to simple version comparison
            current_parts = [int(x) for x in current.split('.')]
            required_parts = [int(x) for x in required.split('.')]

            for curr, req in zip(current_parts, required_parts):
                if curr > req:
                    return True
                if curr < req:
                    return False
            return len(current_parts) >= len(required_parts)

    async def _create_backup(self, target_path: str, operation_id: str) -> str:
        """Create backup of target path"""
        backup_location = os.path.join(self.backup_path, f"backup_{operation_id}_{int(time.time())}")

        logger.info(f"Creating backup at {backup_location}")

        try:
            # Create backup directory
            os.makedirs(backup_location, exist_ok=True)

            # Copy files
            if os.path.isdir(target_path):
                shutil.copytree(target_path, os.path.join(backup_location, 'target'), dirs_exist_ok=True)
            else:
                shutil.copy2(target_path, backup_location)

            # Create backup metadata
            metadata = {
                'operation_id': operation_id,
                'target_path': target_path,
                'backup_time': datetime.now().isoformat(),
                'files_backed_up': self._count_files(target_path)
            }

            with open(os.path.join(backup_location, 'metadata.json'), 'w') as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Backup created successfully at {backup_location}")
            return backup_location

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise

    def _count_files(self, path: str) -> int:
        """Count files in directory"""
        count = 0
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                count += len(files)
        else:
            count = 1
        return count

    async def _create_git_commit(self, message: str, target_path: str, operation_id: str):
        """Create Git commit for patch operation"""
        if not self.git_repo:
            return

        try:
            # Add changes to Git
            self.git_repo.git.add(target_path)

            # Create commit with operation ID in message
            commit_message = f"{message}: {operation_id}"
            self.git_repo.index.commit(commit_message)

            logger.info(f"Created Git commit: {commit_message}")

        except Exception as e:
            logger.warning(f"Failed to create Git commit: {e}")

    async def _run_tests(self, test_commands: List[str], target_path: str) -> Dict[str, Any]:
        """Run test commands"""
        results = {
            'success': True,
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'output': [],
            'errors': []
        }

        if not test_commands:
            return results

        logger.info(f"Running {len(test_commands)} test commands")

        for command in test_commands:
            try:
                if command.startswith('#'):  # Skip comments
                    continue

                # Change to target directory if needed
                cmd_parts = command.split()
                if cmd_parts[0] in ['npm', 'python', 'mvn', 'gradle']:
                    cmd = command.split()
                else:
                    cmd = ['sh', '-c', f'cd {target_path} && {command}']

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.config.get('test_timeout', 600)
                )

                results['tests_run'] += 1
                results['output'].append({
                    'command': command,
                    'return_code': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                })

                if result.returncode == 0:
                    results['tests_passed'] += 1
                else:
                    results['tests_failed'] += 1
                    results['success'] = False
                    results['errors'].append({
                        'command': command,
                        'error': result.stderr
                    })

            except subprocess.TimeoutExpired:
                results['tests_failed'] += 1
                results['success'] = False
                results['errors'].append({
                    'command': command,
                    'error': 'Test timed out'
                })

            except Exception as e:
                results['tests_failed'] += 1
                results['success'] = False
                results['errors'].append({
                    'command': command,
                    'error': str(e)
                })

        logger.info(f"Tests completed: {results['tests_passed']}/{results['tests_run']} passed")
        return results

    async def _execute_patch_commands(self, commands: List[str], target_path: str,
                                    operation_id: str) -> Dict[str, Any]:
        """Execute patch commands"""
        results = {
            'success': True,
            'commands_run': 0,
            'commands_succeeded': 0,
            'commands_failed': 0,
            'output': [],
            'errors': []
        }

        logger.info(f"Executing {len(commands)} patch commands")

        for command in commands:
            try:
                if command.startswith('#'):  # Skip comments
                    continue

                # Execute command
                cmd = ['sh', '-c', f'cd {target_path} && {command}']

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.config.get('patch_timeout', 1800)
                )

                results['commands_run'] += 1
                results['output'].append({
                    'command': command,
                    'return_code': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                })

                if result.returncode == 0:
                    results['commands_succeeded'] += 1
                    logger.info(f"Patch command succeeded: {command}")
                else:
                    results['commands_failed'] += 1
                    results['success'] = False
                    results['errors'].append({
                        'command': command,
                        'error': result.stderr
                    })
                    logger.error(f"Patch command failed: {command} - {result.stderr}")

            except subprocess.TimeoutExpired:
                results['commands_failed'] += 1
                results['success'] = False
                results['errors'].append({
                    'command': command,
                    'error': 'Command timed out'
                })
                logger.error(f"Patch command timed out: {command}")

            except Exception as e:
                results['commands_failed'] += 1
                results['success'] = False
                results['errors'].append({
                    'command': command,
                    'error': str(e)
                })
                logger.error(f"Patch command error: {command} - {e}")

        logger.info(f"Patch commands completed: {results['commands_succeeded']}/{results['commands_run']} succeeded")
        return results

    async def _rollback_patch(self, operation: PatchOperation):
        """Rollback a patch operation"""
        logger.info(f"Rolling back patch operation {operation.id}")

        if not operation.backup_location:
            logger.error("No backup available for rollback")
            return

        try:
            # Get patch details
            patch = self._get_patch(operation.patch_id)
            if not patch:
                logger.error(f"Cannot rollback: patch {operation.patch_id} not found")
                return

            # Execute rollback commands
            rollback_results = await self._execute_patch_commands(
                patch.rollback_commands, operation.target_path, f"rollback_{operation.id}"
            )

            if not rollback_results.get('success', False):
                logger.error("Rollback commands failed")
                return

            # Restore from backup if available
            backup_target = os.path.join(operation.backup_location, 'target')
            if os.path.exists(backup_target):
                if os.path.isdir(operation.target_path):
                    shutil.rmtree(operation.target_path)
                shutil.copytree(backup_target, operation.target_path)

            # Create Git commit for rollback
            if self.git_repo:
                await self._create_git_commit("rollback", operation.target_path, operation.id)

            logger.info(f"Patch operation {operation.id} rolled back successfully")

        except Exception as e:
            logger.error(f"Failed to rollback patch operation {operation.id}: {e}")
            raise

    def _store_operation(self, operation: PatchOperation):
        """Store patch operation in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO patch_operations
            (id, patch_id, vulnerability_id, status, started_at, target_path,
             backup_location, test_results, rollback_available, patch_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            operation.id,
            operation.patch_id,
            operation.vulnerability_id,
            operation.status.value,
            operation.started_at,
            operation.target_path,
            operation.backup_location,
            json.dumps(operation.test_results),
            operation.rollback_available,
            operation.patch_version
        ))

        conn.commit()
        conn.close()

    def _update_operation(self, operation: PatchOperation):
        """Update patch operation in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE patch_operations
            SET status = ?, completed_at = ?, backup_location = ?,
                test_results = ?, error_message = ?, rollback_available = ?
            WHERE id = ?
        ''', (
            operation.status.value,
            operation.completed_at,
            operation.backup_location,
            json.dumps(operation.test_results),
            operation.error_message,
            operation.rollback_available,
            operation.id
        ))

        conn.commit()
        conn.close()

    def _get_current_version(self) -> str:
        """Get current system/application version"""
        try:
            # Try to get Git version
            if self.git_repo:
                return self.git_repo.head.commit.hexsha[:8]
        except:
            pass

        # Fallback to timestamp
        return str(int(time.time()))

    async def auto_patch_vulnerabilities(self, vulnerability_scan_results: List[Dict]) -> List[PatchOperation]:
        """Automatically patch detected vulnerabilities"""
        operations = []

        for vuln in vulnerability_scan_results:
            try:
                # Look for existing patch in registry
                patch = None
                for patch_id, patch_candidate in self.patch_registry.items():
                    if patch_candidate.vulnerability_id == vuln.get('id', ''):
                        patch = patch_candidate
                        break

                # Create patch if not found
                if not patch:
                    patch = await self.create_patch(vuln)

                # Apply patch if criteria are met
                if self._should_apply_patch(patch):
                    operation = await self.apply_patch(patch.id)
                    operations.append(operation)

            except Exception as e:
                logger.error(f"Failed to auto-patch vulnerability {vuln.get('id', 'unknown')}: {e}")

        return operations

    async def schedule_patch(self, patch_id: str, scheduled_time: datetime,
                           priority: PatchPriority = None) -> str:
        """Schedule a patch to be applied at a specific time"""
        schedule_id = f"schedule_{patch_id}_{int(time.time())}"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO patch_schedule
            (id, patch_id, scheduled_time, priority, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            schedule_id,
            patch_id,
            scheduled_time,
            priority.value if priority else 'MEDIUM',
            'SCHEDULED'
        ))

        conn.commit()
        conn.close()

        logger.info(f"Scheduled patch {patch_id} for {scheduled_time}")
        return schedule_id

    async def generate_patch_report(self, operation_id: str) -> PatchReport:
        """Generate patch operation report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get operation details
        cursor.execute('''
            SELECT * FROM patch_operations WHERE id = ?
        ''', (operation_id,))

        op_row = cursor.fetchone()
        if not op_row:
            conn.close()
            raise ValueError(f"Operation {operation_id} not found")

        # Get patch details
        cursor.execute('''
            SELECT * FROM patches WHERE id = ?
        ''', (op_row[1],))

        patch_row = cursor.fetchone()
        conn.close()

        # Create report
        report = PatchReport(
            operation_id=op_row[0],
            patch_id=op_row[1],
            vulnerability_id=op_row[2],
            patch_type=PatchType(patch_row[4]) if patch_row else PatchType.CODE_FIX,
            status=PatchStatus(op_row[3]),
            started_at=op_row[4],
            completed_at=op_row[5],
            success=op_row[3] == 'COMPLETED',
            files_modified=json.loads(op_row[6]) if op_row[6] else [],
            test_results=json.loads(op_row[8]) if op_row[8] else {},
            rollback_info={
                'available': bool(op_row[9]),
                'backup_location': op_row[7]
            },
            error_details=op_row[10]
        )

        return report

async def main():
    """Main function for patch manager"""
    patch_manager = PatchManager()

    # Example usage - create and apply a patch
    vulnerability_data = {
        'id': 'CVE-2021-44228',
        'title': 'Apache Log4j Remote Code Execution',
        'description': 'Critical RCE vulnerability in Log4j',
        'severity': 'CRITICAL',
        'category': 'dependency',
        'affected_component': 'log4j-core',
        'affected_files': ['pom.xml', 'build.gradle'],
        'test_commands': ['mvn test'],
        'auto_applicable': True,
        'requires_restart': True,
        'backup_required': True
    }

    logger.info("Creating vulnerability patch...")
    patch = await patch_manager.create_patch(vulnerability_data)

    logger.info(f"Created patch: {patch.id}")

    if patch_manager._should_apply_patch(patch):
        logger.info("Applying patch automatically...")
        operation = await patch_manager.apply_patch(patch.id)

        # Generate report
        report = await patch_manager.generate_patch_report(operation.id)

        # Save report to file
        report_path = f"/home/activeloguser/DMLogn8n/security/reports/patch_report_{operation.id}.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)

        with open(report_path, 'w') as f:
            json.dump(asdict(report), f, indent=2, default=str)

        logger.info(f"Patch operation completed. Report saved to: {report_path}")

        # Print summary
        print(f"\n=== PATCH OPERATION SUMMARY ===")
        print(f"Operation ID: {operation.id}")
        print(f"Patch ID: {patch.id}")
        print(f"Status: {operation.status.value}")
        print(f"Started: {operation.started_at}")
        print(f"Completed: {operation.completed_at}")
        print(f"Success: {report.success}")
        print(f"Backup Available: {report.rollback_info['available']}")

        if operation.error_message:
            print(f"Error: {operation.error_message}")

    return patch_manager

if __name__ == "__main__":
    asyncio.run(main())