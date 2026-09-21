"""
Authentication and Authorization Service
JWT-based auth with role-based access control
"""

import asyncio
import jwt
import bcrypt
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import redis
import json
import uuid
import logging
from passlib.context import CryptContext
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import asyncpg
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement

logger = logging.getLogger(__name__)


class UserRole(Enum):
    ADMIN = "admin"
    GAME_MASTER = "game_master"
    PLAYER = "player"
    MODERATOR = "moderator"
    DEVELOPER = "developer"
    GUEST = "guest"


class Permission(Enum):
    # Game permissions
    CREATE_GAME = "create_game"
    JOIN_GAME = "join_game"
    MODERATE_GAME = "moderate_game"
    VIEW_GAMES = "view_games"

    # Agent permissions
    CREATE_AGENT = "create_agent"
    CONTROL_AGENT = "control_agent"
    VIEW_AGENTS = "view_agents"

    # System permissions
    VIEW_METRICS = "view_metrics"
    MANAGE_SYSTEM = "manage_system"
    VIEW_LOGS = "view_logs"

    # User permissions
    MANAGE_USERS = "manage_users"
    BAN_USERS = "ban_users"
    VIEW_PROFILES = "view_profiles"


@dataclass
class User:
    user_id: str
    username: str
    email: str
    password_hash: str
    role: UserRole
    permissions: List[Permission] = field(default_factory=list)
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    login_count: int = 0
    profile: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    api_keys: List[str] = field(default_factory=list)
    sessions: List[str] = field(default_factory=list)
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None


@dataclass
class Session:
    session_id: str
    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))
    ip_address: str = ""
    user_agent: str = ""
    is_active: bool = True
    last_activity: datetime = field(default_factory=datetime.now)


@dataclass
class APIKey:
    key_id: str
    user_id: str
    name: str
    key_hash: str
    permissions: List[Permission] = field(default_factory=list)
    rate_limit: int = 1000  # requests per hour
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    last_used: Optional[datetime] = None
    usage_count: int = 0


class AuthConfig:
    def __init__(self):
        self.jwt_secret = "your-super-secret-jwt-key-change-in-production"
        self.jwt_algorithm = "HS256"
        self.jwt_expiration = timedelta(hours=24)
        self.refresh_token_expiration = timedelta(days=30)
        self.max_sessions_per_user = 5
        self.password_min_length = 8
        self.mfa_issuer = "DMLogn8n"
        self.redis_session_prefix = "session:"
        self.failed_login_threshold = 5
        self.account_lockout_duration = timedelta(minutes=15)


class AuthService:
    """Comprehensive authentication and authorization service"""

    def __init__(self, config: AuthConfig):
        self.config = config
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.security = HTTPBearer()

        # Database connections
        self.pg_pool: Optional[asyncpg.Pool] = None
        self.cassandra_cluster: Optional[Cluster] = None
        self.redis_client: Optional[redis.Redis] = None

        # In-memory caches
        self.user_cache: Dict[str, User] = {}
        self.session_cache: Dict[str, Session] = {}
        self.permission_cache: Dict[str, List[Permission]] = {}

        # Rate limiting
        self.rate_limiter: Dict[str, List[datetime]] = {}

        # Role-permission mapping
        self.role_permissions = self._initialize_role_permissions()

    async def initialize(self):
        """Initialize auth service with database connections"""
        logger.info("Initializing authentication service")

        # Initialize PostgreSQL
        self.pg_pool = await asyncpg.create_pool(
            host="localhost",
            port=5432,
            user="dmlogn8n_user",
            password="your_postgres_password",
            database="dmlogn8n_auth",
            min_size=5,
            max_size=20
        )

        # Initialize Cassandra for session storage
        self.cassandra_cluster = Cluster(['localhost'], port=9042)
        self.cassandra_session = self.cassandra_cluster.connect()

        # Initialize Redis for caching
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True,
            db=0
        )

        # Create database tables
        await self._create_tables()

        logger.info("Authentication service initialized")

    def _initialize_role_permissions(self) -> Dict[UserRole, List[Permission]]:
        """Initialize role-permission mappings"""
        return {
            UserRole.ADMIN: list(Permission),  # All permissions
            UserRole.DEVELOPER: [
                Permission.CREATE_AGENT, Permission.CONTROL_AGENT, Permission.VIEW_AGENTS,
                Permission.CREATE_GAME, Permission.JOIN_GAME, Permission.VIEW_GAMES,
                Permission.VIEW_METRICS, Permission.VIEW_PROFILES
            ],
            UserRole.GAME_MASTER: [
                Permission.CREATE_GAME, Permission.JOIN_GAME, Permission.MODERATE_GAME,
                Permission.VIEW_GAMES, Permission.CREATE_AGENT, Permission.CONTROL_AGENT,
                Permission.VIEW_AGENTS, Permission.VIEW_PROFILES
            ],
            UserRole.MODERATOR: [
                Permission.VIEW_GAMES, Permission.MODERATE_GAME, Permission.VIEW_AGENTS,
                Permission.VIEW_PROFILES, Permission.BAN_USERS
            ],
            UserRole.PLAYER: [
                Permission.JOIN_GAME, Permission.VIEW_GAMES, Permission.VIEW_PROFILES,
                Permission.CREATE_AGENT
            ],
            UserRole.GUEST: [
                Permission.VIEW_GAMES, Permission.VIEW_PROFILES
            ]
        }

    async def _create_tables(self):
        """Create database tables"""
        # PostgreSQL tables
        async with self.pg_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL DEFAULT 'player',
                    is_active BOOLEAN DEFAULT true,
                    is_verified BOOLEAN DEFAULT false,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    login_count INTEGER DEFAULT 0,
                    profile JSONB DEFAULT '{}',
                    preferences JSONB DEFAULT '{}',
                    mfa_enabled BOOLEAN DEFAULT false,
                    mfa_secret VARCHAR(32)
                );

                CREATE TABLE IF NOT EXISTS api_keys (
                    key_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
                    name VARCHAR(100) NOT NULL,
                    key_hash VARCHAR(255) NOT NULL,
                    permissions JSONB DEFAULT '[]',
                    rate_limit INTEGER DEFAULT 1000,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT true,
                    last_used TIMESTAMP,
                    usage_count INTEGER DEFAULT 0
                );

                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
                CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);
            """)

        # Cassandra tables for sessions
        await self.cassandra_session.execute("""
            CREATE TABLE IF NOT EXISTS auth.sessions (
                session_id UUID PRIMARY KEY,
                user_id UUID,
                created_at TIMESTAMP,
                expires_at TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                is_active BOOLEAN,
                last_activity TIMESTAMP
            );
        """)

        # Redis indexes
        await self.redis_client.ft().create_index(
            fields=[
                redis.fields.TextField("$.user_id"),
                redis.fields.TagField("$.is_active"),
                redis.fields.NumericField("$.expires_at")
            ],
            prefix="session:"
        )

    async def register_user(self,
                          username: str,
                          email: str,
                          password: str,
                          role: UserRole = UserRole.PLAYER) -> User:
        """Register a new user"""
        # Validate input
        if len(password) < self.config.password_min_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password must be at least {self.config.password_min_length} characters"
            )

        # Check if user exists
        existing_user = await self._get_user_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )

        # Hash password
        password_hash = self.pwd_context.hash(password)

        # Create user
        user = User(
            user_id=str(uuid.uuid4()),
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            permissions=self.role_permissions.get(role, [])
        )

        # Save to database
        await self._save_user(user)

        logger.info(f"User registered: {username} ({email})")
        return user

    async def authenticate_user(self,
                              username: str,
                              password: str,
                              ip_address: str = "",
                              user_agent: str = "") -> Dict[str, Any]:
        """Authenticate user and return tokens"""
        # Check rate limiting
        await self._check_rate_limit(ip_address, "login")

        # Get user
        user = await self._get_user_by_username(username)
        if not user:
            await self._record_failed_attempt(ip_address, "login")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )

        # Verify password
        if not self.pwd_context.verify(password, user.password_hash):
            await self._record_failed_attempt(ip_address, "login")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Update user login info
        user.last_login = datetime.now()
        user.login_count += 1
        await self._save_user(user)

        # Create session
        session = await self._create_session(user.user_id, ip_address, user_agent)

        # Generate tokens
        access_token = await self._generate_access_token(user)
        refresh_token = await self._generate_refresh_token(user)

        # Clear failed attempts
        await self._clear_failed_attempts(ip_address, "login")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": int(self.config.jwt_expiration.total_seconds()),
            "session_id": session.session_id,
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
                "permissions": [p.value for p in user.permissions]
            }
        }

    async def _create_session(self,
                            user_id: str,
                            ip_address: str = "",
                            user_agent: str = "") -> Session:
        """Create a new session"""
        # Check max sessions
        sessions = await self._get_user_sessions(user_id)
        active_sessions = [s for s in sessions if s.is_active and s.expires_at > datetime.now()]

        if len(active_sessions) >= self.config.max_sessions_per_user:
            # Remove oldest session
            oldest = min(active_sessions, key=lambda s: s.created_at)
            await self._revoke_session(oldest.session_id)

        # Create new session
        session = Session(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now() + self.config.jwt_expiration
        )

        # Save to Cassandra
        await self.cassandra_session.execute(
            """
            INSERT INTO auth.sessions
            (session_id, user_id, created_at, expires_at, ip_address, user_agent, is_active, last_activity)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (session.session_id, session.user_id, session.created_at, session.expires_at,
             session.ip_address, session.user_agent, session.is_active, session.last_activity)
        )

        # Cache in Redis
        await self.redis_client.hset(
            f"{self.config.redis_session_prefix}{session.session_id}",
            mapping={
                "user_id": session.user_id,
                "created_at": session.created_at.isoformat(),
                "expires_at": session.expires_at.isoformat(),
                "ip_address": session.ip_address,
                "user_agent": session.user_agent,
                "is_active": str(session.is_active),
                "last_activity": session.last_activity.isoformat()
            }
        )
        await self.redis_client.expire(
            f"{self.config.redis_session_prefix}{session.session_id}",
            int(self.config.jwt_expiration.total_seconds())
        )

        return session

    async def _generate_access_token(self, user: User) -> str:
        """Generate JWT access token"""
        payload = {
            "sub": user.user_id,
            "username": user.username,
            "role": user.role.value,
            "permissions": [p.value for p in user.permissions],
            "type": "access",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + self.config.jwt_expiration
        }

        return jwt.encode(payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm)

    async def _generate_refresh_token(self, user: User) -> str:
        """Generate JWT refresh token"""
        payload = {
            "sub": user.user_id,
            "type": "refresh",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + self.config.refresh_token_expiration
        }

        return jwt.encode(payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm)

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        payload = await self.verify_token(refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Get user
        user = await self._get_user_by_id(payload["sub"])
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Generate new access token
        access_token = await self._generate_access_token(user)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": int(self.config.jwt_expiration.total_seconds())
        }

    async def logout(self, session_id: str) -> None:
        """Logout user by revoking session"""
        await self._revoke_session(session_id)

    async def logout_all_sessions(self, user_id: str) -> None:
        """Logout all sessions for a user"""
        sessions = await self._get_user_sessions(user_id)
        for session in sessions:
            await self._revoke_session(session.session_id)

    async def _revoke_session(self, session_id: str) -> None:
        """Revoke a session"""
        # Update in Cassandra
        await self.cassandra_session.execute(
            "UPDATE auth.sessions SET is_active = false WHERE session_id = %s",
            (session_id,)
        )

        # Remove from Redis
        await self.redis_client.delete(f"{self.config.redis_session_prefix}{session_id}")

    async def create_api_key(self,
                           user_id: str,
                           name: str,
                           permissions: List[Permission],
                           rate_limit: int = 1000,
                           expires_in: Optional[timedelta] = None) -> str:
        """Create API key for user"""
        # Generate API key
        api_key = f"dl8_{uuid.uuid4().hex}"
        key_hash = self.pwd_context.hash(api_key)

        # Create API key object
        api_key_obj = APIKey(
            key_id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            permissions=permissions,
            rate_limit=rate_limit,
            expires_at=datetime.now() + expires_in if expires_in else None
        )

        # Save to database
        await self._save_api_key(api_key_obj)

        return api_key

    async def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Verify API key and return user info"""
        # Get all API keys
        keys = await self._get_all_api_keys()

        for key_obj in keys:
            if self.pwd_context.verify(api_key, key_obj.key_hash):
                if not key_obj.is_active:
                    continue

                if key_obj.expires_at and key_obj.expires_at < datetime.now():
                    continue

                # Update usage
                key_obj.last_used = datetime.now()
                key_obj.usage_count += 1
                await self._save_api_key(key_obj)

                user = await self._get_user_by_id(key_obj.user_id)
                if user and user.is_active:
                    return {
                        "user_id": user.user_id,
                        "username": user.username,
                        "role": user.role.value,
                        "permissions": [p.value for p in key_obj.permissions],
                        "rate_limit": key_obj.rate_limit
                    }

        return None

    async def check_permission(self,
                            user_id: str,
                            permission: Permission) -> bool:
        """Check if user has permission"""
        # Check cache first
        cache_key = f"perm:{user_id}"
        if cache_key in self.permission_cache:
            return permission in self.permission_cache[cache_key]

        # Get user
        user = await self._get_user_by_id(user_id)
        if not user:
            return False

        # Check permissions
        has_permission = permission in user.permissions

        # Cache result
        self.permission_cache[cache_key] = user.permissions

        return has_permission

    async def check_rate_limit(self,
                             identifier: str,
                             limit: int = 100,
                             window: timedelta = timedelta(hours=1)) -> bool:
        """Check rate limit"""
        now = datetime.now()
        window_start = now - window

        # Get existing requests from Redis
        key = f"rate_limit:{identifier}"
        requests = await self.redis_client.zrangebyscore(
            key,
            window_start.timestamp(),
            now.timestamp()
        )

        if len(requests) >= limit:
            return False

        # Add current request
        await self.redis_client.zadd(key, {str(now.timestamp()): now.timestamp()})
        await self.redis_client.expire(key, int(window.total_seconds()))

        return True

    async def _check_rate_limit(self, ip_address: str, action: str) -> None:
        """Check rate limit for specific action"""
        key = f"{action}:{ip_address}"

        if key not in self.rate_limiter:
            self.rate_limiter[key] = []

        # Clean old entries
        now = datetime.now()
        self.rate_limiter[key] = [
            t for t in self.rate_limiter[key]
            if now - t < timedelta(minutes=15)
        ]

        if len(self.rate_limiter[key]) >= self.config.failed_login_threshold:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Please try again later."
            )

    async def _record_failed_attempt(self, ip_address: str, action: str) -> None:
        """Record failed attempt"""
        key = f"{action}:{ip_address}"
        if key not in self.rate_limiter:
            self.rate_limiter[key] = []

        self.rate_limiter[key].append(datetime.now())

    async def _clear_failed_attempts(self, ip_address: str, action: str) -> None:
        """Clear failed attempts"""
        key = f"{action}:{ip_address}"
        if key in self.rate_limiter:
            del self.rate_limiter[key]

    async def _get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        # Check cache
        if user_id in self.user_cache:
            return self.user_cache[user_id]

        # Query database
        async with self.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE user_id = $1",
                user_id
            )

            if row:
                user = User(
                    user_id=row['user_id'],
                    username=row['username'],
                    email=row['email'],
                    password_hash=row['password_hash'],
                    role=UserRole(row['role']),
                    is_active=row['is_active'],
                    is_verified=row['is_verified'],
                    created_at=row['created_at'],
                    last_login=row['last_login'],
                    login_count=row['login_count'],
                    profile=row['profile'],
                    preferences=row['preferences'],
                    mfa_enabled=row['mfa_enabled'],
                    mfa_secret=row['mfa_secret']
                )
                user.permissions = self.role_permissions.get(user.role, [])

                # Cache user
                self.user_cache[user_id] = user
                return user

        return None

    async def _get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        async with self.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1",
                email
            )

            if row:
                return await self._get_user_by_id(row['user_id'])

        return None

    async def _get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        async with self.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE username = $1",
                username
            )

            if row:
                return await self._get_user_by_id(row['user_id'])

        return None

    async def _save_user(self, user: User) -> None:
        """Save user to database"""
        async with self.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users
                (user_id, username, email, password_hash, role, is_active, is_verified,
                 created_at, last_login, login_count, profile, preferences,
                 mfa_enabled, mfa_secret)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                ON CONFLICT (user_id) DO UPDATE SET
                username = EXCLUDED.username,
                email = EXCLUDED.email,
                password_hash = EXCLUDED.password_hash,
                role = EXCLUDED.role,
                is_active = EXCLUDED.is_active,
                is_verified = EXCLUDED.is_verified,
                last_login = EXCLUDED.last_login,
                login_count = EXCLUDED.login_count,
                profile = EXCLUDED.profile,
                preferences = EXCLUDED.preferences,
                mfa_enabled = EXCLUDED.mfa_enabled,
                mfa_secret = EXCLUDED.mfa_secret
                """,
                user.user_id, user.username, user.email, user.password_hash,
                user.role.value, user.is_active, user.is_verified,
                user.created_at, user.last_login, user.login_count,
                json.dumps(user.profile), json.dumps(user.preferences),
                user.mfa_enabled, user.mfa_secret
            )

        # Update cache
        self.user_cache[user.user_id] = user

    async def _get_user_sessions(self, user_id: str) -> List[Session]:
        """Get all sessions for a user"""
        sessions = []

        # Query Cassandra
        rows = await self.cassandra_session.execute(
            "SELECT * FROM auth.sessions WHERE user_id = %s ALLOW FILTERING",
            (user_id,)
        )

        for row in rows:
            session = Session(
                session_id=str(row.session_id),
                user_id=str(row.user_id),
                created_at=row.created_at,
                expires_at=row.expires_at,
                ip_address=row.ip_address,
                user_agent=row.user_agent,
                is_active=row.is_active,
                last_activity=row.last_activity
            )
            sessions.append(session)

        return sessions

    async def _save_api_key(self, api_key: APIKey) -> None:
        """Save API key to database"""
        async with self.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO api_keys
                (key_id, user_id, name, key_hash, permissions, rate_limit,
                 created_at, expires_at, is_active, last_used, usage_count)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (key_id) DO UPDATE SET
                name = EXCLUDED.name,
                permissions = EXCLUDED.permissions,
                rate_limit = EXCLUDED.rate_limit,
                expires_at = EXCLUDED.expires_at,
                is_active = EXCLUDED.is_active,
                last_used = EXCLUDED.last_used,
                usage_count = EXCLUDED.usage_count
                """,
                api_key.key_id, api_key.user_id, api_key.name, api_key.key_hash,
                json.dumps([p.value for p in api_key.permissions]),
                api_key.rate_limit, api_key.created_at, api_key.expires_at,
                api_key.is_active, api_key.last_used, api_key.usage_count
            )

    async def _get_all_api_keys(self) -> List[APIKey]:
        """Get all API keys"""
        keys = []

        async with self.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM api_keys WHERE is_active = true")

            for row in rows:
                key = APIKey(
                    key_id=row['key_id'],
                    user_id=row['user_id'],
                    name=row['name'],
                    key_hash=row['key_hash'],
                    permissions=[Permission(p) for p in json.loads(row['permissions'])],
                    rate_limit=row['rate_limit'],
                    created_at=row['created_at'],
                    expires_at=row['expires_at'],
                    is_active=row['is_active'],
                    last_used=row['last_used'],
                    usage_count=row['usage_count']
                )
                keys.append(key)

        return keys

    async def close(self):
        """Close database connections"""
        if self.pg_pool:
            await self.pg_pool.close()

        if self.cassandra_cluster:
            self.cassandra_cluster.shutdown()

        if self.redis_client:
            self.redis_client.close()


# FastAPI integration
class FastAPIAuth:
    """FastAPI authentication dependencies"""

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    async def get_current_user(self,
                             credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> User:
        """Get current user from JWT token"""
        token = credentials.credentials
        payload = await self.auth_service.verify_token(token)

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        user = await self.auth_service._get_user_by_id(payload["sub"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        return user

    async def require_permission(self, permission: Permission):
        """Require specific permission"""
        def permission_checker(current_user: User = Depends(self.get_current_user)):
            if permission not in current_user.permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return current_user
        return permission_checker

    async def require_role(self, role: UserRole):
        """Require specific role"""
        def role_checker(current_user: User = Depends(self.get_current_user)):
            if current_user.role != role and current_user.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires {role.value} role"
                )
            return current_user
        return role_checker


# Pydantic models for API
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.PLAYER


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    session_id: str
    user: Dict[str, Any]


class APIKeyCreate(BaseModel):
    name: str
    permissions: List[str]
    rate_limit: int = 1000
    expires_in_days: Optional[int] = None


# Initialize auth service
auth_config = AuthConfig()
auth_service = AuthService(auth_config)
fastapi_auth = FastAPIAuth(auth_service)