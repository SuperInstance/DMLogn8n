#!/usr/bin/env python3
"""
DMLogn8n Security Manager
Central security management service for the multi-agent platform
"""

import asyncio
import json
import logging
import time
import hashlib
import secrets
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import yaml
import aiofiles
import redis.asyncio as redis
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import bcrypt
import aiomysql
from fastapi import HTTPException, Request, Response
import ssl
from ssl import SSLContext
import ipaddress
from collections import defaultdict, deque
import uuid

# Import security components
from .waf import WebApplicationFirewall, SecurityEvent, ThreatLevel
from .policies.authentication_policy import AuthenticationPolicy
from .policies.authorization_policy import AuthorizationPolicy
from .policies.data_protection_policy import DataProtectionPolicy
from .policies.api_security_policy import APISecurityPolicy
from .threats.detector import ThreatDetector
from .threats.prevention import ThreatPrevention
from .threats.intelligence import ThreatIntelligence
from .scanners.vulnerability_scanner import VulnerabilityScanner
from .scanners.dependency_scanner import DependencyScanner
from .scanners.compliance_scanner import ComplianceScanner

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityContext(Enum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_PROTECTION = "data_protection"
    API_SECURITY = "api_security"
    NETWORK_SECURITY = "network_security"
    COMPLIANCE = "compliance"

@dataclass
class SecurityPolicy:
    name: str
    context: SecurityContext
    enabled: bool
    priority: int
    rules: List[Dict[str, Any]]
    exceptions: List[str] = None
    last_updated: datetime = None

@dataclass
class SecurityIncident:
    id: str
    timestamp: datetime
    severity: str
    category: str
    description: str
    source_ip: str
    affected_user: Optional[str]
    affected_assets: List[str]
    mitigation_actions: List[str]
    status: str  # open, investigating, resolved, closed
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None

@dataclass
class SecurityMetrics:
    total_requests: int = 0
    blocked_requests: int = 0
    authenticated_users: int = 0
    failed_authentications: int = 0
    security_incidents: int = 0
    vulnerabilities_found: int = 0
    compliance_score: float = 0.0
    threat_intelligence_feeds: int = 0
    encrypted_data_transfers: int = 0

class SecurityManager:
    """
    Central security management system for DMLogn8n multi-agent platform
    """

    def __init__(self, config_path: str = "/home/activeloguser/DMLogn8n/security/config/"):
        self.config_path = config_path
        self.redis_client = None
        self.db_pool = None
        self.encryption_key = None
        self.jwt_secret = None
        self.policies = {}
        self.active_incidents = {}
        self.security_metrics = SecurityMetrics()
        self.session_store = {}
        self.api_keys = {}
        self.certificate_store = {}
        self.compliance_standards = {}

        # Initialize security components
        self.waf = None
        self.auth_policy = None
        self.authz_policy = None
        self.data_policy = None
        self.api_policy = None
        self.threat_detector = None
        self.threat_prevention = None
        self.threat_intelligence = None
        self.vuln_scanner = None
        self.dep_scanner = None
        self.compliance_scanner = None

        # Security contexts and states
        self.security_contexts = {
            SecurityContext.AUTHENTICATION: [],
            SecurityContext.AUTHORIZATION: [],
            SecurityContext.DATA_PROTECTION: [],
            SecurityContext.API_SECURITY: [],
            SecurityContext.NETWORK_SECURITY: [],
            SecurityContext.COMPLIANCE: []
        }

    async def initialize(self):
        """Initialize the security manager and all components"""
        try:
            logger.info("Initializing Security Manager...")

            # Load configuration
            await self.load_configuration()

            # Initialize database connection
            await self.initialize_database()

            # Initialize Redis
            await self.initialize_redis()

            # Initialize encryption
            await self.initialize_encryption()

            # Initialize security components
            await self.initialize_security_components()

            # Load security policies
            await self.load_security_policies()

            # Initialize threat intelligence
            await self.initialize_threat_intelligence()

            # Start background tasks
            await self.start_background_tasks()

            logger.info("Security Manager initialized successfully")

        except Exception as e:
            logger.error(f"Security Manager initialization failed: {e}")
            raise

    async def load_configuration(self):
        """Load security configuration files"""
        try:
            # Load main security config
            config_file = f"{self.config_path}/security-config.yaml"
            async with aiofiles.open(config_file, 'r') as f:
                config = yaml.safe_load(await f.read())

            self.security_config = config

            # Load compliance standards
            compliance_file = f"{self.config_path}/compliance-policies.yaml"
            async with aiofiles.open(compliance_file, 'r') as f:
                self.compliance_standards = yaml.safe_load(await f.read())

            logger.info("Security configuration loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load security configuration: {e}")
            # Set default configuration
            self.security_config = {
                'encryption': {
                    'algorithm': 'AES-256-GCM',
                    'key_rotation_days': 90
                },
                'authentication': {
                    'password_policy': {
                        'min_length': 12,
                        'require_uppercase': True,
                        'require_lowercase': True,
                        'require_numbers': True,
                        'require_special': True
                    },
                    'session_timeout': 3600,
                    'max_failed_attempts': 5,
                    'lockout_duration': 900
                },
                'api_security': {
                    'rate_limiting': {
                        'requests_per_minute': 100,
                        'burst_limit': 200
                    },
                    'key_rotation_days': 30
                }
            }

    async def initialize_database(self):
        """Initialize database connection for security logs and policies"""
        try:
            self.db_pool = await aiomysql.create_pool(
                host='localhost',
                port=3306,
                user='dmlogn8n_sec',
                password='secure_password',
                db='dmlogn8n_security',
                minsize=5,
                maxsize=20
            )

            # Create security tables if they don't exist
            await self.create_security_tables()

            logger.info("Security database initialized")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            # Continue without database for now
            self.db_pool = None

    async def create_security_tables(self):
        """Create security-related database tables"""
        if not self.db_pool:
            return

        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # Security incidents table
                    await cursor.execute("""
                        CREATE TABLE IF NOT EXISTS security_incidents (
                            id VARCHAR(36) PRIMARY KEY,
                            timestamp DATETIME,
                            severity ENUM('low', 'medium', 'high', 'critical'),
                            category VARCHAR(50),
                            description TEXT,
                            source_ip VARCHAR(45),
                            affected_user VARCHAR(50),
                            affected_assets JSON,
                            mitigation_actions JSON,
                            status ENUM('open', 'investigating', 'resolved', 'closed'),
                            assigned_to VARCHAR(50),
                            resolution_notes TEXT,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                        )
                    """)

                    # Security events table
                    await cursor.execute("""
                        CREATE TABLE IF NOT EXISTS security_events (
                            id VARCHAR(36) PRIMARY KEY,
                            timestamp DATETIME,
                            event_type VARCHAR(50),
                            source_ip VARCHAR(45),
                            user_agent TEXT,
                            request_data JSON,
                            response_data JSON,
                            threat_level VARCHAR(20),
                            action_taken VARCHAR(20),
                            details JSON,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    # Security policies table
                    await cursor.execute("""
                        CREATE TABLE IF NOT EXISTS security_policies (
                            id VARCHAR(36) PRIMARY KEY,
                            name VARCHAR(100) UNIQUE,
                            context VARCHAR(50),
                            enabled BOOLEAN,
                            priority INT,
                            rules JSON,
                            exceptions JSON,
                            last_updated DATETIME,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                        )
                    """)

                    # API keys table
                    await cursor.execute("""
                        CREATE TABLE IF NOT EXISTS api_keys (
                            id VARCHAR(36) PRIMARY KEY,
                            key_hash VARCHAR(64),
                            name VARCHAR(100),
                            permissions JSON,
                            rate_limit INT,
                            expires_at DATETIME,
                            created_by VARCHAR(50),
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            last_used DATETIME,
                            is_active BOOLEAN DEFAULT TRUE
                        )
                    """)

                    await conn.commit()

        except Exception as e:
            logger.error(f"Failed to create security tables: {e}")

    async def initialize_redis(self):
        """Initialize Redis for caching and session storage"""
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=1,  # Use separate DB for security
                decode_responses=True
            )

            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection established")

        except Exception as e:
            logger.error(f"Redis initialization failed: {e}")
            self.redis_client = None

    async def initialize_encryption(self):
        """Initialize encryption keys and cryptographic components"""
        try:
            # Generate encryption key
            password = self.security_config.get('encryption', {}).get('master_password', 'default_password')
            salt = b'dmlogn8n_security_salt'

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            self.encryption_key = Fernet(key)

            # Generate JWT secret
            self.jwt_secret = secrets.token_urlsafe(32)

            logger.info("Encryption initialized successfully")

        except Exception as e:
            logger.error(f"Encryption initialization failed: {e}")
            raise

    async def initialize_security_components(self):
        """Initialize all security components"""
        try:
            # Initialize WAF
            from .waf import create_waf
            from fastapi import FastAPI
            dummy_app = FastAPI()
            self.waf = create_waf(dummy_app, f"{self.config_path}/waf-rules.yaml")
            await self.waf.startup()

            # Initialize security policies
            self.auth_policy = AuthenticationPolicy(self.security_config.get('authentication', {}))
            self.authz_policy = AuthorizationPolicy(self.security_config.get('authorization', {}))
            self.data_policy = DataProtectionPolicy(self.security_config.get('data_protection', {}))
            self.api_policy = APISecurityPolicy(self.security_config.get('api_security', {}))

            # Initialize threat detection and prevention
            self.threat_detector = ThreatDetector()
            self.threat_prevention = ThreatPrevention()
            self.threat_intelligence = ThreatIntelligence()

            # Initialize scanners
            self.vuln_scanner = VulnerabilityScanner()
            self.dep_scanner = DependencyScanner()
            self.compliance_scanner = ComplianceScanner(self.compliance_standards)

            logger.info("Security components initialized")

        except Exception as e:
            logger.error(f"Security components initialization failed: {e}")
            raise

    async def load_security_policies(self):
        """Load security policies from database and configuration"""
        try:
            if self.db_pool:
                async with self.db_pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute("SELECT * FROM security_policies WHERE enabled = TRUE")
                        policies = await cursor.fetchall()

                        for policy_data in policies:
                            policy = SecurityPolicy(
                                id=policy_data[0],
                                name=policy_data[1],
                                context=SecurityContext(policy_data[2]),
                                enabled=policy_data[3],
                                priority=policy_data[4],
                                rules=json.loads(policy_data[5]),
                                exceptions=json.loads(policy_data[6]) if policy_data[6] else [],
                                last_updated=policy_data[7]
                            )
                            self.policies[policy.name] = policy

            logger.info(f"Loaded {len(self.policies)} security policies")

        except Exception as e:
            logger.error(f"Failed to load security policies: {e}")

    async def initialize_threat_intelligence(self):
        """Initialize threat intelligence feeds"""
        try:
            await self.threat_intelligence.initialize_feeds()
            logger.info("Threat intelligence initialized")

        except Exception as e:
            logger.error(f"Threat intelligence initialization failed: {e}")

    async def start_background_tasks(self):
        """Start background security tasks"""
        try:
            # Security metrics collection
            asyncio.create_task(self.collect_security_metrics())

            # Threat intelligence updates
            asyncio.create_task(self.update_threat_intelligence())

            # Vulnerability scanning
            asyncio.create_task(self.periodic_vulnerability_scan())

            # Compliance checking
            asyncio.create_task(self.periodic_compliance_check())

            # Security log rotation
            asyncio.create_task(self.rotate_security_logs())

            # Key rotation
            asyncio.create_task(self.rotate_encryption_keys())

            logger.info("Background security tasks started")

        except Exception as e:
            logger.error(f"Failed to start background tasks: {e}")

    async def authenticate_user(self, username: str, password: str, request: Request) -> Optional[Dict[str, Any]]:
        """Authenticate user with comprehensive security checks"""
        try:
            # Get client IP
            client_ip = self.get_client_ip(request)

            # Check for brute force attempts
            if await self.is_brute_force_attempt(client_ip, username):
                await self.handle_brute_force(client_ip, username)
                return None

            # Validate password policy compliance
            if not self.auth_policy.validate_password_format(password):
                await self.log_security_event(
                    "Invalid password format",
                    client_ip,
                    {"username": username}
                )
                return None

            # Authenticate against user store (simplified for demo)
            user = await self.authenticate_user_credential(username, password)
            if not user:
                await self.record_failed_authentication(client_ip, username)
                return None

            # Create secure session
            session_token = await self.create_user_session(user, client_ip)

            # Log successful authentication
            await self.log_security_event(
                "Successful authentication",
                client_ip,
                {"username": username, "user_id": user['id']}
            )

            self.security_metrics.authenticated_users += 1

            return {
                "user": user,
                "session_token": session_token,
                "expires_at": datetime.now() + timedelta(seconds=self.auth_policy.session_timeout)
            }

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    async def authorize_request(self, request: Request, user: Dict[str, Any]) -> bool:
        """Authorize request based on user permissions and policies"""
        try:
            # Check authorization policies
            if not await self.authz_policy.check_permission(user, request):
                await self.log_security_event(
                    "Unauthorized access attempt",
                    self.get_client_ip(request),
                    {"user_id": user.get('id'), "path": request.url.path}
                )
                return False

            # Check resource-specific permissions
            if not await self.check_resource_permissions(user, request):
                return False

            # Check contextual security policies
            if not await self.apply_contextual_policies(request, user):
                return False

            return True

        except Exception as e:
            logger.error(f"Authorization error: {e}")
            return False

    async def validate_api_request(self, request: Request, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate API request with comprehensive security checks"""
        try:
            # Validate API key format
            if not self.api_policy.validate_api_key_format(api_key):
                return None

            # Check API key against store
            key_data = await self.get_api_key_data(api_key)
            if not key_data:
                return None

            # Check if key is active and not expired
            if not key_data['is_active'] or key_data['expires_at'] < datetime.now():
                return None

            # Apply rate limiting
            if not await self.api_policy.check_rate_limit(api_key, request):
                return None

            # Check API permissions
            if not await self.api_policy.check_api_permissions(key_data, request):
                return None

            # Update last used timestamp
            await self.update_api_key_usage(api_key)

            return key_data

        except Exception as e:
            logger.error(f"API validation error: {e}")
            return None

    async def encrypt_sensitive_data(self, data: str, context: str = "general") -> str:
        """Encrypt sensitive data with context-specific keys"""
        try:
            # Apply data protection policies
            if not self.data_policy.allow_encryption(context):
                raise ValueError("Encryption not allowed for this context")

            # Encrypt data
            encrypted_data = self.encryption_key.encrypt(data.encode())

            # Log encryption event
            await self.log_security_event(
                "Data encrypted",
                "system",
                {"context": context, "data_size": len(data)}
            )

            self.security_metrics.encrypted_data_transfers += 1

            return base64.urlsafe_b64encode(encrypted_data).decode()

        except Exception as e:
            logger.error(f"Data encryption error: {e}")
            raise

    async def decrypt_sensitive_data(self, encrypted_data: str, context: str = "general") -> str:
        """Decrypt sensitive data with context-specific validation"""
        try:
            # Apply data protection policies
            if not self.data_policy.allow_decryption(context):
                raise ValueError("Decryption not allowed for this context")

            # Decrypt data
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.encryption_key.decrypt(encrypted_bytes)

            # Log decryption event
            await self.log_security_event(
                "Data decrypted",
                "system",
                {"context": context, "data_size": len(decrypted_data)}
            )

            return decrypted_data.decode()

        except Exception as e:
            logger.error(f"Data decryption error: {e}")
            raise

    async def detect_threats(self, request: Request, response: Response = None) -> List[SecurityEvent]:
        """Detect threats in request and response"""
        try:
            threats = []

            # Use WAF for basic threat detection
            if self.waf:
                waf_threats = await self.waf.check_waf_rules(request, {
                    'client_ip': self.get_client_ip(request),
                    'user_agent': request.headers.get('user-agent', ''),
                    'method': request.method,
                    'path': request.url.path,
                    'query_string': str(request.url.query),
                    'timestamp': time.time()
                })

                if waf_threats:
                    threats.extend([waf_threats[0]])

            # Use advanced threat detector
            advanced_threats = await self.threat_detector.analyze_request(request, response)
            threats.extend(advanced_threats)

            # Check against threat intelligence
            intel_threats = await self.threat_intelligence.check_request(request)
            threats.extend(intel_threats)

            # Process detected threats
            for threat in threats:
                await self.handle_detected_threat(threat)

            return threats

        except Exception as e:
            logger.error(f"Threat detection error: {e}")
            return []

    async def handle_detected_threat(self, threat: SecurityEvent):
        """Handle detected security threat"""
        try:
            # Log threat
            await self.log_security_event(
                f"Threat detected: {threat.threat_type}",
                threat.source_ip,
                threat.details
            )

            # Apply threat prevention measures
            await self.threat_prevention.apply_measures(threat)

            # Create security incident if high severity
            if threat.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                await self.create_security_incident(
                    category=threat.threat_type,
                    severity=threat.threat_level.value,
                    description=f"Security threat detected: {threat.threat_type}",
                    source_ip=threat.source_ip,
                    affected_assets=[threat.request_path]
                )

        except Exception as e:
            logger.error(f"Threat handling error: {e}")

    async def create_security_incident(self, category: str, severity: str, description: str,
                                    source_ip: str, affected_assets: List[str]) -> str:
        """Create security incident record"""
        try:
            incident_id = str(uuid.uuid4())
            incident = SecurityIncident(
                id=incident_id,
                timestamp=datetime.now(),
                severity=severity,
                category=category,
                description=description,
                source_ip=source_ip,
                affected_user=None,
                affected_assets=affected_assets,
                mitigation_actions=[],
                status="open"
            )

            self.active_incidents[incident_id] = incident
            self.security_metrics.security_incidents += 1

            # Store in database
            if self.db_pool:
                await self.store_security_incident(incident)

            # Store in Redis for real-time access
            if self.redis_client:
                await self.redis_client.setex(
                    f"security:incident:{incident_id}",
                    86400,  # 24 hours
                    json.dumps(asdict(incident))
                )

            logger.warning(f"Security incident created: {incident_id} - {description}")
            return incident_id

        except Exception as e:
            logger.error(f"Failed to create security incident: {e}")
            return None

    async def scan_vulnerabilities(self) -> Dict[str, Any]:
        """Perform comprehensive vulnerability scan"""
        try:
            scan_results = {
                'timestamp': datetime.now().isoformat(),
                'vulnerabilities': [],
                'risk_score': 0,
                'recommendations': []
            }

            # System vulnerability scan
            system_vulns = await self.vuln_scanner.scan_system()
            scan_results['vulnerabilities'].extend(system_vulns)

            # Dependency vulnerability scan
            dep_vulns = await self.dep_scanner.scan_dependencies()
            scan_results['vulnerabilities'].extend(dep_vulns)

            # Application vulnerability scan
            app_vulns = await self.vuln_scanner.scan_application()
            scan_results['vulnerabilities'].extend(app_vulns)

            # Calculate risk score
            scan_results['risk_score'] = self.calculate_risk_score(scan_results['vulnerabilities'])

            # Generate recommendations
            scan_results['recommendations'] = self.generate_security_recommendations(scan_results['vulnerabilities'])

            # Store scan results
            if self.redis_client:
                await self.redis_client.setex(
                    "security:last_vulnerability_scan",
                    86400,
                    json.dumps(scan_results)
                )

            self.security_metrics.vulnerabilities_found = len(scan_results['vulnerabilities'])

            return scan_results

        except Exception as e:
            logger.error(f"Vulnerability scan error: {e}")
            return {'error': str(e)}

    async def check_compliance(self) -> Dict[str, Any]:
        """Check compliance against security standards"""
        try:
            compliance_results = {
                'timestamp': datetime.now().isoformat(),
                'standards': {},
                'overall_score': 0,
                'violations': [],
                'recommendations': []
            }

            # Check each compliance standard
            for standard_name, standard_config in self.compliance_standards.items():
                standard_result = await self.compliance_scanner.check_standard(standard_name, standard_config)
                compliance_results['standards'][standard_name] = standard_result

                # Collect violations
                if standard_result.get('violations'):
                    compliance_results['violations'].extend(standard_result['violations'])

            # Calculate overall compliance score
            if compliance_results['standards']:
                total_score = sum(result.get('score', 0) for result in compliance_results['standards'].values())
                compliance_results['overall_score'] = total_score / len(compliance_results['standards'])

            self.security_metrics.compliance_score = compliance_results['overall_score']

            # Store compliance results
            if self.redis_client:
                await self.redis_client.setex(
                    "security:last_compliance_check",
                    86400,
                    json.dumps(compliance_results)
                )

            return compliance_results

        except Exception as e:
            logger.error(f"Compliance check error: {e}")
            return {'error': str(e)}

    async def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'metrics': asdict(self.security_metrics),
                'active_incidents': len(self.active_incidents),
                'recent_threats': await self.get_recent_threats(),
                'vulnerability_summary': await self.get_vulnerability_summary(),
                'compliance_status': await self.get_compliance_status(),
                'recommendations': await self.generate_security_recommendations(),
                'security_posture': await self.assess_security_posture()
            }

            return report

        except Exception as e:
            logger.error(f"Security report generation error: {e}")
            return {'error': str(e)}

    async def get_security_dashboard(self) -> Dict[str, Any]:
        """Get real-time security dashboard data"""
        try:
            dashboard = {
                'timestamp': datetime.now().isoformat(),
                'metrics': asdict(self.security_metrics),
                'active_incidents': [asdict(inc) for inc in self.active_incidents.values()],
                'recent_events': await self.get_recent_security_events(),
                'threat_feed_status': await self.threat_intelligence.get_feed_status() if self.threat_intelligence else {},
                'waf_status': await self.waf.get_security_dashboard() if self.waf else {},
                'compliance_score': self.security_metrics.compliance_score,
                'security_posture': await self.assess_security_posture()
            }

            return dashboard

        except Exception as e:
            logger.error(f"Security dashboard error: {e}")
            return {'error': str(e)}

    # Helper methods
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    async def authenticate_user_credential(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user credentials (simplified implementation)"""
        # In production, this would query a proper user database
        if username == "admin" and password == "SecurePassword123!":
            return {
                'id': 'admin_user',
                'username': 'admin',
                'role': 'administrator',
                'permissions': ['all']
            }
        return None

    async def create_user_session(self, user: Dict[str, Any], client_ip: str) -> str:
        """Create secure user session"""
        session_id = secrets.token_urlsafe(32)
        session_data = {
            'user_id': user['id'],
            'username': user['username'],
            'role': user['role'],
            'client_ip': client_ip,
            'created_at': datetime.now().isoformat()
        }

        # Store session
        if self.redis_client:
            await self.redis_client.setex(
                f"session:{session_id}",
                self.auth_policy.session_timeout,
                json.dumps(session_data)
            )

        return session_id

    async def is_brute_force_attempt(self, client_ip: str, username: str) -> bool:
        """Check for brute force attempts"""
        if not self.redis_client:
            return False

        # Check failed attempts from IP
        ip_key = f"auth:failed:ip:{client_ip}"
        ip_attempts = await self.redis_client.get(ip_key)

        # Check failed attempts for username
        username_key = f"auth:failed:username:{username}"
        username_attempts = await self.redis_client.get(username_key)

        max_attempts = self.auth_policy.max_failed_attempts

        return (ip_attempts and int(ip_attempts) >= max_attempts) or \
               (username_attempts and int(username_attempts) >= max_attempts)

    async def handle_brute_force(self, client_ip: str, username: str):
        """Handle brute force attempts"""
        # Block IP temporarily
        if self.waf:
            await self.waf.block_ip(client_ip, "Brute force attack", 900)

        # Log incident
        await self.create_security_incident(
            category="brute_force",
            severity="high",
            description=f"Brute force attack detected from {client_ip} targeting {username}",
            source_ip=client_ip,
            affected_assets=["authentication_system"]
        )

    async def log_security_event(self, event_type: str, source_ip: str, details: Dict[str, Any]):
        """Log security event"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'source_ip': source_ip,
            'details': details
        }

        # Store in Redis
        if self.redis_client:
            await self.redis_client.lpush("security:events", json.dumps(event))
            await self.redis_client.ltrim("security:events", 0, 10000)

        # Store in database
        if self.db_pool:
            await self.store_security_event(event)

    async def store_security_event(self, event: Dict[str, Any]):
        """Store security event in database"""
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "INSERT INTO security_events (id, timestamp, event_type, source_ip, details) VALUES (%s, %s, %s, %s, %s)",
                        (str(uuid.uuid4()), event['timestamp'], event['event_type'], event['source_ip'], json.dumps(event['details']))
                    )
                    await conn.commit()
        except Exception as e:
            logger.error(f"Failed to store security event: {e}")

    async def store_security_incident(self, incident: SecurityIncident):
        """Store security incident in database"""
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """INSERT INTO security_incidents
                           (id, timestamp, severity, category, description, source_ip, affected_assets, status)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                        (incident.id, incident.timestamp, incident.severity, incident.category,
                         incident.description, incident.source_ip, json.dumps(incident.affected_assets), incident.status)
                    )
                    await conn.commit()
        except Exception as e:
            logger.error(f"Failed to store security incident: {e}")

    async def collect_security_metrics(self):
        """Periodic security metrics collection"""
        while True:
            try:
                await asyncio.sleep(300)  # Collect every 5 minutes

                # Update metrics from various sources
                if self.waf:
                    waf_metrics = await self.waf.get_security_dashboard()
                    self.security_metrics.total_requests = waf_metrics.get('metrics', {}).get('requests_total', 0)
                    self.security_metrics.blocked_requests = waf_metrics.get('metrics', {}).get('requests_blocked', 0)

                # Store metrics in Redis
                if self.redis_client:
                    await self.redis_client.setex(
                        "security:metrics",
                        3600,
                        json.dumps(asdict(self.security_metrics))
                    )

            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(60)

    async def update_threat_intelligence(self):
        """Update threat intelligence feeds"""
        while True:
            try:
                await asyncio.sleep(3600)  # Update every hour

                if self.threat_intelligence:
                    await self.threat_intelligence.update_feeds()
                    self.security_metrics.threat_intelligence_feeds = len(self.threat_intelligence.active_feeds)

            except Exception as e:
                logger.error(f"Threat intelligence update error: {e}")
                await asyncio.sleep(300)

    async def periodic_vulnerability_scan(self):
        """Periodic vulnerability scanning"""
        while True:
            try:
                await asyncio.sleep(86400)  # Scan daily

                scan_results = await self.scan_vulnerabilities()
                if scan_results.get('vulnerabilities'):
                    logger.warning(f"Found {len(scan_results['vulnerabilities'])} vulnerabilities")

            except Exception as e:
                logger.error(f"Periodic vulnerability scan error: {e}")
                await asyncio.sleep(3600)

    async def periodic_compliance_check(self):
        """Periodic compliance checking"""
        while True:
            try:
                await asyncio.sleep(604800)  # Check weekly

                compliance_results = await self.check_compliance()
                if compliance_results.get('overall_score', 0) < 80:
                    logger.warning(f"Low compliance score: {compliance_results['overall_score']}%")

            except Exception as e:
                logger.error(f"Periodic compliance check error: {e}")
                await asyncio.sleep(86400)

    async def rotate_security_logs(self):
        """Rotate security logs"""
        while True:
            try:
                await asyncio.sleep(86400)  # Rotate daily

                if self.redis_client:
                    # Archive old events
                    events = await self.redis_client.lrange("security:events", 0, -1)
                    if len(events) > 10000:
                        # Keep only recent 10000 events
                        await self.redis_client.ltrim("security:events", 0, 9999)

            except Exception as e:
                logger.error(f"Log rotation error: {e}")
                await asyncio.sleep(3600)

    async def rotate_encryption_keys(self):
        """Rotate encryption keys periodically"""
        while True:
            try:
                rotation_days = self.security_config.get('encryption', {}).get('key_rotation_days', 90)
                await asyncio.sleep(rotation_days * 86400)

                # Generate new encryption key
                await self.initialize_encryption()
                logger.info("Encryption keys rotated")

            except Exception as e:
                logger.error(f"Key rotation error: {e}")
                await asyncio.sleep(86400)

    def calculate_risk_score(self, vulnerabilities: List[Dict]) -> float:
        """Calculate risk score from vulnerabilities"""
        if not vulnerabilities:
            return 0.0

        severity_weights = {'low': 1, 'medium': 3, 'high': 7, 'critical': 10}
        total_score = 0

        for vuln in vulnerabilities:
            severity = vuln.get('severity', 'low').lower()
            total_score += severity_weights.get(severity, 1)

        # Normalize to 0-100 scale
        max_possible_score = len(vulnerabilities) * 10
        return min(100, (total_score / max_possible_score) * 100) if max_possible_score > 0 else 0

    async def generate_security_recommendations(self, vulnerabilities: List[Dict] = None) -> List[str]:
        """Generate security recommendations"""
        recommendations = []

        if vulnerabilities is None:
            # Get latest vulnerability scan
            if self.redis_client:
                scan_data = await self.redis_client.get("security:last_vulnerability_scan")
                if scan_data:
                    scan_results = json.loads(scan_data)
                    vulnerabilities = scan_results.get('vulnerabilities', [])

        if vulnerabilities:
            high_vulns = [v for v in vulnerabilities if v.get('severity') == 'high']
            critical_vulns = [v for v in vulnerabilities if v.get('severity') == 'critical']

            if critical_vulns:
                recommendations.append(f"URGENT: Address {len(critical_vulns)} critical vulnerabilities immediately")

            if high_vulns:
                recommendations.append(f"HIGH: Address {len(high_vulns)} high-severity vulnerabilities within 7 days")

            recommendations.append("Implement regular vulnerability scanning and patching")
            recommendations.append("Establish security incident response procedures")

        # Add general recommendations based on metrics
        if self.security_metrics.blocked_requests > self.security_metrics.total_requests * 0.1:
            recommendations.append("Investigate high block rate - possible ongoing attack")

        if self.security_metrics.compliance_score < 80:
            recommendations.append("Improve compliance posture - address compliance violations")

        recommendations.extend([
            "Regular security awareness training for all users",
            "Implement principle of least privilege",
            "Regular security audits and penetration testing",
            "Monitor and review security logs regularly"
        ])

        return recommendations

    async def assess_security_posture(self) -> str:
        """Assess overall security posture"""
        score = 0

        # Vulnerability score (40%)
        vuln_score = max(0, 100 - self.calculate_risk_score([]))  # Placeholder
        score += vuln_score * 0.4

        # Compliance score (30%)
        score += self.security_metrics.compliance_score * 0.3

        # Incident rate (20%)
        incident_score = max(0, 100 - (len(self.active_incidents) * 10))
        score += incident_score * 0.2

        # Configuration score (10%)
        config_score = 100  # Assume good configuration
        score += config_score * 0.1

        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Fair"
        elif score >= 40:
            return "Poor"
        else:
            return "Critical"

    async def get_recent_threats(self, limit: int = 10) -> List[Dict]:
        """Get recent security threats"""
        if not self.redis_client:
            return []

        try:
            events = await self.redis_client.lrange("security:events", 0, limit - 1)
            threats = []
            for event_json in events:
                event = json.loads(event_json)
                if 'threat' in event.get('event_type', '').lower():
                    threats.append(event)
            return threats
        except Exception as e:
            logger.error(f"Failed to get recent threats: {e}")
            return []

    async def get_vulnerability_summary(self) -> Dict[str, Any]:
        """Get vulnerability scan summary"""
        if not self.redis_client:
            return {}

        try:
            scan_data = await self.redis_client.get("security:last_vulnerability_scan")
            if scan_data:
                scan_results = json.loads(scan_data)
                return {
                    'last_scan': scan_results.get('timestamp'),
                    'total_vulnerabilities': len(scan_results.get('vulnerabilities', [])),
                    'risk_score': scan_results.get('risk_score', 0),
                    'critical_count': len([v for v in scan_results.get('vulnerabilities', []) if v.get('severity') == 'critical']),
                    'high_count': len([v for v in scan_results.get('vulnerabilities', []) if v.get('severity') == 'high'])
                }
        except Exception as e:
            logger.error(f"Failed to get vulnerability summary: {e}")
            return {}

    async def get_compliance_status(self) -> Dict[str, Any]:
        """Get compliance status summary"""
        if not self.redis_client:
            return {}

        try:
            compliance_data = await self.redis_client.get("security:last_compliance_check")
            if compliance_data:
                results = json.loads(compliance_data)
                return {
                    'overall_score': results.get('overall_score', 0),
                    'standards_checked': len(results.get('standards', {})),
                    'violations_count': len(results.get('violations', [])),
                    'last_check': results.get('timestamp')
                }
        except Exception as e:
            logger.error(f"Failed to get compliance status: {e}")
            return {}

    async def get_recent_security_events(self, limit: int = 20) -> List[Dict]:
        """Get recent security events"""
        if not self.redis_client:
            return []

        try:
            events = await self.redis_client.lrange("security:events", 0, limit - 1)
            return [json.loads(event) for event in events]
        except Exception as e:
            logger.error(f"Failed to get recent security events: {e}")
            return []

    async def check_resource_permissions(self, user: Dict[str, Any], request: Request) -> bool:
        """Check if user has permission to access specific resource"""
        # Simplified implementation - in production, this would check against ACL
        if user.get('role') == 'administrator':
            return True

        # Check basic path permissions
        path = request.url.path
        if path.startswith('/admin/') and user.get('role') != 'administrator':
            return False

        return True

    async def apply_contextual_policies(self, request: Request, user: Dict[str, Any]) -> bool:
        """Apply contextual security policies"""
        # Time-based access control
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:  # Outside business hours
            if user.get('role') not in ['administrator', 'security_admin']:
                # Require additional authentication
                return False

        # Location-based access control (simplified)
        client_ip = self.get_client_ip(request)
        if await self.is_suspicious_location(client_ip):
            return False

        return True

    async def is_suspicious_location(self, ip_address: str) -> bool:
        """Check if IP address is from suspicious location"""
        # Simplified implementation - in production, use GeoIP
        suspicious_ranges = ['192.168.1.', '10.0.0.']
        return any(ip_address.startswith(prefix) for prefix in suspicious_ranges)

    async def get_api_key_data(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Get API key data from store"""
        # In production, this would query database
        # For demo, return mock data
        if api_key == "demo_api_key_12345":
            return {
                'id': 'demo_key',
                'name': 'Demo API Key',
                'permissions': ['read', 'write'],
                'rate_limit': 1000,
                'expires_at': datetime.now() + timedelta(days=30),
                'is_active': True
            }
        return None

    async def update_api_key_usage(self, api_key: str):
        """Update API key last used timestamp"""
        # In production, this would update database
        pass

    async def record_failed_authentication(self, client_ip: str, username: str):
        """Record failed authentication attempt"""
        if not self.redis_client:
            return

        # Increment failed attempts for IP
        ip_key = f"auth:failed:ip:{client_ip}"
        await self.redis_client.incr(ip_key)
        await self.redis_client.expire(ip_key, 900)  # 15 minutes

        # Increment failed attempts for username
        username_key = f"auth:failed:username:{username}"
        await self.redis_client.incr(username_key)
        await self.redis_client.expire(username_key, 900)

        self.security_metrics.failed_authentications += 1

# Singleton instance
security_manager = None

async def get_security_manager() -> SecurityManager:
    """Get singleton security manager instance"""
    global security_manager
    if security_manager is None:
        security_manager = SecurityManager()
        await security_manager.initialize()
    return security_manager

# CLI interface
async def security_cli():
    """Command-line interface for security management"""
    import argparse

    parser = argparse.ArgumentParser(description="DMLogn8n Security Manager CLI")
    parser.add_argument("--scan-vulnerabilities", action="store_true", help="Run vulnerability scan")
    parser.add_argument("--check-compliance", action="store_true", help="Run compliance check")
    parser.add_argument("--generate-report", action="store_true", help="Generate security report")
    parser.add_argument("--show-dashboard", action="store_true", help="Show security dashboard")
    parser.add_argument("--block-ip", help="Block an IP address")
    parser.add_argument("--create-api-key", help="Create new API key")

    args = parser.parse_args()

    manager = await get_security_manager()

    if args.scan_vulnerabilities:
        results = await manager.scan_vulnerabilities()
        print(json.dumps(results, indent=2))

    elif args.check_compliance:
        results = await manager.check_compliance()
        print(json.dumps(results, indent=2))

    elif args.generate_report:
        report = await manager.generate_security_report()
        print(json.dumps(report, indent=2))

    elif args.show_dashboard:
        dashboard = await manager.get_security_dashboard()
        print(json.dumps(dashboard, indent=2))

    elif args.block_ip:
        if manager.waf:
            await manager.waf.block_ip(args.block_ip, "Manual block via CLI")
            print(f"IP {args.block_ip} blocked")

    elif args.create_api_key:
        # Generate new API key
        api_key = f"dmlogn8n_{secrets.token_urlsafe(32)}"
        print(f"Generated API key: {api_key}")
        print("Store this key securely - it will not be shown again")

    else:
        print("Use --help to see available commands")

if __name__ == "__main__":
    asyncio.run(security_cli())