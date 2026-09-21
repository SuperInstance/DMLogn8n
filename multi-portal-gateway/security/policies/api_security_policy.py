#!/usr/bin/env python3
"""
DMLogn8n API Security Policy
Comprehensive API security including authentication, rate limiting, and threat protection
"""

import json
import logging
import asyncio
import time
import hashlib
import secrets
import re
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import yaml
import redis.asyncio as redis
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
import aiofiles
import ipaddress
from collections import defaultdict, deque
import uuid

logger = logging.getLogger(__name__)

class APIKeyStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"

class APIKeyPermission(Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    ANALYTICS = "analytics"
    WEBHOOKS = "webhooks"
    BULK_OPERATIONS = "bulk_operations"

class RateLimitScope(Enum):
    GLOBAL = "global"
    PER_KEY = "per_key"
    PER_IP = "per_ip"
    PER_USER = "per_user"
    PER_ENDPOINT = "per_endpoint"

class ThreatLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class APIKey:
    key_id: str
    key_hash: str
    name: str
    description: str
    permissions: Set[APIKeyPermission]
    rate_limit: int
    rate_limit_window: int
    allowed_ips: List[str] = None
    allowed_endpoints: List[str] = None
    expires_at: Optional[datetime] = None
    created_by: str = "system"
    created_at: datetime = None
    last_used: Optional[datetime] = None
    usage_count: int = 0
    status: APIKeyStatus = APIKeyStatus.ACTIVE
    metadata: Dict[str, Any] = None

@dataclass
class RateLimitRule:
    name: str
    scope: RateLimitScope
    requests_per_window: int
    window_seconds: int
    burst_limit: int
    penalty_seconds: int = 300
    whitelist: List[str] = None
    blacklist: List[str] = None

@dataclass
class APISecurityEvent:
    event_id: str
    timestamp: datetime
    event_type: str
    source_ip: str
    api_key: Optional[str]
    endpoint: str
    method: str
    user_agent: str
    threat_level: ThreatLevel
    details: Dict[str, Any]
    action_taken: str

class APISecurityPolicy(BaseHTTPMiddleware):
    """
    Comprehensive API security policy enforcement middleware
    """

    def __init__(self, app, config: Dict[str, Any]):
        super().__init__(app)
        self.config = config
        self.redis_client = None
        self.api_keys = {}
        self.rate_limit_rules = {}
        self.blocked_ips = set()
        self.suspicious_patterns = {}
        self.security_events = deque(maxlen=10000)
        self.rate_limit_buckets = defaultdict(lambda: deque(maxlen=1000))

        # Security settings
        self.require_api_key = config.get('require_api_key', False)
        self.enable_rate_limiting = config.get('enable_rate_limiting', True)
        self.enable_ip_filtering = config.get('enable_ip_filtering', True)
        self.enable_request_validation = config.get('enable_request_validation', True)
        self.enable_response_filtering = config.get('enable_response_filtering', True)

        # Initialize default rules
        self._initialize_default_rate_limits()
        self._initialize_security_patterns()

    async def initialize(self):
        """Initialize API security policy components"""
        try:
            # Initialize Redis
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=5,  # API security specific DB
                decode_responses=True
            )

            # Load API keys from storage
            await self._load_api_keys()

            # Load rate limit rules
            await self._load_rate_limit_rules()

            # Load blocked IPs
            await self._load_blocked_ips()

            # Start background tasks
            await self._start_background_tasks()

            logger.info("API Security Policy initialized")

        except Exception as e:
            logger.error(f"API Security Policy initialization failed: {e}")
            raise

    async def dispatch(self, request: Request, call_next):
        """Main API security middleware dispatcher"""
        start_time = time.time()

        try:
            # Extract request information
            client_ip = self._get_client_ip(request)
            api_key = self._extract_api_key(request)
            endpoint = request.url.path
            method = request.method

            # Create security context
            security_context = {
                'client_ip': client_ip,
                'api_key': api_key,
                'endpoint': endpoint,
                'method': method,
                'user_agent': request.headers.get('user-agent', ''),
                'timestamp': time.time()
            }

            # Pre-request security checks
            violation_response = await self._pre_request_checks(request, security_context)
            if violation_response:
                return violation_response

            # Validate request body
            if self.enable_request_validation:
                validation_error = await self._validate_request(request, security_context)
                if validation_error:
                    return validation_error

            # Process request
            response = await call_next(request)

            # Post-request security checks
            await self._post_request_checks(request, response, security_context)

            # Add security headers
            await self._add_security_headers(response)

            # Log successful request
            await self._log_api_request(security_context, response.status_code)

            return response

        except Exception as e:
            logger.error(f"API security middleware error: {e}")
            return self._create_error_response(
                "Internal security error",
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def validate_api_key_format(self, api_key: str) -> bool:
        """Validate API key format"""
        try:
            if not api_key:
                return False

            # Check length
            if len(api_key) < 32 or len(api_key) > 128:
                return False

            # Check format - should be alphanumeric with optional underscores and hyphens
            if not re.match(r'^[a-zA-Z0-9_-]+$', api_key):
                return False

            # Check for common weak patterns
            weak_patterns = [
                r'(test|demo|sample|example|default)',
                r'(123|abc|password|secret|key)',
                r'(.)\1{5,}'  # 6+ repeated characters
            ]

            for pattern in weak_patterns:
                if re.search(pattern, api_key, re.IGNORECASE):
                    return False

            return True

        except Exception as e:
            logger.error(f"API key format validation error: {e}")
            return False

    async def check_rate_limit(self, api_key: str, request: Request) -> bool:
        """Check if API request exceeds rate limits"""
        try:
            if not self.enable_rate_limiting:
                return True

            client_ip = self._get_client_ip(request)
            endpoint = request.url.path

            # Check all applicable rate limits
            for rule in self.rate_limit_rules.values():
                if not await self._is_rule_applicable(rule, api_key, client_ip, endpoint):
                    continue

                # Get rate limit bucket key
                bucket_key = self._get_rate_limit_bucket_key(rule, api_key, client_ip, endpoint)

                # Check rate limit
                if not await self._check_rate_limit_bucket(rule, bucket_key):
                    await self._handle_rate_limit_violation(rule, api_key, client_ip, endpoint)
                    return False

            return True

        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return False

    async def check_api_permissions(self, key_data: Dict[str, Any], request: Request) -> bool:
        """Check if API key has required permissions"""
        try:
            method = request.method.lower()
            endpoint = request.url.path

            # Get required permissions for endpoint and method
            required_permissions = self._get_required_permissions(endpoint, method)

            # Check if key has required permissions
            key_permissions = set(key_data.get('permissions', []))

            if not required_permissions.issubset(key_permissions):
                await self._log_security_event(
                    "permission_denied",
                    self._get_client_ip(request),
                    key_data.get('key_id'),
                    endpoint,
                    method,
                    request.headers.get('user-agent', ''),
                    ThreatLevel.MEDIUM,
                    {
                        'required_permissions': list(required_permissions),
                        'key_permissions': list(key_permissions)
                    },
                    "blocked"
                )
                return False

            # Check endpoint-specific restrictions
            if key_data.get('allowed_endpoints'):
                allowed_endpoints = key_data['allowed_endpoints']
                if not any(endpoint.startswith(pattern) for pattern in allowed_endpoints):
                    return False

            return True

        except Exception as e:
            logger.error(f"API permission check error: {e}")
            return False

    async def create_api_key(self, name: str, description: str, permissions: List[str],
                           rate_limit: int = 1000, expires_in_days: int = None,
                           allowed_ips: List[str] = None, allowed_endpoints: List[str] = None,
                           created_by: str = "system") -> Dict[str, Any]:
        """Create new API key"""
        try:
            # Generate API key
            api_key = f"dmlogn8n_{secrets.token_urlsafe(32)}"
            key_id = str(uuid.uuid4())

            # Hash API key for storage
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            # Create API key object
            api_key_obj = APIKey(
                key_id=key_id,
                key_hash=key_hash,
                name=name,
                description=description,
                permissions=set(APIKeyPermission(p) for p in permissions),
                rate_limit=rate_limit,
                rate_limit_window=3600,  # 1 hour
                allowed_ips=allowed_ips or [],
                allowed_endpoints=allowed_endpoints or [],
                expires_at=datetime.now() + timedelta(days=expires_in_days) if expires_in_days else None,
                created_by=created_by,
                created_at=datetime.now(),
                metadata={}
            )

            # Store API key
            self.api_keys[key_id] = api_key_obj

            # Store in Redis
            if self.redis_client:
                await self._store_api_key_in_redis(api_key_obj)

            logger.info(f"Created API key: {name} ({key_id})")

            return {
                'api_key': api_key,
                'key_id': key_id,
                'name': name,
                'permissions': permissions,
                'rate_limit': rate_limit,
                'expires_at': api_key_obj.expires_at.isoformat() if api_key_obj.expires_at else None
            }

        except Exception as e:
            logger.error(f"API key creation error: {e}")
            raise

    async def revoke_api_key(self, key_id: str) -> bool:
        """Revoke API key"""
        try:
            if key_id not in self.api_keys:
                return False

            api_key_obj = self.api_keys[key_id]
            api_key_obj.status = APIKeyStatus.REVOKED

            # Update in Redis
            if self.redis_client:
                await self._update_api_key_in_redis(api_key_obj)

            logger.info(f"Revoked API key: {key_id}")
            return True

        except Exception as e:
            logger.error(f"API key revocation error: {e}")
            return False

    async def get_api_key_usage(self, key_id: str, days: int = 30) -> Dict[str, Any]:
        """Get API key usage statistics"""
        try:
            if key_id not in self.api_keys:
                return {}

            # Get usage from Redis
            usage_data = {
                'key_id': key_id,
                'name': self.api_keys[key_id].name,
                'usage_count': self.api_keys[key_id].usage_count,
                'last_used': self.api_keys[key_id].last_used.isoformat() if self.api_keys[key_id].last_used else None,
                'status': self.api_keys[key_id].status.value
            }

            if self.redis_client:
                # Get detailed usage from logs
                usage_logs = await self.redis_client.lrange(f"api_usage:{key_id}", 0, -1)
                daily_usage = defaultdict(int)

                for log_entry in usage_logs:
                    log_data = json.loads(log_entry)
                    date = log_data['timestamp'][:10]  # YYYY-MM-DD
                    daily_usage[date] += 1

                usage_data['daily_usage'] = dict(daily_usage)

            return usage_data

        except Exception as e:
            logger.error(f"API key usage retrieval error: {e}")
            return {}

    # Private methods
    async def _pre_request_checks(self, request: Request, context: Dict[str, Any]) -> Optional[Any]:
        """Perform pre-request security checks"""
        client_ip = context['client_ip']
        api_key = context['api_key']

        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            await self._log_security_event(
                "blocked_ip_access",
                client_ip,
                api_key,
                context['endpoint'],
                context['method'],
                context['user_agent'],
                ThreatLevel.HIGH,
                {'reason': 'IP is blocked'},
                "blocked"
            )
            return self._create_error_response("Access denied", status.HTTP_403_FORBIDDEN)

        # Check for API key requirement
        if self.require_api_key and not api_key:
            return self._create_error_response("API key required", status.HTTP_401_UNAUTHORIZED)

        # Validate API key if provided
        if api_key:
            key_data = await self._get_api_key_data(api_key)
            if not key_data:
                await self._log_security_event(
                    "invalid_api_key",
                    client_ip,
                    api_key,
                    context['endpoint'],
                    context['method'],
                    context['user_agent'],
                    ThreatLevel.MEDIUM,
                    {'reason': 'Invalid API key'},
                    "blocked"
                )
                return self._create_error_response("Invalid API key", status.HTTP_401_UNAUTHORIZED)

            # Check API key status
            if key_data.get('status') != APIKeyStatus.ACTIVE.value:
                return self._create_error_response("API key is not active", status.HTTP_401_UNAUTHORIZED)

            # Check API key expiration
            if key_data.get('expires_at'):
                expires_at = datetime.fromisoformat(key_data['expires_at'])
                if datetime.now() > expires_at:
                    return self._create_error_response("API key has expired", status.HTTP_401_UNAUTHORIZED)

            # Check IP restrictions
            if key_data.get('allowed_ips') and client_ip not in key_data['allowed_ips']:
                return self._create_error_response("IP not allowed", status.HTTP_403_FORBIDDEN)

            # Check rate limiting
            if not await self.check_rate_limit(api_key, request):
                return self._create_error_response("Rate limit exceeded", status.HTTP_429_TOO_MANY_REQUESTS)

            # Check API permissions
            if not await self.check_api_permissions(key_data, request):
                return self._create_error_response("Insufficient permissions", status.HTTP_403_FORBIDDEN)

            # Update API key usage
            await self._update_api_key_usage(api_key)

        # Check for suspicious patterns
        if await self._detect_suspicious_patterns(request, context):
            await self._log_security_event(
                "suspicious_request",
                client_ip,
                api_key,
                context['endpoint'],
                context['method'],
                context['user_agent'],
                ThreatLevel.MEDIUM,
                {'suspicious_patterns': True},
                "monitored"
            )

        return None

    async def _post_request_checks(self, request: Request, response, context: Dict[str, Any]):
        """Perform post-request security checks"""
        try:
            # Check for sensitive data exposure
            if self.enable_response_filtering:
                await self._filter_response_data(response, context)

            # Check response size limits
            if hasattr(response, 'body') and len(response.body) > 10485760:  # 10MB
                await self._log_security_event(
                    "large_response",
                    context['client_ip'],
                    context['api_key'],
                    context['endpoint'],
                    context['method'],
                    context['user_agent'],
                    ThreatLevel.LOW,
                    {'response_size': len(response.body)},
                    "logged"
                )

        except Exception as e:
            logger.error(f"Post-request check error: {e}")

    async def _validate_request(self, request: Request, context: Dict[str, Any]) -> Optional[Any]:
        """Validate request content and structure"""
        try:
            # Check content-type
            content_type = request.headers.get('content-type', '')
            if request.method in ['POST', 'PUT', 'PATCH'] and not content_type:
                return self._create_error_response("Content-Type required", status.HTTP_400_BAD_REQUEST)

            # Validate request body size
            content_length = request.headers.get('content-length')
            if content_length and int(content_length) > 1048576:  # 1MB
                return self._create_error_response("Request too large", status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

            # Check for SQL injection patterns
            if request.method in ['POST', 'PUT', 'PATCH']:
                body = await request.body()
                if self._detect_sql_injection(body.decode('utf-8', errors='ignore')):
                    await self._log_security_event(
                        "sql_injection_attempt",
                        context['client_ip'],
                        context['api_key'],
                        context['endpoint'],
                        context['method'],
                        context['user_agent'],
                        ThreatLevel.HIGH,
                        {'sql_injection': True},
                        "blocked"
                    )
                    return self._create_error_response("Invalid request", status.HTTP_400_BAD_REQUEST)

            # Check for XSS patterns
            if request.method in ['POST', 'PUT', 'PATCH']:
                body = await request.body()
                if self._detect_xss(body.decode('utf-8', errors='ignore')):
                    await self._log_security_event(
                        "xss_attempt",
                        context['client_ip'],
                        context['api_key'],
                        context['endpoint'],
                        context['method'],
                        context['user_agent'],
                        ThreatLevel.HIGH,
                        {'xss_attempt': True},
                        "blocked"
                    )
                    return self._create_error_response("Invalid request", status.HTTP_400_BAD_REQUEST)

            return None

        except Exception as e:
            logger.error(f"Request validation error: {e}")
            return None

    def _extract_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from request"""
        # Check Authorization header (Bearer token)
        auth_header = request.headers.get('authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]

        # Check X-API-Key header
        api_key_header = request.headers.get('x-api-key')
        if api_key_header:
            return api_key_header

        # Check query parameter
        if 'api_key' in request.query_params:
            return request.query_params['api_key']

        return None

    async def _get_api_key_data(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Get API key data from storage"""
        try:
            # Hash the provided key
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            # Check in-memory cache
            for key_obj in self.api_keys.values():
                if key_obj.key_hash == key_hash and key_obj.status == APIKeyStatus.ACTIVE:
                    return {
                        'key_id': key_obj.key_id,
                        'name': key_obj.name,
                        'permissions': [p.value for p in key_obj.permissions],
                        'rate_limit': key_obj.rate_limit,
                        'allowed_ips': key_obj.allowed_ips,
                        'allowed_endpoints': key_obj.allowed_endpoints,
                        'expires_at': key_obj.expires_at.isoformat() if key_obj.expires_at else None,
                        'status': key_obj.status.value
                    }

            # Check Redis
            if self.redis_client:
                key_data = await self.redis_client.get(f"api_key:{key_hash}")
                if key_data:
                    return json.loads(key_data)

            return None

        except Exception as e:
            logger.error(f"API key data retrieval error: {e}")
            return None

    async def _update_api_key_usage(self, api_key: str):
        """Update API key usage statistics"""
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            # Find and update key in memory
            for key_obj in self.api_keys.values():
                if key_obj.key_hash == key_hash:
                    key_obj.usage_count += 1
                    key_obj.last_used = datetime.now()
                    break

            # Update in Redis
            if self.redis_client:
                usage_log = {
                    'timestamp': datetime.now().isoformat(),
                    'api_key': api_key
                }
                await self.redis_client.lpush(f"api_usage:{key_hash}", json.dumps(usage_log))
                await self.redis_client.ltrim(f"api_usage:{key_hash}", 0, 10000)

        except Exception as e:
            logger.error(f"API key usage update error: {e}")

    def _get_required_permissions(self, endpoint: str, method: str) -> Set[APIKeyPermission]:
        """Get required permissions for endpoint and method"""
        permissions = set()

        # Default read permissions
        if method in ['GET', 'HEAD', 'OPTIONS']:
            permissions.add(APIKeyPermission.READ)

        # Write permissions
        if method in ['POST', 'PUT', 'PATCH']:
            permissions.add(APIKeyPermission.WRITE)

        # Delete permissions
        if method == 'DELETE':
            permissions.add(APIKeyPermission.DELETE)

        # Admin endpoints
        if endpoint.startswith('/admin/') or endpoint.startswith('/api/admin/'):
            permissions.add(APIKeyPermission.ADMIN)

        # Analytics endpoints
        if endpoint.startswith('/analytics/') or endpoint.startswith('/api/analytics/'):
            permissions.add(APIKeyPermission.ANALYTICS)

        # Webhook endpoints
        if endpoint.startswith('/webhooks/') or endpoint.startswith('/api/webhooks/'):
            permissions.add(APIKeyPermission.WEBHOOKS)

        # Bulk operations
        if 'bulk' in endpoint or endpoint.endswith('/batch'):
            permissions.add(APIKeyPermission.BULK_OPERATIONS)

        return permissions

    async def _detect_suspicious_patterns(self, request: Request, context: Dict[str, Any]) -> bool:
        """Detect suspicious request patterns"""
        try:
            user_agent = context['user_agent'].lower()
            endpoint = context['endpoint']

            # Check for suspicious user agents
            suspicious_agents = ['bot', 'crawler', 'scanner', 'sqlmap', 'nikto']
            for agent in suspicious_agents:
                if agent in user_agent:
                    return True

            # Check for common attack patterns in endpoint
            attack_patterns = [
                r'\.\./',  # Path traversal
                r'<script',  # XSS
                r'union.*select',  # SQL injection
                r'exec\(',  # Code injection
            ]

            for pattern in attack_patterns:
                if re.search(pattern, endpoint, re.IGNORECASE):
                    return True

            # Check for rapid requests
            client_ip = context['client_ip']
            current_time = time.time()
            recent_requests = [
                req_time for req_time in self.rate_limit_buckets[client_ip]
                if current_time - req_time < 60  # Last minute
            ]

            if len(recent_requests) > 30:  # More than 30 requests per minute
                return True

            return False

        except Exception as e:
            logger.error(f"Suspicious pattern detection error: {e}")
            return False

    def _detect_sql_injection(self, content: str) -> bool:
        """Detect SQL injection patterns"""
        sql_patterns = [
            r"(\bunion\b.*\bselect\b)",
            r"(\bselect\b.*\bfrom\b)",
            r"(\binsert\b.*\binto\b)",
            r"(\bupdate\b.*\bset\b)",
            r"(\bdelete\b.*\bfrom\b)",
            r"(\bdrop\b.*\btable\b)",
            r"(;|\-\-|\/\*|\*\/)",
            r"(\bor\b.*\b1\b.*\b=\b.*\b1\b)",
            r"(\band\b.*\b1\b.*\b=\b.*\b1\b)"
        ]

        for pattern in sql_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE | re.DOTALL):
                return True

        return False

    def _detect_xss(self, content: str) -> bool:
        """Detect XSS patterns"""
        xss_patterns = [
            r"(<script[^>]*>.*?</script>)",
            r"(javascript\s*:)",
            r"(on\w+\s*=)",
            r"(<iframe[^>]*>)",
            r"(eval\s*\()",
            r"(alert\s*\()",
            r"(document\s*\.\s*cookie)"
        ]

        for pattern in xss_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                return True

        return False

    async def _filter_response_data(self, response, context: Dict[str, Any]):
        """Filter sensitive data from response"""
        try:
            # Remove sensitive headers
            sensitive_headers = ['server', 'x-powered-by', 'x-aspnet-version']
            for header in sensitive_headers:
                if header in response.headers:
                    del response.headers[header]

        except Exception as e:
            logger.error(f"Response filtering error: {e}")

    async def _add_security_headers(self, response):
        """Add security headers to response"""
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'X-API-Security-Policy': 'DMLogn8n-v1.0'
        }

        for header, value in security_headers.items():
            response.headers[header] = value

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _create_error_response(self, message: str, status_code: int) -> Any:
        """Create standardized error response"""
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status_code,
            content={
                "error": message,
                "timestamp": datetime.now().isoformat(),
                "request_id": str(uuid.uuid4())
            }
        )

    # Rate limiting methods
    def _get_rate_limit_bucket_key(self, rule: RateLimitRule, api_key: str,
                                 client_ip: str, endpoint: str) -> str:
        """Generate rate limit bucket key"""
        if rule.scope == RateLimitScope.GLOBAL:
            return f"rate_limit:global:{rule.name}"
        elif rule.scope == RateLimitScope.PER_KEY:
            return f"rate_limit:key:{api_key}:{rule.name}"
        elif rule.scope == RateLimitScope.PER_IP:
            return f"rate_limit:ip:{client_ip}:{rule.name}"
        elif rule.scope == RateLimitScope.PER_USER:
            return f"rate_limit:user:{api_key}:{rule.name}"
        elif rule.scope == RateLimitScope.PER_ENDPOINT:
            return f"rate_limit:endpoint:{endpoint}:{rule.name}"
        else:
            return f"rate_limit:default:{rule.name}"

    async def _is_rule_applicable(self, rule: RateLimitRule, api_key: str,
                                client_ip: str, endpoint: str) -> bool:
        """Check if rate limit rule applies to request"""
        # Check whitelist
        if rule.whitelist:
            if client_ip not in rule.whitelist and api_key not in rule.whitelist:
                return False

        # Check blacklist
        if rule.blacklist:
            if client_ip in rule.blacklist or api_key in rule.blacklist:
                return False

        return True

    async def _check_rate_limit_bucket(self, rule: RateLimitRule, bucket_key: str) -> bool:
        """Check rate limit for specific bucket"""
        try:
            current_time = time.time()
            window_start = current_time - rule.window_seconds

            # Get existing requests from bucket
            if self.redis_client:
                # Remove expired entries
                await self.redis_client.zremrangebyscore(bucket_key, 0, window_start)

                # Count current requests
                request_count = await self.redis_client.zcard(bucket_key)

                if request_count >= rule.requests_per_window:
                    return False

                # Add current request
                await self.redis_client.zadd(bucket_key, {str(current_time): current_time})
                await self.redis_client.expire(bucket_key, rule.window_seconds)
            else:
                # In-memory fallback
                bucket = self.rate_limit_buckets[bucket_key]
                bucket.append(current_time)

                # Remove old entries
                while bucket and bucket[0] < window_start:
                    bucket.popleft()

                if len(bucket) > rule.requests_per_window:
                    return False

            return True

        except Exception as e:
            logger.error(f"Rate limit bucket check error: {e}")
            return True  # Allow request on error

    async def _handle_rate_limit_violation(self, rule: RateLimitRule, api_key: str,
                                         client_ip: str, endpoint: str):
        """Handle rate limit violation"""
        try:
            # Apply penalty
            penalty_key = f"rate_limit_penalty:{client_ip}:{rule.name}"
            if self.redis_client:
                await self.redis_client.setex(penalty_key, rule.penalty_seconds, "1")

            # Log security event
            await self._log_security_event(
                "rate_limit_violation",
                client_ip,
                api_key,
                endpoint,
                "",
                "",
                ThreatLevel.MEDIUM,
                {
                    'rule_name': rule.name,
                    'requests_per_window': rule.requests_per_window,
                    'window_seconds': rule.window_seconds
                },
                "penalized"
            )

        except Exception as e:
            logger.error(f"Rate limit violation handling error: {e}")

    async def _log_security_event(self, event_type: str, source_ip: str, api_key: str,
                                endpoint: str, method: str, user_agent: str,
                                threat_level: ThreatLevel, details: Dict[str, Any],
                                action_taken: str):
        """Log security event"""
        try:
            event = APISecurityEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                event_type=event_type,
                source_ip=source_ip,
                api_key=api_key,
                endpoint=endpoint,
                method=method,
                user_agent=user_agent,
                threat_level=threat_level,
                details=details,
                action_taken=action_taken
            )

            self.security_events.append(event)

            # Store in Redis
            if self.redis_client:
                await self.redis_client.lpush(
                    "api_security_events",
                    json.dumps(asdict(event))
                )
                await self.redis_client.ltrim("api_security_events", 0, 10000)

        except Exception as e:
            logger.error(f"Security event logging error: {e}")

    async def _log_api_request(self, context: Dict[str, Any], status_code: int):
        """Log API request for analytics"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'client_ip': context['client_ip'],
                'api_key': context['api_key'],
                'endpoint': context['endpoint'],
                'method': context['method'],
                'status_code': status_code,
                'response_time': time.time() - context['timestamp']
            }

            if self.redis_client:
                await self.redis_client.lpush("api_requests_log", json.dumps(log_entry))
                await self.redis_client.ltrim("api_requests_log", 0, 100000)

        except Exception as e:
            logger.error(f"API request logging error: {e}")

    async def _load_api_keys(self):
        """Load API keys from storage"""
        try:
            if self.redis_client:
                # Load from Redis
                keys = await self.redis_client.keys("api_key:*")
                for key in keys:
                    key_data = await self.redis_client.get(key)
                    if key_data:
                        data = json.loads(key_data)
                        # Recreate APIKey object
                        api_key_obj = APIKey(
                            key_id=data['key_id'],
                            key_hash=key.split(':')[-1],  # Extract hash from key name
                            name=data['name'],
                            description=data.get('description', ''),
                            permissions=set(APIKeyPermission(p) for p in data['permissions']),
                            rate_limit=data['rate_limit'],
                            rate_limit_window=data.get('rate_limit_window', 3600),
                            allowed_ips=data.get('allowed_ips', []),
                            allowed_endpoints=data.get('allowed_endpoints', []),
                            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None,
                            created_by=data.get('created_by', 'system'),
                            created_at=datetime.fromisoformat(data['created_at']),
                            last_used=datetime.fromisoformat(data['last_used']) if data.get('last_used') else None,
                            usage_count=data.get('usage_count', 0),
                            status=APIKeyStatus(data.get('status', 'active')),
                            metadata=data.get('metadata', {})
                        )
                        self.api_keys[data['key_id']] = api_key_obj

        except Exception as e:
            logger.error(f"API keys loading error: {e}")

    async def _load_rate_limit_rules(self):
        """Load rate limit rules"""
        try:
            rules_config = self.config.get('rate_limiting', {}).get('rules', {})
            for rule_name, rule_config in rules_config.items():
                rule = RateLimitRule(
                    name=rule_name,
                    scope=RateLimitScope(rule_config.get('scope', 'per_key')),
                    requests_per_window=rule_config.get('requests_per_window', 1000),
                    window_seconds=rule_config.get('window_seconds', 3600),
                    burst_limit=rule_config.get('burst_limit', 100),
                    penalty_seconds=rule_config.get('penalty_seconds', 300),
                    whitelist=rule_config.get('whitelist', []),
                    blacklist=rule_config.get('blacklist', [])
                )
                self.rate_limit_rules[rule_name] = rule

        except Exception as e:
            logger.error(f"Rate limit rules loading error: {e}")

    async def _load_blocked_ips(self):
        """Load blocked IPs"""
        try:
            if self.redis_client:
                blocked_ips = await self.redis_client.smembers("blocked_ips")
                self.blocked_ips.update(blocked_ips)

        except Exception as e:
            logger.error(f"Blocked IPs loading error: {e}")

    def _initialize_default_rate_limits(self):
        """Initialize default rate limit rules"""
        # Global rate limit
        self.rate_limit_rules['global'] = RateLimitRule(
            name='global',
            scope=RateLimitScope.GLOBAL,
            requests_per_window=10000,
            window_seconds=3600,
            burst_limit=100,
            penalty_seconds=300
        )

        # Per-key rate limit
        self.rate_limit_rules['per_key'] = RateLimitRule(
            name='per_key',
            scope=RateLimitScope.PER_KEY,
            requests_per_window=1000,
            window_seconds=3600,
            burst_limit=50,
            penalty_seconds=300
        )

        # Per-IP rate limit
        self.rate_limit_rules['per_ip'] = RateLimitRule(
            name='per_ip',
            scope=RateLimitScope.PER_IP,
            requests_per_window=100,
            window_seconds=60,
            burst_limit=20,
            penalty_seconds=600
        )

    def _initialize_security_patterns(self):
        """Initialize security pattern definitions"""
        self.suspicious_patterns = {
            'sql_injection': [
                r"(\bunion\b.*\bselect\b)",
                r"(\bselect\b.*\bfrom\b)",
                r"(;|\-\-|\/\*|\*\/)"
            ],
            'xss': [
                r"(<script[^>]*>)",
                r"(javascript\s*:)",
                r"(on\w+\s*=)"
            ],
            'path_traversal': [
                r"(\.\./)",
                r"(%2e%2e%2f)"
            ]
        }

    async def _store_api_key_in_redis(self, api_key_obj: APIKey):
        """Store API key in Redis"""
        try:
            key_data = {
                'key_id': api_key_obj.key_id,
                'name': api_key_obj.name,
                'description': api_key_obj.description,
                'permissions': [p.value for p in api_key_obj.permissions],
                'rate_limit': api_key_obj.rate_limit,
                'rate_limit_window': api_key_obj.rate_limit_window,
                'allowed_ips': api_key_obj.allowed_ips,
                'allowed_endpoints': api_key_obj.allowed_endpoints,
                'expires_at': api_key_obj.expires_at.isoformat() if api_key_obj.expires_at else None,
                'created_by': api_key_obj.created_by,
                'created_at': api_key_obj.created_at.isoformat(),
                'last_used': api_key_obj.last_used.isoformat() if api_key_obj.last_used else None,
                'usage_count': api_key_obj.usage_count,
                'status': api_key_obj.status.value,
                'metadata': api_key_obj.metadata
            }

            await self.redis_client.setex(
                f"api_key:{api_key_obj.key_hash}",
                86400 * 365,  # 1 year
                json.dumps(key_data)
            )

        except Exception as e:
            logger.error(f"API key Redis storage error: {e}")

    async def _update_api_key_in_redis(self, api_key_obj: APIKey):
        """Update API key in Redis"""
        await self._store_api_key_in_redis(api_key_obj)

    async def _start_background_tasks(self):
        """Start background tasks"""
        try:
            # Cleanup old rate limit buckets
            asyncio.create_task(self._cleanup_rate_limits())

            # Cleanup old security events
            asyncio.create_task(self._cleanup_security_events())

        except Exception as e:
            logger.error(f"Background tasks startup error: {e}")

    async def _cleanup_rate_limits(self):
        """Clean up old rate limit data"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes

                if self.redis_client:
                    # Clean up old rate limit buckets
                    keys = await self.redis_client.keys("rate_limit:*")
                    for key in keys:
                        ttl = await self.redis_client.ttl(key)
                        if ttl == -1:  # No expiry set
                            await self.redis_client.expire(key, 3600)  # Set 1 hour expiry

            except Exception as e:
                logger.error(f"Rate limit cleanup error: {e}")
                await asyncio.sleep(60)

    async def _cleanup_security_events(self):
        """Clean up old security events"""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour

                # Keep only last 5000 events in memory
                if len(self.security_events) > 5000:
                    self.security_events = deque(
                        list(self.security_events)[-5000:],
                        maxlen=10000
                    )

            except Exception as e:
                logger.error(f"Security events cleanup error: {e}")
                await asyncio.sleep(300)