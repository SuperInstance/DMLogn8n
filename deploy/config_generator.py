#!/usr/bin/env python3
"""
Configuration Generator for DMLogn8n
Generates environment-specific configurations for all services
"""

import os
import sys
import json
import secrets
import logging
import string
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from cryptography.fernet import Fernet
import yaml


@dataclass
class DatabaseConfig:
    host: str
    port: int
    username: str
    password: str
    database: str
    ssl_enabled: bool = False
    pool_size: int = 10
    max_overflow: int = 20


@dataclass
class RedisConfig:
    host: str
    port: int
    password: Optional[str] = None
    db: int = 0
    ssl_enabled: bool = False
    max_connections: int = 10


@dataclass
class N8NConfig:
    host: str
    port: int
    basic_auth_enabled: bool = True
    basic_auth_user: str = "admin"
    basic_auth_password: str = ""
    webhook_url: str = ""
    encryption_key: str = ""
    jwt_secret: str = ""


@dataclass
class APIConfig:
    host: str
    port: int
    secret_key: str = ""
    jwt_secret_key: str = ""
    cors_origins: str = "*"
    rate_limit: str = "100/hour"
    debug: bool = False


@dataclass
class WebConfig:
    host: str
    port: int
    api_url: str = ""
    n8n_url: str = ""
    ws_url: str = ""
    ssl_enabled: bool = False


@dataclass
class EnvironmentConfig:
    name: str
    database: DatabaseConfig
    redis: RedisConfig
    n8n: N8NConfig
    api: APIConfig
    web: WebConfig
    monitoring_enabled: bool = True
    log_level: str = "INFO"
    timezone: str = "UTC"


class ConfigGenerator:
    """Environment-specific configuration generator"""

    def __init__(self, environment: str):
        self.environment = environment
        self.logger = logging.getLogger(__name__)

        # Paths
        self.config_dir = Path("/etc/dmlogn8n")
        self.templates_dir = Path(__file__).parent / "templates"
        self.output_dir = Path(__file__).parent / "configs"

        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Generate secrets
        self.secrets = self.generate_secrets()

    def generate_secrets(self) -> Dict[str, str]:
        """Generate secure secrets for the environment"""
        return {
            "db_root_password": self.generate_password(32),
            "db_user_password": self.generate_password(24),
            "redis_password": self.generate_password(24),
            "n8n_basic_auth_password": self.generate_password(16),
            "n8n_encryption_key": Fernet.generate_key().decode(),
            "n8n_jwt_secret": self.generate_password(32),
            "api_secret_key": self.generate_password(32),
            "api_jwt_secret": self.generate_password(32),
            "flask_secret_key": self.generate_password(32),
            "session_secret": self.generate_password(32),
        }

    def generate_password(self, length: int = 16) -> str:
        """Generate a secure password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def get_base_config(self) -> EnvironmentConfig:
        """Get base configuration for the environment"""
        # Environment-specific hosts and settings
        if self.environment == "development":
            return EnvironmentConfig(
                name="development",
                database=DatabaseConfig(
                    host="localhost",
                    port=3306,
                    username="dmlogn8n_user",
                    password=self.secrets["db_user_password"],
                    database="dmlogn8n",
                    ssl_enabled=False
                ),
                redis=RedisConfig(
                    host="localhost",
                    port=6379,
                    password=None,
                    db=0,
                    ssl_enabled=False
                ),
                n8n=N8NConfig(
                    host="localhost",
                    port=5678,
                    basic_auth_enabled=True,
                    basic_auth_user="admin",
                    basic_auth_password=self.secrets["n8n_basic_auth_password"],
                    webhook_url="http://localhost:5678/",
                    encryption_key=self.secrets["n8n_encryption_key"],
                    jwt_secret=self.secrets["n8n_jwt_secret"]
                ),
                api=APIConfig(
                    host="localhost",
                    port=8000,
                    secret_key=self.secrets["api_secret_key"],
                    jwt_secret_key=self.secrets["api_jwt_secret"],
                    cors_origins="*",
                    rate_limit="1000/hour",
                    debug=True
                ),
                web=WebConfig(
                    host="localhost",
                    port=3000,
                    api_url="http://localhost:8000",
                    n8n_url="http://localhost:5678",
                    ws_url="ws://localhost:8000",
                    ssl_enabled=False
                ),
                monitoring_enabled=False,
                log_level="DEBUG",
                timezone="UTC"
            )

        elif self.environment == "staging":
            return EnvironmentConfig(
                name="staging",
                database=DatabaseConfig(
                    host="staging-db.dmlogn8n.com",
                    port=3306,
                    username="dmlogn8n_user",
                    password=self.secrets["db_user_password"],
                    database="dmlogn8n_staging",
                    ssl_enabled=True
                ),
                redis=RedisConfig(
                    host="staging-redis.dmlogn8n.com",
                    port=6379,
                    password=self.secrets["redis_password"],
                    db=0,
                    ssl_enabled=True
                ),
                n8n=N8NConfig(
                    host="staging-n8n.dmlogn8n.com",
                    port=5678,
                    basic_auth_enabled=True,
                    basic_auth_user="admin",
                    basic_auth_password=self.secrets["n8n_basic_auth_password"],
                    webhook_url="https://staging-n8n.dmlogn8n.com/",
                    encryption_key=self.secrets["n8n_encryption_key"],
                    jwt_secret=self.secrets["n8n_jwt_secret"]
                ),
                api=APIConfig(
                    host="staging-api.dmlogn8n.com",
                    port=8000,
                    secret_key=self.secrets["api_secret_key"],
                    jwt_secret_key=self.secrets["api_jwt_secret"],
                    cors_origins="https://staging.dmlogn8n.com",
                    rate_limit="500/hour",
                    debug=False
                ),
                web=WebConfig(
                    host="staging.dmlogn8n.com",
                    port=443,
                    api_url="https://staging-api.dmlogn8n.com",
                    n8n_url="https://staging-n8n.dmlogn8n.com",
                    ws_url="wss://staging-api.dmlogn8n.com",
                    ssl_enabled=True
                ),
                monitoring_enabled=True,
                log_level="INFO",
                timezone="UTC"
            )

        else:  # production
            return EnvironmentConfig(
                name="production",
                database=DatabaseConfig(
                    host="prod-db.dmlogn8n.com",
                    port=3306,
                    username="dmlogn8n_user",
                    password=self.secrets["db_user_password"],
                    database="dmlogn8n_prod",
                    ssl_enabled=True,
                    pool_size=20,
                    max_overflow=40
                ),
                redis=RedisConfig(
                    host="prod-redis.dmlogn8n.com",
                    port=6379,
                    password=self.secrets["redis_password"],
                    db=0,
                    ssl_enabled=True,
                    max_connections=20
                ),
                n8n=N8NConfig(
                    host="prod-n8n.dmlogn8n.com",
                    port=5678,
                    basic_auth_enabled=True,
                    basic_auth_user="admin",
                    basic_auth_password=self.secrets["n8n_basic_auth_password"],
                    webhook_url="https://prod-n8n.dmlogn8n.com/",
                    encryption_key=self.secrets["n8n_encryption_key"],
                    jwt_secret=self.secrets["n8n_jwt_secret"]
                ),
                api=APIConfig(
                    host="prod-api.dmlogn8n.com",
                    port=8000,
                    secret_key=self.secrets["api_secret_key"],
                    jwt_secret_key=self.secrets["api_jwt_secret"],
                    cors_origins="https://dmlogn8n.com",
                    rate_limit="100/hour",
                    debug=False
                ),
                web=WebConfig(
                    host="dmlogn8n.com",
                    port=443,
                    api_url="https://api.dmlogn8n.com",
                    n8n_url="https://n8n.dmlogn8n.com",
                    ws_url="wss://api.dmlogn8n.com",
                    ssl_enabled=True
                ),
                monitoring_enabled=True,
                log_level="WARNING",
                timezone="UTC"
            )

    def generate_env_file(self, service: str, config: EnvironmentConfig) -> str:
        """Generate .env file content for a service"""
        if service == "n8n":
            return f"""
# N8N Configuration
ENVIRONMENT={config.name}
N8N_HOST={config.n8n.host}
N8N_PORT={config.n8n.port}
N8N_PROTOCOL={'https' if config.web.ssl_enabled else 'http'}
N8N_BASIC_AUTH_ACTIVE={str(config.n8n.basic_auth_enabled).lower()}
N8N_BASIC_AUTH_USER={config.n8n.basic_auth_user}
N8N_BASIC_AUTH_PASSWORD={config.n8n.basic_auth_password}
N8N_ENCRYPTION_KEY={config.n8n.encryption_key}
N8N_JWT_AUTH_HEADER=authorization
N8N_JWT_AUTH_HEADER_VALUE_PREFIX=Bearer
N8N_JWT_SECRET={config.n8n.jwt_secret}
WEBHOOK_URL={config.n8n.webhook_url}

# Database Configuration
DB_TYPE=mysql
DB_MYSQLDB_HOST={config.database.host}
DB_MYSQLDB_PORT={config.database.port}
DB_MYSQLDB_DATABASE=n8n
DB_MYSQLDB_USER=n8n_user
DB_MYSQLDB_PASSWORD={config.database.password}

# Redis Configuration
QUEUE_BULL_REDIS_HOST={config.redis.host}
QUEUE_BULL_REDIS_PORT={config.redis.port}
QUEUE_BULL_REDIS_PASSWORD={config.redis.password}

# General Configuration
TZ={config.timezone}
LOG_LEVEL={config.log_level}
"""

        elif service == "api":
            return f"""
# API Configuration
ENVIRONMENT={config.name}
FLASK_ENV={'production' if config.name == 'production' else 'development'}
DEBUG={str(config.api.debug).lower()}
SECRET_KEY={config.api.secret_key}
JWT_SECRET_KEY={config.api.jwt_secret_key}

# Database Configuration
DATABASE_URL=mysql://{config.database.username}:{config.database.password}@{config.database.host}:{config.database.port}/{config.database.database}
DATABASE_POOL_SIZE={config.database.pool_size}
DATABASE_MAX_OVERFLOW={config.database.max_overflow}

# Redis Configuration
REDIS_URL=redis://:{config.redis.password}@{config.redis.host}:{config.redis.port}/{config.redis.db}

# CORS Configuration
CORS_ORIGINS={config.api.cors_origins}

# Rate Limiting
RATE_LIMIT={config.api.rate_limit}

# Monitoring
MONITORING_ENABLED={str(config.monitoring_enabled).lower()}

# Logging
LOG_LEVEL={config.log_level}
TZ={config.timezone}
"""

        elif service == "character-coder":
            return f"""
# Character Coder Configuration
ENVIRONMENT={config.name}
FLASK_ENV={'production' if config.name == 'production' else 'development'}
DEBUG={str(config.api.debug).lower()}
SECRET_KEY={config.secrets['flask_secret_key']}

# Database Configuration
DATABASE_URL=mysql://{config.database.username}:{config.database.password}@{config.database.host}:{config.database.port}/{config.database.database}

# Redis Configuration
REDIS_URL=redis://:{config.redis.password}@{config.redis.host}:{config.redis.port}/{config.redis.db}

# N8N Integration
N8N_WEBHOOK_URL={config.n8n.webhook_url}
N8N_API_KEY={config.secrets['n8n_encryption_key']}

# Character Generation
CHARACTER_MODEL=gpt-4
CHARACTER_TEMPERATURE=0.7
CHARACTER_MAX_TOKENS=1000

# Logging
LOG_LEVEL={config.log_level}
TZ={config.timezone}
"""

        elif service == "player-portal":
            return f"""
# Player Portal Configuration
ENVIRONMENT={config.name}
REACT_APP_API_URL={config.web.api_url}
REACT_APP_N8N_URL={config.web.n8n_url}
REACT_APP_WS_URL={config.web.ws_url}
REACT_APP_ENVIRONMENT={config.name}
REACT_APP_VERSION=1.0.0

# Feature Flags
REACT_APP_FEATURES_CHARACTER_CODE=true
REACT_APP_FEATURES_VOICE_CHAT=true
REACT_APP_FEATURES_REAL_TIME_COMBAT=true

# Monitoring
REACT_APP_SENTRY_DSN={"SENTRY_DSN_HERE" if config.monitoring_enabled else ""}
"""

        else:
            return f"# Unknown service: {service}"

    def generate_nginx_config(self, config: EnvironmentConfig) -> str:
        """Generate Nginx configuration"""
        upstream_servers = """
upstream dmlogn8n_api {
    server {api_host}:{api_port};
}

upstream dmlogn8n_n8n {
    server {n8n_host}:{n8n_port};
}

upstream dmlogn8n_web {
    server {web_host}:{web_port};
}
""".format(
            api_host=config.api.host,
            api_port=config.api.port,
            n8n_host=config.n8n.host,
            n8n_port=config.n8n.port,
            web_host=config.web.host,
            web_port=config.web.port
        )

        if config.web.ssl_enabled:
            return f"""
{upstream_servers}

# HTTP to HTTPS redirect
server {{
    listen 80;
    server_name {config.web.host} www.{config.web.host};
    return 301 https://$server_name$request_uri;
}}

# HTTPS server
server {{
    listen 443 ssl http2;
    server_name {config.web.host} www.{config.web.host};

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/dmlogn8n.crt;
    ssl_certificate_key /etc/nginx/ssl/dmlogn8n.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # API Routes
    location /api/ {{
        proxy_pass http://dmlogn8n_api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
    }}

    # WebSocket Routes
    location /ws/ {{
        proxy_pass http://dmlogn8n_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    # N8N Routes
    location /n8n/ {{
        proxy_pass http://dmlogn8n_n8n/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
    }}

    # Web Application
    location / {{
        proxy_pass http://dmlogn8n_web/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Serve static files directly
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {{
            expires 1y;
            add_header Cache-Control "public, immutable";
        }}
    }}

    # Health Check
    location /health {{
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }}
}}
"""
        else:
            return f"""
{upstream_servers}

server {{
    listen 80;
    server_name {config.web.host};

    # API Routes
    location /api/ {{
        proxy_pass http://dmlogn8n_api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
    }}

    # WebSocket Routes
    location /ws/ {{
        proxy_pass http://dmlogn8n_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    # N8N Routes
    location /n8n/ {{
        proxy_pass http://dmlogn8n_n8n/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
    }}

    # Web Application
    location / {{
        proxy_pass http://dmlogn8n_web/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}

    # Health Check
    location /health {{
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }}
}}
"""

    def generate_mysql_config(self, config: EnvironmentConfig) -> str:
        """Generate MySQL configuration"""
        return f"""
# MySQL Configuration for {config.name}
[mysqld]
# General Settings
bind-address = 0.0.0.0
port = {config.database.port}
datadir = /var/lib/mysql
socket = /var/run/mysqld/mysqld.sock
pid-file = /var/run/mysqld/mysqld.pid

# Character Set
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
init-connect = 'SET NAMES utf8mb4'

# Performance Settings
innodb_buffer_pool_size = {'2G' if config.name == 'production' else '512M'}
innodb_log_file_size = {'256M' if config.name == 'production' else '64M'}
innodb_flush_log_at_trx_commit = 1
innodb_flush_method = O_DIRECT

# Connection Settings
max_connections = {config.database.pool_size + config.database.max_overflow}
max_connect_errors = 1000
connect_timeout = 60
wait_timeout = 28800

# Query Cache
query_cache_type = 1
query_cache_size = {'256M' if config.name == 'production' else '64M'}
query_cache_limit = 2M

# Slow Query Log
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2

# Error Log
log_error = /var/log/mysql/error.log

# Binary Log
log_bin = /var/log/mysql/mysql-bin.log
expire_logs_days = 7
max_binlog_size = 100M

# SSL Configuration (if enabled)
ssl = {'ON' if config.database.ssl_enabled else 'OFF'}
{'ssl-ca = /etc/mysql/ssl/ca.pem' if config.database.ssl_enabled else ''}
{'ssl-cert = /etc/mysql/ssl/server-cert.pem' if config.database.ssl_enabled else ''}
{'ssl-key = /etc/mysql/ssl/server-key.pem' if config.database.ssl_enabled else ''}

[mysql]
default-character-set = utf8mb4

[client]
default-character-set = utf8mb4
"""

    def generate_redis_config(self, config: EnvironmentConfig) -> str:
        """Generate Redis configuration"""
        return f"""
# Redis Configuration for {config.name}

# Network
bind {config.redis.host}
port {config.redis.port}
protected-mode yes

# Authentication
{'requirepass ' + config.redis.password if config.redis.password else '# No password set'}

# Memory
maxmemory {'2gb' if config.name == 'production' else '512mb'}
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Append Only File
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec

# Logs
loglevel {config.log_level.lower()}
logfile /var/log/redis/redis-server.log

# Security
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command KEYS ""
rename-command CONFIG "CONFIG_b835c3f8a2d6e7f1"

# SSL Configuration (if enabled)
{'tls-port 6380' if config.redis.ssl_enabled else '# TLS disabled'}
{'tls-cert-file /etc/redis/ssl/redis.crt' if config.redis.ssl_enabled else ''}
{'tls-key-file /etc/redis/ssl/redis.key' if config.redis.ssl_enabled else ''}
{'tls-ca-cert-file /etc/redis/ssl/ca.crt' if config.redis.ssl_enabled else ''}
"""

    def generate_supervisor_config(self, config: EnvironmentConfig) -> str:
        """Generate Supervisor configuration"""
        return f"""
# Supervisor Configuration for {config.name}
[unix_http_server]
file=/var/run/supervisor.sock

[supervisord]
logfile=/var/log/supervisor/supervisord.log
pidfile=/var/run/supervisord.pid
childlogdir=/var/log/supervisor
nodaemon=false
environment=ENVIRONMENT="{config.name}"

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix:///var/run/supervisor.sock

# Programs
[program:dmlogn8n-api]
command=/opt/dmlogn8n/venv/bin/gunicorn --bind {config.api.host}:{config.api.port} --workers 4 --timeout 120 app:app
directory=/opt/dmlogn8n/api
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/dmlogn8n/api.log
environment=PATH="/opt/dmlogn8n/venv/bin"

[program:character-coder]
command=/opt/dmlogn8n/venv/bin/python app.py
directory=/opt/dmlogn8n/character-coder
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/dmlogn8n/character-coder.log
environment=PATH="/opt/dmlogn8n/venv/bin"

[program:n8n]
command=n8n start
user=n8n
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/dmlogn8n/n8n.log
environment=HOME="/var/lib/n8n"
"""

    def write_config_files(self, config: EnvironmentConfig) -> bool:
        """Write all configuration files"""
        try:
            # Create service directories
            services = ["api", "n8n", "character-coder", "player-portal"]
            for service in services:
                service_dir = self.config_dir / service
                service_dir.mkdir(parents=True, exist_ok=True)

                # Write .env file
                env_content = self.generate_env_file(service, config)
                with open(service_dir / ".env", "w") as f:
                    f.write(env_content.strip())

            # Write Nginx configuration
            nginx_dir = self.config_dir / "nginx"
            nginx_dir.mkdir(parents=True, exist_ok=True)

            nginx_config = self.generate_nginx_config(config)
            with open(nginx_dir / "dmlogn8n.conf", "w") as f:
                f.write(nginx_config.strip())

            # Write MySQL configuration
            mysql_dir = self.config_dir / "mysql"
            mysql_dir.mkdir(parents=True, exist_ok=True)

            mysql_config = self.generate_mysql_config(config)
            with open(mysql_dir / "my.cnf", "w") as f:
                f.write(mysql_config.strip())

            # Write Redis configuration
            redis_dir = self.config_dir / "redis"
            redis_dir.mkdir(parents=True, exist_ok=True)

            redis_config = self.generate_redis_config(config)
            with open(redis_dir / "redis.conf", "w") as f:
                f.write(redis_config.strip())

            # Write Supervisor configuration
            supervisor_dir = self.config_dir / "supervisor"
            supervisor_dir.mkdir(parents=True, exist_ok=True)

            supervisor_config = self.generate_supervisor_config(config)
            with open(supervisor_dir / "dmlogn8n.conf", "w") as f:
                f.write(supervisor_config.strip())

            # Write main configuration JSON
            config_dict = asdict(config)
            config_dict["secrets"] = self.secrets

            with open(self.output_dir / f"{self.environment}.json", "w") as f:
                json.dump(config_dict, f, indent=2)

            self.logger.info(f"Configuration files generated for {self.environment}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to write configuration files: {e}")
            return False

    def generate_configs(self) -> bool:
        """Generate all configurations for the environment"""
        self.logger.info(f"Generating configurations for {self.environment} environment...")

        # Get base configuration
        config = self.get_base_config()

        # Write configuration files
        if not self.write_config_files(config):
            return False

        # Set proper permissions
        try:
            # Set secure permissions on sensitive files
            sensitive_files = [
                self.config_dir / "api" / ".env",
                self.config_dir / "n8n" / ".env",
                self.config_dir / "character-coder" / ".env",
                self.output_dir / f"{self.environment}.json"
            ]

            for file_path in sensitive_files:
                if file_path.exists():
                    os.chmod(file_path, 0o600)

            self.logger.info("Configuration file permissions set")
            return True

        except Exception as e:
            self.logger.error(f"Failed to set file permissions: {e}")
            return False


def main():
    """Main entry point for configuration generation"""
    import argparse

    parser = argparse.ArgumentParser(description="DMLogn8n Configuration Generator")
    parser.add_argument("environment", choices=["development", "staging", "production"],
                       help="Target environment")
    parser.add_argument("--output-dir",
                       help="Output directory for configurations")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize configuration generator
    generator = ConfigGenerator(args.environment)

    if args.output_dir:
        generator.output_dir = Path(args.output_dir)
        generator.output_dir.mkdir(parents=True, exist_ok=True)

    # Generate configurations
    success = generator.generate_configs()

    if success:
        print(f"✅ Configurations generated successfully for {args.environment}!")
        print(f"📁 Output directory: {generator.output_dir}")
        print(f"⚙️  Config directory: {generator.config_dir}")
        sys.exit(0)
    else:
        print("❌ Configuration generation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()