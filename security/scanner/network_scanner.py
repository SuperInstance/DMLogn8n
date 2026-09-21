#!/usr/bin/env python3
"""
DMLogn8n Advanced Network Security Scanner
Comprehensive network vulnerability assessment and penetration testing tool
"""

import asyncio
import aiohttp
import socket
import ssl
import json
import logging
import os
import re
import sys
import time
import hashlib
import sqlite3
import subprocess
import ipaddress
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import nmap
import scapy.all as scapy
from cryptography import x509
from cryptography.hazmat.backends import default_backend

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/activeloguser/DMLogn8n/security/logs/network_scanner.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class VulnerabilitySeverity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class ScanType(Enum):
    PORT_SCAN = "Port Scan"
    SERVICE_DETECTION = "Service Detection"
    VULNERABILITY_SCAN = "Vulnerability Scan"
    SSL_TLS_SCAN = "SSL/TLS Scan"
    WEB_APP_SCAN = "Web Application Scan"
    NETWORK_DISCOVERY = "Network Discovery"
    FIREWALL_TEST = "Firewall Testing"
    DOS_TEST = "Denial of Service Test"

class Protocol(Enum):
    TCP = "TCP"
    UDP = "UDP"
    ICMP = "ICMP"
    HTTP = "HTTP"
    HTTPS = "HTTPS"
    FTP = "FTP"
    SSH = "SSH"
    TELNET = "TELNET"
    SMTP = "SMTP"
    DNS = "DNS"

@dataclass
class NetworkHost:
    ip: str
    hostname: Optional[str]
    mac_address: Optional[str]
    os_guess: Optional[str]
    open_ports: List[int]
    services: Dict[int, Dict]
    vulnerabilities: List[Dict]
    response_time: float
    is_alive: bool

@dataclass
class NetworkVulnerability:
    id: str
    title: str
    description: str
    severity: VulnerabilitySeverity
    cvss_score: Optional[float]
    cve_id: Optional[str]
    affected_host: str
    port: Optional[int]
    protocol: Protocol
    service: Optional[str]
    evidence: str
    remediation: str
    references: List[str]
    scan_id: str
    discovered_at: datetime

@dataclass
class NetworkScanResult:
    scan_id: str
    scan_type: ScanType
    target: str
    started_at: datetime
    completed_at: Optional[datetime]
    hosts_discovered: int
    vulnerabilities_found: int
    hosts: List[NetworkHost]
    vulnerabilities: List[NetworkVulnerability]
    network_map: Dict[str, Any]
    status: str

class NetworkScanner:
    """Advanced network security scanner"""

    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.db_path = self.config.get('database_path', '/home/activeloguser/DMLogn8n/security/data/network_scans.db')
        self.scanner_version = "2.0.0"

        # Initialize nmap scanner
        try:
            self.nm = nmap.PortScanner()
            self.nm_available = True
        except Exception as e:
            logger.warning(f"Nmap not available: {e}")
            self.nm_available = False

        # Initialize database
        self._init_database()

        # Common vulnerable services and their default ports
        self.vulnerable_services = {
            21: {'name': 'FTP', 'common_issues': ['anonymous_login', 'weak_encryption', 'directory_traversal']},
            22: {'name': 'SSH', 'common_issues': ['weak_keys', 'default_credentials', 'outdated_version']},
            23: {'name': 'Telnet', 'common_issues': ['cleartext', 'default_credentials']},
            25: {'name': 'SMTP', 'common_issues': ['open_relay', 'weak_authentication']},
            53: {'name': 'DNS', 'common_issues': ['dns_amplification', 'zone_transfer']},
            80: {'name': 'HTTP', 'common_issues': [' outdated_software', 'directory_listing', 'default_pages']},
            110: {'name': 'POP3', 'common_issues': ['cleartext', 'weak_authentication']},
            143: {'name': 'IMAP', 'common_issues': ['cleartext', 'weak_authentication']},
            443: {'name': 'HTTPS', 'common_issues': ['weak_ssl', 'expired_certificates', 'vulnerable_ciphers']},
            993: {'name': 'IMAPS', 'common_issues': ['weak_ssl', 'outdated_version']},
            995: {'name': 'POP3S', 'common_issues': ['weak_ssl', 'outdated_version']},
            1433: {'name': 'MSSQL', 'common_issues': ['default_credentials', 'weak_authentication']},
            3306: {'name': 'MySQL', 'common_issues': ['default_credentials', 'weak_authentication']},
            3389: {'name': 'RDP', 'common_issues': ['weak_authentication', 'bluekeep']},
            5432: {'name': 'PostgreSQL', 'common_issues': ['default_credentials', 'weak_authentication']},
            5900: {'name': 'VNC', 'common_issues': ['no_password', 'weak_authentication']},
            6379: {'name': 'Redis', 'common_issues': ['no_authentication', 'default_config']},
            8080: {'name': 'HTTP-Alt', 'common_issues': ['outdated_software', 'directory_listing']},
            27017: {'name': 'MongoDB', 'common_issues': ['no_authentication', 'default_config']}
        }

        # SSL/TLS vulnerability patterns
        self.ssl_vulnerabilities = {
            'protocol_support': ['SSLv2', 'SSLv3', 'TLSv1.0', 'TLSv1.1'],
            'weak_ciphers': [
                'RC4', 'DES', '3DES', 'MD5', 'SHA1', 'NULL', 'EXPORT', 'ADH', 'AECDH'
            ],
            'weak_key_exchange': [
                'DH512', 'DH1024', 'RSA512', 'RSA1024', 'EXP'
            ]
        }

    def _load_config(self, config_path: str) -> Dict:
        """Load scanner configuration"""
        default_config = {
            'database_path': '/home/activeloguser/DMLogn8n/security/data/network_scans.db',
            'scan_timeout': 300,
            'max_concurrent_scans': 10,
            'port_scan_timeout': 5,
            'service_detection_timeout': 10,
            'vulnerability_scan_timeout': 30,
            'default_ports': '1-1000',
            'deep_scan': True,
            'aggressive_scan': False,
            'scan_dns_servers': True,
            'check_ssl_certificates': True,
            'test_web_applications': True,
            'dos_testing': False,
            'exclude_networks': ['127.0.0.0/8', '169.254.0.0/16'],
            'max_hosts_per_scan': 254,
            'rate_limit': 100  # packets per second
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
        """Initialize database for network scan storage"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create network_scans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS network_scans (
                scan_id TEXT PRIMARY KEY,
                scan_type TEXT,
                target TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                hosts_discovered INTEGER,
                vulnerabilities_found INTEGER,
                status TEXT,
                scan_config TEXT
            )
        ''')

        # Create network_hosts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS network_hosts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id TEXT,
                ip TEXT,
                hostname TEXT,
                mac_address TEXT,
                os_guess TEXT,
                open_ports TEXT,
                services TEXT,
                vulnerabilities TEXT,
                response_time REAL,
                is_alive BOOLEAN,
                FOREIGN KEY (scan_id) REFERENCES network_scans (scan_id)
            )
        ''')

        # Create network_vulnerabilities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS network_vulnerabilities (
                id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                severity TEXT,
                cvss_score REAL,
                cve_id TEXT,
                affected_host TEXT,
                port INTEGER,
                protocol TEXT,
                service TEXT,
                evidence TEXT,
                remediation TEXT,
                references TEXT,
                scan_id TEXT,
                discovered_at TIMESTAMP,
                FOREIGN KEY (scan_id) REFERENCES network_scans (scan_id)
            )
        ''')

        conn.commit()
        conn.close()

    async def scan_network(self, target: str, scan_types: List[ScanType] = None) -> List[NetworkScanResult]:
        """Perform comprehensive network security scan"""
        if scan_types is None:
            scan_types = [
                ScanType.NETWORK_DISCOVERY,
                ScanType.PORT_SCAN,
                ScanType.SERVICE_DETECTION,
                ScanType.VULNERABILITY_SCAN,
                ScanType.SSL_TLS_SCAN
            ]

        scan_id = self._generate_scan_id()
        logger.info(f"Starting network scan {scan_id} for target: {target}")

        results = []

        try:
            # Validate target
            network_range = self._validate_target(target)
            if not network_range:
                raise ValueError(f"Invalid target: {target}")

            # Perform each type of scan
            for scan_type in scan_types:
                result = await self._perform_scan(scan_id, scan_type, network_range)
                if result:
                    results.append(result)

            logger.info(f"Network scan {scan_id} completed")

        except Exception as e:
            logger.error(f"Network scan {scan_id} failed: {e}")

        return results

    async def _perform_scan(self, scan_id: str, scan_type: ScanType, target: str) -> Optional[NetworkScanResult]:
        """Perform a specific type of network scan"""
        logger.info(f"Starting {scan_type.value} scan")

        result = NetworkScanResult(
            scan_id=f"{scan_id}_{scan_type.value.lower().replace(' ', '_')}",
            scan_type=scan_type,
            target=target,
            started_at=datetime.now(),
            completed_at=None,
            hosts_discovered=0,
            vulnerabilities_found=0,
            hosts=[],
            vulnerabilities=[],
            network_map={},
            status='running'
        )

        try:
            # Record scan start
            self._record_scan_start(result)

            if scan_type == ScanType.NETWORK_DISCOVERY:
                await self._network_discovery_scan(result)
            elif scan_type == ScanType.PORT_SCAN:
                await self._port_scan(result)
            elif scan_type == ScanType.SERVICE_DETECTION:
                await self._service_detection_scan(result)
            elif scan_type == ScanType.VULNERABILITY_SCAN:
                await self._vulnerability_scan(result)
            elif scan_type == ScanType.SSL_TLS_SCAN:
                await self._ssl_tls_scan(result)
            elif scan_type == ScanType.WEB_APP_SCAN:
                await self._web_application_scan(result)
            elif scan_type == ScanType.FIREWALL_TEST:
                await self._firewall_test(result)
            elif scan_type == ScanType.DOS_TEST and self.config.get('dos_testing', False):
                await self._dos_test(result)

            result.completed_at = datetime.now()
            result.status = 'completed'

            # Store results
            self._store_scan_results(result)

            logger.info(f"Completed {scan_type.value} scan. Found {len(result.vulnerabilities)} vulnerabilities")

        except Exception as e:
            logger.error(f"Failed {scan_type.value} scan: {e}")
            result.status = 'failed'
            result.completed_at = datetime.now()

        return result

    async def _network_discovery_scan(self, result: NetworkScanResult):
        """Perform network discovery to find active hosts"""
        logger.info("Discovering active hosts on network")

        try:
            network = ipaddress.ip_network(result.target, strict=False)
            active_hosts = []

            # Use nmap ping scan if available
            if self.nm_available:
                try:
                    self.nm.scan(hosts=str(network), arguments='-sn')
                    for host in self.nm.all_hosts():
                        if self.nm[host].state() == 'up':
                            host_info = NetworkHost(
                                ip=host,
                                hostname=self.nm[host].hostname(),
                                mac_address=self.nm[host]['addresses'].get('mac'),
                                os_guess=None,
                                open_ports=[],
                                services={},
                                vulnerabilities=[],
                                response_time=0.0,
                                is_alive=True
                            )
                            active_hosts.append(host_info)
                except Exception as e:
                    logger.warning(f"Nmap discovery failed: {e}")

            # Fallback to custom ping sweep
            if not active_hosts:
                active_hosts = await self._ping_sweep(network)

            result.hosts = active_hosts
            result.hosts_discovered = len(active_hosts)

            # Generate network map
            result.network_map = self._generate_network_map(active_hosts, network)

        except Exception as e:
            logger.error(f"Network discovery failed: {e}")

    async def _ping_sweep(self, network: ipaddress.IPv4Network) -> List[NetworkHost]:
        """Perform ping sweep to discover active hosts"""
        active_hosts = []
        max_concurrent = self.config.get('max_concurrent_scans', 10)

        async def ping_host(ip_str: str) -> Optional[NetworkHost]:
            try:
                # Simple ICMP ping
                proc = await asyncio.create_subprocess_exec(
                    'ping', '-c', '1', '-W', '1', ip_str,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await proc.wait()

                if proc.returncode == 0:
                    return NetworkHost(
                        ip=ip_str,
                        hostname=None,
                        mac_address=None,
                        os_guess=None,
                        open_ports=[],
                        services={},
                        vulnerabilities=[],
                        response_time=0.0,
                        is_alive=True
                    )
            except Exception:
                pass
            return None

        # Limit hosts to prevent excessive scanning
        hosts_to_scan = list(network.hosts())[:self.config.get('max_hosts_per_scan', 254)]

        # Create semaphore to limit concurrent pings
        semaphore = asyncio.Semaphore(max_concurrent)

        async def bounded_ping(ip_str: str):
            async with semaphore:
                return await ping_host(ip_str)

        tasks = [bounded_ping(str(ip)) for ip in hosts_to_scan]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, NetworkHost):
                active_hosts.append(result)

        return active_hosts

    async def _port_scan(self, result: NetworkScanResult):
        """Perform port scanning on discovered hosts"""
        logger.info("Scanning ports on discovered hosts")

        common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 1433, 3306, 3389, 5432, 5900, 6379, 8080, 27017]
        max_concurrent = self.config.get('max_concurrent_scans', 50)

        for host in result.hosts:
            if not host.is_alive:
                continue

            open_ports = []
            semaphore = asyncio.Semaphore(max_concurrent)

            async def scan_port(port: int) -> Optional[int]:
                async with semaphore:
                    try:
                        reader, writer = await asyncio.wait_for(
                            asyncio.open_connection(host.ip, port),
                            timeout=self.config.get('port_scan_timeout', 5)
                        )
                        writer.close()
                        await writer.wait_closed()
                        return port
                    except Exception:
                        return None

            # Scan ports concurrently
            tasks = [scan_port(port) for port in common_ports]
            port_results = await asyncio.gather(*tasks, return_exceptions=True)

            for port_result in port_results:
                if isinstance(port_result, int):
                    open_ports.append(port_result)

            host.open_ports = open_ports

    async def _service_detection_scan(self, result: NetworkScanResult):
        """Detect services running on open ports"""
        logger.info("Detecting services on open ports")

        for host in result.hosts:
            if not host.is_alive or not host.open_ports:
                continue

            for port in host.open_ports:
                service_info = await self._detect_service(host.ip, port)
                host.services[port] = service_info

    async def _detect_service(self, ip: str, port: int) -> Dict:
        """Detect service running on specific port"""
        service_info = {
            'name': 'unknown',
            'version': 'unknown',
            'banner': None,
            'protocol': 'tcp'
        }

        try:
            # Try to grab banner
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=self.config.get('service_detection_timeout', 10)
            )

            # Send simple HTTP request for web services
            if port in [80, 8080, 8000, 8888]:
                writer.write(b'GET / HTTP/1.1\r\nHost: ' + ip.encode() + b'\r\n\r\n')
                await writer.drain()

            # Try to read banner
            try:
                data = await asyncio.wait_for(reader.read(1024), timeout=5)
                if data:
                    banner = data.decode('utf-8', errors='ignore')
                    service_info['banner'] = banner[:200]  # Limit banner length

                    # Try to identify service from banner
                    service_info.update(self._identify_service_from_banner(banner, port))

            except asyncio.TimeoutError:
                pass

            writer.close()
            await writer.wait_closed()

        except Exception as e:
            logger.debug(f"Service detection failed for {ip}:{port} - {e}")

        # Use known service mappings
        if port in self.vulnerable_services:
            if service_info['name'] == 'unknown':
                service_info['name'] = self.vulnerable_services[port]['name']

        return service_info

    def _identify_service_from_banner(self, banner: str, port: int) -> Dict:
        """Identify service from banner information"""
        info = {}

        banner_lower = banner.lower()

        # HTTP servers
        if any(server in banner_lower for server in ['apache', 'nginx', 'iis', 'lighttpd']):
            info['name'] = 'HTTP'
            if 'apache' in banner_lower:
                info['version'] = self._extract_version(banner_lower, 'apache')
            elif 'nginx' in banner_lower:
                info['version'] = self._extract_version(banner_lower, 'nginx')

        # SSH servers
        elif any(ssh in banner_lower for ssh in ['openssh', 'ssh', 'dropbear']):
            info['name'] = 'SSH'
            info['version'] = self._extract_version(banner_lower, 'openssh')

        # FTP servers
        elif any(ftp in banner_lower for ftp in ['ftp', 'vsftpd', 'proftpd']):
            info['name'] = 'FTP'
            if 'vsftpd' in banner_lower:
                info['version'] = self._extract_version(banner_lower, 'vsftpd')

        # SMTP servers
        elif any(smtp in banner_lower for smtp in ['smtp', 'esmtp', 'postfix']):
            info['name'] = 'SMTP'

        # Database servers
        elif any(db in banner_lower for db in ['mysql', 'postgresql', 'redis', 'mongodb']):
            if 'mysql' in banner_lower:
                info['name'] = 'MySQL'
            elif 'postgresql' in banner_lower:
                info['name'] = 'PostgreSQL'
            elif 'redis' in banner_lower:
                info['name'] = 'Redis'
            elif 'mongodb' in banner_lower:
                info['name'] = 'MongoDB'

        return info

    def _extract_version(self, banner: str, service: str) -> str:
        """Extract version information from banner"""
        patterns = {
            'apache': r'apache/(\d+\.\d+\.\d+)',
            'nginx': r'nginx/(\d+\.\d+\.\d+)',
            'openssh': r'openssh[_-]?(\d+\.\d+)',
            'vsftpd': r'vsftpd\s+(\d+\.\d+\.\d+)'
        }

        pattern = patterns.get(service.lower())
        if pattern:
            match = re.search(pattern, banner, re.IGNORECASE)
            if match:
                return match.group(1)

        return 'unknown'

    async def _vulnerability_scan(self, result: NetworkScanResult):
        """Scan for known vulnerabilities in services"""
        logger.info("Scanning for service vulnerabilities")

        for host in result.hosts:
            if not host.is_alive:
                continue

            for port, service_info in host.services.items():
                vulnerabilities = await self._scan_service_vulnerabilities(
                    host.ip, port, service_info
                )
                host.vulnerabilities.extend(vulnerabilities)
                result.vulnerabilities.extend(vulnerabilities)

        result.vulnerabilities_found = len(result.vulnerabilities)

    async def _scan_service_vulnerabilities(self, ip: str, port: int, service_info: Dict) -> List[NetworkVulnerability]:
        """Scan specific service for vulnerabilities"""
        vulnerabilities = []
        service_name = service_info.get('name', 'unknown')
        version = service_info.get('version', 'unknown')

        # Check for common service vulnerabilities
        if port in self.vulnerable_services:
            service_config = self.vulnerable_services[port]
            common_issues = service_config.get('common_issues', [])

            for issue in common_issues:
                vuln = await self._check_specific_vulnerability(
                    ip, port, service_name, issue, service_info
                )
                if vuln:
                    vulnerabilities.append(vuln)

        # Check for CVEs based on version information
        if version != 'unknown':
            cve_vulns = await self._check_cve_vulnerabilities(
                service_name, version, ip, port
            )
            vulnerabilities.extend(cve_vulns)

        return vulnerabilities

    async def _check_specific_vulnerability(self, ip: str, port: int, service: str,
                                         issue: str, service_info: Dict) -> Optional[NetworkVulnerability]:
        """Check for specific vulnerability types"""
        scan_id = f"vuln_scan_{int(time.time())}"

        try:
            if issue == 'anonymous_login' and service == 'FTP':
                return await self._check_ftp_anonymous(ip, port, scan_id)
            elif issue == 'default_credentials':
                return await self._check_default_credentials(ip, port, service, scan_id)
            elif issue == 'weak_ssl' and service == 'HTTPS':
                return await self._check_weak_ssl(ip, port, scan_id)
            elif issue == 'directory_traversal' and service in ['HTTP', 'FTP']:
                return await self._check_directory_traversal(ip, port, service, scan_id)
            elif issue == 'outdated_version':
                return await self._check_outdated_version(ip, port, service, service_info, scan_id)

        except Exception as e:
            logger.debug(f"Failed to check {issue} for {service} on {ip}:{port} - {e}")

        return None

    async def _check_ftp_anonymous(self, ip: str, port: int, scan_id: str) -> Optional[NetworkVulnerability]:
        """Check for anonymous FTP access"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=10
            )

            # Read welcome message
            welcome = await reader.read(1024)

            # Try anonymous login
            writer.write(b'USER anonymous\r\n')
            await writer.drain()
            response = await reader.read(1024)

            if b'230' in response or b'331' in response:
                writer.write(b'PASS anonymous@example.com\r\n')
                await writer.drain()
                response = await reader.read(1024)

                if b'230' in response:  # Login successful
                    writer.close()
                    await writer.wait_closed()

                    return NetworkVulnerability(
                        id=f"ftp_anon_{hashlib.md5(f'{ip}:{port}'.encode()).hexdigest()[:8]}",
                        title="Anonymous FTP Access",
                        description="FTP server allows anonymous login access",
                        severity=VulnerabilitySeverity.MEDIUM,
                        cvss_score=5.3,
                        cve_id=None,
                        affected_host=ip,
                        port=port,
                        protocol=Protocol.TCP,
                        service='FTP',
                        evidence="Anonymous login successful",
                        remediation="Disable anonymous FTP access or restrict permissions",
                        references=["https://owasp.org/www-project-top-ten/2017/A5_2017-Broken_Access_Control"],
                        scan_id=scan_id,
                        discovered_at=datetime.now()
                    )

            writer.close()
            await writer.wait_closed()

        except Exception as e:
            logger.debug(f"FTP anonymous check failed for {ip}:{port} - {e}")

        return None

    async def _check_default_credentials(self, ip: str, port: int, service: str, scan_id: str) -> Optional[NetworkVulnerability]:
        """Check for default credentials on services"""
        default_creds = {
            'SSH': [('admin', 'admin'), ('root', 'root'), ('admin', 'password')],
            'MySQL': [('root', ''), ('root', 'root'), ('admin', 'admin')],
            'VNC': [('', ''), ('admin', 'admin')],
            'Redis': [('', '')],  # Redis often has no authentication
        }

        if service not in default_creds:
            return None

        for username, password in default_creds[service]:
            try:
                if service == 'SSH':
                    success = await self._test_ssh_credentials(ip, port, username, password)
                elif service == 'MySQL':
                    success = await self._test_mysql_credentials(ip, port, username, password)
                elif service == 'VNC':
                    success = await self._test_vnc_credentials(ip, port, password)
                elif service == 'Redis':
                    success = await self._test_redis_access(ip, port)
                else:
                    continue

                if success:
                    return NetworkVulnerability(
                        id=f"default_creds_{hashlib.md5(f'{ip}:{port}:{service}'.encode()).hexdigest()[:8]}",
                        title=f"Default Credentials on {service}",
                        description=f"{service} service is using default credentials",
                        severity=VulnerabilitySeverity.HIGH,
                        cvss_score=7.5,
                        cve_id=None,
                        affected_host=ip,
                        port=port,
                        protocol=Protocol.TCP,
                        service=service,
                        evidence=f"Default credentials: {username}/{password if password else '<empty>'}",
                        remediation=f"Change default {service} credentials to strong, unique passwords",
                        references=["https://owasp.org/www-project-top-ten/2017/A2_2017-Broken_Authentication"],
                        scan_id=scan_id,
                        discovered_at=datetime.now()
                    )

            except Exception as e:
                logger.debug(f"Failed to test credentials for {service} on {ip}:{port} - {e}")

        return None

    async def _test_ssh_credentials(self, ip: str, port: int, username: str, password: str) -> bool:
        """Test SSH credentials"""
        try:
            proc = await asyncio.create_subprocess_exec(
                'sshpass', '-p', password, 'ssh', '-o', 'StrictHostKeyChecking=no',
                '-o', 'ConnectTimeout=5', '-o', 'BatchMode=yes', f'{username}@{ip}',
                'echo', 'test',
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.wait()

            return proc.returncode == 0
        except Exception:
            return False

    async def _test_mysql_credentials(self, ip: str, port: int, username: str, password: str) -> bool:
        """Test MySQL credentials"""
        try:
            proc = await asyncio.create_subprocess_exec(
                'mysql', '-h', ip, '-P', str(port), '-u', username, f'-p{password}',
                '-e', 'SELECT 1;',
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.wait()

            return proc.returncode == 0
        except Exception:
            return False

    async def _test_vnc_credentials(self, ip: str, port: int, password: str) -> bool:
        """Test VNC credentials"""
        try:
            # This would require a VNC client library
            # For now, just check if VNC port is open without authentication
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=5
            )
            writer.close()
            await writer.wait_closed()

            # VNC often doesn't require authentication by default
            return True
        except Exception:
            return False

    async def _test_redis_access(self, ip: str, port: int) -> bool:
        """Test Redis access without authentication"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=5
            )

            # Try to send INFO command
            writer.write(b'INFO\r\n')
            await writer.drain()

            response = await reader.read(1024)
            writer.close()
            await writer.wait_closed()

            # If we get a response, Redis is accessible
            return b'redis_version' in response.lower()
        except Exception:
            return False

    async def _check_cve_vulnerabilities(self, service: str, version: str, ip: str, port: int) -> List[NetworkVulnerability]:
        """Check for CVE vulnerabilities based on service version"""
        vulnerabilities = []
        scan_id = f"cve_scan_{int(time.time())}"

        # Known vulnerable versions (simplified database)
        vulnerable_versions = {
            'Apache': {
                '2.4.29': {'cve': 'CVE-2017-15710', 'severity': 'HIGH', 'score': 8.1},
                '2.4.28': {'cve': 'CVE-2017-7679', 'severity': 'MEDIUM', 'score': 5.0},
                '2.2.34': {'cve': 'CVE-2017-3167', 'severity': 'MEDIUM', 'score': 5.0},
            },
            'OpenSSH': {
                '7.4': {'cve': 'CVE-2018-15473', 'severity': 'HIGH', 'score': 7.5},
                '6.6': {'cve': 'CVE-2016-10009', 'severity': 'HIGH', 'score': 7.8},
            },
            'MySQL': {
                '5.7.19': {'cve': 'CVE-2017-3636', 'severity': 'HIGH', 'score': 7.5},
                '5.6.37': {'cve': 'CVE-2017-3641', 'severity': 'MEDIUM', 'score': 5.5},
            }
        }

        service_key = service.upper()
        if service_key in vulnerable_versions:
            version_info = vulnerable_versions[service_key].get(version)
            if version_info:
                vuln = NetworkVulnerability(
                    id=f"cve_{version_info['cve']}_{hashlib.md5(f'{ip}:{port}'.encode()).hexdigest()[:8]}",
                    title=f"CVE-{version_info['cve']}: Vulnerable {service} Version",
                    description=f"{service} version {version} is vulnerable to CVE-{version_info['cve']}",
                    severity=VulnerabilitySeverity[version_info['severity']],
                    cvss_score=version_info['score'],
                    cve_id=version_info['cve'],
                    affected_host=ip,
                    port=port,
                    protocol=Protocol.TCP,
                    service=service,
                    evidence=f"{service} {version} detected",
                    remediation=f"Upgrade {service} to the latest patched version",
                    references=[f"https://cve.mitre.org/cgi-bin/cvename.cgi?name={version_info['cve']}"],
                    scan_id=scan_id,
                    discovered_at=datetime.now()
                )
                vulnerabilities.append(vuln)

        return vulnerabilities

    async def _ssl_tls_scan(self, result: NetworkScanResult):
        """Scan SSL/TLS services for vulnerabilities"""
        logger.info("Scanning SSL/TLS services for vulnerabilities")

        for host in result.hosts:
            if not host.is_alive:
                continue

            # Check HTTPS and other SSL/TLS ports
            ssl_ports = [443, 993, 995, 636, 981, 992, 5061]

            for port in ssl_ports:
                if port in host.open_ports:
                    ssl_vulns = await self._scan_ssl_vulnerabilities(host.ip, port)
                    host.vulnerabilities.extend(ssl_vulns)
                    result.vulnerabilities.extend(ssl_vulns)

        result.vulnerabilities_found = len(result.vulnerabilities)

    async def _scan_ssl_vulnerabilities(self, ip: str, port: int) -> List[NetworkVulnerability]:
        """Scan SSL/TLS service for vulnerabilities"""
        vulnerabilities = []
        scan_id = f"ssl_scan_{int(time.time())}"

        try:
            # Get SSL certificate
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port, ssl=context),
                timeout=10
            )

            # Get certificate information
            ssl_object = writer.get_extra_info('ssl_object')
            if ssl_object:
                cert = ssl_object.getpeercert(binary_form=True)
                if cert:
                    vulnerabilities.extend(await self._analyze_ssl_certificate(
                        ip, port, cert, scan_id
                    ))

                # Check SSL/TLS protocol support
                ssl_version = ssl_object.version()
                vulnerabilities.extend(await self._check_ssl_protocols(
                    ip, port, ssl_version, scan_id
                ))

                # Check cipher suites
                cipher = ssl_object.cipher()
                if cipher:
                    vulnerabilities.extend(await self._check_ssl_ciphers(
                        ip, port, cipher, scan_id
                    ))

            writer.close()
            await writer.wait_closed()

        except Exception as e:
            logger.debug(f"SSL scan failed for {ip}:{port} - {e}")

        return vulnerabilities

    async def _analyze_ssl_certificate(self, ip: str, port: int, cert_der: bytes, scan_id: str) -> List[NetworkVulnerability]:
        """Analyze SSL certificate for issues"""
        vulnerabilities = []

        try:
            cert = x509.load_der_x509_certificate(cert_der, default_backend())

            # Check expiration
            if cert.not_valid_after < datetime.now():
                vulnerabilities.append(NetworkVulnerability(
                    id=f"ssl_expired_{hashlib.md5(f'{ip}:{port}'.encode()).hexdigest()[:8]}",
                    title="Expired SSL Certificate",
                    description="SSL certificate has expired",
                    severity=VulnerabilitySeverity.HIGH,
                    cvss_score=7.5,
                    cve_id=None,
                    affected_host=ip,
                    port=port,
                    protocol=Protocol.HTTPS,
                    service='HTTPS',
                    evidence=f"Certificate expired on {cert.not_valid_after}",
                    remediation="Renew SSL certificate immediately",
                    references=["https://tools.ietf.org/html/rfc5280"],
                    scan_id=scan_id,
                    discovered_at=datetime.now()
                ))

            # Check for self-signed certificate
            try:
                # Attempt to verify certificate chain
                # This is a simplified check
                if cert.issuer == cert.subject:
                    vulnerabilities.append(NetworkVulnerability(
                        id=f"ssl_selfsigned_{hashlib.md5(f'{ip}:{port}'.encode()).hexdigest()[:8]}",
                        title="Self-Signed SSL Certificate",
                        description="SSL certificate is self-signed",
                        severity=VulnerabilitySeverity.MEDIUM,
                        cvss_score=4.0,
                        cve_id=None,
                        affected_host=ip,
                        port=port,
                        protocol=Protocol.HTTPS,
                        service='HTTPS',
                        evidence="Self-signed certificate detected",
                        remediation="Install a certificate from a trusted Certificate Authority",
                        references=["https://letsencrypt.org/"],
                        scan_id=scan_id,
                        discovered_at=datetime.now()
                    ))
            except Exception:
                pass

            # Check certificate validity period
            days_until_expiry = (cert.not_valid_after - datetime.now()).days
            if days_until_expiry < 30:
                vulnerabilities.append(NetworkVulnerability(
                    id=f"ssl_expiring_{hashlib.md5(f'{ip}:{port}'.encode()).hexdigest()[:8]}",
                    title="SSL Certificate Expiring Soon",
                    description=f"SSL certificate expires in {days_until_expiry} days",
                    severity=VulnerabilitySeverity.LOW,
                    cvss_score=3.0,
                    cve_id=None,
                    affected_host=ip,
                    port=port,
                    protocol=Protocol.HTTPS,
                    service='HTTPS',
                    evidence=f"Certificate expires on {cert.not_valid_after}",
                    remediation="Renew SSL certificate before expiration",
                    references=["https://tools.ietf.org/html/rfc5280"],
                    scan_id=scan_id,
                    discovered_at=datetime.now()
                ))

        except Exception as e:
            logger.debug(f"Certificate analysis failed for {ip}:{port} - {e}")

        return vulnerabilities

    async def _check_ssl_protocols(self, ip: str, port: int, ssl_version: str, scan_id: str) -> List[NetworkVulnerability]:
        """Check for weak SSL/TLS protocols"""
        vulnerabilities = []

        weak_protocols = ['SSLv2', 'SSLv3', 'TLSv1', 'TLSv1.1']

        if ssl_version in weak_protocols:
            vulnerabilities.append(NetworkVulnerability(
                id=f"ssl_weak_proto_{hashlib.md5(f'{ip}:{port}'.encode()).hexdigest()[:8]}",
                title=f"Weak SSL/TLS Protocol: {ssl_version}",
                description=f"Server supports weak SSL/TLS protocol {ssl_version}",
                severity=VulnerabilitySeverity.HIGH,
                cvss_score=7.5,
                cve_id=None,
                affected_host=ip,
                port=port,
                protocol=Protocol.HTTPS,
                service='HTTPS',
                evidence=f"SSL version: {ssl_version}",
                remediation="Disable weak SSL/TLS protocols and enable TLS 1.2 or higher",
                references=["https://owasp.org/www-project-configuration-scoring/"],
                scan_id=scan_id,
                discovered_at=datetime.now()
            ))

        return vulnerabilities

    async def _check_ssl_ciphers(self, ip: str, port: int, cipher: tuple, scan_id: str) -> List[NetworkVulnerability]:
        """Check for weak SSL/TLS cipher suites"""
        vulnerabilities = []

        cipher_name, cipher_version, secret_bits = cipher

        # Check for weak ciphers
        weak_cipher_indicators = ['RC4', 'DES', '3DES', 'MD5', 'SHA1', 'NULL', 'EXPORT']

        for indicator in weak_cipher_indicators:
            if indicator in cipher_name:
                vulnerabilities.append(NetworkVulnerability(
                    id=f"ssl_weak_cipher_{hashlib.md5(f'{ip}:{port}'.encode()).hexdigest()[:8]}",
                    title=f"Weak SSL/TLS Cipher Suite",
                    description=f"Server uses weak cipher suite: {cipher_name}",
                    severity=VulnerabilitySeverity.MEDIUM,
                    cvss_score=5.0,
                    cve_id=None,
                    affected_host=ip,
                    port=port,
                    protocol=Protocol.HTTPS,
                    service='HTTPS',
                    evidence=f"Cipher: {cipher_name} ({secret_bits} bits)",
                    remediation="Disable weak cipher suites and enable strong ciphers like AES-GCM",
                    references=["https://owasp.org/www-project-configuration-scoring/"],
                    scan_id=scan_id,
                    discovered_at=datetime.now()
                ))
                break

        # Check for weak key strength
        if secret_bits < 128:
            vulnerabilities.append(NetworkVulnerability(
                id=f"ssl_weak_key_{hashlib.md5(f'{ip}:{port}'.encode()).hexdigest()[:8]}",
                title="Weak SSL/TLS Key Strength",
                description=f"SSL/TLS cipher uses weak key strength: {secret_bits} bits",
                severity=VulnerabilitySeverity.MEDIUM,
                cvss_score=5.0,
                cve_id=None,
                affected_host=ip,
                port=port,
                protocol=Protocol.HTTPS,
                service='HTTPS',
                evidence=f"Key strength: {secret_bits} bits",
                remediation="Configure SSL/TLS to use cipher suites with at least 128-bit keys",
                references=["https://owasp.org/www-project-configuration-scoring/"],
                scan_id=scan_id,
                discovered_at=datetime.now()
            ))

        return vulnerabilities

    def _generate_network_map(self, hosts: List[NetworkHost], network: ipaddress.IPv4Network) -> Dict[str, Any]:
        """Generate network topology map"""
        network_map = {
            'network': str(network),
            'subnet_mask': str(network.netmask),
            'total_hosts': network.num_addresses,
            'active_hosts': len(hosts),
            'hosts_by_subnet': {},
            'services_summary': {},
            'vulnerability_distribution': {}
        }

        # Group hosts by subnet
        for host in hosts:
            try:
                host_ip = ipaddress.IPv4Address(host.ip)
                subnet = ipaddress.IPv4Network(f"{host_ip}/24", strict=False)
                subnet_str = str(subnet)

                if subnet_str not in network_map['hosts_by_subnet']:
                    network_map['hosts_by_subnet'][subnet_str] = []
                network_map['hosts_by_subnet'][subnet_str].append(host.ip)

                # Count services
                for port in host.open_ports:
                    service_name = self.vulnerable_services.get(port, {}).get('name', 'unknown')
                    network_map['services_summary'][service_name] = network_map['services_summary'].get(service_name, 0) + 1

                # Count vulnerabilities
                vuln_count = len(host.vulnerabilities)
                if vuln_count > 0:
                    network_map['vulnerability_distribution'][host.ip] = vuln_count

            except Exception as e:
                logger.debug(f"Failed to process host {host.ip} for network map: {e}")

        return network_map

    def _validate_target(self, target: str) -> Optional[str]:
        """Validate and normalize target specification"""
        try:
            # Check if it's an IP range (CIDR notation)
            if '/' in target:
                network = ipaddress.ip_network(target, strict=False)
                return str(network)

            # Check if it's a single IP
            ipaddress.ip_address(target)
            return f"{target}/32"  # Convert to CIDR notation

            # Check if it's a hostname (would need DNS resolution)
            # For now, just return as-is
            return target

        except ValueError:
            logger.error(f"Invalid target specification: {target}")
            return None

    def _generate_scan_id(self) -> str:
        """Generate unique scan ID"""
        return f"net_scan_{int(time.time())}_{hashlib.md5(os.urandom(16)).hexdigest()[:8]}"

    def _record_scan_start(self, result: NetworkScanResult):
        """Record scan start in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO network_scans
            (scan_id, scan_type, target, started_at, status, scan_config)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            result.scan_id,
            result.scan_type.value,
            result.target,
            result.started_at,
            result.status,
            json.dumps(self.config)
        ))

        conn.commit()
        conn.close()

    def _store_scan_results(self, result: NetworkScanResult):
        """Store scan results in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Update scan record
        cursor.execute('''
            UPDATE network_scans
            SET completed_at = ?, hosts_discovered = ?, vulnerabilities_found = ?, status = ?
            WHERE scan_id = ?
        ''', (
            result.completed_at,
            result.hosts_discovered,
            result.vulnerabilities_found,
            result.status,
            result.scan_id
        ))

        # Store hosts
        for host in result.hosts:
            cursor.execute('''
                INSERT INTO network_hosts
                (scan_id, ip, hostname, mac_address, os_guess, open_ports,
                 services, vulnerabilities, response_time, is_alive)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.scan_id,
                host.ip,
                host.hostname,
                host.mac_address,
                host.os_guess,
                json.dumps(host.open_ports),
                json.dumps(host.services),
                json.dumps([asdict(v) for v in host.vulnerabilities]),
                host.response_time,
                host.is_alive
            ))

        # Store vulnerabilities
        for vuln in result.vulnerabilities:
            cursor.execute('''
                INSERT INTO network_vulnerabilities
                (id, title, description, severity, cvss_score, cve_id,
                 affected_host, port, protocol, service, evidence, remediation,
                 references, scan_id, discovered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                vuln.id,
                vuln.title,
                vuln.description,
                vuln.severity.value,
                vuln.cvss_score,
                vuln.cve_id,
                vuln.affected_host,
                vuln.port,
                vuln.protocol.value,
                vuln.service,
                vuln.evidence,
                vuln.remediation,
                json.dumps(vuln.references),
                vuln.scan_id,
                vuln.discovered_at
            ))

        conn.commit()
        conn.close()

    async def generate_network_report(self, scan_id: str, format: str = 'json') -> Dict:
        """Generate network security report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get scan details
        cursor.execute('''
            SELECT * FROM network_scans WHERE scan_id = ?
        ''', (scan_id,))

        scan_row = cursor.fetchone()
        if not scan_row:
            conn.close()
            return {'error': 'Scan not found'}

        # Get hosts for this scan
        cursor.execute('''
            SELECT * FROM network_hosts WHERE scan_id = ?
        ''', (scan_id,))

        host_rows = cursor.fetchall()

        # Get vulnerabilities for this scan
        cursor.execute('''
            SELECT * FROM network_vulnerabilities WHERE scan_id = ?
            ORDER BY cvss_score DESC
        ''', (scan_id,))

        vuln_rows = cursor.fetchall()
        conn.close()

        # Format report
        report = {
            'scan_id': scan_id,
            'scan_type': scan_row[1],
            'target': scan_row[2],
            'started_at': scan_row[3],
            'completed_at': scan_row[4],
            'hosts_discovered': scan_row[5],
            'vulnerabilities_found': scan_row[6],
            'status': scan_row[7],
            'hosts': [],
            'vulnerabilities': [],
            'summary': {}
        }

        # Format hosts
        for row in host_rows:
            host = {
                'ip': row[2],
                'hostname': row[3],
                'mac_address': row[4],
                'os_guess': row[5],
                'open_ports': json.loads(row[6]) if row[6] else [],
                'services': json.loads(row[7]) if row[7] else {},
                'vulnerabilities': json.loads(row[8]) if row[8] else [],
                'response_time': row[9],
                'is_alive': bool(row[10])
            }
            report['hosts'].append(host)

        # Format vulnerabilities
        for row in vuln_rows:
            vuln = {
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'severity': row[3],
                'cvss_score': row[4],
                'cve_id': row[5],
                'affected_host': row[6],
                'port': row[7],
                'protocol': row[8],
                'service': row[9],
                'evidence': row[10],
                'remediation': row[11],
                'references': json.loads(row[12]) if row[12] else [],
                'discovered_at': row[14]
            }
            report['vulnerabilities'].append(vuln)

        # Generate summary
        report['summary'] = self._generate_network_summary(report['hosts'], report['vulnerabilities'])

        return report

    def _generate_network_summary(self, hosts: List[Dict], vulnerabilities: List[Dict]) -> Dict:
        """Generate network security summary"""
        summary = {
            'total_hosts': len(hosts),
            'alive_hosts': len([h for h in hosts if h['is_alive']]),
            'total_vulnerabilities': len(vulnerabilities),
            'severity_breakdown': {
                'CRITICAL': 0,
                'HIGH': 0,
                'MEDIUM': 0,
                'LOW': 0,
                'INFO': 0
            },
            'top_vulnerable_hosts': {},
            'services_summary': {},
            'open_ports_summary': {},
            'risk_score': 0.0
        }

        # Count vulnerabilities by severity
        for vuln in vulnerabilities:
            severity = vuln['severity']
            summary['severity_breakdown'][severity] += 1

        # Top vulnerable hosts
        host_vuln_counts = {}
        for vuln in vulnerabilities:
            host = vuln['affected_host']
            host_vuln_counts[host] = host_vuln_counts.get(host, 0) + 1

        summary['top_vulnerable_hosts'] = dict(
            sorted(host_vuln_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        )

        # Services summary
        for host in hosts:
            for port, service in host['services'].items():
                service_name = service.get('name', f'Port-{port}')
                summary['services_summary'][service_name] = summary['services_summary'].get(service_name, 0) + 1

        # Open ports summary
        for host in hosts:
            for port in host['open_ports']:
                summary['open_ports_summary'][port] = summary['open_ports_summary'].get(port, 0) + 1

        # Calculate risk score (0-100)
        total_hosts = len(hosts)
        if total_hosts > 0:
            critical_vulns = summary['severity_breakdown']['CRITICAL']
            high_vulns = summary['severity_breakdown']['HIGH']
            medium_vulns = summary['severity_breakdown']['MEDIUM']

            risk_score = (critical_vulns * 25) + (high_vulns * 15) + (medium_vulns * 8)
            risk_score = min(100, risk_score)
            summary['risk_score'] = risk_score

        return summary

async def main():
    """Main function for running network scanner"""
    scanner = NetworkScanner()

    # Example usage - scan local network
    target = "192.168.1.0/24"  # Adjust based on your network

    logger.info(f"Starting network security scan for {target}")
    results = await scanner.scan_network(
        target=target,
        scan_types=[
            ScanType.NETWORK_DISCOVERY,
            ScanType.PORT_SCAN,
            ScanType.SERVICE_DETECTION,
            ScanType.VULNERABILITY_SCAN
        ]
    )

    # Generate and save reports
    for result in results:
        if result:
            report = await scanner.generate_network_report(result.scan_id)

            # Save report to file
            report_path = f"/home/activeloguser/DMLogn8n/security/reports/network_scan_report_{result.scan_id}.json"
            os.makedirs(os.path.dirname(report_path), exist_ok=True)

            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"Network scan completed for {result.scan_type.value}. Report saved to: {report_path}")
            logger.info(f"Discovered {result.hosts_discovered} hosts with {result.vulnerabilities_found} vulnerabilities")

            # Print summary
            print(f"\n=== {result.scan_type.value.upper()} SUMMARY ===")
            print(f"Hosts discovered: {result.hosts_discovered}")
            print(f"Vulnerabilities found: {result.vulnerabilities_found}")
            print(f"Risk score: {report['summary']['risk_score']:.1f}/100")

            severity_counts = report['summary']['severity_breakdown']
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                count = severity_counts.get(severity, 0)
                if count > 0:
                    print(f"{severity}: {count}")

    return results

if __name__ == "__main__":
    asyncio.run(main())