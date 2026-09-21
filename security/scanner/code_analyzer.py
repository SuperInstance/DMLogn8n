#!/usr/bin/env python3
"""
DMLogn8n Advanced Code Security Analyzer
Comprehensive static code analysis for security vulnerabilities and anti-patterns
"""

import ast
import asyncio
import json
import logging
import os
import re
import sys
import time
import hashlib
import sqlite3
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import importlib.util

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/activeloguser/DMLogn8n/security/logs/code_analyzer.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class CodeLanguage(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    PHP = "php"
    C = "c"
    CPP = "cpp"
    CSHARP = "csharp"
    GO = "go"
    RUBY = "ruby"
    SWIFT = "swift"
    KOTLIN = "kotlin"

class VulnerabilityType(Enum):
    SQL_INJECTION = "SQL Injection"
    XSS = "Cross-Site Scripting"
    PATH_TRAVERSAL = "Path Traversal"
    COMMAND_INJECTION = "Command Injection"
    INSECURE_DESERIALIZATION = "Insecure Deserialization"
    HARDCODED_CREDENTIALS = "Hardcoded Credentials"
    WEAK_CRYPTOGRAPHY = "Weak Cryptography"
    BUFFER_OVERFLOW = "Buffer Overflow"
    RACE_CONDITION = "Race Condition"
    MEMORY_LEAK = "Memory Leak"
    INSECURE_RANDOM = "Insecure Random Number Generation"
    MISSING_INPUT_VALIDATION = "Missing Input Validation"
    INSECURE_FILE_HANDLING = "Insecure File Handling"
    AUTHENTICATION_BYPASS = "Authentication Bypass"
    PRIVILEGE_ESCALATION = "Privilege Escalation"
    INFORMATION_DISCLOSURE = "Information Disclosure"
    INSECURE_COMMUNICATION = "Insecure Communication"
    UNSAFE_TYPE_CASTING = "Unsafe Type Casting"
    RESOURCE_EXHAUSTION = "Resource Exhaustion"

@dataclass
class CodeVulnerability:
    id: str
    title: str
    description: str
    vulnerability_type: VulnerabilityType
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    file_path: str
    line_number: int
    column_number: int
    code_snippet: str
    language: CodeLanguage
    confidence: str  # HIGH, MEDIUM, LOW
    cwe_id: Optional[str]
    owasp_category: Optional[str]
    remediation: str
    references: List[str]
    context: Dict[str, Any]

@dataclass
class AnalysisResult:
    scan_id: str
    target_path: str
    language: CodeLanguage
    started_at: datetime
    completed_at: Optional[datetime]
    total_files: int
    analyzed_files: int
    vulnerabilities: List[CodeVulnerability]
    metrics: Dict[str, Any]
    status: str

class CodeAnalyzer:
    """Advanced static code security analyzer"""

    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.db_path = self.config.get('database_path', '/home/activeloguser/DMLogn8n/security/data/code_analysis.db')
        self.scanner_version = "2.0.0"

        # Security patterns for different languages
        self.security_patterns = self._initialize_security_patterns()

        # Initialize database
        self._init_database()

        # Language-specific analyzers
        self.analyzers = {
            CodeLanguage.PYTHON: self._analyze_python,
            CodeLanguage.JAVASCRIPT: self._analyze_javascript,
            CodeLanguage.TYPESCRIPT: self._analyze_typescript,
            CodeLanguage.JAVA: self._analyze_java,
            CodeLanguage.PHP: self._analyze_php,
            CodeLanguage.C: self._analyze_c,
            CodeLanguage.CPP: self._analyze_cpp,
            CodeLanguage.CSHARP: self._analyze_csharp,
            CodeLanguage.GO: self._analyze_go,
            CodeLanguage.RUBY: self._analyze_ruby
        }

    def _load_config(self, config_path: str) -> Dict:
        """Load analyzer configuration"""
        default_config = {
            'database_path': '/home/activeloguser/DMLogn8n/security/data/code_analysis.db',
            'max_file_size_mb': 10,
            'max_workers': 4,
            'exclude_patterns': ['*.min.js', '*.min.css', 'node_modules/*', '.git/*', '__pycache__/*'],
            'include_test_files': False,
            'deep_analysis': True,
            'taint_analysis': True,
            'dataflow_analysis': True,
            'confidence_threshold': 'MEDIUM',
            'severity_threshold': 'LOW'
        }

        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")

        return default_config

    def _initialize_security_patterns(self) -> Dict[CodeLanguage, Dict]:
        """Initialize security patterns for different languages"""
        return {
            CodeLanguage.PYTHON: {
                'sql_injection': [
                    (r'execute\s*\(\s*["\'].*%s.*["\']', 'String formatting in SQL query'),
                    (r'execute\s*\(\s*f["\'].*\{.*\}.*["\']', 'f-string in SQL query'),
                    (r'cursor\.execute\s*\([^)]*\+\s*[^)]*\)', 'String concatenation in SQL query'),
                    (r'query\s*=\s*["\'].*\+.*["\']', 'String concatenation in SQL query'),
                ],
                'command_injection': [
                    (r'os\.system\s*\([^)]*\)', 'Use of os.system() with user input'),
                    (r'subprocess\.call\s*\([^)]*\)', 'Use of subprocess.call() with user input'),
                    (r'subprocess\.run\s*\([^,]*,\s*shell\s*=\s*True', 'shell=True in subprocess.run()'),
                    (r'eval\s*\([^)]*\)', 'Use of eval() with user input'),
                    (r'exec\s*\([^)]*\)', 'Use of exec() with user input'),
                ],
                'hardcoded_secrets': [
                    (r'password\s*=\s*["\'][^"\']{8,}["\']', 'Hardcoded password'),
                    (r'api_key\s*=\s*["\'][^"\']{16,}["\']', 'Hardcoded API key'),
                    (r'secret\s*=\s*["\'][^"\']{16,}["\']', 'Hardcoded secret'),
                    (r'token\s*=\s*["\'][^"\']{16,}["\']', 'Hardcoded token'),
                ],
                'weak_crypto': [
                    (r'md5\s*\(', 'Use of weak MD5 hash'),
                    (r'sha1\s*\(', 'Use of weak SHA1 hash'),
                    (r'hashlib\.md5\s*\(', 'Use of weak MD5 hash'),
                    (r'hashlib\.sha1\s*\(', 'Use of weak SHA1 hash'),
                    (r'Crypto\.Cipher\.DES\s*\(', 'Use of weak DES encryption'),
                    (r'Crypto\.Cipher\.ARC4\s*\(', 'Use of weak RC4 encryption'),
                ],
                'insecure_random': [
                    (r'random\.random\s*\(', 'Use of insecure random module'),
                    (r'random\.randint\s*\(', 'Use of insecure random module'),
                    (r'random\.choice\s*\(', 'Use of insecure random module'),
                ],
                'path_traversal': [
                    (r'open\s*\([^)]*\.\./[^)]*\)', 'Potential path traversal'),
                    (r'open\s*\([^)]*\.\.\\\\[^)]*\)', 'Potential path traversal'),
                    (r'os\.path\.join\s*\([^)]*\.\.[^)]*\)', 'Potential path traversal'),
                ],
                'insecure_deserialization': [
                    (r'pickle\.loads?\s*\(', 'Use of unsafe pickle deserialization'),
                    (r'cPickle\.loads?\s*\(', 'Use of unsafe cPickle deserialization'),
                    (r'marshal\.loads?\s*\(', 'Use of unsafe marshal deserialization'),
                    (r'yaml\.load\s*\([^,]*\)', 'Use of unsafe YAML loading'),
                ],
                'information_disclosure': [
                    (r'print\s*\([^)]*password[^)]*\)', 'Potential password disclosure'),
                    (r'print\s*\([^)]*secret[^)]*\)', 'Potential secret disclosure'),
                    (r'logging\.debug\s*\([^)]*password[^)]*\)', 'Potential password in logs'),
                    (r'traceback\.print_exc\s*\(\)', 'Stack trace exposure'),
                ]
            },
            CodeLanguage.JAVASCRIPT: {
                'xss': [
                    (r'innerHTML\s*=\s*[^;]+', 'Direct innerHTML assignment'),
                    (r'outerHTML\s*=\s*[^;]+', 'Direct outerHTML assignment'),
                    (r'document\.write\s*\(', 'Use of document.write()'),
                    (r'eval\s*\(', 'Use of eval() function'),
                    (r'setTimeout\s*\(\s*["\']', 'setTimeout with string'),
                    (r'setInterval\s*\(\s*["\']', 'setInterval with string'),
                ],
                'sql_injection': [
                    (r'query\s*\(\s*["\'].*\$\s*\{.*\}.*["\']', 'Template literal in SQL query'),
                    (r'query\s*\(\s*["\'].*\+.*["\']', 'String concatenation in SQL query'),
                ],
                'command_injection': [
                    (r'exec\s*\(', 'Use of exec() with user input'),
                    (r'spawn\s*\(', 'Use of spawn() with user input'),
                    (r'child_process\.exec\s*\(', 'Use of child_process.exec()'),
                ],
                'hardcoded_secrets': [
                    (r'password\s*:\s*["\'][^"\']{8,}["\']', 'Hardcoded password'),
                    (r'apiKey\s*:\s*["\'][^"\']{16,}["\']', 'Hardcoded API key'),
                    (r'secret\s*:\s*["\'][^"\']{16,}["\']', 'Hardcoded secret'),
                ],
                'weak_crypto': [
                    (r'md5\s*\(', 'Use of weak MD5 hash'),
                    (r'sha1\s*\(', 'Use of weak SHA1 hash'),
                ],
                'insecure_random': [
                    (r'Math\.random\s*\(', 'Use of insecure Math.random()'),
                ]
            },
            CodeLanguage.JAVA: {
                'sql_injection': [
                    (r'executeQuery\s*\([^)]*\+[^)]*\)', 'String concatenation in SQL query'),
                    (r'execute\s*\([^)]*\+[^)]*\)', 'String concatenation in SQL query'),
                    (r'createStatement\s*\(\)\.executeQuery\s*\([^)]*\+[^)]*\)', 'SQL injection vulnerability'),
                ],
                'command_injection': [
                    (r'Runtime\.getRuntime\(\)\.exec\s*\(', 'Command execution with user input'),
                    (r'ProcessBuilder\s*\([^)]*\)', 'Process creation with user input'),
                ],
                'hardcoded_secrets': [
                    (r'password\s*=\s*"[^"]{8,}"', 'Hardcoded password'),
                    (r'apiKey\s*=\s*"[^"]{16,}"', 'Hardcoded API key'),
                    (r'secret\s*=\s*"[^"]{16,}"', 'Hardcoded secret'),
                ],
                'weak_crypto': [
                    (r'MessageDigest\.getInstance\s*\(\s*"MD3"', 'Use of weak MD3 hash'),
                    (r'MessageDigest\.getInstance\s*\(\s*"MD5"', 'Use of weak MD5 hash'),
                    (r'MessageDigest\.getInstance\s*\(\s*"SHA1"', 'Use of weak SHA1 hash'),
                    (r'Cipher\.getInstance\s*\(\s*"DES', 'Use of weak DES encryption'),
                ],
                'deserialization': [
                    (r'ObjectInputStream\s*\(', 'Use of ObjectInputStream'),
                    (r'readObject\s*\(\)', 'Object deserialization'),
                ],
                'path_traversal': [
                    (r'new\s+File\s*\([^)]*\.\.[^)]*\)', 'Potential path traversal'),
                ]
            },
            CodeLanguage.PHP: {
                'sql_injection': [
                    (r'mysql_query\s*\([^)]*\$[^)]*\)', 'SQL query with variable'),
                    (r'mysqli_query\s*\([^)]*\$[^)]*\)', 'MySQLi query with variable'),
                    (r'pg_query\s*\([^)]*\$[^)]*\)', 'PostgreSQL query with variable'),
                ],
                'command_injection': [
                    (r'exec\s*\(', 'Use of exec() function'),
                    (r'shell_exec\s*\(', 'Use of shell_exec() function'),
                    (r'system\s*\(', 'Use of system() function'),
                    (r'passthru\s*\(', 'Use of passthru() function'),
                    (r'`\$\{[^}]*\}`', 'Backtick operator execution'),
                ],
                'xss': [
                    (r'echo\s+\$[^;]+', 'Direct echo of variable'),
                    (r'print\s+\$[^;]+', 'Direct print of variable'),
                ],
                'hardcoded_secrets': [
                    (r'\$password\s*=\s*["\'][^"\']{8,}["\']', 'Hardcoded password'),
                    (r'\$api_key\s*=\s*["\'][^"\']{16,}["\']', 'Hardcoded API key'),
                ],
                'weak_crypto': [
                    (r'md5\s*\(', 'Use of weak MD5 hash'),
                    (r'sha1\s*\(', 'Use of weak SHA1 hash'),
                ],
                'file_inclusion': [
                    (r'include\s+\$[^;]+', 'Dynamic file inclusion'),
                    (r'require\s+\$[^;]+', 'Dynamic file requirement'),
                    (r'include_once\s+\$[^;]+', 'Dynamic file inclusion once'),
                    (r'require_once\s+\$[^;]+', 'Dynamic file requirement once'),
                ]
            }
        }

    def _init_database(self):
        """Initialize database for code analysis storage"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create vulnerabilities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_vulnerabilities (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                vulnerability_type TEXT,
                severity TEXT,
                file_path TEXT,
                line_number INTEGER,
                column_number INTEGER,
                code_snippet TEXT,
                language TEXT,
                confidence TEXT,
                cwe_id TEXT,
                owasp_category TEXT,
                remediation TEXT,
                references TEXT,
                context TEXT,
                scan_id TEXT,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create scans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_scans (
                scan_id TEXT PRIMARY KEY,
                target_path TEXT,
                language TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                total_files INTEGER,
                analyzed_files INTEGER,
                vulnerabilities_count INTEGER,
                status TEXT
            )
        ''')

        # Create metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id TEXT,
                file_path TEXT,
                lines_of_code INTEGER,
                cyclomatic_complexity INTEGER,
                function_count INTEGER,
                class_count INTEGER,
                security_score REAL,
                FOREIGN KEY (scan_id) REFERENCES code_scans (scan_id)
            )
        ''')

        conn.commit()
        conn.close()

    async def analyze_codebase(self, target_path: str, language_filter: List[CodeLanguage] = None) -> List[AnalysisResult]:
        """Analyze entire codebase for security vulnerabilities"""
        scan_id = self._generate_scan_id()
        logger.info(f"Starting codebase analysis {scan_id} for {target_path}")

        results = []

        try:
            target_path = Path(target_path)

            # Discover code files by language
            files_by_language = self._discover_code_files(target_path, language_filter)

            # Analyze each language
            for language, files in files_by_language.items():
                if files:
                    result = await self._analyze_language_files(scan_id, language, files, target_path)
                    results.append(result)

            logger.info(f"Codebase analysis {scan_id} completed")

        except Exception as e:
            logger.error(f"Codebase analysis {scan_id} failed: {e}")

        return results

    def _discover_code_files(self, target_path: Path, language_filter: List[CodeLanguage] = None) -> Dict[CodeLanguage, List[Path]]:
        """Discover code files grouped by language"""
        files_by_language = {}

        language_extensions = {
            CodeLanguage.PYTHON: ['.py'],
            CodeLanguage.JAVASCRIPT: ['.js', '.jsx'],
            CodeLanguage.TYPESCRIPT: ['.ts', '.tsx'],
            CodeLanguage.JAVA: ['.java'],
            CodeLanguage.PHP: ['.php'],
            CodeLanguage.C: ['.c', '.h'],
            CodeLanguage.CPP: ['.cpp', '.cxx', '.cc', '.hpp', '.hxx'],
            CodeLanguage.CSHARP: ['.cs'],
            CodeLanguage.GO: ['.go'],
            CodeLanguage.RUBY: ['.rb'],
            CodeLanguage.SWIFT: ['.swift'],
            CodeLanguage.KOTLIN: ['.kt', '.kts']
        }

        for language, extensions in language_extensions.items():
            if language_filter and language not in language_filter:
                continue

            files = []
            for ext in extensions:
                for file_path in target_path.rglob(f'*{ext}'):
                    if self._should_analyze_file(file_path):
                        files.append(file_path)

            if files:
                files_by_language[language] = files

        return files_by_language

    def _should_analyze_file(self, file_path: Path) -> bool:
        """Check if file should be analyzed"""
        # Check file size
        if file_path.stat().st_size > self.config.get('max_file_size_mb', 10) * 1024 * 1024:
            return False

        # Check exclude patterns
        file_str = str(file_path)
        for pattern in self.config.get('exclude_patterns', []):
            if re.match(pattern.replace('*', '.*'), file_str):
                return False

        # Check if it's a test file
        if not self.config.get('include_test_files', False):
            if any(test_dir in file_str.lower() for test_dir in ['test', 'spec', '__tests__']):
                return False
            if file_path.name.lower().startswith(('test_', 'spec_')):
                return False

        return True

    async def _analyze_language_files(self, scan_id: str, language: CodeLanguage, files: List[Path], target_path: Path) -> AnalysisResult:
        """Analyze files for a specific language"""
        logger.info(f"Analyzing {len(files)} {language.value} files")

        analyzer_func = self.analyzers.get(language)
        if not analyzer_func:
            logger.warning(f"No analyzer available for {language.value}")
            return None

        result = AnalysisResult(
            scan_id=f"{scan_id}_{language.value}",
            target_path=str(target_path),
            language=language,
            started_at=datetime.now(),
            completed_at=None,
            total_files=len(files),
            analyzed_files=0,
            vulnerabilities=[],
            metrics={},
            status='running'
        )

        try:
            # Record scan start
            self._record_scan_start(result)

            # Analyze files in parallel
            with ThreadPoolExecutor(max_workers=self.config.get('max_workers', 4)) as executor:
                loop = asyncio.get_event_loop()
                tasks = []

                for file_path in files:
                    task = loop.run_in_executor(executor, analyzer_func, file_path)
                    tasks.append((file_path, task))

                # Process results as they complete
                for file_path, task in tasks:
                    try:
                        file_vulnerabilities = await task
                        result.vulnerabilities.extend(file_vulnerabilities)
                        result.analyzed_files += 1
                    except Exception as e:
                        logger.warning(f"Failed to analyze {file_path}: {e}")

            # Calculate metrics
            result.metrics = self._calculate_metrics(result.vulnerabilities, files)
            result.completed_at = datetime.now()
            result.status = 'completed'

            # Store results
            self._store_analysis_results(result)

            logger.info(f"Completed analysis of {language.value} files. Found {len(result.vulnerabilities)} vulnerabilities")

        except Exception as e:
            logger.error(f"Failed to analyze {language.value} files: {e}")
            result.status = 'failed'
            result.completed_at = datetime.now()

        return result

    def _analyze_python(self, file_path: Path) -> List[CodeVulnerability]:
        """Analyze Python file for security vulnerabilities"""
        vulnerabilities = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')

            # Pattern-based analysis
            patterns = self.security_patterns.get(CodeLanguage.PYTHON, {})
            for vuln_type, pattern_list in patterns.items():
                for pattern, description in pattern_list:
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            vuln = self._create_vulnerability(
                                file_path=file_path,
                                line_number=line_num,
                                vulnerability_type=vuln_type,
                                title=f"{vuln_type.replace('_', ' ').title()}",
                                description=description,
                                code_snippet=line.strip(),
                                language=CodeLanguage.PYTHON,
                                pattern=pattern
                            )
                            vulnerabilities.append(vuln)

            # AST-based analysis
            if self.config.get('deep_analysis', True):
                ast_vulnerabilities = self._analyze_python_ast(file_path, content)
                vulnerabilities.extend(ast_vulnerabilities)

        except Exception as e:
            logger.warning(f"Failed to analyze Python file {file_path}: {e}")

        return vulnerabilities

    def _analyze_python_ast(self, file_path: Path, content: str) -> List[CodeVulnerability]:
        """Analyze Python code using AST for deeper security analysis"""
        vulnerabilities = []

        try:
            tree = ast.parse(content)

            class SecurityVisitor(ast.NodeVisitor):
                def visit_Call(self, node):
                    # Check for dangerous function calls
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id

                        # Check eval/exec usage
                        if func_name in ['eval', 'exec']:
                            if node.args:
                                arg_source = ast.get_source_segment(content, node.args[0])
                                vuln = self._create_vulnerability(
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    column_number=node.col_offset,
                                    vulnerability_type="COMMAND_INJECTION",
                                    title=f"Use of dangerous function: {func_name}",
                                    description=f"Use of {func_name}() can lead to code injection",
                                    code_snippet=arg_source or func_name,
                                    language=CodeLanguage.PYTHON,
                                    confidence='HIGH'
                                )
                                vulnerabilities.append(vuln)

                    # Check for subprocess calls with shell=True
                    elif isinstance(node.func, ast.Attribute):
                        if (isinstance(node.func.value, ast.Name) and
                            node.func.value.id == 'subprocess' and
                            node.func.attr in ['run', 'call', 'Popen']):

                            # Check for shell=True
                            for keyword in node.keywords:
                                if (keyword.arg == 'shell' and
                                    isinstance(keyword.value, ast.Constant) and
                                    keyword.value.value is True):

                                    vuln = self._create_vulnerability(
                                        file_path=file_path,
                                        line_number=node.lineno,
                                        column_number=node.col_offset,
                                        vulnerability_type="COMMAND_INJECTION",
                                        title="subprocess with shell=True",
                                        description="Use of shell=True in subprocess can lead to command injection",
                                        code_snippet=ast.get_source_segment(content, node) or '',
                                        language=CodeLanguage.PYTHON,
                                        confidence='HIGH'
                                    )
                                    vulnerabilities.append(vuln)

                    self.generic_visit(node)

                def visit_Import(self, node):
                    # Check for dangerous imports
                    for alias in node.names:
                        if alias.name in ['pickle', 'cPickle', 'marshal']:
                            vuln = self._create_vulnerability(
                                file_path=file_path,
                                line_number=node.lineno,
                                column_number=node.col_offset,
                                vulnerability_type="INSECURE_DESERIALIZATION",
                                title=f"Potentially unsafe import: {alias.name}",
                                description=f"Import of {alias.name} can lead to insecure deserialization",
                                code_snippet=f"import {alias.name}",
                                language=CodeLanguage.PYTHON,
                                confidence='MEDIUM'
                            )
                            vulnerabilities.append(vuln)

                    self.generic_visit(node)

            visitor = SecurityVisitor()
            visitor.visit(tree)

        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            logger.warning(f"AST analysis failed for {file_path}: {e}")

        return vulnerabilities

    def _analyze_javascript(self, file_path: Path) -> List[CodeVulnerability]:
        """Analyze JavaScript file for security vulnerabilities"""
        vulnerabilities = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')

            # Pattern-based analysis
            patterns = self.security_patterns.get(CodeLanguage.JAVASCRIPT, {})
            for vuln_type, pattern_list in patterns.items():
                for pattern, description in pattern_list:
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            vuln = self._create_vulnerability(
                                file_path=file_path,
                                line_number=line_num,
                                vulnerability_type=vuln_type,
                                title=f"{vuln_type.replace('_', ' ').title()}",
                                description=description,
                                code_snippet=line.strip(),
                                language=CodeLanguage.JAVASCRIPT,
                                pattern=pattern
                            )
                            vulnerabilities.append(vuln)

        except Exception as e:
            logger.warning(f"Failed to analyze JavaScript file {file_path}: {e}")

        return vulnerabilities

    def _analyze_typescript(self, file_path: Path) -> List[CodeVulnerability]:
        """Analyze TypeScript file for security vulnerabilities"""
        # TypeScript analysis similar to JavaScript
        return self._analyze_javascript(file_path)

    def _analyze_java(self, file_path: Path) -> List[CodeVulnerability]:
        """Analyze Java file for security vulnerabilities"""
        vulnerabilities = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')

            # Pattern-based analysis
            patterns = self.security_patterns.get(CodeLanguage.JAVA, {})
            for vuln_type, pattern_list in patterns.items():
                for pattern, description in pattern_list:
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            vuln = self._create_vulnerability(
                                file_path=file_path,
                                line_number=line_num,
                                vulnerability_type=vuln_type,
                                title=f"{vuln_type.replace('_', ' ').title()}",
                                description=description,
                                code_snippet=line.strip(),
                                language=CodeLanguage.JAVA,
                                pattern=pattern
                            )
                            vulnerabilities.append(vuln)

        except Exception as e:
            logger.warning(f"Failed to analyze Java file {file_path}: {e}")

        return vulnerabilities

    def _analyze_php(self, file_path: Path) -> List[CodeVulnerability]:
        """Analyze PHP file for security vulnerabilities"""
        vulnerabilities = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')

            # Pattern-based analysis
            patterns = self.security_patterns.get(CodeLanguage.PHP, {})
            for vuln_type, pattern_list in patterns.items():
                for pattern, description in pattern_list:
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            vuln = self._create_vulnerability(
                                file_path=file_path,
                                line_number=line_num,
                                vulnerability_type=vuln_type,
                                title=f"{vuln_type.replace('_', ' ').title()}",
                                description=description,
                                code_snippet=line.strip(),
                                language=CodeLanguage.PHP,
                                pattern=pattern
                            )
                            vulnerabilities.append(vuln)

        except Exception as e:
            logger.warning(f"Failed to analyze PHP file {file_path}: {e}")

        return vulnerabilities

    def _analyze_c(self, file_path: Path) -> List[CodeVulnerability]:
        """Analyze C file for security vulnerabilities"""
        vulnerabilities = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')

            # C-specific patterns
            c_patterns = {
                'buffer_overflow': [
                    (r'strcpy\s*\([^)]+\)', 'Use of unsafe strcpy()'),
                    (r'strcat\s*\([^)]+\)', 'Use of unsafe strcat()'),
                    (r'sprintf\s*\([^)]+\)', 'Use of unsafe sprintf()'),
                    (r'gets\s*\([^)]+\)', 'Use of dangerous gets() function'),
                    (r'scanf\s*\([^)]*%s[^)]*\)', 'Use of unsafe scanf() with %s'),
                ],
                'memory_leaks': [
                    (r'malloc\s*\([^)]+\)', 'Memory allocation - check for free()'),
                    (r'calloc\s*\([^)]+\)', 'Memory allocation - check for free()'),
                    (r'realloc\s*\([^)]+\)', 'Memory reallocation - check for free()'),
                ],
                'format_string': [
                    (r'printf\s*\([^,)]*[^"'][^)]*\)', 'Possible format string vulnerability'),
                    (r'sprintf\s*\([^,)]*[^"'][^)]*\)', 'Possible format string vulnerability'),
                    (r'snprintf\s*\([^,)]*[^"'][^)]*\)', 'Possible format string vulnerability'),
                ]
            }

            for vuln_type, pattern_list in c_patterns.items():
                for pattern, description in pattern_list:
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            vuln = self._create_vulnerability(
                                file_path=file_path,
                                line_number=line_num,
                                vulnerability_type=vuln_type,
                                title=f"{vuln_type.replace('_', ' ').title()}",
                                description=description,
                                code_snippet=line.strip(),
                                language=CodeLanguage.C,
                                pattern=pattern
                            )
                            vulnerabilities.append(vuln)

        except Exception as e:
            logger.warning(f"Failed to analyze C file {file_path}: {e}")

        return vulnerabilities

    def _analyze_cpp(self, file_path: Path) -> List[CodeVulnerability]:
        """Analyze C++ file for security vulnerabilities"""
        # C++ analysis similar to C with additional patterns
        vulnerabilities = self._analyze_c(file_path)

        # Add C++ specific patterns
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')

            cpp_patterns = {
                'unsafe_casting': [
                    (r'reinterpret_cast\s*<[^>]*>\s*\([^)]+\)', 'Use of unsafe reinterpret_cast'),
                    (r'const_cast\s*<[^>]*>\s*\([^)]+\)', 'Use of const_cast'),
                    (r'C-style cast:\s*\([^)]+\)', 'Use of unsafe C-style cast'),
                ],
                'exception_handling': [
                    (r'throw\s+[^;]+', 'Exception thrown without proper handling'),
                    (r'catch\s*\(\s*\.\.\.\s*\)', 'Catch-all exception handler'),
                ]
            }

            for vuln_type, pattern_list in cpp_patterns.items():
                for pattern, description in pattern_list:
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            vuln = self._create_vulnerability(
                                file_path=file_path,
                                line_number=line_num,
                                vulnerability_type=vuln_type,
                                title=f"{vuln_type.replace('_', ' ').title()}",
                                description=description,
                                code_snippet=line.strip(),
                                language=CodeLanguage.CPP,
                                pattern=pattern
                            )
                            vulnerabilities.append(vuln)

        except Exception as e:
            logger.warning(f"Failed to analyze C++ file {file_path}: {e}")

        return vulnerabilities

    def _analyze_csharp(self, file_path: Path) -> List[CodeVulnerability]:
        """Analyze C# file for security vulnerabilities"""
        vulnerabilities = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')

            # C# specific patterns
            csharp_patterns = {
                'sql_injection': [
                    (r'ExecuteNonQuery\s*\([^)]*\+[^)]*\)', 'String concatenation in SQL query'),
                    (r'ExecuteReader\s*\([^)]*\+[^)]*\)', 'String concatenation in SQL query'),
                    (r'ExecuteScalar\s*\([^)]*\+[^)]*\)', 'String concatenation in SQL query'),
                ],
                'deserialization': [
                    (r'BinaryFormatter\.Deserialize\s*\(', 'Use of unsafe BinaryFormatter'),
                    (r'SoapFormatter\.Deserialize\s*\(', 'Use of unsafe SoapFormatter'),
                    (r'NetDataContractSerializer\.ReadObject\s*\(', 'Use of unsafe NetDataContractSerializer'),
                ],
                'hardcoded_secrets': [
                    (r'password\s*=\s*"[^"]{8,}"', 'Hardcoded password'),
                    (r'connectionString\s*=\s*"[^"]*password[^"]*"', 'Password in connection string'),
                ]
            }

            for vuln_type, pattern_list in csharp_patterns.items():
                for pattern, description in pattern_list:
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            vuln = self._create_vulnerability(
                                file_path=file_path,
                                line_number=line_num,
                                vulnerability_type=vuln_type,
                                title=f"{vuln_type.replace('_', ' ').title()}",
                                description=description,
                                code_snippet=line.strip(),
                                language=CodeLanguage.CSHARP,
                                pattern=pattern
                            )
                            vulnerabilities.append(vuln)

        except Exception as e:
            logger.warning(f"Failed to analyze C# file {file_path}: {e}")

        return vulnerabilities

    def _analyze_go(self, file_path: Path) -> List[CodeVulnerability]:
        """Analyze Go file for security vulnerabilities"""
        vulnerabilities = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')

            # Go specific patterns
            go_patterns = {
                'sql_injection': [
                    (r'Exec\s*\([^)]*\+[^)]*\)', 'String concatenation in SQL query'),
                    (r'Query\s*\([^)]*\+[^)]*\)', 'String concatenation in SQL query'),
                    (r'QueryRow\s*\([^)]*\+[^)]*\)', 'String concatenation in SQL query'),
                ],
                'command_injection': [
                    (r'exec\.Command\s*\([^)]*\+[^)]*\)', 'Command execution with string concatenation'),
                    (r'os\.Exec\s*\([^)]*\+[^)]*\)', 'Command execution with string concatenation'),
                ],
                'path_traversal': [
                    (r'ioutil\.WriteFile\s*\([^)]*\.\.[^)]*\)', 'Potential path traversal'),
                    (r'os\.Open\s*\([^)]*\.\.[^)]*\)', 'Potential path traversal'),
                ],
                'hardcoded_secrets': [
                    (r'password\s*:=\s*"[^"]{8,}"', 'Hardcoded password'),
                    (r'apiKey\s*:=\s*"[^"]{16,}"', 'Hardcoded API key'),
                ]
            }

            for vuln_type, pattern_list in go_patterns.items():
                for pattern, description in pattern_list:
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            vuln = self._create_vulnerability(
                                file_path=file_path,
                                line_number=line_num,
                                vulnerability_type=vuln_type,
                                title=f"{vuln_type.replace('_', ' ').title()}",
                                description=description,
                                code_snippet=line.strip(),
                                language=CodeLanguage.GO,
                                pattern=pattern
                            )
                            vulnerabilities.append(vuln)

        except Exception as e:
            logger.warning(f"Failed to analyze Go file {file_path}: {e}")

        return vulnerabilities

    def _analyze_ruby(self, file_path: Path) -> List[CodeVulnerability]:
        """Analyze Ruby file for security vulnerabilities"""
        vulnerabilities = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')

            # Ruby specific patterns
            ruby_patterns = {
                'sql_injection': [
                    (r'execute\s*\([^)]*\#\{[^}]*\}[^)]*\)', 'String interpolation in SQL query'),
                    (r'execute\s*\([^)]*\+[^)]*\)', 'String concatenation in SQL query'),
                ],
                'command_injection': [
                    (r'system\s*\([^)]*\#\{[^}]*\}[^)]*\)', 'Command injection with string interpolation'),
                    (r'exec\s*\([^)]*\#\{[^}]*\}[^)]*\)', 'Command injection with string interpolation'),
                    (r'`\#\{[^}]*\}`', 'Command injection with backticks'),
                ],
                'xss': [
                    (r'html_safe', 'Potential XSS with html_safe'),
                    (r'raw\s*\(', 'Potential XSS with raw()'),
                ],
                'deserialization': [
                    (r'Marshal\.load\s*\(', 'Use of unsafe Marshal.load'),
                    (r'YAML\.load\s*\(', 'Use of unsafe YAML.load'),
                ]
            }

            for vuln_type, pattern_list in ruby_patterns.items():
                for pattern, description in pattern_list:
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            vuln = self._create_vulnerability(
                                file_path=file_path,
                                line_number=line_num,
                                vulnerability_type=vuln_type,
                                title=f"{vuln_type.replace('_', ' ').title()}",
                                description=description,
                                code_snippet=line.strip(),
                                language=CodeLanguage.RUBY,
                                pattern=pattern
                            )
                            vulnerabilities.append(vuln)

        except Exception as e:
            logger.warning(f"Failed to analyze Ruby file {file_path}: {e}")

        return vulnerabilities

    def _create_vulnerability(self, file_path: Path, line_number: int, vulnerability_type: str,
                            title: str, description: str, code_snippet: str, language: CodeLanguage,
                            pattern: str, column_number: int = None, confidence: str = 'MEDIUM') -> CodeVulnerability:
        """Create a vulnerability object"""
        vulnerability_id = f"{language.value}_{vulnerability_type}_{hashlib.md5(f'{file_path}:{line_number}'.encode()).hexdigest()[:8]}"

        # Map vulnerability type to enum
        vuln_type_map = {
            'SQL_INJECTION': VulnerabilityType.SQL_INJECTION,
            'XSS': VulnerabilityType.XSS,
            'PATH_TRAVERSAL': VulnerabilityType.PATH_TRAVERSAL,
            'COMMAND_INJECTION': VulnerabilityType.COMMAND_INJECTION,
            'INSECURE_DESERIALIZATION': VulnerabilityType.INSECURE_DESERIALIZATION,
            'HARDCODED_SECRETS': VulnerabilityType.HARDCODED_CREDENTIALS,
            'WEAK_CRYPTOGRAPHY': VulnerabilityType.WEAK_CRYPTOGRAPHY,
            'BUFFER_OVERFLOW': VulnerabilityType.BUFFER_OVERFLOW,
            'INSECURE_RANDOM': VulnerabilityType.INSECURE_RANDOM,
            'INFORMATION_DISCLOSURE': VulnerabilityType.INFORMATION_DISCLOSURE,
            'INSECURE_FILE_HANDLING': VulnerabilityType.INSECURE_FILE_HANDLING,
            'FILE_INCLUSION': VulnerabilityType.INSECURE_FILE_HANDLING,
            'MEMORY_LEAKS': VulnerabilityType.MEMORY_LEAK,
            'UNSAFE_CASTING': VulnerabilityType.UNSAFE_TYPE_CASTING,
            'FORMAT_STRING': VulnerabilityType.COMMAND_INJECTION,
        }

        vuln_type = vuln_type_map.get(vulnerability_type, VulnerabilityType.INFORMATION_DISCLOSURE)

        # Determine severity
        severity = self._determine_severity(vuln_type, confidence)

        # Get CWE ID and OWASP category
        cwe_id = self._get_cwe_id(vuln_type)
        owasp_category = self._get_owasp_category(vuln_type)

        # Generate remediation
        remediation = self._generate_remediation(vuln_type, language)

        # Get references
        references = self._get_references(vuln_type)

        return CodeVulnerability(
            id=vulnerability_id,
            title=title,
            description=description,
            vulnerability_type=vuln_type,
            severity=severity,
            file_path=str(file_path),
            line_number=line_number,
            column_number=column_number or 1,
            code_snippet=code_snippet,
            language=language,
            confidence=confidence,
            cwe_id=cwe_id,
            owasp_category=owasp_category,
            remediation=remediation,
            references=references,
            context={
                'pattern': pattern,
                'file_extension': file_path.suffix,
                'scan_version': self.scanner_version
            }
        )

    def _determine_severity(self, vuln_type: VulnerabilityType, confidence: str) -> str:
        """Determine vulnerability severity based on type and confidence"""
        severity_map = {
            VulnerabilityType.SQL_INJECTION: 'HIGH',
            VulnerabilityType.XSS: 'HIGH',
            VulnerabilityType.COMMAND_INJECTION: 'CRITICAL',
            VulnerabilityType.HARDCODED_CREDENTIALS: 'CRITICAL',
            VulnerabilityType.PATH_TRAVERSAL: 'HIGH',
            VulnerabilityType.INSECURE_DESERIALIZATION: 'HIGH',
            VulnerabilityType.WEAK_CRYPTOGRAPHY: 'MEDIUM',
            VulnerabilityType.BUFFER_OVERFLOW: 'HIGH',
            VulnerabilityType.INSECURE_RANDOM: 'MEDIUM',
            VulnerabilityType.INFORMATION_DISCLOSURE: 'LOW',
            VulnerabilityType.INSECURE_FILE_HANDLING: 'MEDIUM',
            VulnerabilityType.UNSAFE_TYPE_CASTING: 'MEDIUM',
            VulnerabilityType.MEMORY_LEAK: 'LOW',
        }

        base_severity = severity_map.get(vuln_type, 'MEDIUM')

        # Adjust based on confidence
        if confidence == 'LOW' and base_severity == 'CRITICAL':
            return 'HIGH'
        elif confidence == 'LOW' and base_severity == 'HIGH':
            return 'MEDIUM'

        return base_severity

    def _get_cwe_id(self, vuln_type: VulnerabilityType) -> Optional[str]:
        """Get CWE ID for vulnerability type"""
        cwe_map = {
            VulnerabilityType.SQL_INJECTION: 'CWE-89',
            VulnerabilityType.XSS: 'CWE-79',
            VulnerabilityType.COMMAND_INJECTION: 'CWE-78',
            VulnerabilityType.HARDCODED_CREDENTIALS: 'CWE-798',
            VulnerabilityType.PATH_TRAVERSAL: 'CWE-22',
            VulnerabilityType.INSECURE_DESERIALIZATION: 'CWE-502',
            VulnerabilityType.WEAK_CRYPTOGRAPHY: 'CWE-327',
            VulnerabilityType.BUFFER_OVERFLOW: 'CWE-120',
            VulnerabilityType.INSECURE_RANDOM: 'CWE-338',
            VulnerabilityType.INFORMATION_DISCLOSURE: 'CWE-200',
            VulnerabilityType.INSECURE_FILE_HANDLING: 'CWE-20',
            VulnerabilityType.UNSAFE_TYPE_CASTING: 'CWE-843',
            VulnerabilityType.MEMORY_LEAK: 'CWE-401',
        }

        return cwe_map.get(vuln_type)

    def _get_owasp_category(self, vuln_type: VulnerabilityType) -> Optional[str]:
        """Get OWASP category for vulnerability type"""
        owasp_map = {
            VulnerabilityType.SQL_INJECTION: 'A03:2021 – Injection',
            VulnerabilityType.XSS: 'A03:2021 – Injection',
            VulnerabilityType.COMMAND_INJECTION: 'A03:2021 – Injection',
            VulnerabilityType.HARDCODED_CREDENTIALS: 'A02:2021 – Cryptographic Failures',
            VulnerabilityType.PATH_TRAVERSAL: 'A01:2021 – Broken Access Control',
            VulnerabilityType.INSECURE_DESERIALIZATION: 'A08:2021 – Software and Data Integrity Failures',
            VulnerabilityType.WEAK_CRYPTOGRAPHY: 'A02:2021 – Cryptographic Failures',
            VulnerabilityType.BUFFER_OVERFLOW: 'A03:2021 – Injection',
            VulnerabilityType.INSECURE_RANDOM: 'A02:2021 – Cryptographic Failures',
            VulnerabilityType.INFORMATION_DISCLOSURE: 'A04:2021 – Insecure Design',
            VulnerabilityType.INSECURE_FILE_HANDLING: 'A01:2021 – Broken Access Control',
        }

        return owasp_map.get(vuln_type)

    def _generate_remediation(self, vuln_type: VulnerabilityType, language: CodeLanguage) -> str:
        """Generate remediation advice for vulnerability"""
        remediation_map = {
            VulnerabilityType.SQL_INJECTION: {
                CodeLanguage.PYTHON: "Use parameterized queries or prepared statements with proper escaping",
                CodeLanguage.JAVASCRIPT: "Use parameterized queries or ORM with built-in protection",
                CodeLanguage.JAVA: "Use PreparedStatement with parameter binding",
                CodeLanguage.PHP: "Use prepared statements or parameterized queries",
                CodeLanguage.GO: "Use prepared statements with proper parameter binding",
                CodeLanguage.RUBY: "Use ActiveRecord or parameterized queries",
            },
            VulnerabilityType.XSS: {
                CodeLanguage.JAVASCRIPT: "Use textContent instead of innerHTML, implement proper output encoding",
                CodeLanguage.PYTHON: "Use proper template engines with auto-escaping",
                CodeLanguage.PHP: "Use htmlspecialchars() or proper template frameworks",
                CodeLanguage.RUBY: "Use proper output encoding in Rails templates",
            },
            VulnerabilityType.COMMAND_INJECTION: {
                CodeLanguage.PYTHON: "Avoid shell=True in subprocess, use parameterized calls",
                CodeLanguage.JAVASCRIPT: "Avoid exec() with user input, validate and sanitize inputs",
                CodeLanguage.JAVA: "Use ProcessBuilder with proper argument separation",
                CodeLanguage.PHP: "Avoid exec(), system(), shell_exec() with user input",
                CodeLanguage.GO: "Use exec.Command with separate arguments",
                CodeLanguage.RUBY: "Avoid system() and backticks with user input",
            },
            VulnerabilityType.HARDCODED_CREDENTIALS: {
                CodeLanguage.PYTHON: "Store credentials in environment variables or secure vaults",
                CodeLanguage.JAVASCRIPT: "Use environment variables or secret management services",
                CodeLanguage.JAVA: "Use external configuration or secret management",
                CodeLanguage.PHP: "Use environment variables or secure configuration",
                CodeLanguage.GO: "Use environment variables or secret management",
                CodeLanguage.RUBY: "Use credentials.yml.enc or environment variables",
            },
            VulnerabilityType.WEAK_CRYPTOGRAPHY: {
                CodeLanguage.PYTHON: "Use strong algorithms like AES-256, SHA-256, bcrypt",
                CodeLanguage.JAVASCRIPT: "Use strong crypto libraries and algorithms",
                CodeLanguage.JAVA: "Use AES-256, SHA-256, PBKDF2 for password hashing",
                CodeLanguage.PHP: "Use password_hash() with PASSWORD_DEFAULT",
                CodeLanguage.GO: "Use crypto package with strong algorithms",
                CodeLanguage.RUBY: "Use bcrypt for passwords, AES-256 for encryption",
            }
        }

        language_remediations = remediation_map.get(vuln_type, {})
        return language_remediations.get(language, "Review and implement proper security controls for this vulnerability type")

    def _get_references(self, vuln_type: VulnerabilityType) -> List[str]:
        """Get reference links for vulnerability type"""
        reference_map = {
            VulnerabilityType.SQL_INJECTION: [
                "https://owasp.org/www-community/attacks/SQL_Injection",
                "https://cwe.mitre.org/data/definitions/89.html"
            ],
            VulnerabilityType.XSS: [
                "https://owasp.org/www-community/attacks/xss/",
                "https://cwe.mitre.org/data/definitions/79.html"
            ],
            VulnerabilityType.COMMAND_INJECTION: [
                "https://owasp.org/www-project-cheat-sheets/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html",
                "https://cwe.mitre.org/data/definitions/78.html"
            ],
            VulnerabilityType.HARDCODED_CREDENTIALS: [
                "https://owasp.org/www-project-cheat-sheets/cheatsheets/Secrets_Management_Cheat_Sheet.html",
                "https://cwe.mitre.org/data/definitions/798.html"
            ],
            VulnerabilityType.WEAK_CRYPTOGRAPHY: [
                "https://owasp.org/www-project-cheat-sheets/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html",
                "https://cwe.mitre.org/data/definitions/327.html"
            ]
        }

        return reference_map.get(vuln_type, ["https://owasp.org/"])

    def _calculate_metrics(self, vulnerabilities: List[CodeVulnerability], files: List[Path]) -> Dict[str, Any]:
        """Calculate code security metrics"""
        metrics = {
            'total_vulnerabilities': len(vulnerabilities),
            'files_analyzed': len(files),
            'vulnerabilities_per_file': len(vulnerabilities) / len(files) if files else 0,
            'severity_distribution': {
                'CRITICAL': 0,
                'HIGH': 0,
                'MEDIUM': 0,
                'LOW': 0
            },
            'type_distribution': {},
            'top_vulnerability_files': {},
            'security_score': 0.0
        }

        # Count by severity
        for vuln in vulnerabilities:
            metrics['severity_distribution'][vuln.severity] += 1

        # Count by type
        for vuln in vulnerabilities:
            vuln_type = vuln.vulnerability_type.value
            metrics['type_distribution'][vuln_type] = metrics['type_distribution'].get(vuln_type, 0) + 1

        # Top vulnerability files
        file_vuln_counts = {}
        for vuln in vulnerabilities:
            file_path = vuln.file_path
            file_vuln_counts[file_path] = file_vuln_counts.get(file_path, 0) + 1

        metrics['top_vulnerability_files'] = dict(
            sorted(file_vuln_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        )

        # Calculate security score (0-100, higher is better)
        total_files = len(files)
        critical_vulns = metrics['severity_distribution']['CRITICAL']
        high_vulns = metrics['severity_distribution']['HIGH']
        medium_vulns = metrics['severity_distribution']['MEDIUM']
        low_vulns = metrics['severity_distribution']['LOW']

        # Weighted score calculation
        score = 100
        score -= (critical_vulns * 25)  # Critical: -25 points each
        score -= (high_vulns * 15)      # High: -15 points each
        score -= (medium_vulns * 8)     # Medium: -8 points each
        score -= (low_vulns * 3)        # Low: -3 points each

        # Penalty for high vulnerability density
        vuln_density = len(vulnerabilities) / total_files if total_files > 0 else 0
        if vuln_density > 5:
            score -= 20
        elif vuln_density > 2:
            score -= 10

        metrics['security_score'] = max(0, score)

        return metrics

    def _generate_scan_id(self) -> str:
        """Generate unique scan ID"""
        return f"code_scan_{int(time.time())}_{hashlib.md5(os.urandom(16)).hexdigest()[:8]}"

    def _record_scan_start(self, result: AnalysisResult):
        """Record scan start in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO code_scans
            (scan_id, target_path, language, started_at, total_files, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            result.scan_id,
            result.target_path,
            result.language.value,
            result.started_at,
            result.total_files,
            result.status
        ))

        conn.commit()
        conn.close()

    def _store_analysis_results(self, result: AnalysisResult):
        """Store analysis results in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Update scan record
        cursor.execute('''
            UPDATE code_scans
            SET completed_at = ?, analyzed_files = ?, vulnerabilities_count = ?, status = ?
            WHERE scan_id = ?
        ''', (
            result.completed_at,
            result.analyzed_files,
            len(result.vulnerabilities),
            result.status,
            result.scan_id
        ))

        # Store vulnerabilities
        for vuln in result.vulnerabilities:
            cursor.execute('''
                INSERT INTO code_vulnerabilities
                (id, title, description, vulnerability_type, severity, file_path,
                 line_number, column_number, code_snippet, language, confidence,
                 cwe_id, owasp_category, remediation, references, context, scan_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                vuln.id,
                vuln.title,
                vuln.description,
                vuln.vulnerability_type.value,
                vuln.severity,
                vuln.file_path,
                vuln.line_number,
                vuln.column_number,
                vuln.code_snippet,
                vuln.language.value,
                vuln.confidence,
                vuln.cwe_id,
                vuln.owasp_category,
                vuln.remediation,
                json.dumps(vuln.references),
                json.dumps(vuln.context),
                result.scan_id
            ))

        conn.commit()
        conn.close()

    async def generate_analysis_report(self, scan_id: str, format: str = 'json') -> Dict:
        """Generate code analysis report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get scan details
        cursor.execute('''
            SELECT * FROM code_scans WHERE scan_id = ?
        ''', (scan_id,))

        scan_row = cursor.fetchone()
        if not scan_row:
            conn.close()
            return {'error': 'Scan not found'}

        # Get vulnerabilities for this scan
        cursor.execute('''
            SELECT * FROM code_vulnerabilities WHERE scan_id = ?
            ORDER BY severity DESC, line_number
        ''', (scan_id,))

        vuln_rows = cursor.fetchall()
        conn.close()

        # Format report
        report = {
            'scan_id': scan_id,
            'target_path': scan_row[1],
            'language': scan_row[2],
            'started_at': scan_row[3],
            'completed_at': scan_row[4],
            'total_files': scan_row[5],
            'analyzed_files': scan_row[6],
            'total_vulnerabilities': len(vuln_rows),
            'vulnerabilities': []
        }

        for row in vuln_rows:
            vuln = {
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'vulnerability_type': row[3],
                'severity': row[4],
                'file_path': row[5],
                'line_number': row[6],
                'column_number': row[7],
                'code_snippet': row[8],
                'language': row[9],
                'confidence': row[10],
                'cwe_id': row[11],
                'owasp_category': row[12],
                'remediation': row[13],
                'references': json.loads(row[14]) if row[14] else [],
                'context': json.loads(row[15]) if row[15] else {}
            }
            report['vulnerabilities'].append(vuln)

        # Generate summary statistics
        report['summary'] = self._generate_analysis_summary(report['vulnerabilities'])

        return report

    def _generate_analysis_summary(self, vulnerabilities: List[Dict]) -> Dict:
        """Generate analysis summary statistics"""
        summary = {
            'severity_breakdown': {
                'CRITICAL': 0,
                'HIGH': 0,
                'MEDIUM': 0,
                'LOW': 0
            },
            'type_breakdown': {},
            'confidence_breakdown': {
                'HIGH': 0,
                'MEDIUM': 0,
                'LOW': 0
            },
            'cwe_breakdown': {},
            'files_with_vulnerabilities': set(),
            'top_vulnerability_types': {},
            'remediation_priority': []
        }

        for vuln in vulnerabilities:
            # Count by severity
            severity = vuln['severity']
            summary['severity_breakdown'][severity] += 1

            # Count by type
            vuln_type = vuln['vulnerability_type']
            summary['type_breakdown'][vuln_type] = summary['type_breakdown'].get(vuln_type, 0) + 1

            # Count by confidence
            confidence = vuln['confidence']
            summary['confidence_breakdown'][confidence] += 1

            # Count by CWE
            cwe = vuln.get('cwe_id', 'Unknown')
            summary['cwe_breakdown'][cwe] = summary['cwe_breakdown'].get(cwe, 0) + 1

            # Track files with vulnerabilities
            summary['files_with_vulnerabilities'].add(vuln['file_path'])

        # Convert set to count
        summary['files_with_vulnerabilities'] = len(summary['files_with_vulnerabilities'])

        # Top vulnerability types
        summary['top_vulnerability_types'] = dict(
            sorted(summary['type_breakdown'].items(), key=lambda x: x[1], reverse=True)[:10]
        )

        # Generate remediation priority (Critical first, then High)
        critical_vulns = [v for v in vulnerabilities if v['severity'] == 'CRITICAL']
        high_vulns = [v for v in vulnerabilities if v['severity'] == 'HIGH']
        medium_vulns = [v for v in vulnerabilities if v['severity'] == 'MEDIUM']

        summary['remediation_priority'] = {
            'critical': len(critical_vulns),
            'high': len(high_vulns),
            'medium': len(medium_vulns),
            'total': len(vulnerabilities)
        }

        return summary

async def main():
    """Main function for running code analyzer"""
    analyzer = CodeAnalyzer()

    # Example usage
    target_path = "/home/activeloguser/DMLogn8n"

    logger.info("Starting code security analysis...")
    results = await analyzer.analyze_codebase(target_path)

    # Generate and save reports
    for result in results:
        if result:
            report = await analyzer.generate_analysis_report(result.scan_id)

            # Save report to file
            report_path = f"/home/activeloguser/DMLogn8n/security/reports/code_analysis_report_{result.scan_id}.json"
            os.makedirs(os.path.dirname(report_path), exist_ok=True)

            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"Code analysis completed for {result.language.value}. Report saved to: {report_path}")
            logger.info(f"Found {len(result.vulnerabilities)} vulnerabilities in {result.analyzed_files} files")

            # Print summary
            print(f"\n=== {result.language.value.upper()} CODE ANALYSIS SUMMARY ===")
            print(f"Files analyzed: {result.analyzed_files}")
            print(f"Total vulnerabilities: {len(result.vulnerabilities)}")
            print(f"Security score: {result.metrics.get('security_score', 0):.1f}/100")

            severity_counts = report['summary']['severity_breakdown']
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                count = severity_counts.get(severity, 0)
                if count > 0:
                    print(f"{severity}: {count}")

    return results

if __name__ == "__main__":
    asyncio.run(main())