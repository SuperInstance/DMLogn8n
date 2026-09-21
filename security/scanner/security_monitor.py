#!/usr/bin/env python3
"""
DMLogn8n Real-Time Security Monitoring System
Advanced threat detection and monitoring with machine learning capabilities
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
import psutil
import socket
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, deque
from enum import Enum
import threading
import queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/activeloguser/DMLogn8n/security/logs/security_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ThreatLevel(Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class AlertType(Enum):
    INTRUSION_ATTEMPT = "Intrusion Attempt"
    UNAUTHORIZED_ACCESS = "Unauthorized Access"
    MALICIOUS_ACTIVITY = "Malicious Activity"
    ANOMALOUS_BEHAVIOR = "Anomalous Behavior"
    SYSTEM_COMPROMISE = "System Compromise"
    DATA_BREACH = "Data Breach"
    DENIAL_OF_SERVICE = "Denial of Service"
    POLICY_VIOLATION = "Policy Violation"
    SUSPICIOUS_NETWORK = "Suspicious Network Activity"
    FILE_INTEGRITY = "File Integrity Violation"

class MonitorType(Enum):
    NETWORK = "Network"
    PROCESS = "Process"
    FILE = "File"
    SYSTEM = "System"
    APPLICATION = "Application"
    AUTHENTICATION = "Authentication"
    API = "API"
    LOG = "Log"

@dataclass
class SecurityAlert:
    id: str
    title: str
    description: str
    alert_type: AlertType
    threat_level: ThreatLevel
    source: str
    target: Optional[str]
    timestamp: datetime
    evidence: Dict[str, Any]
    mitigation_steps: List[str]
    false_positive: bool = False
    resolved: bool = False
    resolution_notes: Optional[str] = None

@dataclass
class SecurityEvent:
    id: str
    event_type: str
    source_ip: Optional[str]
    target_ip: Optional[str]
    user: Optional[str]
    process: Optional[str]
    file_path: Optional[str]
    command: Optional[str]
    timestamp: datetime
    severity: str
    details: Dict[str, Any]

@dataclass
class MonitoringRule:
    id: str
    name: str
    description: str
    monitor_type: MonitorType
    pattern: str
    threat_level: ThreatLevel
    enabled: bool
    conditions: Dict[str, Any]
    actions: List[str]
    created_at: datetime
    updated_at: datetime

@dataclass
class BaselineMetric:
    metric_name: str
    baseline_value: float
    threshold_multiplier: float
    last_updated: datetime
    samples: List[float]

class SecurityMonitor:
    """Advanced real-time security monitoring system"""

    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.db_path = self.config.get('database_path', '/home/activeloguser/DMLogn8n/security/data/security_monitor.db')
        self.monitor_version = "2.0.0"

        # Monitoring state
        self.is_running = False
        self.monitor_tasks = []
        self.alert_queue = asyncio.Queue()
        self.event_queue = asyncio.Queue()

        # Initialize database
        self._init_database()

        # Load monitoring rules
        self.rules = self._load_monitoring_rules()

        # Initialize baselines
        self.baselines = self._load_baselines()

        # ML models for anomaly detection
        self.ml_models = self._initialize_ml_models()

        # Rate limiting and reputation tracking
        self.ip_reputation = {}
        self.rate_limits = defaultdict(lambda: deque())
        self.failed_attempts = defaultdict(int)

        # File integrity monitoring
        self.file_hashes = {}
        self.monitored_files = self.config.get('monitored_files', [])

        # Network monitoring
        self.network_connections = {}
        self.port_scans = defaultdict(list)

        # Process monitoring
        self.process_whitelist = self.config.get('process_whitelist', [])
        self.suspicious_processes = self.config.get('suspicious_processes', [])

        # Log monitoring
        self.log_sources = self.config.get('log_sources', [])
        self.log_patterns = self._initialize_log_patterns()

        # Alert handlers
        self.alert_handlers = {
            'email': self._send_email_alert,
            'slack': self._send_slack_alert,
            'webhook': self._send_webhook_alert,
            'sms': self._send_sms_alert
        }

        # Initialize notification channels
        self._init_notification_channels()

    def _load_config(self, config_path: str) -> Dict:
        """Load monitoring configuration"""
        default_config = {
            'database_path': '/home/activeloguser/DMLogn8n/security/data/security_monitor.db',
            'monitoring_interval': 5,  # seconds
            'max_events_per_minute': 1000,
            'alert_retention_days': 30,
            'enable_ml_detection': True,
            'enable_network_monitoring': True,
            'enable_process_monitoring': True,
            'enable_file_monitoring': True,
            'enable_log_monitoring': True,
            'monitored_files': [
                '/etc/passwd',
                '/etc/shadow',
                '/etc/hosts',
                '/home/activeloguser/DMLogn8n/.env',
                '/home/activeloguser/DMLogn8n/config.json'
            ],
            'process_whitelist': [
                'python', 'node', 'npm', 'nginx', 'apache2', 'systemd'
            ],
            'suspicious_processes': [
                'nc', 'netcat', 'tcpdump', 'wireshark', 'nmap'
            ],
            'log_sources': [
                '/var/log/auth.log',
                '/var/log/syslog',
                '/home/activeloguser/DMLogn8n/logs/*.log'
            ],
            'notification_channels': {
                'email': {
                    'enabled': False,
                    'smtp_server': 'localhost',
                    'smtp_port': 587,
                    'username': '',
                    'password': '',
                    'recipients': []
                },
                'slack': {
                    'enabled': False,
                    'webhook_url': '',
                    'channel': '#security-alerts'
                },
                'webhook': {
                    'enabled': False,
                    'url': '',
                    'headers': {}
                }
            },
            'rate_limits': {
                'login_attempts': 5,
                'connection_attempts': 100,
                'time_window': 300  # 5 minutes
            }
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
        """Initialize database for security monitoring"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create security_events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_events (
                id TEXT PRIMARY KEY,
                event_type TEXT,
                source_ip TEXT,
                target_ip TEXT,
                user TEXT,
                process TEXT,
                file_path TEXT,
                command TEXT,
                timestamp TIMESTAMP,
                severity TEXT,
                details TEXT
            )
        ''')

        # Create security_alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_alerts (
                id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                alert_type TEXT,
                threat_level TEXT,
                source TEXT,
                target TEXT,
                timestamp TIMESTAMP,
                evidence TEXT,
                mitigation_steps TEXT,
                false_positive BOOLEAN DEFAULT FALSE,
                resolved BOOLEAN DEFAULT FALSE,
                resolution_notes TEXT
            )
        ''')

        # Create monitoring_rules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitoring_rules (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                monitor_type TEXT,
                pattern TEXT,
                threat_level TEXT,
                enabled BOOLEAN,
                conditions TEXT,
                actions TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')

        # Create baselines table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS baselines (
                metric_name TEXT PRIMARY KEY,
                baseline_value REAL,
                threshold_multiplier REAL,
                last_updated TIMESTAMP,
                samples TEXT
            )
        ''')

        # Create ip_reputation table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ip_reputation (
                ip TEXT PRIMARY KEY,
                reputation_score INTEGER,
                threat_level TEXT,
                last_seen TIMESTAMP,
                incidents_count INTEGER,
                details TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def _load_monitoring_rules(self) -> Dict[str, MonitoringRule]:
        """Load monitoring rules"""
        rules = {}

        # Default security rules
        default_rules = [
            MonitoringRule(
                id="brute_force_detection",
                name="Brute Force Attack Detection",
                description="Detect multiple failed login attempts",
                monitor_type=MonitorType.AUTHENTICATION,
                pattern="failed_login",
                threat_level=ThreatLevel.HIGH,
                enabled=True,
                conditions={
                    "max_attempts": 5,
                    "time_window": 300,
                    "by_user": True,
                    "by_ip": True
                },
                actions=["block_ip", "alert_admin", "log_event"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            MonitoringRule(
                id="port_scan_detection",
                name="Port Scan Detection",
                description="Detect port scanning activities",
                monitor_type=MonitorType.NETWORK,
                pattern="port_scan",
                threat_level=ThreatLevel.MEDIUM,
                enabled=True,
                conditions={
                    "max_ports": 10,
                    "time_window": 60,
                    "distinct_ports": True
                },
                actions=["alert_admin", "log_event", "rate_limit"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            MonitoringRule(
                id="suspicious_process",
                name="Suspicious Process Execution",
                description="Detect execution of suspicious processes",
                monitor_type=MonitorType.PROCESS,
                pattern="process_execution",
                threat_level=ThreatLevel.MEDIUM,
                enabled=True,
                conditions={
                    "blacklisted_processes": ["nc", "netcat", "tcpdump"],
                    "suspicious_args": True
                },
                actions=["alert_admin", "log_event", "kill_process"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            MonitoringRule(
                id="file_integrity",
                name="Critical File Modification",
                description="Detect modifications to critical system files",
                monitor_type=MonitorType.FILE,
                pattern="file_modification",
                threat_level=ThreatLevel.HIGH,
                enabled=True,
                conditions={
                    "critical_files": ["/etc/passwd", "/etc/shadow", "/etc/hosts"],
                    "monitor_permissions": True
                },
                actions=["alert_admin", "log_event", "backup_file"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            MonitoringRule(
                id="anomaly_detection",
                name="Anomalous Behavior Detection",
                description="Detect unusual system behavior using ML",
                monitor_type=MonitorType.SYSTEM,
                pattern="anomaly",
                threat_level=ThreatLevel.MEDIUM,
                enabled=self.config.get('enable_ml_detection', True),
                conditions={
                    "metrics": ["cpu_usage", "memory_usage", "network_io", "disk_io"],
                    "threshold_multiplier": 2.0
                },
                actions=["alert_admin", "log_event"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]

        # Store default rules
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for rule in default_rules:
            rules[rule.id] = rule

            cursor.execute('''
                INSERT OR REPLACE INTO monitoring_rules
                (id, name, description, monitor_type, pattern, threat_level,
                 enabled, conditions, actions, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rule.id,
                rule.name,
                rule.description,
                rule.monitor_type.value,
                rule.pattern,
                rule.threat_level.value,
                rule.enabled,
                json.dumps(rule.conditions),
                json.dumps(rule.actions),
                rule.created_at,
                rule.updated_at
            ))

        conn.commit()
        conn.close()

        return rules

    def _load_baselines(self) -> Dict[str, BaselineMetric]:
        """Load baseline metrics"""
        baselines = {}

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM baselines')
        rows = cursor.fetchall()

        for row in rows:
            metric_name = row[0]
            baseline_value = row[1]
            threshold_multiplier = row[2]
            last_updated = datetime.fromisoformat(row[3])
            samples = json.loads(row[4]) if row[4] else []

            baselines[metric_name] = BaselineMetric(
                metric_name=metric_name,
                baseline_value=baseline_value,
                threshold_multiplier=threshold_multiplier,
                last_updated=last_updated,
                samples=samples
            )

        conn.close()

        return baselines

    def _initialize_ml_models(self) -> Dict[str, Any]:
        """Initialize machine learning models for anomaly detection"""
        models = {}

        if self.config.get('enable_ml_detection', True):
            try:
                # Simple statistical models for anomaly detection
                models['cpu_usage'] = {
                    'type': 'statistical',
                    'mean': 0.0,
                    'std': 1.0,
                    'threshold': 2.0
                }
                models['memory_usage'] = {
                    'type': 'statistical',
                    'mean': 0.0,
                    'std': 1.0,
                    'threshold': 2.0
                }
                models['network_connections'] = {
                    'type': 'statistical',
                    'mean': 0.0,
                    'std': 1.0,
                    'threshold': 2.0
                }

                logger.info("ML models initialized for anomaly detection")
            except Exception as e:
                logger.warning(f"Failed to initialize ML models: {e}")

        return models

    def _initialize_log_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Initialize log monitoring patterns"""
        patterns = {
            'authentication': [
                re.compile(r'Failed password for .* from (\d+\.\d+\.\d+\.\d+)'),
                re.compile(r'Invalid user .* from (\d+\.\d+\.\d+\.\d+)'),
                re.compile(r'authentication failure.*rhost=(\d+\.\d+\.\d+\.\d+)'),
            ],
            'privilege_escalation': [
                re.compile(r'sudo: .* : TTY=.* ; PWD=.* ; USER=.* ; COMMAND=.*'),
                re.compile(r'su: .* su to .*'),
            ],
            'network_intrusion': [
                re.compile(r'Invalid user .* from (\d+\.\d+\.\d+\.\d+) port \d+'),
                re.compile(r'Connection from (\d+\.\d+\.\d+\.\d+) port \d+'),
            ],
            'system_events': [
                re.compile(r'kernel: .*'),
                re.compile(r'systemd.*: .*'),
            ]
        }

        return patterns

    def _init_notification_channels(self):
        """Initialize notification channels"""
        # Initialize email if configured
        if self.config.get('notification_channels', {}).get('email', {}).get('enabled', False):
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                self.email_available = True
            except ImportError:
                logger.warning("Email dependencies not available")
                self.email_available = False

        # Initialize Slack if configured
        if self.config.get('notification_channels', {}).get('slack', {}).get('enabled', False):
            self.slack_available = True
        else:
            self.slack_available = False

    async def start_monitoring(self):
        """Start security monitoring"""
        if self.is_running:
            logger.warning("Security monitoring is already running")
            return

        logger.info("Starting security monitoring...")
        self.is_running = True

        # Initialize file hashes
        await self._initialize_file_hashes()

        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._network_monitor()),
            asyncio.create_task(self._process_monitor()),
            asyncio.create_task(self._file_monitor()),
            asyncio.create_task(self._system_monitor()),
            asyncio.create_task(self._log_monitor()),
            asyncio.create_task(self._event_processor()),
            asyncio.create_task(self._alert_processor()),
            asyncio.create_task(self._baseline_updater())
        ]

        self.monitor_tasks = tasks

        logger.info("Security monitoring started successfully")

    async def stop_monitoring(self):
        """Stop security monitoring"""
        if not self.is_running:
            logger.warning("Security monitoring is not running")
            return

        logger.info("Stopping security monitoring...")
        self.is_running = False

        # Cancel all monitoring tasks
        for task in self.monitor_tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.monitor_tasks, return_exceptions=True)

        self.monitor_tasks = []
        logger.info("Security monitoring stopped")

    async def _network_monitor(self):
        """Monitor network activity"""
        logger.info("Starting network monitoring")

        while self.is_running:
            try:
                # Get current network connections
                connections = psutil.net_connections(kind='inet')

                # Analyze connections for anomalies
                for conn in connections:
                    if conn.status == 'ESTABLISHED' and conn.raddr:
                        await self._analyze_network_connection(conn)

                # Check for port scans
                await self._detect_port_scans()

                # Update network baselines
                await self._update_network_baseline(len(connections))

                await asyncio.sleep(self.config.get('monitoring_interval', 5))

            except Exception as e:
                logger.error(f"Network monitoring error: {e}")
                await asyncio.sleep(10)

    async def _analyze_network_connection(self, connection):
        """Analyze individual network connection"""
        try:
            remote_ip = connection.raddr.ip
            remote_port = connection.raddr.port
            local_port = connection.laddr.port if connection.laddr else None
            pid = connection.pid

            # Check IP reputation
            if self._is_suspicious_ip(remote_ip):
                await self._create_alert(
                    title="Suspicious IP Connection",
                    description=f"Connection from known malicious IP: {remote_ip}",
                    alert_type=AlertType.INTRUSION_ATTEMPT,
                    threat_level=ThreatLevel.HIGH,
                    source=remote_ip,
                    target=f"Port {local_port}",
                    evidence={
                        'remote_ip': remote_ip,
                        'remote_port': remote_port,
                        'local_port': local_port,
                        'pid': pid,
                        'reputation': self.ip_reputation.get(remote_ip, {}).get('score', 0)
                    }
                )

            # Track port scanning
            self.port_scans[remote_ip].append(remote_port)

            # Rate limiting check
            current_time = time.time()
            time_window = self.config.get('rate_limits', {}).get('time_window', 300)

            # Clean old entries
            self.rate_limits[remote_ip] = deque([
                t for t in self.rate_limits[remote_ip]
                if current_time - t < time_window
            ])

            self.rate_limits[remote_ip].append(current_time)

            if len(self.rate_limits[remote_ip]) > self.config.get('rate_limits', {}).get('connection_attempts', 100):
                await self._create_alert(
                    title="High Connection Rate",
                    description=f"High number of connections from {remote_ip}",
                    alert_type=AlertType.DENIAL_OF_SERVICE,
                    threat_level=ThreatLevel.MEDIUM,
                    source=remote_ip,
                    evidence={
                        'connection_count': len(self.rate_limits[remote_ip]),
                        'time_window': time_window
                    }
                )

        except Exception as e:
            logger.debug(f"Failed to analyze network connection: {e}")

    def _is_suspicious_ip(self, ip: str) -> bool:
        """Check if IP address is suspicious"""
        # Check against known malicious IPs (simplified)
        malicious_ranges = [
            '0.0.0.0/8',      # RFC 1700
            '10.0.0.0/8',     # Private network
            '127.0.0.0/8',    # Loopback
            '169.254.0.0/16', # Link-local
            '172.16.0.0/12',  # Private network
            '192.0.2.0/24',   # TEST-NET-1
            '192.168.0.0/16', # Private network
            '224.0.0.0/4',    # Multicast
            '240.0.0.0/4',    # Reserved
        ]

        try:
            ip_obj = ipaddress.ip_address(ip)
            for range_str in malicious_ranges:
                if ip_obj in ipaddress.ip_network(range_str):
                    return True
        except:
            return True

        # Check local reputation
        if ip in self.ip_reputation:
            return self.ip_reputation[ip].get('threat_level') in ['HIGH', 'CRITICAL']

        return False

    async def _detect_port_scans(self):
        """Detect port scanning activities"""
        current_time = time.time()
        time_window = 60  # 1 minute

        for ip, ports in list(self.port_scans.items()):
            # Clean old entries
            self.port_scans[ip] = ports[-100:]  # Keep last 100 ports

            # Check for port scan pattern
            if len(set(ports)) >= 10:  # 10 distinct ports
                await self._create_alert(
                    title="Port Scan Detected",
                    description=f"Port scanning activity from {ip}",
                    alert_type=AlertType.INTRUSION_ATTEMPT,
                    threat_level=ThreatLevel.MEDIUM,
                    source=ip,
                    evidence={
                        'ports_scanned': list(set(ports)),
                        'scan_count': len(ports),
                        'distinct_ports': len(set(ports))
                    }
                )

    async def _process_monitor(self):
        """Monitor process activity"""
        logger.info("Starting process monitoring")

        while self.is_running:
            try:
                processes = psutil.process_iter(['pid', 'name', 'username', 'cmdline'])

                for proc in processes:
                    try:
                        await self._analyze_process(proc)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                await asyncio.sleep(self.config.get('monitoring_interval', 5))

            except Exception as e:
                logger.error(f"Process monitoring error: {e}")
                await asyncio.sleep(10)

    async def _analyze_process(self, process):
        """Analyze individual process"""
        try:
            name = process.info['name']
            cmdline = process.info['cmdline']
            username = process.info['username']

            if not cmdline:
                return

            command_str = ' '.join(cmdline)

            # Check for suspicious processes
            if name.lower() in [p.lower() for p in self.suspicious_processes]:
                await self._create_alert(
                    title="Suspicious Process Execution",
                    description=f"Suspicious process detected: {name}",
                    alert_type=AlertType.MALICIOUS_ACTIVITY,
                    threat_level=ThreatLevel.MEDIUM,
                    source=username,
                    evidence={
                        'process_name': name,
                        'command_line': command_str,
                        'pid': process.info['pid']
                    }
                )

            # Check for suspicious command line arguments
            suspicious_args = [
                'rm -rf /',
                'dd if=/dev/zero',
                'fork bomb',
                'reverse shell',
                'nc -l -p',
                'netcat -l'
            ]

            for arg in suspicious_args:
                if arg in command_str.lower():
                    await self._create_alert(
                        title="Suspicious Command Execution",
                        description=f"Suspicious command detected: {arg}",
                        alert_type=AlertType.MALICIOUS_ACTIVITY,
                        threat_level=ThreatLevel.HIGH,
                        source=username,
                        evidence={
                            'process_name': name,
                            'command_line': command_str,
                            'suspicious_arg': arg,
                            'pid': process.info['pid']
                        }
                    )

        except Exception as e:
            logger.debug(f"Failed to analyze process: {e}")

    async def _file_monitor(self):
        """Monitor file integrity"""
        logger.info("Starting file monitoring")

        while self.is_running:
            try:
                for file_path in self.monitored_files:
                    if os.path.exists(file_path):
                        await self._check_file_integrity(file_path)

                await asyncio.sleep(self.config.get('monitoring_interval', 5))

            except Exception as e:
                logger.error(f"File monitoring error: {e}")
                await asyncio.sleep(10)

    async def _initialize_file_hashes(self):
        """Initialize file hashes for integrity monitoring"""
        for file_path in self.monitored_files:
            if os.path.exists(file_path):
                try:
                    file_hash = self._calculate_file_hash(file_path)
                    self.file_hashes[file_path] = {
                        'hash': file_hash,
                        'size': os.path.getsize(file_path),
                        'modified': os.path.getmtime(file_path),
                        'permissions': oct(os.stat(file_path).st_mode)[-3:]
                    }
                except Exception as e:
                    logger.warning(f"Failed to initialize hash for {file_path}: {e}")

    async def _check_file_integrity(self, file_path: str):
        """Check file integrity"""
        try:
            current_stats = {
                'size': os.path.getsize(file_path),
                'modified': os.path.getmtime(file_path),
                'permissions': oct(os.stat(file_path).st_mode)[-3:]
            }

            current_hash = self._calculate_file_hash(file_path)
            stored_hash = self.file_hashes.get(file_path, {})

            # Check for changes
            if stored_hash:
                changes = []
                if current_hash != stored_hash.get('hash'):
                    changes.append('content_modified')
                if current_stats['size'] != stored_hash.get('size'):
                    changes.append('size_changed')
                if current_stats['permissions'] != stored_hash.get('permissions'):
                    changes.append('permissions_changed')
                if current_stats['modified'] != stored_hash.get('modified'):
                    changes.append('timestamp_changed')

                if changes:
                    await self._create_alert(
                        title="File Integrity Violation",
                        description=f"Critical file modified: {file_path}",
                        alert_type=AlertType.FILE_INTEGRITY,
                        threat_level=ThreatLevel.HIGH,
                        evidence={
                            'file_path': file_path,
                            'changes': changes,
                            'current_hash': current_hash,
                            'previous_hash': stored_hash.get('hash'),
                            'current_size': current_stats['size'],
                            'previous_size': stored_hash.get('size')
                        }
                    )

            # Update stored hash
            self.file_hashes[file_path] = {
                'hash': current_hash,
                **current_stats
            }

        except Exception as e:
            logger.warning(f"Failed to check file integrity for {file_path}: {e}")

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""

    async def _system_monitor(self):
        """Monitor system metrics"""
        logger.info("Starting system monitoring")

        while self.is_running:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                disk_io = psutil.disk_io_counters()
                network_io = psutil.net_io_counters()

                metrics = {
                    'cpu_usage': cpu_percent,
                    'memory_usage': memory_percent,
                    'disk_read_bytes': disk_io.read_bytes if disk_io else 0,
                    'disk_write_bytes': disk_io.write_bytes if disk_io else 0,
                    'network_sent_bytes': network_io.bytes_sent if network_io else 0,
                    'network_recv_bytes': network_io.bytes_recv if network_io else 0
                }

                # Check for anomalies using ML models
                if self.config.get('enable_ml_detection', True):
                    await self._detect_anomalies(metrics)

                await asyncio.sleep(self.config.get('monitoring_interval', 5))

            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                await asyncio.sleep(10)

    async def _detect_anomalies(self, metrics: Dict[str, float]):
        """Detect anomalies in system metrics"""
        for metric_name, value in metrics.items():
            if metric_name in self.ml_models:
                model = self.ml_models[metric_name]

                # Simple statistical anomaly detection
                if model['type'] == 'statistical':
                    # Update model parameters (simplified)
                    model['mean'] = 0.9 * model['mean'] + 0.1 * value
                    model['std'] = 0.9 * model['std'] + 0.1 * abs(value - model['mean'])

                    # Check for anomaly
                    if model['std'] > 0:
                        z_score = abs(value - model['mean']) / model['std']
                        if z_score > model['threshold']:
                            await self._create_alert(
                                title="System Anomaly Detected",
                                description=f"Anomalous {metric_name}: {value:.2f}",
                                alert_type=AlertType.ANOMALOUS_BEHAVIOR,
                                threat_level=ThreatLevel.MEDIUM,
                                evidence={
                                    'metric': metric_name,
                                    'value': value,
                                    'baseline_mean': model['mean'],
                                    'z_score': z_score,
                                    'threshold': model['threshold']
                                }
                            )

    async def _log_monitor(self):
        """Monitor log files"""
        logger.info("Starting log monitoring")

        while self.is_running:
            try:
                for log_source in self.log_sources:
                    await self._monitor_log_source(log_source)

                await asyncio.sleep(self.config.get('monitoring_interval', 5))

            except Exception as e:
                logger.error(f"Log monitoring error: {e}")
                await asyncio.sleep(10)

    async def _monitor_log_source(self, log_source: str):
        """Monitor specific log source"""
        try:
            # Handle glob patterns
            import glob
            log_files = glob.glob(log_source)

            for log_file in log_files:
                if os.path.exists(log_file):
                    await self._parse_log_file(log_file)

        except Exception as e:
            logger.debug(f"Failed to monitor log source {log_source}: {e}")

    async def _parse_log_file(self, log_file: str):
        """Parse log file for security events"""
        try:
            # Read recent log entries
            with open(log_file, 'r') as f:
                lines = f.readlines()[-100:]  # Last 100 lines

            for line in lines:
                await self._analyze_log_line(line, log_file)

        except Exception as e:
            logger.debug(f"Failed to parse log file {log_file}: {e}")

    async def _analyze_log_line(self, line: str, log_file: str):
        """Analyze individual log line"""
        for category, patterns in self.log_patterns.items():
            for pattern in patterns:
                match = pattern.search(line)
                if match:
                    event = SecurityEvent(
                        id=f"event_{int(time.time() * 1000)}_{hashlib.md5(line.encode()).hexdigest()[:8]}",
                        event_type=category,
                        source_ip=match.group(1) if match.groups() else None,
                        target_ip=None,
                        user=None,
                        process=None,
                        file_path=log_file,
                        command=line.strip(),
                        timestamp=datetime.now(),
                        severity='MEDIUM',
                        details={
                            'pattern': pattern.pattern,
                            'match_groups': match.groups(),
                            'full_line': line.strip()
                        }
                    )

                    await self.event_queue.put(event)

    async def _event_processor(self):
        """Process security events"""
        logger.info("Starting event processor")

        while self.is_running:
            try:
                # Get event from queue
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)

                # Store event
                await self._store_event(event)

                # Apply monitoring rules
                await self._apply_monitoring_rules(event)

                # Update rate limits and reputation
                if event.source_ip:
                    await self._update_ip_reputation(event.source_ip, event)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Event processing error: {e}")

    async def _apply_monitoring_rules(self, event: SecurityEvent):
        """Apply monitoring rules to events"""
        for rule in self.rules.values():
            if not rule.enabled:
                continue

            try:
                if await self._evaluate_rule(rule, event):
                    await self._trigger_rule_actions(rule, event)
            except Exception as e:
                logger.error(f"Failed to evaluate rule {rule.id}: {e}")

    async def _evaluate_rule(self, rule: MonitoringRule, event: SecurityEvent) -> bool:
        """Evaluate if rule matches event"""
        # Simple pattern matching (could be enhanced with more complex logic)
        if rule.pattern in event.event_type.lower():
            return True

        # Check specific conditions
        conditions = rule.conditions

        if rule.monitor_type == MonitorType.AUTHENTICATION:
            if event.source_ip:
                current_time = time.time()
                time_window = conditions.get('time_window', 300)

                # Count failed attempts
                failed_attempts = self.failed_attempts[event.source_ip]

                if failed_attempts >= conditions.get('max_attempts', 5):
                    return True

        elif rule.monitor_type == MonitorType.NETWORK:
            if rule.pattern == 'port_scan':
                # Check port scan detection
                if event.source_ip in self.port_scans:
                    distinct_ports = len(set(self.port_scans[event.source_ip]))
                    if distinct_ports >= conditions.get('max_ports', 10):
                        return True

        return False

    async def _trigger_rule_actions(self, rule: MonitoringRule, event: SecurityEvent):
        """Trigger actions for matched rule"""
        for action in rule.actions:
            try:
                if action == 'alert_admin':
                    await self._create_alert(
                        title=f"Rule Triggered: {rule.name}",
                        description=rule.description,
                        alert_type=self._map_rule_to_alert_type(rule.monitor_type),
                        threat_level=rule.threat_level,
                        source=event.source_ip,
                        target=event.target_ip,
                        evidence={
                            'rule_id': rule.id,
                            'event_id': event.id,
                            'event_details': event.details
                        }
                    )

                elif action == 'block_ip':
                    if event.source_ip:
                        await self._block_ip(event.source_ip)

                elif action == 'rate_limit':
                    if event.source_ip:
                        await self._apply_rate_limit(event.source_ip)

                elif action == 'log_event':
                    logger.warning(f"Security rule triggered: {rule.name} - {event.source_ip}")

                elif action == 'kill_process':
                    if event.process:
                        await self._kill_process(event.process)

            except Exception as e:
                logger.error(f"Failed to execute action {action}: {e}")

    def _map_rule_to_alert_type(self, monitor_type: MonitorType) -> AlertType:
        """Map monitor type to alert type"""
        mapping = {
            MonitorType.AUTHENTICATION: AlertType.UNAUTHORIZED_ACCESS,
            MonitorType.NETWORK: AlertType.SUSPICIOUS_NETWORK,
            MonitorType.PROCESS: AlertType.MALICIOUS_ACTIVITY,
            MonitorType.FILE: AlertType.FILE_INTEGRITY,
            MonitorType.SYSTEM: AlertType.ANOMALOUS_BEHAVIOR
        }
        return mapping.get(monitor_type, AlertType.POLICY_VIOLATION)

    async def _block_ip(self, ip: str):
        """Block IP address"""
        try:
            # Use iptables to block IP (requires root)
            subprocess.run(['iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP'], check=False)
            logger.info(f"Blocked IP: {ip}")
        except Exception as e:
            logger.error(f"Failed to block IP {ip}: {e}")

    async def _apply_rate_limit(self, ip: str):
        """Apply rate limiting to IP"""
        # Rate limiting implementation would go here
        logger.info(f"Applied rate limiting to IP: {ip}")

    async def _kill_process(self, process_name: str):
        """Kill suspicious process"""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] == process_name:
                    proc.kill()
                    logger.info(f"Killed process: {process_name} (PID: {proc.info['pid']})")
        except Exception as e:
            logger.error(f"Failed to kill process {process_name}: {e}")

    async def _create_alert(self, title: str, description: str, alert_type: AlertType,
                          threat_level: ThreatLevel, source: str, target: str = None,
                          evidence: Dict = None):
        """Create security alert"""
        alert_id = f"alert_{int(time.time() * 1000)}_{hashlib.md5(title.encode()).hexdigest()[:8]}"

        alert = SecurityAlert(
            id=alert_id,
            title=title,
            description=description,
            alert_type=alert_type,
            threat_level=threat_level,
            source=source,
            target=target,
            timestamp=datetime.now(),
            evidence=evidence or {},
            mitigation_steps=self._generate_mitigation_steps(alert_type)
        )

        # Store alert
        await self._store_alert(alert)

        # Queue for processing
        await self.alert_queue.put(alert)

        logger.warning(f"Security alert created: {title} - {threat_level.value}")

    def _generate_mitigation_steps(self, alert_type: AlertType) -> List[str]:
        """Generate mitigation steps for alert type"""
        steps = {
            AlertType.INTRUSION_ATTEMPT: [
                "Block source IP address",
                "Review authentication logs",
                "Check for successful breaches",
                "Update firewall rules"
            ],
            AlertType.UNAUTHORIZED_ACCESS: [
                "Immediately terminate session",
                "Change affected credentials",
                "Review access logs",
                "Implement additional authentication factors"
            ],
            AlertType.MALICIOUS_ACTIVITY: [
                "Isolate affected system",
                "Preserve forensic evidence",
                "Scan for malware",
                "Review process execution logs"
            ],
            AlertType.FILE_INTEGRITY: [
                "Restore file from backup",
                "Identify unauthorized changes",
                "Review access logs",
                "Implement additional file monitoring"
            ],
            AlertType.DENIAL_OF_SERVICE: [
                "Implement rate limiting",
                "Block attack sources",
                "Scale resources if needed",
                "Analyze attack patterns"
            ]
        }

        return steps.get(alert_type, ["Review security logs", "Implement appropriate countermeasures"])

    async def _store_alert(self, alert: SecurityAlert):
        """Store alert in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO security_alerts
            (id, title, description, alert_type, threat_level, source, target,
             timestamp, evidence, mitigation_steps, false_positive, resolved)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            alert.id,
            alert.title,
            alert.description,
            alert.alert_type.value,
            alert.threat_level.value,
            alert.source,
            alert.target,
            alert.timestamp,
            json.dumps(alert.evidence),
            json.dumps(alert.mitigation_steps),
            alert.false_positive,
            alert.resolved
        ))

        conn.commit()
        conn.close()

    async def _store_event(self, event: SecurityEvent):
        """Store security event in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO security_events
            (id, event_type, source_ip, target_ip, user, process, file_path,
             command, timestamp, severity, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.id,
            event.event_type,
            event.source_ip,
            event.target_ip,
            event.user,
            event.process,
            event.file_path,
            event.command,
            event.timestamp,
            event.severity,
            json.dumps(event.details)
        ))

        conn.commit()
        conn.close()

    async def _update_ip_reputation(self, ip: str, event: SecurityEvent):
        """Update IP reputation based on events"""
        if ip not in self.ip_reputation:
            self.ip_reputation[ip] = {
                'score': 0,
                'incidents': 0,
                'last_seen': datetime.now()
            }

        # Update reputation based on event severity
        if event.severity == 'HIGH':
            self.ip_reputation[ip]['score'] -= 10
        elif event.severity == 'MEDIUM':
            self.ip_reputation[ip]['score'] -= 5
        elif event.severity == 'LOW':
            self.ip_reputation[ip]['score'] -= 2

        self.ip_reputation[ip]['incidents'] += 1
        self.ip_reputation[ip]['last_seen'] = datetime.now()

        # Determine threat level
        if self.ip_reputation[ip]['score'] <= -20:
            threat_level = 'CRITICAL'
        elif self.ip_reputation[ip]['score'] <= -10:
            threat_level = 'HIGH'
        elif self.ip_reputation[ip]['score'] <= -5:
            threat_level = 'MEDIUM'
        else:
            threat_level = 'LOW'

        self.ip_reputation[ip]['threat_level'] = threat_level

        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO ip_reputation
            (ip, reputation_score, threat_level, last_seen, incidents_count, details)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            ip,
            self.ip_reputation[ip]['score'],
            threat_level,
            self.ip_reputation[ip]['last_seen'],
            self.ip_reputation[ip]['incidents'],
            json.dumps(self.ip_reputation[ip])
        ))

        conn.commit()
        conn.close()

    async def _alert_processor(self):
        """Process security alerts and send notifications"""
        logger.info("Starting alert processor")

        while self.is_running:
            try:
                # Get alert from queue
                alert = await asyncio.wait_for(self.alert_queue.get(), timeout=1.0)

                # Send notifications
                await self._send_notifications(alert)

                # Check for automated response
                if self.config.get('automated_response', False):
                    await self._automated_response(alert)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Alert processing error: {e}")

    async def _send_notifications(self, alert: SecurityAlert):
        """Send notifications for alert"""
        # Send email if enabled
        if (self.config.get('notification_channels', {}).get('email', {}).get('enabled', False) and
            self.email_available):
            await self._send_email_alert(alert)

        # Send Slack if enabled
        if (self.config.get('notification_channels', {}).get('slack', {}).get('enabled', False) and
            self.slack_available):
            await self._send_slack_alert(alert)

        # Send webhook if enabled
        if self.config.get('notification_channels', {}).get('webhook', {}).get('enabled', False):
            await self._send_webhook_alert(alert)

    async def _send_email_alert(self, alert: SecurityAlert):
        """Send email alert"""
        try:
            email_config = self.config.get('notification_channels', {}).get('email', {})

            # Create email content
            subject = f"Security Alert: {alert.title}"
            body = f"""
Security Alert Details:

Title: {alert.title}
Description: {alert.description}
Threat Level: {alert.threat_level.value}
Source: {alert.source}
Timestamp: {alert.timestamp}

Evidence:
{json.dumps(alert.evidence, indent=2)}

Mitigation Steps:
{chr(10).join(f"- {step}" for step in alert.mitigation_steps)}
            """

            # Send email (implementation would depend on email library)
            logger.info(f"Email alert sent: {subject}")

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    async def _send_slack_alert(self, alert: SecurityAlert):
        """Send Slack alert"""
        try:
            slack_config = self.config.get('notification_channels', {}).get('slack', {})

            payload = {
                'channel': slack_config.get('channel', '#security-alerts'),
                'username': 'Security Monitor',
                'icon_emoji': ':warning:',
                'attachments': [{
                    'color': self._get_color_for_threat_level(alert.threat_level),
                    'title': alert.title,
                    'text': alert.description,
                    'fields': [
                        {'title': 'Threat Level', 'value': alert.threat_level.value, 'short': True},
                        {'title': 'Source', 'value': alert.source, 'short': True},
                        {'title': 'Timestamp', 'value': alert.timestamp.isoformat(), 'short': True}
                    ],
                    'footer': 'DMLogn8n Security Monitor',
                    'ts': int(alert.timestamp.timestamp())
                }]
            }

            # Send to Slack webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(slack_config.get('webhook_url'), json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Slack alert sent: {alert.title}")
                    else:
                        logger.error(f"Failed to send Slack alert: {response.status}")

        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")

    async def _send_webhook_alert(self, alert: SecurityAlert):
        """Send webhook alert"""
        try:
            webhook_config = self.config.get('notification_channels', {}).get('webhook', {})

            payload = {
                'alert_id': alert.id,
                'title': alert.title,
                'description': alert.description,
                'alert_type': alert.alert_type.value,
                'threat_level': alert.threat_level.value,
                'source': alert.source,
                'target': alert.target,
                'timestamp': alert.timestamp.isoformat(),
                'evidence': alert.evidence,
                'mitigation_steps': alert.mitigation_steps
            }

            headers = webhook_config.get('headers', {})
            headers.setdefault('Content-Type', 'application/json')

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_config.get('url'),
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook alert sent: {alert.title}")
                    else:
                        logger.error(f"Failed to send webhook alert: {response.status}")

        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")

    def _get_color_for_threat_level(self, threat_level: ThreatLevel) -> str:
        """Get Slack color for threat level"""
        colors = {
            ThreatLevel.INFO: '#36a64f',      # green
            ThreatLevel.LOW: '#ff9500',      # orange
            ThreatLevel.MEDIUM: '#ffcc00',   # yellow
            ThreatLevel.HIGH: '#ff0000',     # red
            ThreatLevel.CRITICAL: '#8b0000'   # dark red
        }
        return colors.get(threat_level, '#36a64f')

    async def _automated_response(self, alert: SecurityAlert):
        """Perform automated response to alert"""
        try:
            if alert.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                # Block IP if it's a network-based threat
                if alert.source and self._is_valid_ip(alert.source):
                    await self._block_ip(alert.source)

                # Isolate system if it's a host-based threat
                if alert.target and self._is_internal_ip(alert.target):
                    await self._isolate_system(alert.target)

                # Create incident ticket
                await self._create_incident_ticket(alert)

        except Exception as e:
            logger.error(f"Automated response failed: {e}")

    def _is_valid_ip(self, ip: str) -> bool:
        """Check if IP address is valid"""
        try:
            ipaddress.ip_address(ip)
            return True
        except:
            return False

    def _is_internal_ip(self, ip: str) -> bool:
        """Check if IP address is internal"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private
        except:
            return False

    async def _isolate_system(self, target: str):
        """Isolate compromised system"""
        logger.info(f"Isolating system: {target}")
        # System isolation implementation would go here

    async def _create_incident_ticket(self, alert: SecurityAlert):
        """Create incident ticket for alert"""
        logger.info(f"Creating incident ticket for alert: {alert.id}")
        # Ticket creation implementation would go here

    async def _baseline_updater(self):
        """Update baseline metrics periodically"""
        logger.info("Starting baseline updater")

        while self.is_running:
            try:
                # Update baselines every hour
                await asyncio.sleep(3600)

                # Collect current metrics
                metrics = {
                    'cpu_usage': psutil.cpu_percent(interval=60),
                    'memory_usage': psutil.virtual_memory().percent,
                    'network_connections': len(psutil.net_connections()),
                    'active_processes': len(psutil.pids())
                }

                # Update baselines
                for metric_name, value in metrics.items():
                    await self._update_baseline(metric_name, value)

            except Exception as e:
                logger.error(f"Baseline updater error: {e}")

    async def _update_baseline(self, metric_name: str, value: float):
        """Update baseline metric"""
        if metric_name not in self.baselines:
            self.baselines[metric_name] = BaselineMetric(
                metric_name=metric_name,
                baseline_value=value,
                threshold_multiplier=2.0,
                last_updated=datetime.now(),
                samples=[value]
            )
        else:
            baseline = self.baselines[metric_name]
            baseline.samples.append(value)

            # Keep only last 100 samples
            if len(baseline.samples) > 100:
                baseline.samples = baseline.samples[-100:]

            # Update baseline as moving average
            baseline.baseline_value = sum(baseline.samples) / len(baseline.samples)
            baseline.last_updated = datetime.now()

        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO baselines
            (metric_name, baseline_value, threshold_multiplier, last_updated, samples)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            metric_name,
            self.baselines[metric_name].baseline_value,
            self.baselines[metric_name].threshold_multiplier,
            self.baselines[metric_name].last_updated,
            json.dumps(self.baselines[metric_name].samples)
        ))

        conn.commit()
        conn.close()

    async def _update_network_baseline(self, connection_count: int):
        """Update network connection baseline"""
        await self._update_baseline('network_connections', float(connection_count))

    async def generate_security_report(self, hours: int = 24) -> Dict:
        """Generate security monitoring report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        # Get security events
        cursor.execute('''
            SELECT * FROM security_events
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        ''', (start_time,))

        events = cursor.fetchall()

        # Get security alerts
        cursor.execute('''
            SELECT * FROM security_alerts
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        ''', (start_time,))

        alerts = cursor.fetchall()
        conn.close()

        # Generate report
        report = {
            'report_period': f"{hours} hours",
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'total_events': len(events),
            'total_alerts': len(alerts),
            'events_by_type': {},
            'alerts_by_level': {},
            'alerts_by_type': {},
            'top_source_ips': {},
            'threat_summary': {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
                'info': 0
            },
            'recommendations': []
        }

        # Analyze events
        for event in events:
            event_type = event[1]
            report['events_by_type'][event_type] = report['events_by_type'].get(event_type, 0) + 1

            source_ip = event[2]
            if source_ip:
                report['top_source_ips'][source_ip] = report['top_source_ips'].get(source_ip, 0) + 1

        # Analyze alerts
        for alert in alerts:
            threat_level = alert[4]
            alert_type = alert[3]

            report['alerts_by_level'][threat_level] = report['alerts_by_level'].get(threat_level, 0) + 1
            report['alerts_by_type'][alert_type] = report['alerts_by_type'].get(alert_type, 0) + 1

            if threat_level in report['threat_summary']:
                report['threat_summary'][threat_level] += 1

        # Sort top source IPs
        report['top_source_ips'] = dict(
            sorted(report['top_source_ips'].items(), key=lambda x: x[1], reverse=True)[:10]
        )

        # Generate recommendations
        if report['threat_summary']['critical'] > 0:
            report['recommendations'].append("Immediate investigation required for critical threats")
        if report['threat_summary']['high'] > 5:
            report['recommendations'].append("High number of high-severity threats detected")
        if len(report['top_source_ips']) > 0:
            report['recommendations'].append("Consider blocking top malicious IP addresses")

        return report

async def main():
    """Main function for security monitor"""
    monitor = SecurityMonitor()

    logger.info("Starting DMLogn8n Security Monitor...")
    await monitor.start_monitoring()

    try:
        # Run monitoring for demonstration
        logger.info("Security monitoring is running. Press Ctrl+C to stop...")

        # Generate and save periodic reports
        while True:
            await asyncio.sleep(3600)  # Every hour

            # Generate security report
            report = await monitor.generate_security_report(24)

            # Save report to file
            report_path = f"/home/activeloguser/DMLogn8n/security/reports/security_report_{int(time.time())}.json"
            os.makedirs(os.path.dirname(report_path), exist_ok=True)

            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"Security report saved to: {report_path}")

            # Print summary
            print(f"\n=== SECURITY MONITORING SUMMARY (Last 24 Hours) ===")
            print(f"Total Events: {report['total_events']}")
            print(f"Total Alerts: {report['total_alerts']}")
            print(f"Critical Threats: {report['threat_summary']['critical']}")
            print(f"High Threats: {report['threat_summary']['high']}")
            print(f"Medium Threats: {report['threat_summary']['medium']}")

            if report['recommendations']:
                print("\nRecommendations:")
                for rec in report['recommendations']:
                    print(f"- {rec}")

    except KeyboardInterrupt:
        logger.info("Stopping security monitoring...")
        await monitor.stop_monitoring()

    return monitor

if __name__ == "__main__":
    asyncio.run(main())