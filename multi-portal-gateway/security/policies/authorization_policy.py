#!/usr/bin/env python3
"""
DMLogn8n Authorization Security Policy
Role-Based Access Control (RBAC) and authorization enforcement
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import yaml
import redis.asyncio as redis
from fastapi import Request, HTTPException
import re

logger = logging.getLogger(__name__)

class Permission(Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    SECURITY_ADMIN = "security_admin"
    USER_ADMIN = "user_admin"
    SYSTEM_ADMIN = "system_admin"
    API_ACCESS = "api_access"
    VIEW_LOGS = "view_logs"
    MANAGE_SESSIONS = "manage_sessions"
    CONFIGURE_SECURITY = "configure_security"

class ResourceType(Enum):
    USER_DATA = "user_data"
    SYSTEM_CONFIG = "system_config"
    SECURITY_LOGS = "security_logs"
    API_ENDPOINTS = "api_endpoints"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    NETWORK = "network"
    AUDIT_LOGS = "audit_logs"

class AccessLevel(Enum):
    NONE = 0
    READ_ONLY = 1
    READ_WRITE = 2
    FULL_ACCESS = 3
    ADMIN = 4

@dataclass
class Role:
    name: str
    description: str
    permissions: Set[Permission]
    resource_access: Dict[ResourceType, AccessLevel]
    inherits_from: List[str] = None
    constraints: Dict[str, Any] = None
    time_restrictions: Dict[str, Any] = None
    ip_restrictions: List[str] = None

@dataclass
class AccessPolicy:
    name: str
    resource_type: ResourceType
    required_permissions: Set[Permission]
    access_level: AccessLevel
    conditions: List[str] = None
    exceptions: List[str] = None
    time_constraints: Dict[str, Any] = None
    location_constraints: List[str] = None

@dataclass
class AccessRequest:
    user_id: str
    username: str
    role: str
    resource: str
    resource_type: ResourceType
    action: str
    context: Dict[str, Any]
    timestamp: datetime

@dataclass
class AccessDecision:
    allowed: bool
    reason: str
    conditions: List[str] = None
    ttl: Optional[int] = None
    audit_required: bool = True

class AuthorizationPolicy:
    """
    Comprehensive authorization and RBAC policy enforcement
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_client = None
        self.roles = {}
        self.access_policies = {}
        self.user_permissions_cache = {}
        self.access_logs = []

        # Initialize default roles and policies
        self._initialize_default_roles()
        self._initialize_default_policies()

        # Security constraints
        self.max_cache_ttl = config.get('max_cache_ttl', 300)  # 5 minutes
        self.audit_all_access = config.get('audit_all_access', True)
        self.strict_mode = config.get('strict_mode', True)

    async def initialize(self):
        """Initialize authorization policy components"""
        try:
            # Initialize Redis
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=3,  # AuthZ-specific DB
                decode_responses=True
            )

            # Load roles and policies from configuration
            await self._load_configuration()

            logger.info("Authorization Policy initialized")

        except Exception as e:
            logger.error(f"Authorization Policy initialization failed: {e}")

    async def check_permission(self, user: Dict[str, Any], request: Request) -> bool:
        """
        Check if user has permission for the requested resource
        """
        try:
            # Extract access request details
            access_request = self._create_access_request(user, request)

            # Check access
            decision = await self.evaluate_access(access_request)

            # Log access attempt
            await self._log_access_attempt(access_request, decision)

            # Cache decision if allowed
            if decision.allowed and decision.ttl:
                await self._cache_access_decision(access_request, decision)

            return decision.allowed

        except Exception as e:
            logger.error(f"Permission check error: {e}")
            if self.strict_mode:
                return False
            return True

    async def check_api_access(self, user: Dict[str, Any], endpoint: str, method: str) -> AccessDecision:
        """
        Check API access permissions
        """
        try:
            # Map endpoint to resource type
            resource_type = self._map_api_endpoint(endpoint)

            # Create access request
            access_request = AccessRequest(
                user_id=user.get('id', 'unknown'),
                username=user.get('username', 'unknown'),
                role=user.get('role', 'user'),
                resource=endpoint,
                resource_type=resource_type,
                action=method.lower(),
                context={
                    'user_agent': user.get('user_agent', ''),
                    'source_ip': user.get('source_ip', ''),
                    'timestamp': datetime.now().isoformat()
                },
                timestamp=datetime.now()
            )

            # Evaluate access
            decision = await self.evaluate_access(access_request)

            return decision

        except Exception as e:
            logger.error(f"API access check error: {e}")
            return AccessDecision(
                allowed=False,
                reason="Access check failed due to system error",
                audit_required=True
            )

    async def evaluate_access(self, request: AccessRequest) -> AccessDecision:
        """
        Evaluate access request against all policies
        """
        try:
            # Get user role
            user_role = self.roles.get(request.role)
            if not user_role:
                return AccessDecision(
                    allowed=False,
                    reason=f"Invalid role: {request.role}",
                    audit_required=True
                )

            # Check role-based permissions
            role_decision = self._check_role_permissions(request, user_role)
            if not role_decision.allowed:
                return role_decision

            # Check access policies
            policy_decision = await self._check_access_policies(request)
            if not policy_decision.allowed:
                return policy_decision

            # Check contextual constraints
            context_decision = self._check_contextual_constraints(request, user_role)
            if not context_decision.allowed:
                return context_decision

            # Check time-based restrictions
            time_decision = self._check_time_restrictions(request, user_role)
            if not time_decision.allowed:
                return time_decision

            # Check location-based restrictions
            location_decision = self._check_location_restrictions(request, user_role)
            if not location_decision.allowed:
                return location_decision

            # Access granted
            return AccessDecision(
                allowed=True,
                reason="Access granted",
                ttl=self.max_cache_ttl,
                audit_required=self.audit_all_access or self._requires_audit(request)
            )

        except Exception as e:
            logger.error(f"Access evaluation error: {e}")
            return AccessDecision(
                allowed=False,
                reason=f"Access evaluation failed: {str(e)}",
                audit_required=True
            )

    def _check_role_permissions(self, request: AccessRequest, role: Role) -> AccessDecision:
        """Check role-based permissions"""
        try:
            # Check resource access level
            required_access = self._get_required_access_level(request.action)
            role_access = role.resource_access.get(request.resource_type, AccessLevel.NONE)

            if role_access.value < required_access.value:
                return AccessDecision(
                    allowed=False,
                    reason=f"Insufficient access level. Required: {required_access.name}, Has: {role_access.name}",
                    audit_required=True
                )

            # Check specific permissions
            required_permissions = self._get_required_permissions(request.action, request.resource_type)
            missing_permissions = required_permissions - role.permissions

            if missing_permissions:
                return AccessDecision(
                    allowed=False,
                    reason=f"Missing permissions: {[p.value for p in missing_permissions]}",
                    audit_required=True
                )

            return AccessDecision(allowed=True, reason="Role permissions satisfied")

        except Exception as e:
            logger.error(f"Role permission check error: {e}")
            return AccessDecision(allowed=False, reason="Role permission check failed")

    async def _check_access_policies(self, request: AccessRequest) -> AccessDecision:
        """Check against defined access policies"""
        try:
            # Get applicable policies
            applicable_policies = [
                policy for policy in self.access_policies.values()
                if policy.resource_type == request.resource_type
            ]

            for policy in applicable_policies:
                # Check if policy applies to this request
                if self._policy_applies(policy, request):
                    # Check policy conditions
                    if not await self._evaluate_policy_conditions(policy, request):
                        return AccessDecision(
                            allowed=False,
                            reason=f"Access denied by policy: {policy.name}",
                            audit_required=True
                        )

            return AccessDecision(allowed=True, reason="All policies satisfied")

        except Exception as e:
            logger.error(f"Access policy check error: {e}")
            return AccessDecision(allowed=False, reason="Access policy check failed")

    def _check_contextual_constraints(self, request: AccessRequest, role: Role) -> AccessDecision:
        """Check contextual security constraints"""
        try:
            if not role.constraints:
                return AccessDecision(allowed=True, reason="No contextual constraints")

            # Check session security
            if 'secure_session_required' in role.constraints:
                if not request.context.get('secure_session'):
                    return AccessDecision(
                        allowed=False,
                        reason="Secure session required",
                        audit_required=True
                    )

            # Check device trust
            if 'trusted_device_required' in role.constraints:
                if not self._is_trusted_device(request):
                    return AccessDecision(
                        allowed=False,
                        reason="Trusted device required",
                        audit_required=True
                    )

            # Check concurrent sessions
            if 'max_concurrent_sessions' in role.constraints:
                max_sessions = role.constraints['max_concurrent_sessions']
                if not self._check_concurrent_sessions(request.user_id, max_sessions):
                    return AccessDecision(
                        allowed=False,
                        reason=f"Maximum concurrent sessions ({max_sessions}) exceeded",
                        audit_required=True
                    )

            return AccessDecision(allowed=True, reason="Contextual constraints satisfied")

        except Exception as e:
            logger.error(f"Contextual constraints check error: {e}")
            return AccessDecision(allowed=False, reason="Contextual constraints check failed")

    def _check_time_restrictions(self, request: AccessRequest, role: Role) -> AccessDecision:
        """Check time-based access restrictions"""
        try:
            if not role.time_restrictions:
                return AccessDecision(allowed=True, reason="No time restrictions")

            current_time = datetime.now()
            current_hour = current_time.hour
            current_day = current_time.weekday()  # 0 = Monday, 6 = Sunday

            # Check allowed hours
            if 'allowed_hours' in role.time_restrictions:
                allowed_hours = role.time_restrictions['allowed_hours']
                if isinstance(allowed_hours, list) and current_hour not in allowed_hours:
                    return AccessDecision(
                        allowed=False,
                        reason=f"Access not allowed at this hour ({current_hour})",
                        audit_required=True
                    )

            # Check allowed days
            if 'allowed_days' in role.time_restrictions:
                allowed_days = role.time_restrictions['allowed_days']
                if isinstance(allowed_days, list) and current_day not in allowed_days:
                    return AccessDecision(
                        allowed=False,
                        reason=f"Access not allowed on this day",
                        audit_required=True
                    )

            # Check business hours
            if 'business_hours_only' in role.time_restrictions and role.time_restrictions['business_hours_only']:
                if current_hour < 9 or current_hour > 17 or current_day >= 5:  # Weekend
                    return AccessDecision(
                        allowed=False,
                        reason="Access only allowed during business hours",
                        audit_required=True
                    )

            return AccessDecision(allowed=True, reason="Time restrictions satisfied")

        except Exception as e:
            logger.error(f"Time restrictions check error: {e}")
            return AccessDecision(allowed=False, reason="Time restrictions check failed")

    def _check_location_restrictions(self, request: AccessRequest, role: Role) -> AccessDecision:
        """Check location-based access restrictions"""
        try:
            if not role.ip_restrictions:
                return AccessDecision(allowed=True, reason="No location restrictions")

            source_ip = request.context.get('source_ip', '')
            if not source_ip:
                return AccessDecision(
                    allowed=False,
                    reason="Source IP not available for location validation",
                    audit_required=True
                )

            # Check if IP is in allowed list
            ip_allowed = False
            for allowed_ip in role.ip_restrictions:
                if self._ip_matches(source_ip, allowed_ip):
                    ip_allowed = True
                    break

            if not ip_allowed:
                return AccessDecision(
                    allowed=False,
                    reason=f"IP address {source_ip} not in allowed locations",
                    audit_required=True
                )

            return AccessDecision(allowed=True, reason="Location restrictions satisfied")

        except Exception as e:
            logger.error(f"Location restrictions check error: {e}")
            return AccessDecision(allowed=False, reason="Location restrictions check failed")

    def _create_access_request(self, user: Dict[str, Any], request: Request) -> AccessRequest:
        """Create access request from HTTP request"""
        return AccessRequest(
            user_id=user.get('id', 'unknown'),
            username=user.get('username', 'unknown'),
            role=user.get('role', 'user'),
            resource=request.url.path,
            resource_type=self._map_path_to_resource_type(request.url.path),
            action=request.method.lower(),
            context={
                'user_agent': request.headers.get('user-agent', ''),
                'source_ip': self._get_client_ip(request),
                'referer': request.headers.get('referer', ''),
                'timestamp': datetime.now().isoformat()
            },
            timestamp=datetime.now()
        )

    def _map_path_to_resource_type(self, path: str) -> ResourceType:
        """Map URL path to resource type"""
        path_mapping = {
            '/api/users': ResourceType.USER_DATA,
            '/api/admin': ResourceType.SYSTEM_CONFIG,
            '/api/security': ResourceType.SECURITY_LOGS,
            '/api/logs': ResourceType.AUDIT_LOGS,
            '/api/config': ResourceType.SYSTEM_CONFIG,
            '/api/database': ResourceType.DATABASE,
            '/api/files': ResourceType.FILE_SYSTEM,
            '/api/network': ResourceType.NETWORK
        }

        for pattern, resource_type in path_mapping.items():
            if path.startswith(pattern):
                return resource_type

        return ResourceType.API_ENDPOINTS

    def _map_api_endpoint(self, endpoint: str) -> ResourceType:
        """Map API endpoint to resource type"""
        return self._map_path_to_resource_type(endpoint)

    def _get_required_access_level(self, action: str) -> AccessLevel:
        """Get required access level for action"""
        action_mapping = {
            'get': AccessLevel.READ_ONLY,
            'head': AccessLevel.READ_ONLY,
            'options': AccessLevel.READ_ONLY,
            'post': AccessLevel.READ_WRITE,
            'put': AccessLevel.READ_WRITE,
            'patch': AccessLevel.READ_WRITE,
            'delete': AccessLevel.FULL_ACCESS
        }

        return action_mapping.get(action.lower(), AccessLevel.READ_ONLY)

    def _get_required_permissions(self, action: str, resource_type: ResourceType) -> Set[Permission]:
        """Get required permissions for action and resource type"""
        required = set()

        # Base permissions
        if action.lower() in ['get', 'head', 'options']:
            required.add(Permission.READ)
        elif action.lower() in ['post', 'put', 'patch']:
            required.add(Permission.READ)
            required.add(Permission.WRITE)
        elif action.lower() == 'delete':
            required.add(Permission.DELETE)

        # Resource-specific permissions
        if resource_type == ResourceType.SECURITY_LOGS:
            required.add(Permission.VIEW_LOGS)
        elif resource_type == ResourceType.SYSTEM_CONFIG:
            required.add(Permission.SYSTEM_ADMIN)
        elif resource_type == ResourceType.USER_DATA and action.lower() in ['post', 'put', 'patch', 'delete']:
            required.add(Permission.USER_ADMIN)

        return required

    def _policy_applies(self, policy: AccessPolicy, request: AccessRequest) -> bool:
        """Check if access policy applies to request"""
        try:
            # Check resource type match
            if policy.resource_type != request.resource_type:
                return False

            # Check exceptions
            if policy.exceptions:
                for exception in policy.exceptions:
                    if re.search(exception, request.resource):
                        return False

            return True

        except Exception as e:
            logger.error(f"Policy applicability check error: {e}")
            return False

    async def _evaluate_policy_conditions(self, policy: AccessPolicy, request: AccessRequest) -> bool:
        """Evaluate policy conditions"""
        try:
            if not policy.conditions:
                return True

            for condition in policy.conditions:
                if not await self._evaluate_condition(condition, request):
                    return False

            return True

        except Exception as e:
            logger.error(f"Policy condition evaluation error: {e}")
            return False

    async def _evaluate_condition(self, condition: str, request: AccessRequest) -> bool:
        """Evaluate individual policy condition"""
        try:
            # Simple condition evaluation (in production, use a proper expression engine)
            if condition == "business_hours_only":
                current_hour = datetime.now().hour
                return 9 <= current_hour <= 17

            elif condition.startswith("ip_in_range"):
                # ip_in_range:192.168.1.0/24
                ip_range = condition.split(":")[1]
                return self._ip_in_range(request.context.get('source_ip', ''), ip_range)

            elif condition.startswith("user_has_attribute"):
                # user_has_attribute:department=IT
                attr_parts = condition.split(":")[1].split("=")
                # In production, check user attributes from database
                return True

            return True

        except Exception as e:
            logger.error(f"Condition evaluation error: {e}")
            return False

    def _is_trusted_device(self, request: AccessRequest) -> bool:
        """Check if request is from trusted device"""
        # In production, implement device fingerprinting and trust management
        return True

    def _check_concurrent_sessions(self, user_id: str, max_sessions: int) -> bool:
        """Check concurrent session limit"""
        # In production, check active sessions for user
        return True

    def _ip_matches(self, ip: str, pattern: str) -> bool:
        """Check if IP matches pattern"""
        try:
            from ipaddress import ip_address, ip_network
            return ip_address(ip) in ip_network(pattern, strict=False)
        except:
            return ip.startswith(pattern)

    def _ip_in_range(self, ip: str, ip_range: str) -> bool:
        """Check if IP is in range"""
        return self._ip_matches(ip, ip_range)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _requires_audit(self, request: AccessRequest) -> bool:
        """Check if access requires audit"""
        # High-risk operations always require audit
        high_risk_resources = [ResourceType.SECURITY_LOGS, ResourceType.SYSTEM_CONFIG, ResourceType.USER_DATA]
        high_risk_actions = ['delete', 'post', 'put', 'patch']

        return (request.resource_type in high_risk_resources or
                request.action in high_risk_actions)

    async def _log_access_attempt(self, request: AccessRequest, decision: AccessDecision):
        """Log access attempt for audit"""
        try:
            log_entry = {
                'timestamp': request.timestamp.isoformat(),
                'user_id': request.user_id,
                'username': request.username,
                'role': request.role,
                'resource': request.resource,
                'resource_type': request.resource_type.value,
                'action': request.action,
                'allowed': decision.allowed,
                'reason': decision.reason,
                'source_ip': request.context.get('source_ip'),
                'user_agent': request.context.get('user_agent'),
                'audit_required': decision.audit_required
            }

            self.access_logs.append(log_entry)

            # Store in Redis
            if self.redis_client:
                await self.redis_client.lpush("authz:access_logs", json.dumps(log_entry))
                await self.redis_client.ltrim("authz:access_logs", 0, 10000)

        except Exception as e:
            logger.error(f"Access logging error: {e}")

    async def _cache_access_decision(self, request: AccessRequest, decision: AccessDecision):
        """Cache access decision for performance"""
        try:
            if not self.redis_client or not decision.ttl:
                return

            cache_key = f"authz:decision:{hash(str(request))}"
            cache_data = {
                'allowed': decision.allowed,
                'reason': decision.reason,
                'timestamp': datetime.now().isoformat()
            }

            await self.redis_client.setex(
                cache_key,
                decision.ttl,
                json.dumps(cache_data)
            )

        except Exception as e:
            logger.error(f"Access decision caching error: {e}")

    async def _load_configuration(self):
        """Load roles and policies from configuration"""
        try:
            # Load roles configuration
            roles_config = self.config.get('roles', {})
            for role_name, role_data in roles_config.items():
                role = Role(
                    name=role_name,
                    description=role_data.get('description', ''),
                    permissions=set(Permission(p) for p in role_data.get('permissions', [])),
                    resource_access={
                        ResourceType(rt): AccessLevel(al)
                        for rt, al in role_data.get('resource_access', {}).items()
                    },
                    inherits_from=role_data.get('inherits_from', []),
                    constraints=role_data.get('constraints', {}),
                    time_restrictions=role_data.get('time_restrictions', {}),
                    ip_restrictions=role_data.get('ip_restrictions', [])
                )
                self.roles[role_name] = role

            # Load access policies configuration
            policies_config = self.config.get('access_policies', {})
            for policy_name, policy_data in policies_config.items():
                policy = AccessPolicy(
                    name=policy_name,
                    resource_type=ResourceType(policy_data.get('resource_type')),
                    required_permissions=set(Permission(p) for p in policy_data.get('required_permissions', [])),
                    access_level=AccessLevel(policy_data.get('access_level')),
                    conditions=policy_data.get('conditions', []),
                    exceptions=policy_data.get('exceptions', []),
                    time_constraints=policy_data.get('time_constraints', {}),
                    location_constraints=policy_data.get('location_constraints', [])
                )
                self.access_policies[policy_name] = policy

            logger.info(f"Loaded {len(self.roles)} roles and {len(self.access_policies)} access policies")

        except Exception as e:
            logger.error(f"Configuration loading error: {e}")

    def _initialize_default_roles(self):
        """Initialize default roles"""
        # Administrator role
        self.roles['administrator'] = Role(
            name='administrator',
            description='Full system administrator',
            permissions=set(Permission),
            resource_access={rt: AccessLevel.ADMIN for rt in ResourceType},
            constraints={},
            time_restrictions={},
            ip_restrictions=[]
        )

        # Security Admin role
        self.roles['security_admin'] = Role(
            name='security_admin',
            description='Security administrator',
            permissions={
                Permission.READ, Permission.WRITE, Permission.SECURITY_ADMIN,
                Permission.VIEW_LOGS, Permission.MANAGE_SESSIONS, Permission.CONFIGURE_SECURITY
            },
            resource_access={
                ResourceType.SECURITY_LOGS: AccessLevel.FULL_ACCESS,
                ResourceType.AUDIT_LOGS: AccessLevel.FULL_ACCESS,
                ResourceType.SYSTEM_CONFIG: AccessLevel.READ_WRITE,
                ResourceType.USER_DATA: AccessLevel.READ_ONLY
            },
            constraints={'secure_session_required': True},
            time_restrictions={'business_hours_only': False},
            ip_restrictions=[]
        )

        # User role
        self.roles['user'] = Role(
            name='user',
            description='Regular user',
            permissions={Permission.READ},
            resource_access={
                ResourceType.USER_DATA: AccessLevel.READ_ONLY,
                ResourceType.API_ENDPOINTS: AccessLevel.READ_ONLY
            },
            constraints={},
            time_restrictions={'allowed_hours': list(range(6, 22))},  # 6 AM to 10 PM
            ip_restrictions=[]
        )

        # API User role
        self.roles['api_user'] = Role(
            name='api_user',
            description='API service user',
            permissions={Permission.READ, Permission.WRITE, Permission.API_ACCESS},
            resource_access={
                ResourceType.API_ENDPOINTS: AccessLevel.READ_WRITE
            },
            constraints={'trusted_device_required': True},
            time_restrictions={},
            ip_restrictions=[]
        )

    def _initialize_default_policies(self):
        """Initialize default access policies"""
        # Security logs access policy
        self.access_policies['security_logs_policy'] = AccessPolicy(
            name='security_logs_policy',
            resource_type=ResourceType.SECURITY_LOGS,
            required_permissions={Permission.VIEW_LOGS, Permission.SECURITY_ADMIN},
            access_level=AccessLevel.READ_ONLY,
            conditions=['secure_session_required'],
            exceptions=[]
        )

        # System configuration policy
        self.access_policies['system_config_policy'] = AccessPolicy(
            name='system_config_policy',
            resource_type=ResourceType.SYSTEM_CONFIG,
            required_permissions={Permission.SYSTEM_ADMIN},
            access_level=AccessLevel.READ_WRITE,
            conditions=['business_hours_only'],
            exceptions=['^/api/config/readonly']
        )

        # User management policy
        self.access_policies['user_management_policy'] = AccessPolicy(
            name='user_management_policy',
            resource_type=ResourceType.USER_DATA,
            required_permissions={Permission.USER_ADMIN},
            access_level=AccessLevel.FULL_ACCESS,
            conditions=[],
            exceptions=[f'^/api/users/{Permission}']  # Users can access their own data
        )

    async def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """Get all permissions for a user"""
        try:
            # Check cache first
            if user_id in self.user_permissions_cache:
                cache_time, permissions = self.user_permissions_cache[user_id]
                if datetime.now() - cache_time < timedelta(minutes=5):
                    return permissions

            # Get user role (placeholder implementation)
            user_role_name = 'user'  # In production, get from database

            if user_role_name not in self.roles:
                return set()

            user_role = self.roles[user_role_name]
            permissions = user_role.permissions.copy()

            # Add inherited permissions
            if user_role.inherits_from:
                for parent_role_name in user_role.inherits_from:
                    if parent_role_name in self.roles:
                        permissions.update(self.roles[parent_role_name].permissions)

            # Cache result
            self.user_permissions_cache[user_id] = (datetime.now(), permissions)

            return permissions

        except Exception as e:
            logger.error(f"Get user permissions error: {e}")
            return set()

    async def create_role(self, role_data: Dict[str, Any]) -> bool:
        """Create new role"""
        try:
            role_name = role_data.get('name')
            if not role_name or role_name in self.roles:
                return False

            role = Role(
                name=role_name,
                description=role_data.get('description', ''),
                permissions=set(Permission(p) for p in role_data.get('permissions', [])),
                resource_access={
                    ResourceType(rt): AccessLevel(al)
                    for rt, al in role_data.get('resource_access', {}).items()
                },
                inherits_from=role_data.get('inherits_from', []),
                constraints=role_data.get('constraints', {}),
                time_restrictions=role_data.get('time_restrictions', {}),
                ip_restrictions=role_data.get('ip_restrictions', [])
            )

            self.roles[role_name] = role

            # Save to database (placeholder)
            await self._save_role_to_database(role)

            logger.info(f"Created role: {role_name}")
            return True

        except Exception as e:
            logger.error(f"Create role error: {e}")
            return False

    async def update_role(self, role_name: str, role_data: Dict[str, Any]) -> bool:
        """Update existing role"""
        try:
            if role_name not in self.roles:
                return False

            existing_role = self.roles[role_name]

            # Update role properties
            if 'description' in role_data:
                existing_role.description = role_data['description']
            if 'permissions' in role_data:
                existing_role.permissions = set(Permission(p) for p in role_data['permissions'])
            if 'resource_access' in role_data:
                existing_role.resource_access = {
                    ResourceType(rt): AccessLevel(al)
                    for rt, al in role_data['resource_access'].items()
                }
            if 'constraints' in role_data:
                existing_role.constraints = role_data['constraints']
            if 'time_restrictions' in role_data:
                existing_role.time_restrictions = role_data['time_restrictions']
            if 'ip_restrictions' in role_data:
                existing_role.ip_restrictions = role_data['ip_restrictions']

            # Save to database (placeholder)
            await self._save_role_to_database(existing_role)

            # Clear permissions cache
            self.user_permissions_cache.clear()

            logger.info(f"Updated role: {role_name}")
            return True

        except Exception as e:
            logger.error(f"Update role error: {e}")
            return False

    async def delete_role(self, role_name: str) -> bool:
        """Delete role"""
        try:
            if role_name not in self.roles:
                return False

            # Check if role is in use
            # In production, check if any users have this role

            del self.roles[role_name]

            # Remove from database (placeholder)
            await self._delete_role_from_database(role_name)

            # Clear permissions cache
            self.user_permissions_cache.clear()

            logger.info(f"Deleted role: {role_name}")
            return True

        except Exception as e:
            logger.error(f"Delete role error: {e}")
            return False

    async def create_access_policy(self, policy_data: Dict[str, Any]) -> bool:
        """Create new access policy"""
        try:
            policy_name = policy_data.get('name')
            if not policy_name or policy_name in self.access_policies:
                return False

            policy = AccessPolicy(
                name=policy_name,
                resource_type=ResourceType(policy_data.get('resource_type')),
                required_permissions=set(Permission(p) for p in policy_data.get('required_permissions', [])),
                access_level=AccessLevel(policy_data.get('access_level')),
                conditions=policy_data.get('conditions', []),
                exceptions=policy_data.get('exceptions', []),
                time_constraints=policy_data.get('time_constraints', {}),
                location_constraints=policy_data.get('location_constraints', [])
            )

            self.access_policies[policy_name] = policy

            # Save to database (placeholder)
            await self._save_policy_to_database(policy)

            logger.info(f"Created access policy: {policy_name}")
            return True

        except Exception as e:
            logger.error(f"Create access policy error: {e}")
            return False

    async def get_access_logs(self, user_id: str = None, start_time: datetime = None,
                            end_time: datetime = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get access logs with filtering"""
        try:
            logs = self.access_logs.copy()

            # Filter by user
            if user_id:
                logs = [log for log in logs if log['user_id'] == user_id]

            # Filter by time range
            if start_time:
                logs = [log for log in logs if datetime.fromisoformat(log['timestamp']) >= start_time]
            if end_time:
                logs = [log for log in logs if datetime.fromisoformat(log['timestamp']) <= end_time]

            # Sort by timestamp (most recent first)
            logs.sort(key=lambda x: x['timestamp'], reverse=True)

            return logs[:limit]

        except Exception as e:
            logger.error(f"Get access logs error: {e}")
            return []

    async def _save_role_to_database(self, role: Role):
        """Save role to database (placeholder)"""
        pass

    async def _delete_role_from_database(self, role_name: str):
        """Delete role from database (placeholder)"""
        pass

    async def _save_policy_to_database(self, policy: AccessPolicy):
        """Save policy to database (placeholder)"""
        pass