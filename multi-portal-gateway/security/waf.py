#!/usr/bin/env python3
"""
DMLogn8n Web Application Firewall (WAF)
Production-ready WAF implementation for multi-agent platform security
"""

import re
import json
import time
import hashlib
import logging
import asyncio
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
from urllib.parse import urlparse, parse_qs, unquote
from ipaddress import ip_address, ip_network
import yaml
import aiofiles
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis
import jwt
from cryptography.fernet import Fernet
import geoip2.database
import aiomysql
from bs4 import BeautifulSoup
import requests_async as http

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThreatLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ActionType(Enum):
    ALLOW = "allow"
    BLOCK = "block"
    RATE_LIMIT = "rate_limit"
    CHALLENGE = "challenge"
    LOG_ONLY = "log_only"

@dataclass
class SecurityEvent:
    timestamp: float
    source_ip: str
    user_agent: str
    request_method: str
    request_path: str
    threat_type: str
    threat_level: ThreatLevel
    action_taken: ActionType
    details: Dict[str, Any]
    request_id: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    country: Optional[str] = None

@dataclass
class WAFRule:
    name: str
    description: str
    pattern: str
    threat_level: ThreatLevel
    action: ActionType
    enabled: bool = True
    methods: List[str] = None
    paths: List[str] = None
    exceptions: List[str] = None
    rate_limit: Optional[Dict] = None

class WAFMetrics:
    def __init__(self):
        self.requests_total = 0
        self.requests_blocked = 0
        self.requests_allowed = 0
        self.threats_detected = defaultdict(int)
        self.top_attackers = defaultdict(int)
        self.response_times = deque(maxlen=1000)
        self.rule_matches = defaultdict(int)

    def get_metrics(self) -> Dict:
        return {
            'requests_total': self.requests_total,
            'requests_blocked': self.requests_blocked,
            'requests_allowed': self.requests_allowed,
            'block_rate': self.requests_blocked / max(self.requests_total, 1),
            'threats_detected': dict(self.threats_detected),
            'top_attackers': dict(sorted(self.top_attackers.items(),
                                       key=lambda x: x[1], reverse=True)[:10]),
            'avg_response_time': sum(self.response_times) / len(self.response_times) if self.response_times else 0,
            'rule_matches': dict(self.rule_matches)
        }

class WebApplicationFirewall(BaseHTTPMiddleware):
    """
    Production-ready Web Application Firewall for DMLogn8n
    """

    def __init__(self, app, config_path: str = "/home/activeloguser/DMLogn8n/security/config/waf-rules.yaml"):
        super().__init__(app)
        self.config_path = config_path
        self.rules = []
        self.metrics = WAFMetrics()
        self.redis_client = None
        self.geoip_reader = None
        self.encryption_key = None
        self.blocked_ips = set()
        self.rate_limit_buckets = defaultdict(deque)
        self.request_history = defaultdict(lambda: deque(maxlen=100))
        self.threat_intelligence = {}
        self.compliance_mode = False

        # OWASP Top 10 patterns
        self.sql_injection_patterns = [
            r"(\bunion\b.*\bselect\b)",
            r"(\bselect\b.*\bfrom\b)",
            r"(\binsert\b.*\binto\b)",
            r"(\bupdate\b.*\bset\b)",
            r"(\bdelete\b.*\bfrom\b)",
            r"(\bdrop\b.*\btable\b)",
            r"(\bcreate\b.*\btable\b)",
            r"(\balter\b.*\btable\b)",
            r"(\bexec\b|\bexecute\b)",
            r"(;|\-\-|\/\*|\*\/)",
            r"(\bor\b.*\b1\b.*\b=\b.*\b1\b)",
            r"(\band\b.*\b1\b.*\b=\b.*\b1\b)",
            r"('.*'|\".*\".*\bor\b)",
            r"(\bwaitfor\b.*\bdelay\b)",
            r"(\bbenchmark\b)",
            r"(\bsleep\b\s*\(\s*\d+\s*\))"
        ]

        self.xss_patterns = [
            r"(<script[^>]*>.*?</script>)",
            r"(javascript\s*:)",
            r"(on\w+\s*=)",
            r"(<iframe[^>]*>)",
            r"(<object[^>]*>)",
            r"(<embed[^>]*>)",
            r"(<link[^>]*>)",
            r"(<meta[^>]*>)",
            r"(eval\s*\()",
            r"(alert\s*\()",
            r"(confirm\s*\()",
            r"(prompt\s*\()",
            r"(document\s*\.\s*cookie)",
            r"(window\s*\.\s*location)",
            r"(document\s*\.\s*write)"
        ]

        self.command_injection_patterns = [
            r"(;\s*(whoami|id|uname|pwd|ls|cat|rm|mv|cp|ps|kill|chmod|chown))",
            r"(\|\s*(whoami|id|uname|pwd|ls|cat|rm|mv|cp|ps|kill|chmod|chown))",
            r"(&&\s*(whoami|id|uname|pwd|ls|cat|rm|mv|cp|ps|kill|chmod|chown))",
            r"(\$\([^)]*\))",
            r"`[^`]*`",
            r"(\${[^}]*})",
            r"(>\s*/dev/null)",
            r"(2>&1)"
        ]

        self.path_traversal_patterns = [
            r"(\.\./)",
            r"(\.\.\\)",
            r"(/etc/passwd)",
            r"(/etc/shadow)",
            r"(/proc/)",
            r"(/sys/)",
            r"(%2e%2e%2f)",
            r"(%2e%2e\\)",
            r"(\.\.%2f)",
            r"(\.\.%5c)"
        ]

        self.file_inclusion_patterns = [
            r"(php://)",
            r"(file://)",
            r"(data://)",
            r"(expect://)",
            r"(input://)",
            r"(zip://)",
            r"(phar://)",
            r"(compress.zlib://)",
            r"(compress.bzip2://)"
        ]

    async def startup(self):
        """Initialize WAF components"""
        try:
            # Load configuration
            await self.load_config()

            # Initialize Redis
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )

            # Initialize GeoIP
            try:
                self.geoip_reader = geoip2.database.Reader('/usr/share/GeoIP/GeoLite2-Country.mmdb')
            except:
                logger.warning("GeoIP database not found, country detection disabled")

            # Initialize encryption
            self.encryption_key = Fernet.generate_key()

            # Load blocked IPs from Redis
            await self.load_blocked_ips()

            # Start background tasks
            asyncio.create_task(self.update_threat_intelligence())
            asyncio.create_task(self.cleanup_rate_limits())
            asyncio.create_task(self.generate_security_reports())

            logger.info("WAF initialized successfully")

        except Exception as e:
            logger.error(f"WAF initialization failed: {e}")
            raise

    async def load_config(self):
        """Load WAF rules from configuration file"""
        try:
            async with aiofiles.open(self.config_path, 'r') as f:
                config = yaml.safe_load(await f.read())

            self.rules = []
            for rule_data in config.get('rules', []):
                rule = WAFRule(**rule_data)
                self.rules.append(rule)

            self.compliance_mode = config.get('compliance_mode', False)
            logger.info(f"Loaded {len(self.rules)} WAF rules")

        except Exception as e:
            logger.error(f"Failed to load WAF config: {e}")
            await self.load_default_rules()

    async def load_default_rules(self):
        """Load default WAF rules if config file not available"""
        default_rules = [
            WAFRule(
                name="SQL Injection Detection",
                description="Detect SQL injection attempts",
                pattern="|".join(self.sql_injection_patterns),
                threat_level=ThreatLevel.HIGH,
                action=ActionType.BLOCK
            ),
            WAFRule(
                name="XSS Detection",
                description="Detect cross-site scripting attempts",
                pattern="|".join(self.xss_patterns),
                threat_level=ThreatLevel.HIGH,
                action=ActionType.BLOCK
            ),
            WAFRule(
                name="Command Injection Detection",
                description="Detect command injection attempts",
                pattern="|".join(self.command_injection_patterns),
                threat_level=ThreatLevel.CRITICAL,
                action=ActionType.BLOCK
            ),
            WAFRule(
                name="Path Traversal Detection",
                description="Detect path traversal attempts",
                pattern="|".join(self.path_traversal_patterns),
                threat_level=ThreatLevel.HIGH,
                action=ActionType.BLOCK
            ),
            WAFRule(
                name="File Inclusion Detection",
                description="Detect file inclusion vulnerabilities",
                pattern="|".join(self.file_inclusion_patterns),
                threat_level=ThreatLevel.HIGH,
                action=ActionType.BLOCK
            )
        ]

        self.rules.extend(default_rules)

    async def dispatch(self, request: Request, call_next):
        """Main WAF middleware dispatcher"""
        start_time = time.time()

        try:
            # Extract request information
            client_ip = self.get_client_ip(request)
            user_agent = request.headers.get("user-agent", "")
            method = request.method
            path = request.url.path
            query_string = str(request.url.query)

            # Generate request ID
            request_id = hashlib.sha256(f"{client_ip}{time.time()}{path}".encode()).hexdigest()[:16]

            # Initialize security context
            security_context = {
                'request_id': request_id,
                'client_ip': client_ip,
                'user_agent': user_agent,
                'method': method,
                'path': path,
                'query_string': query_string,
                'timestamp': time.time()
            }

            # Pre-request security checks
            block_response = await self.pre_request_checks(request, security_context)
            if block_response:
                return block_response

            # Process request through application
            response = await call_next(request)

            # Post-request security checks
            await self.post_request_checks(request, response, security_context)

            # Update metrics
            self.metrics.requests_total += 1
            self.metrics.requests_allowed += 1
            response_time = time.time() - start_time
            self.metrics.response_times.append(response_time)

            # Add security headers
            await self.add_security_headers(response)

            return response

        except Exception as e:
            logger.error(f"WAF processing error: {e}")
            self.metrics.requests_total += 1
            self.metrics.requests_blocked += 1

            return Response(
                content=json.dumps({"error": "Security check failed"}),
                status_code=403,
                media_type="application/json"
            )

    async def pre_request_checks(self, request: Request, context: Dict) -> Optional[Response]:
        """Pre-request security validations"""
        client_ip = context['client_ip']

        # Check if IP is blocked
        if await self.is_ip_blocked(client_ip):
            await self.log_security_event(
                SecurityEvent(
                    timestamp=context['timestamp'],
                    source_ip=client_ip,
                    user_agent=context['user_agent'],
                    request_method=context['method'],
                    request_path=context['path'],
                    threat_type="Blocked IP",
                    threat_level=ThreatLevel.HIGH,
                    action_taken=ActionType.BLOCK,
                    details={'reason': 'IP address is blocked'},
                    request_id=context['request_id']
                )
            )
            return Response(
                content=json.dumps({"error": "Access denied"}),
                status_code=403,
                media_type="application/json"
            )

        # Rate limiting
        if await self.check_rate_limit(client_ip, context):
            return Response(
                content=json.dumps({"error": "Rate limit exceeded"}),
                status_code=429,
                media_type="application/json"
            )

        # Check against WAF rules
        threat_detected = await self.check_waf_rules(request, context)
        if threat_detected:
            event, action = threat_detected
            await self.log_security_event(event)

            if action == ActionType.BLOCK:
                self.metrics.requests_blocked += 1
                return Response(
                    content=json.dumps({"error": "Security violation detected"}),
                    status_code=403,
                    media_type="application/json"
                )
            elif action == ActionType.CHALLENGE:
                return await self.challenge_request(request, context)

        # Bot detection
        if await self.is_malicious_bot(request, context):
            await self.log_security_event(
                SecurityEvent(
                    timestamp=context['timestamp'],
                    source_ip=client_ip,
                    user_agent=context['user_agent'],
                    request_method=context['method'],
                    request_path=context['path'],
                    threat_type="Malicious Bot",
                    threat_level=ThreatLevel.MEDIUM,
                    action_taken=ActionType.CHALLENGE,
                    details={'user_agent': context['user_agent']},
                    request_id=context['request_id']
                )
            )
            return await self.challenge_request(request, context)

        return None

    async def post_request_checks(self, request: Request, response: Response, context: Dict):
        """Post-request security validations"""
        # Log sensitive data access
        if await self.contains_sensitive_data(response):
            await self.log_security_event(
                SecurityEvent(
                    timestamp=context['timestamp'],
                    source_ip=context['client_ip'],
                    user_agent=context['user_agent'],
                    request_method=context['method'],
                    request_path=context['path'],
                    threat_type="Sensitive Data Access",
                    threat_level=ThreatLevel.LOW,
                    action_taken=ActionType.LOG_ONLY,
                    details={'response_code': response.status_code},
                    request_id=context['request_id']
                )
            )

        # Check for data leakage
        if await self.check_data_leakage(response):
            await self.log_security_event(
                SecurityEvent(
                    timestamp=context['timestamp'],
                    source_ip=context['client_ip'],
                    user_agent=context['user_agent'],
                    request_method=context['method'],
                    request_path=context['path'],
                    threat_type="Potential Data Leakage",
                    threat_level=ThreatLevel.MEDIUM,
                    action_taken=ActionType.LOG_ONLY,
                    details={'response_size': len(response.body) if hasattr(response, 'body') else 0},
                    request_id=context['request_id']
                )
            )

    async def check_waf_rules(self, request: Request, context: Dict) -> Optional[Tuple[SecurityEvent, ActionType]]:
        """Check request against WAF rules"""
        try:
            # Get request body for analysis
            body = await request.body()
            body_str = body.decode('utf-8', errors='ignore')

            # Combine all request data for analysis
            request_data = f"{context['method']} {context['path']} {context['query_string']} {body_str}"

            for rule in self.rules:
                if not rule.enabled:
                    continue

                # Check method filter
                if rule.methods and context['method'] not in rule.methods:
                    continue

                # Check path filter
                if rule.paths and not any(context['path'].startswith(path) for path in rule.paths):
                    continue

                # Apply rule pattern
                matches = re.findall(rule.pattern, request_data, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                if matches:
                    # Check exceptions
                    if rule.exceptions:
                        is_exception = False
                        for exception in rule.exceptions:
                            if re.search(exception, request_data, re.IGNORECASE):
                                is_exception = True
                                break
                        if is_exception:
                            continue

                    self.metrics.rule_matches[rule.name] += 1

                    event = SecurityEvent(
                        timestamp=context['timestamp'],
                        source_ip=context['client_ip'],
                        user_agent=context['user_agent'],
                        request_method=context['method'],
                        request_path=context['path'],
                        threat_type=rule.name,
                        threat_level=rule.threat_level,
                        action_taken=rule.action,
                        details={
                            'rule_description': rule.description,
                            'matches': matches[:5],  # Limit matches for privacy
                            'request_sample': request_data[:200] + "..." if len(request_data) > 200 else request_data
                        },
                        request_id=context['request_id']
                    )

                    return event, rule.action

            return None

        except Exception as e:
            logger.error(f"WAF rule check error: {e}")
            return None

    async def check_rate_limit(self, client_ip: str, context: Dict) -> bool:
        """Check if request exceeds rate limits"""
        try:
            current_time = time.time()

            # Clean old entries
            bucket = self.rate_limit_buckets[client_ip]
            while bucket and bucket[0] < current_time - 60:  # 1-minute window
                bucket.popleft()

            # Add current request
            bucket.append(current_time)

            # Check limits (100 requests per minute by default)
            if len(bucket) > 100:
                await self.log_security_event(
                    SecurityEvent(
                        timestamp=context['timestamp'],
                        source_ip=client_ip,
                        user_agent=context['user_agent'],
                        request_method=context['method'],
                        request_path=context['path'],
                        threat_type="Rate Limit Exceeded",
                        threat_level=ThreatLevel.MEDIUM,
                        action_taken=ActionType.RATE_LIMIT,
                        details={'requests_per_minute': len(bucket)},
                        request_id=context['request_id']
                    )
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return False

    async def is_ip_blocked(self, client_ip: str) -> bool:
        """Check if IP address is blocked"""
        try:
            # Check local blocklist
            if client_ip in self.blocked_ips:
                return True

            # Check Redis blocklist
            if self.redis_client:
                if await self.redis_client.sismember("waf:blocked_ips", client_ip):
                    return True

            # Check threat intelligence
            if client_ip in self.threat_intelligence:
                threat_data = self.threat_intelligence[client_ip]
                if threat_data.get('reputation_score', 100) < 20:
                    return True

            return False

        except Exception as e:
            logger.error(f"IP block check error: {e}")
            return False

    async def is_malicious_bot(self, request: Request, context: Dict) -> bool:
        """Detect malicious bot activity"""
        try:
            user_agent = context['user_agent'].lower()

            # Known malicious bot patterns
            malicious_patterns = [
                'sqlmap', 'nikto', 'nmap', 'masscan', 'zap', 'burp',
                'scanner', 'crawler', 'spider', 'bot', 'crawl'
            ]

            # Check user agent
            for pattern in malicious_patterns:
                if pattern in user_agent:
                    return True

            # Check for missing or empty user agent
            if not user_agent or user_agent == '':
                return True

            # Check request patterns
            client_ip = context['client_ip']
            history = self.request_history[client_ip]

            # Add current request to history
            history.append(context['timestamp'])

            # Check for rapid requests
            if len(history) >= 10:
                time_span = history[-1] - history[0]
                if time_span < 5:  # 10 requests in 5 seconds
                    return True

            return False

        except Exception as e:
            logger.error(f"Bot detection error: {e}")
            return False

    async def challenge_request(self, request: Request, context: Dict) -> Response:
        """Present challenge to suspicious requests"""
        # Generate simple JavaScript challenge
        challenge_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Security Challenge</title>
            <script>
                setTimeout(function() {
                    window.location.href = window.location.href + '&challenge=passed';
                }, 2000);
            </script>
        </head>
        <body>
            <h1>Security Verification</h1>
            <p>Please wait while we verify your request...</p>
        </body>
        </html>
        """

        return Response(
            content=challenge_html,
            status_code=200,
            media_type="text/html"
        )

    async def add_security_headers(self, response: Response):
        """Add security headers to response"""
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
        }

        for header, value in security_headers.items():
            response.headers[header] = value

    async def contains_sensitive_data(self, response: Response) -> bool:
        """Check if response contains sensitive data"""
        try:
            if hasattr(response, 'body'):
                content = response.body.decode('utf-8', errors='ignore').lower()

                sensitive_patterns = [
                    'password', 'secret', 'token', 'key', 'credential',
                    'ssn', 'social security', 'credit card', 'api_key',
                    'private_key', 'auth_token'
                ]

                for pattern in sensitive_patterns:
                    if pattern in content:
                        return True

            return False

        except Exception as e:
            logger.error(f"Sensitive data check error: {e}")
            return False

    async def check_data_leakage(self, response: Response) -> bool:
        """Check for potential data leakage"""
        try:
            if hasattr(response, 'body'):
                content = response.body.decode('utf-8', errors='ignore')

                # Check for large data responses
                if len(content) > 100000:  # 100KB
                    return True

                # Check for JSON dumps of databases
                try:
                    json_data = json.loads(content)
                    if isinstance(json_data, list) and len(json_data) > 1000:
                        return True
                except:
                    pass

                # Check for data dump patterns
                dump_patterns = [
                    r'\[\{.*?\}\,{100,}',  # Large JSON arrays
                    r'<table>.*</table>',  # HTML tables
                    r'dump|export|backup'  # Common dump terms
                ]

                for pattern in dump_patterns:
                    if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                        return True

            return False

        except Exception as e:
            logger.error(f"Data leakage check error: {e}")
            return False

    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for proxy headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to client IP
        return request.client.host if request.client else "unknown"

    async def log_security_event(self, event: SecurityEvent):
        """Log security event to various systems"""
        try:
            # Log to application logger
            log_message = f"WAF Event: {event.threat_type} from {event.source_ip} - {event.action_taken.value}"
            if event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                logger.warning(log_message)
            else:
                logger.info(log_message)

            # Store in Redis for real-time monitoring
            if self.redis_client:
                event_data = asdict(event)
                await self.redis_client.lpush("waf:security_events", json.dumps(event_data))
                await self.redis_client.ltrim("waf:security_events", 0, 10000)  # Keep last 10k events

            # Update metrics
            self.metrics.threats_detected[event.threat_type] += 1
            self.metrics.top_attackers[event.source_ip] += 1

            # Block IP if critical threat
            if event.threat_level == ThreatLevel.CRITICAL and event.action_taken == ActionType.BLOCK:
                await self.block_ip(event.source_ip, "Critical threat detected")

        except Exception as e:
            logger.error(f"Security event logging error: {e}")

    async def block_ip(self, ip_address: str, reason: str, duration: int = 3600):
        """Block an IP address"""
        try:
            self.blocked_ips.add(ip_address)

            if self.redis_client:
                await self.redis_client.sadd("waf:blocked_ips", ip_address)
                await self.redis_client.expire("waf:blocked_ips", duration)
                await self.redis_client.set(f"waf:block_reason:{ip_address}", reason, ex=duration)

            logger.warning(f"IP {ip_address} blocked for {duration} seconds: {reason}")

        except Exception as e:
            logger.error(f"IP blocking error: {e}")

    async def load_blocked_ips(self):
        """Load blocked IPs from Redis"""
        try:
            if self.redis_client:
                blocked_ips = await self.redis_client.smembers("waf:blocked_ips")
                self.blocked_ips.update(blocked_ips)
                logger.info(f"Loaded {len(blocked_ips)} blocked IPs")

        except Exception as e:
            logger.error(f"Failed to load blocked IPs: {e}")

    async def update_threat_intelligence(self):
        """Update threat intelligence data"""
        while True:
            try:
                # Simulate threat intelligence updates
                # In production, integrate with threat intelligence feeds
                await asyncio.sleep(3600)  # Update every hour

            except Exception as e:
                logger.error(f"Threat intelligence update error: {e}")
                await asyncio.sleep(300)  # Retry after 5 minutes

    async def cleanup_rate_limits(self):
        """Clean up old rate limit data"""
        while True:
            try:
                current_time = time.time()

                # Clean old rate limit buckets
                for ip in list(self.rate_limit_buckets.keys()):
                    bucket = self.rate_limit_buckets[ip]
                    while bucket and bucket[0] < current_time - 3600:  # 1 hour
                        bucket.popleft()
                    if not bucket:
                        del self.rate_limit_buckets[ip]

                await asyncio.sleep(300)  # Clean every 5 minutes

            except Exception as e:
                logger.error(f"Rate limit cleanup error: {e}")
                await asyncio.sleep(60)

    async def generate_security_reports(self):
        """Generate periodic security reports"""
        while True:
            try:
                await asyncio.sleep(3600)  # Generate reports every hour

                metrics = self.metrics.get_metrics()

                # Store metrics in Redis
                if self.redis_client:
                    await self.redis_client.setex(
                        "waf:metrics",
                        3600,
                        json.dumps(metrics)
                    )

                # Check for alerts
                if metrics['block_rate'] > 0.1:  # More than 10% block rate
                    logger.warning(f"High block rate detected: {metrics['block_rate']:.2%}")

            except Exception as e:
                logger.error(f"Security report generation error: {e}")

    async def get_security_dashboard(self) -> Dict:
        """Get security dashboard data"""
        try:
            metrics = self.metrics.get_metrics()

            # Get recent events from Redis
            recent_events = []
            if self.redis_client:
                events = await self.redis_client.lrange("waf:security_events", 0, 100)
                for event_json in events:
                    event = json.loads(event_json)
                    recent_events.append(event)

            return {
                'metrics': metrics,
                'recent_events': recent_events,
                'blocked_ips_count': len(self.blocked_ips),
                'active_rules': len([r for r in self.rules if r.enabled]),
                'compliance_mode': self.compliance_mode
            }

        except Exception as e:
            logger.error(f"Security dashboard error: {e}")
            return {'error': str(e)}

# WAF Factory function
def create_waf(app, config_path: str = None) -> WebApplicationFirewall:
    """Create and configure WAF instance"""
    if config_path is None:
        config_path = "/home/activeloguser/DMLogn8n/security/config/waf-rules.yaml"

    waf = WebApplicationFirewall(app, config_path)
    return waf

# CLI management interface
class WAFManager:
    """Command-line interface for WAF management"""

    def __init__(self, waf: WebApplicationFirewall):
        self.waf = waf

    async def block_ip_command(self, ip_address: str, reason: str = "Manual block"):
        """Manually block an IP address"""
        await self.waf.block_ip(ip_address, reason)
        print(f"IP {ip_address} blocked: {reason}")

    async def unblock_ip_command(self, ip_address: str):
        """Manually unblock an IP address"""
        try:
            self.waf.blocked_ips.discard(ip_address)
            if self.waf.redis_client:
                await self.waf.redis_client.srem("waf:blocked_ips", ip_address)
            print(f"IP {ip_address} unblocked")
        except Exception as e:
            print(f"Error unblocking IP: {e}")

    async def show_metrics(self):
        """Display WAF metrics"""
        metrics = self.waf.metrics.get_metrics()
        print("\n=== WAF Metrics ===")
        print(f"Total Requests: {metrics['requests_total']}")
        print(f"Blocked Requests: {metrics['requests_blocked']}")
        print(f"Block Rate: {metrics['block_rate']:.2%}")
        print(f"Average Response Time: {metrics['avg_response_time']:.3f}s")

        print("\nTop Threats:")
        for threat, count in metrics['threats_detected'].items():
            print(f"  {threat}: {count}")

        print("\nTop Attackers:")
        for ip, count in list(metrics['top_attackers'].items())[:5]:
            print(f"  {ip}: {count}")

    async def show_rules(self):
        """Display WAF rules"""
        print("\n=== WAF Rules ===")
        for rule in self.waf.rules:
            status = "ENABLED" if rule.enabled else "DISABLED"
            print(f"{rule.name} ({status}) - {rule.threat_level.value} - {rule.action.value}")
            print(f"  {rule.description}")

    async def reload_rules(self):
        """Reload WAF rules from configuration"""
        await self.waf.load_config()
        print("WAF rules reloaded")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DMLogn8n WAF Management")
    parser.add_argument("--block-ip", help="Block an IP address")
    parser.add_argument("--unblock-ip", help="Unblock an IP address")
    parser.add_argument("--reason", help="Reason for blocking", default="Manual block")
    parser.add_argument("--metrics", action="store_true", help="Show metrics")
    parser.add_argument("--rules", action="store_true", help="Show rules")
    parser.add_argument("--reload", action="store_true", help="Reload rules")

    args = parser.parse_args()

    async def main():
        from fastapi import FastAPI
        app = FastAPI()
        waf = WebApplicationFirewall(app)
        await waf.startup()

        manager = WAFManager(waf)

        if args.block_ip:
            await manager.block_ip_command(args.block_ip, args.reason)
        elif args.unblock_ip:
            await manager.unblock_ip_command(args.unblock_ip)
        elif args.metrics:
            await manager.show_metrics()
        elif args.rules:
            await manager.show_rules()
        elif args.reload:
            await manager.reload_rules()
        else:
            print("Use --help to see available commands")

    asyncio.run(main())