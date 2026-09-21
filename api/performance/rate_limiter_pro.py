#!/usr/bin/env python3
"""
Advanced Rate Limiting System with Burst Handling
Intelligent rate limiting that protects without blocking legitimate users
"""

import asyncio
import time
import json
import logging
import hashlib
import ipaddress
from typing import Dict, List, Any, Optional, Callable, Union, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum
import aioredis
import redis.asyncio as redis
from fastapi import Request, Response, HTTPException, status
from fastapi.routing import APIRoute
import mmh3
import xxhash
import jwt
import geoip2.database
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class RateLimitStrategy(Enum):
    """Rate limiting strategies"""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    ADAPTIVE = "adaptive"
    LEAKY_BUCKET = "leaky_bucket"

class LimitScope(Enum):
    """Rate limiting scopes"""
    IP_ADDRESS = "ip_address"
    USER_ID = "user_id"
    API_KEY = "api_key"
    ENDPOINT = "endpoint"
    GLOBAL = "global"
    CUSTOM = "custom"

class UserType(Enum):
    """User types for tiered rate limiting"""
    ANONYMOUS = "anonymous"
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    ADMIN = "admin"

@dataclass
class RateLimitRule:
    """Rate limiting rule configuration"""
    strategy: RateLimitStrategy
    scope: LimitScope
    requests_per_window: int
    window_seconds: int
    burst_capacity: int = 0
    user_types: List[UserType] = None
    endpoints: List[str] = None
    priority: int = 0

    def __post_init__(self):
        if self.user_types is None:
            self.user_types = list(UserType)
        if self.endpoints is None:
            self.endpoints = ["*"]
        if self.burst_capacity == 0:
            self.burst_capacity = int(self.requests_per_window * 0.2)  # 20% burst capacity

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting system"""
    # Redis settings
    redis_url: str = "redis://localhost:6379"
    redis_prefix: str = "rate_limit"

    # Default limits
    default_limits: Dict[UserType, RateLimitRule] = None

    # Advanced features
    enable_geographic_limiting: bool = True
    enable_adaptive_limiting: bool = True
    enable_whitelist: bool = True
    enable_blacklist: bool = True
    enable_priority_queue: bool = True

    # Geographic database
    geoip_database_path: str = "/path/to/GeoLite2-City.mmdb"

    # Adaptive settings
    adaptive_learning_rate: float = 0.1
    adaptive_min_multiplier: float = 0.5
    adaptive_max_multiplier: float = 3.0

    # Queue settings
    priority_queue_size: int = 1000
    queue_timeout_seconds: int = 30

    def __post_init__(self):
        if self.default_limits is None:
            self.default_limits = {
                UserType.ANONYMOUS: RateLimitRule(
                    strategy=RateLimitStrategy.TOKEN_BUCKET,
                    scope=LimitScope.IP_ADDRESS,
                    requests_per_window=100,
                    window_seconds=3600,
                    priority=0
                ),
                UserType.FREE: RateLimitRule(
                    strategy=RateLimitStrategy.TOKEN_BUCKET,
                    scope=LimitScope.USER_ID,
                    requests_per_window=1000,
                    window_seconds=3600,
                    priority=1
                ),
                UserType.PREMIUM: RateLimitRule(
                    strategy=RateLimitStrategy.TOKEN_BUCKET,
                    scope=LimitScope.USER_ID,
                    requests_per_window=10000,
                    window_seconds=3600,
                    priority=2
                ),
                UserType.ENTERPRISE: RateLimitRule(
                    strategy=RateLimitStrategy.TOKEN_BUCKET,
                    scope=LimitScope.USER_ID,
                    requests_per_window=100000,
                    window_seconds=3600,
                    priority=3
                ),
                UserType.ADMIN: RateLimitRule(
                    strategy=RateLimitStrategy.TOKEN_BUCKET,
                    scope=LimitScope.USER_ID,
                    requests_per_window=1000000,
                    window_seconds=3600,
                    priority=4
                )
            }

@dataclass
class RateLimitState:
    """Current rate limit state"""
    requests_used: int
    window_start: float
    tokens_remaining: float
    last_request_time: float
    is_bursting: bool = False
    queue_position: Optional[int] = None

class TokenBucketLimiter:
    """Token bucket rate limiting algorithm"""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.states: Dict[str, RateLimitState] = {}

    def _get_key(self, request: Request, scope: LimitScope) -> str:
        """Generate key for rate limiting"""
        if scope == LimitScope.IP_ADDRESS:
            return self._get_client_ip(request)
        elif scope == LimitScope.USER_ID:
            # Extract user ID from request
            user_id = getattr(request.state, 'user_id', None)
            return user_id or self._get_client_ip(request)
        elif scope == LimitScope.API_KEY:
            api_key = request.headers.get('X-API-Key', '')
            return api_key or self._get_client_ip(request)
        elif scope == LimitScope.ENDPOINT:
            return f"{request.method}:{request.url.path}"
        else:
            return self._get_client_ip(request)

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()

        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip

        return request.client.host if request.client else 'unknown'

    async def check_rate_limit(self, request: Request, rule: RateLimitRule) -> Tuple[bool, RateLimitState]:
        """Check if request is within rate limits"""
        key = self._get_key(request, rule.scope)
        current_time = time.time()

        # Get or create state
        state = self.states.get(key)
        if not state:
            state = RateLimitState(
                requests_used=0,
                window_start=current_time,
                tokens_remaining=self.capacity,
                last_request_time=current_time
            )
            self.states[key] = state

        # Calculate tokens to add
        time_passed = current_time - state.last_request_time
        tokens_to_add = time_passed * self.refill_rate
        state.tokens_remaining = min(self.capacity, state.tokens_remaining + tokens_to_add)
        state.last_request_time = current_time

        # Check if we have tokens
        if state.tokens_remaining >= 1:
            state.tokens_remaining -= 1
            state.requests_used += 1
            return True, state
        else:
            return False, state

class SlidingWindowLimiter:
    """Sliding window rate limiting algorithm"""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.windows: Dict[str, deque] = {}

    async def check_rate_limit(self, request: Request, rule: RateLimitRule) -> Tuple[bool, RateLimitState]:
        """Check sliding window rate limit"""
        key = self._get_key(request, rule.scope)
        current_time = time.time()

        # Get or create window
        if key not in self.windows:
            self.windows[key] = deque()

        window = self.windows[key]

        # Remove old requests outside the window
        while window and current_time - window[0] > self.window_seconds:
            window.popleft()

        # Check if we're within limits
        if len(window) < self.max_requests:
            window.append(current_time)
            return True, RateLimitState(
                requests_used=len(window),
                window_start=current_time - self.window_seconds,
                tokens_remaining=self.max_requests - len(window),
                last_request_time=current_time
            )
        else:
            return False, RateLimitState(
                requests_used=len(window),
                window_start=current_time - self.window_seconds,
                tokens_remaining=0,
                last_request_time=current_time
            )

    def _get_key(self, request: Request, scope: LimitScope) -> str:
        """Generate key for rate limiting"""
        if scope == LimitScope.IP_ADDRESS:
            return request.client.host if request.client else 'unknown'
        elif scope == LimitScope.USER_ID:
            return getattr(request.state, 'user_id', 'anonymous')
        else:
            return request.client.host if request.client else 'unknown'

class AdaptiveRateLimiter:
    """Adaptive rate limiting based on usage patterns"""

    def __init__(self, base_limiter, learning_rate: float = 0.1):
        self.base_limiter = base_limiter
        self.learning_rate = learning_rate
        self.usage_patterns: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.min_multiplier = 0.5
        self.max_multiplier = 3.0

    async def check_rate_limit(self, request: Request, rule: RateLimitRule) -> Tuple[bool, RateLimitState]:
        """Check adaptive rate limit"""
        key = self._get_key(request, rule.scope)

        # Get base rate limit result
        allowed, state = await self.base_limiter.check_rate_limit(request, rule)

        # Update usage patterns
        self._update_usage_pattern(key, allowed)

        # Adjust limits based on patterns
        multiplier = self._calculate_multiplier(key)
        adjusted_tokens = state.tokens_remaining * multiplier

        if adjusted_tokens >= 1:
            state.tokens_remaining = adjusted_tokens - 1
            return True, state
        else:
            return False, state

    def _get_key(self, request: Request, scope: LimitScope) -> str:
        """Generate key for adaptive limiting"""
        if scope == LimitScope.IP_ADDRESS:
            return request.client.host if request.client else 'unknown'
        else:
            return getattr(request.state, 'user_id', 'anonymous')

    def _update_usage_pattern(self, key: str, allowed: bool):
        """Update usage patterns for learning"""
        if key not in self.usage_patterns:
            self.usage_patterns[key] = {
                'success_rate': 0.5,
                'request_count': 0,
                'blocked_count': 0
            }

        pattern = self.usage_patterns[key]
        pattern['request_count'] += 1

        if allowed:
            pattern['success_rate'] = (
                pattern['success_rate'] * (1 - self.learning_rate) +
                1.0 * self.learning_rate
            )
        else:
            pattern['blocked_count'] += 1
            pattern['success_rate'] = (
                pattern['success_rate'] * (1 - self.learning_rate) +
                0.0 * self.learning_rate
            )

    def _calculate_multiplier(self, key: str) -> float:
        """Calculate adaptive multiplier based on usage patterns"""
        if key not in self.usage_patterns:
            return 1.0

        pattern = self.usage_patterns[key]

        # Adjust based on success rate
        if pattern['success_rate'] > 0.8:
            # High success rate, allow more requests
            multiplier = min(self.max_multiplier, 1.0 + (pattern['success_rate'] - 0.8) * 2)
        elif pattern['success_rate'] < 0.5:
            # Low success rate, be more restrictive
            multiplier = max(self.min_multiplier, pattern['success_rate'] * 2)
        else:
            multiplier = 1.0

        return multiplier

class PriorityQueue:
    """Priority queue for handling rate-limited requests"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.queues: Dict[int, deque] = defaultdict(deque)
        self.waiting_requests: Dict[str, asyncio.Future] = {}
        self.request_count = 0

    async def enqueue(self, request: Request, priority: int) -> Optional[asyncio.Future]:
        """Enqueue request with priority"""
        if len(self.waiting_requests) >= self.max_size:
            return None  # Queue full

        self.request_count += 1
        request_id = f"{self._get_client_ip(request)}_{self.request_count}"

        future = asyncio.Future()
        self.waiting_requests[request_id] = future
        self.queues[priority].append(request_id)

        return future

    async def dequeue(self) -> Optional[str]:
        """Dequeue highest priority request"""
        for priority in sorted(self.queues.keys(), reverse=True):
            if self.queues[priority]:
                request_id = self.queues[priority].popleft()
                return request_id
        return None

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        return request.client.host if request.client else 'unknown'

class GeographicLimiter:
    """Geographic-based rate limiting"""

    def __init__(self, geoip_database_path: str):
        self.geoip_reader = None
        self.geoip_database_path = geoip_database_path
        self.country_limits: Dict[str, RateLimitRule] = {}

    def initialize(self):
        """Initialize GeoIP database"""
        try:
            self.geoip_reader = geoip2.database.Reader(self.geoip_database_path)
        except Exception as e:
            logger.error(f"Failed to initialize GeoIP database: {e}")

    def get_country_code(self, ip_address: str) -> Optional[str]:
        """Get country code for IP address"""
        if not self.geoip_reader:
            return None

        try:
            response = self.geoip_reader.city(ip_address)
            return response.country.iso_code
        except Exception:
            return None

    def should_limit(self, request: Request) -> bool:
        """Check if geographic limiting should apply"""
        if not self.geoip_reader:
            return False

        ip_address = request.client.host if request.client else 'unknown'
        country_code = self.get_country_code(ip_address)

        return country_code in self.country_limits

class AdvancedRateLimiter:
    """Advanced rate limiting system with multiple strategies"""

    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        self.redis = None
        self.limiters = {}
        self.priority_queue = PriorityQueue(self.config.priority_queue_size)
        self.geographic_limiter = GeographicLimiter(self.config.geoip_database_path)

        # Whitelists and blacklists
        self.whitelisted_ips: Set[str] = set()
        self.blacklisted_ips: Set[str] = set()
        self.whitelisted_users: Set[str] = set()
        self.blacklisted_users: Set[str] = set()

        # Initialize limiters
        self._initialize_limiters()

    def _initialize_limiters(self):
        """Initialize rate limiting algorithms"""
        for rule in self.config.default_limits.values():
            if rule.strategy == RateLimitStrategy.TOKEN_BUCKET:
                self.limiters[rule.strategy] = TokenBucketLimiter(
                    rule.requests_per_window + rule.burst_capacity,
                    rule.requests_per_window / rule.window_seconds
                )
            elif rule.strategy == RateLimitStrategy.SLIDING_WINDOW:
                self.limiters[rule.strategy] = SlidingWindowLimiter(
                    rule.requests_per_window,
                    rule.window_seconds
                )

    async def initialize(self):
        """Initialize rate limiting components"""
        self.redis = await redis.from_url(self.config.redis_url)
        self.geographic_limiter.initialize()

    async def check_rate_limit(self, request: Request) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is within rate limits"""
        # Check whitelists and blacklists
        client_ip = request.client.host if request.client else 'unknown'
        user_id = getattr(request.state, 'user_id', None)

        # Check blacklists
        if client_ip in self.blacklisted_ips or (user_id and user_id in self.blacklisted_users):
            return False, {
                "error": "Blocked",
                "message": "Access denied",
                "retry_after": 3600
            }

        # Check whitelists
        if client_ip in self.whitelisted_ips or (user_id and user_id in self.whitelisted_users):
            return True, {
                "allowed": True,
                "message": "Whitelisted access"
            }

        # Check geographic limits
        if self.config.enable_geographic_limiting and self.geographic_limiter.should_limit(request):
            # Apply geographic rate limiting
            pass

        # Determine user type
        user_type = self._get_user_type(request)

        # Get applicable rule
        rule = self._get_applicable_rule(user_type, request)
        if not rule:
            return True, {"allowed": True, "message": "No rate limit applicable"}

        # Check rate limit using appropriate strategy
        limiter = self.limiters.get(rule.strategy)
        if not limiter:
            return True, {"allowed": True, "message": "No limiter configured"}

        # Apply adaptive limiting if enabled
        if self.config.enable_adaptive_limiting and rule.strategy == RateLimitStrategy.TOKEN_BUCKET:
            limiter = AdaptiveRateLimiter(limiter, self.config.adaptive_learning_rate)

        allowed, state = await limiter.check_rate_limit(request, rule)

        # Prepare response
        response_data = {
            "allowed": allowed,
            "limit": rule.requests_per_window,
            "remaining": int(state.tokens_remaining),
            "reset_time": state.window_start + rule.window_seconds,
            "retry_after": max(1, int((state.window_start + rule.window_seconds) - time.time())),
            "user_type": user_type.value,
            "strategy": rule.strategy.value
        }

        if not allowed:
            # Handle rate limit exceeded
            if self.config.enable_priority_queue and rule.priority > 0:
                # Try to queue the request
                future = await self.priority_queue.enqueue(request, rule.priority)
                if future:
                    response_data["queued"] = True
                    response_data["queue_position"] = len(self.priority_queue.waiting_requests)
                    return False, response_data

            response_data["error"] = "Rate limit exceeded"
            return False, response_data

        return True, response_data

    def _get_user_type(self, request: Request) -> UserType:
        """Determine user type from request"""
        # Check for admin token
        auth_header = request.headers.get('Authorization', '')
        if 'admin' in auth_header.lower():
            return UserType.ADMIN

        # Check for API key
        api_key = request.headers.get('X-API-Key')
        if api_key:
            # Determine user type from API key
            if api_key.startswith('ent_'):
                return UserType.ENTERPRISE
            elif api_key.startswith('prem_'):
                return UserType.PREMIUM
            elif api_key.startswith('free_'):
                return UserType.FREE

        # Check for JWT token
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if token:
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
                if payload.get('plan') == 'enterprise':
                    return UserType.ENTERPRISE
                elif payload.get('plan') == 'premium':
                    return UserType.PREMIUM
                else:
                    return UserType.FREE
            except:
                pass

        # Default to anonymous
        return UserType.ANONYMOUS

    def _get_applicable_rule(self, user_type: UserType, request: Request) -> Optional[RateLimitRule]:
        """Get applicable rate limiting rule"""
        # Get default rule for user type
        default_rule = self.config.default_limits.get(user_type)
        if not default_rule:
            return None

        # Check if endpoint matches
        current_path = request.url.path
        if any(current_path.startswith(endpoint.replace('*', ''))
               for endpoint in default_rule.endpoints):
            return default_rule

        return None

    def add_to_whitelist(self, identifier: str, is_ip: bool = True):
        """Add identifier to whitelist"""
        if is_ip:
            self.whitelisted_ips.add(identifier)
        else:
            self.whitelisted_users.add(identifier)

    def add_to_blacklist(self, identifier: str, is_ip: bool = True):
        """Add identifier to blacklist"""
        if is_ip:
            self.blacklisted_ips.add(identifier)
        else:
            self.blacklisted_users.add(identifier)

    def remove_from_whitelist(self, identifier: str, is_ip: bool = True):
        """Remove identifier from whitelist"""
        if is_ip:
            self.whitelisted_ips.discard(identifier)
        else:
            self.whitelisted_users.discard(identifier)

    def remove_from_blacklist(self, identifier: str, is_ip: bool = True):
        """Remove identifier from blacklist"""
        if is_ip:
            self.blacklisted_ips.discard(identifier)
        else:
            self.blacklisted_users.discard(identifier)

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        return {
            "whitelisted_ips": len(self.whitelisted_ips),
            "blacklisted_ips": len(self.blacklisted_ips),
            "whitelisted_users": len(self.whitelisted_users),
            "blacklisted_users": len(self.blacklisted_users),
            "queue_size": len(self.priority_queue.waiting_requests),
            "limiters": list(self.limiters.keys())
        }

# FastAPI middleware integration
class RateLimitMiddleware:
    """FastAPI middleware for rate limiting"""

    def __init__(self, app, limiter: AdvancedRateLimiter):
        self.app = app
        self.limiter = limiter

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Create request object
        request = Request(scope, receive)

        # Check rate limit
        allowed, limit_info = await self.limiter.check_rate_limit(request)

        if not allowed:
            # Send rate limit response
            await send({
                "type": "http.response.start",
                "status": status.HTTP_429_TOO_MANY_REQUESTS,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"X-RateLimit-Limit", str(limit_info.get("limit", 0)).encode()),
                    (b"X-RateLimit-Remaining", str(limit_info.get("remaining", 0)).encode()),
                    (b"X-RateLimit-Reset", str(limit_info.get("reset_time", 0)).encode()),
                    (b"Retry-After", str(limit_info.get("retry_after", 60)).encode()),
                ],
            })

            await send({
                "type": "http.response.body",
                "body": json.dumps(limit_info).encode(),
            })
            return

        # Add rate limit headers to response
        # This would need integration with the actual response handling
        await self.app(scope, receive, send)

# Decorator for rate limiting specific endpoints
def rate_limit(requests: int, window: int, strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET):
    """Decorator for rate limiting specific endpoints"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would need implementation to work with the rate limiting system
            return await func(*args, **kwargs)
        return wrapper
    return decorator

if __name__ == "__main__":
    # Example usage
    async def main():
        config = RateLimitConfig()
        limiter = AdvancedRateLimiter(config)
        await limiter.initialize()

        # Add some IPs to whitelist/blacklist
        limiter.add_to_whitelist("192.168.1.100")
        limiter.add_to_blacklist("192.168.1.200")

        print("Rate limiter stats:", limiter.get_stats())

    asyncio.run(main())