"""
Database configuration schemas for DMLogn8n multi-agent platform.
"""

from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, validator, RootModel
from enum import Enum
import secrets


class DatabaseType(str, Enum):
    """Supported database types."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    REDIS = "redis"
    MONGODB = "mongodb"


class SSLMode(str, Enum):
    """SSL connection modes."""
    DISABLE = "disable"
    ALLOW = "allow"
    PREFER = "prefer"
    REQUIRE = "require"
    VERIFY_CA = "verify-ca"
    VERIFY_FULL = "verify-full"


class DatabaseCredentials(BaseModel):
    """Database connection credentials."""
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    host: str = Field(..., description="Database host")
    port: int = Field(..., ge=1, le=65535, description="Database port")
    database: str = Field(..., description="Database name")

    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class SSLConfig(BaseModel):
    """SSL configuration for database connections."""
    ssl_mode: SSLMode = Field(default=SSLMode.PREFER, description="SSL mode")
    ssl_cert: Optional[str] = Field(default=None, description="Path to SSL certificate")
    ssl_key: Optional[str] = Field(default=None, description="Path to SSL private key")
    ssl_ca: Optional[str] = Field(default=None, description="Path to CA certificate")
    ssl_crl: Optional[str] = Field(default=None, description="Path to CRL file")


class ConnectionPool(BaseModel):
    """Database connection pool configuration."""
    min_connections: int = Field(default=1, ge=1, description="Minimum number of connections")
    max_connections: int = Field(default=10, ge=1, description="Maximum number of connections")
    connection_timeout: int = Field(default=30, ge=1, description="Connection timeout in seconds")
    idle_timeout: int = Field(default=300, ge=1, description="Idle timeout in seconds")
    max_lifetime: int = Field(default=3600, ge=1, description="Maximum connection lifetime in seconds")
    health_check_interval: int = Field(default=30, ge=1, description="Health check interval in seconds")

    @validator('max_connections')
    def validate_pool_size(cls, v, values):
        """Validate pool size constraints."""
        if 'min_connections' in values and v < values['min_connections']:
            raise ValueError("max_connections must be greater than or equal to min_connections")
        return v


class RetryConfig(BaseModel):
    """Database retry configuration."""
    max_retries: int = Field(default=3, ge=0, description="Maximum number of retry attempts")
    retry_delay: float = Field(default=1.0, ge=0, description="Initial retry delay in seconds")
    backoff_multiplier: float = Field(default=2.0, ge=1.0, description="Backoff multiplier")
    max_retry_delay: float = Field(default=60.0, ge=0, description="Maximum retry delay in seconds")
    retry_on_errors: List[str] = Field(
        default=["connection_error", "timeout_error", "deadlock"],
        description="List of error types to retry on"
    )


class DatabaseConfig(BaseModel):
    """Main database configuration."""
    name: str = Field(..., description="Database configuration name")
    type: DatabaseType = Field(..., description="Database type")
    credentials: DatabaseCredentials = Field(..., description="Database credentials")
    pool: ConnectionPool = Field(default_factory=ConnectionPool, description="Connection pool settings")
    ssl: Optional[SSLConfig] = Field(default=None, description="SSL configuration")
    retry: RetryConfig = Field(default_factory=RetryConfig, description="Retry configuration")
    enabled: bool = Field(default=True, description="Whether this database is enabled")
    read_only: bool = Field(default=False, description="Whether this database is read-only")

    # Database-specific options
    options: Dict[str, Any] = Field(default_factory=dict, description="Database-specific options")

    # Connection string template (optional, overrides auto-generated)
    connection_string: Optional[str] = Field(default=None, description="Custom connection string")

    @validator('name')
    def validate_name(cls, v):
        """Validate database name."""
        if not v or not v.strip():
            raise ValueError("Database name cannot be empty")
        if not v.replace('-', '_').replace('_', '').isalnum():
            raise ValueError("Database name must contain only alphanumeric characters, hyphens, and underscores")
        return v.strip()

    def get_connection_string(self) -> str:
        """Generate connection string."""
        if self.connection_string:
            return self.connection_string

        if self.type == DatabaseType.POSTGRESQL:
            return (
                f"postgresql://{self.credentials.username}:{self.credentials.password}"
                f"@{self.credentials.host}:{self.credentials.port}/{self.credentials.database}"
            )
        elif self.type == DatabaseType.MYSQL:
            return (
                f"mysql+pymysql://{self.credentials.username}:{self.credentials.password}"
                f"@{self.credentials.host}:{self.credentials.port}/{self.credentials.database}"
            )
        elif self.type == DatabaseType.SQLITE:
            return f"sqlite:///{self.credentials.database}"
        elif self.type == DatabaseType.REDIS:
            return (
                f"redis://:{self.credentials.password}"
                f"@{self.credentials.host}:{self.credentials.port}/{self.credentials.database}"
            )
        elif self.type == DatabaseType.MONGODB:
            return (
                f"mongodb://{self.credentials.username}:{self.credentials.password}"
                f"@{self.credentials.host}:{self.credentials.port}/{self.credentials.database}"
            )
        else:
            raise ValueError(f"Unsupported database type: {self.type}")


class DatabaseCluster(BaseModel):
    """Database cluster configuration for high availability."""
    name: str = Field(..., description="Cluster name")
    primary: DatabaseConfig = Field(..., description="Primary database configuration")
    replicas: List[DatabaseConfig] = Field(default_factory=list, description="Replica database configurations")
    load_balancing_strategy: str = Field(default="round_robin", description="Load balancing strategy")
    failover_timeout: int = Field(default=30, ge=1, description="Failover timeout in seconds")
    health_check_interval: int = Field(default=10, ge=1, description="Health check interval in seconds")

    @validator('replicas')
    def validate_replicas(cls, v):
        """Validate replica configurations."""
        if len(v) > 10:
            raise ValueError("Maximum 10 replicas allowed per cluster")
        return v


class MultiDatabaseConfig(RootModel):
    """Multi-database configuration root model."""
    databases: Dict[str, DatabaseConfig] = Field(default_factory=dict, description="Database configurations")
    clusters: Dict[str, DatabaseCluster] = Field(default_factory=dict, description="Database clusters")
    default_database: str = Field(..., description="Default database name")

    @validator('default_database')
    def validate_default_exists(cls, v, values):
        """Validate default database exists."""
        if 'databases' in values and v not in values['databases']:
            raise ValueError(f"Default database '{v}' not found in databases")
        return v

    def get_database(self, name: Optional[str] = None) -> DatabaseConfig:
        """Get database configuration by name."""
        db_name = name or self.default_database
        if db_name not in self.databases:
            raise ValueError(f"Database '{db_name}' not found")
        return self.databases[db_name]

    def get_cluster(self, name: str) -> DatabaseCluster:
        """Get cluster configuration by name."""
        if name not in self.clusters:
            raise ValueError(f"Cluster '{name}' not found")
        return self.clusters[name]


# Predefined database configurations for common use cases
class DatabasePresets:
    """Predefined database configurations."""

    @staticmethod
    def postgresql_high_performance() -> DatabaseConfig:
        """High-performance PostgreSQL configuration."""
        return DatabaseConfig(
            name="postgresql_high_perf",
            type=DatabaseType.POSTGRESQL,
            credentials=DatabaseCredentials(
                username="${DB_USERNAME}",
                password="${DB_PASSWORD}",
                host="${DB_HOST}",
                port=5432,
                database="${DB_NAME}"
            ),
            pool=ConnectionPool(
                min_connections=5,
                max_connections=50,
                connection_timeout=10,
                idle_timeout=600,
                max_lifetime=7200
            ),
            ssl=SSLConfig(ssl_mode=SSLMode.REQUIRE),
            options={
                "sslmode": "require",
                "application_name": "dmlogn8n",
                "connect_timeout": 10,
                "statement_timeout": 30000
            }
        )

    @staticmethod
    def redis_cache() -> DatabaseConfig:
        """Redis cache configuration."""
        return DatabaseConfig(
            name="redis_cache",
            type=DatabaseType.REDIS,
            credentials=DatabaseCredentials(
                username="${REDIS_USERNAME}",
                password="${REDIS_PASSWORD}",
                host="${REDIS_HOST}",
                port=6379,
                database="0"
            ),
            pool=ConnectionPool(
                min_connections=2,
                max_connections=20,
                connection_timeout=5,
                idle_timeout=300
            ),
            options={
                "decode_responses": True,
                "socket_connect_timeout": 5,
                "socket_timeout": 5,
                "max_connections": 20
            }
        )

    @staticmethod
    def sqlite_development() -> DatabaseConfig:
        """SQLite development configuration."""
        return DatabaseConfig(
            name="sqlite_dev",
            type=DatabaseType.SQLITE,
            credentials=DatabaseCredentials(
                username="",
                password="",
                host="",
                port=0,
                database="./data/dmlogn8n_dev.db"
            ),
            pool=ConnectionPool(
                min_connections=1,
                max_connections=5,
                connection_timeout=30
            ),
            options={
                "check_same_thread": False,
                "echo": True,
                "pool_pre_ping": True
            }
        )