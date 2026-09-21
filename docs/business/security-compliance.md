# DMLog Security and Compliance Documentation

## Table of Contents

1. [Security Overview](#security-overview)
2. [Data Protection](#data-protection)
3. [Access Control](#access-control)
4. [Application Security](#application-security)
5. [Infrastructure Security](#infrastructure-security)
6. [Compliance Standards](#compliance-standards)
7. [Privacy Policy](#privacy-policy)
8. [Security Monitoring](#security-monitoring)
9. [Incident Response](#incident-response)
10. [Third-Party Security](#third-party-security)

---

## Security Overview

DMLog is committed to maintaining the highest standards of security and data protection. Our security program is designed to protect user data, ensure service availability, and maintain compliance with global regulations.

### Security Principles

1. **Defense in Depth**: Multiple layers of security controls
2. **Zero Trust**: Verify and authenticate all access requests
3. **Privacy by Design**: Privacy considerations built into all features
4. **Transparency**: Open communication about security practices
5. **Continuous Improvement**: Regular security assessments and updates

### Security Team Structure

```
Chief Information Security Officer (CISO)
├── Security Engineering Team
│   ├── Application Security
│   ├── Infrastructure Security
│   └── Cloud Security
├── Security Operations Center (SOC)
│   ├── Threat Intelligence
│   ├── Incident Response
│   └── Security Monitoring
└── Compliance & Governance
    ├── Risk Management
    ├── Audit & Compliance
    └── Policy Management
```

---

## Data Protection

### Data Classification

#### Data Categories
- **Public Data**: Marketing materials, public documentation
- **Internal Data**: Internal processes, non-sensitive business information
- **Confidential Data**: User personal information, campaign data
- **Restricted Data**: Financial information, authentication credentials

#### Data Handling Policies

```python
# Example of data handling policy implementation
class DataClassifier:
    """Classifies and handles data according to sensitivity."""

    DATA_SENSITIVITY = {
        'email': 'confidential',
        'password': 'restricted',
        'character_name': 'confidential',
        'campaign_notes': 'confidential',
        'payment_info': 'restricted'
    }

    @staticmethod
    def classify_data(data_type: str, value: str) -> str:
        """Classify data based on type and content."""
        base_classification = DataClassifier.DATA_SENSITIVITY.get(data_type, 'internal')

        # Enhanced classification for sensitive content
        if base_classification == 'confidential' and DataClassifier._contains_pii(value):
            return 'restricted'

        return base_classification

    @staticmethod
    def _contains_pii(data: str) -> bool:
        """Check if data contains personally identifiable information."""
        pii_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email
        ]

        import re
        return any(re.search(pattern, data, re.IGNORECASE) for pattern in pii_patterns)
```

### Encryption Standards

#### Data at Rest
- **Database Encryption**: AES-256 encryption for all database fields
- **File Storage**: AES-256 encryption for all stored files
- **Backup Encryption**: Encrypted backups with key rotation
- **Key Management**: AWS KMS or equivalent for encryption key management

#### Data in Transit
- **TLS 1.3**: All network communications encrypted with TLS 1.3
- **Certificate Management**: Automated certificate lifecycle management
- **API Security**: Encrypted API communications with token authentication
- **End-to-End Encryption**: Sensitive data encrypted end-to-end

#### Key Management

```python
# Example of secure key management implementation
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class SecureKeyManager:
    """Manages encryption keys securely."""

    def __init__(self, master_key_env: str):
        self.master_key = self._get_master_key(master_key_env)
        self.key_cache = {}

    def _get_master_key(self, env_var: str) -> bytes:
        """Retrieve master key from secure environment."""
        key = os.environ.get(env_var)
        if not key:
            raise ValueError("Master key not found in environment")
        return key.encode()

    def generate_data_key(self, context: str) -> bytes:
        """Generate a unique encryption key for specific context."""
        if context in self.key_cache:
            return self.key_cache[context]

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=context.encode(),
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key))

        self.key_cache[context] = key
        return key

    def encrypt_data(self, data: str, context: str) -> bytes:
        """Encrypt data with context-specific key."""
        key = self.generate_data_key(context)
        f = Fernet(key)
        return f.encrypt(data.encode())

    def decrypt_data(self, encrypted_data: bytes, context: str) -> str:
        """Decrypt data with context-specific key."""
        key = self.generate_data_key(context)
        f = Fernet(key)
        return f.decrypt(encrypted_data).decode()
```

### Data Retention and Deletion

#### Retention Policy
- **User Data**: Retained for 365 days after account deletion
- **Session Data**: Retained for 90 days
- **Analytics Data**: Retained for 730 days (2 years)
- **Backup Data**: Retained for 90 days with encrypted storage

#### Data Deletion Process
```python
# Example of secure data deletion
class SecureDataDeletion:
    """Handles secure deletion of sensitive data."""

    @staticmethod
    async def delete_user_data(user_id: str) -> bool:
        """Securely delete all user data."""
        try:
            # Delete user from primary database
            await db.users.filter(id=user_id).delete()

            # Delete associated character data
            await db.characters.filter(user_id=user_id).delete()

            # Delete campaign associations
            await db.campaign_players.filter(user_id=user_id).delete()

            # Delete from analytics databases
            await analytics_db.delete_user_analytics(user_id)

            # Delete from backup systems
            await backup_system.delete_user_backups(user_id)

            # Log deletion for audit trail
            await security_logger.log_data_deletion(user_id, 'USER_INITIATED')

            return True

        except Exception as e:
            await security_logger.log_deletion_error(user_id, str(e))
            return False
```

---

## Access Control

### Authentication System

#### Multi-Factor Authentication (MFA)
- **TOTP Support**: Time-based one-time passwords
- **SMS Authentication**: SMS-based verification codes
- **Email Verification**: Email-based two-factor authentication
- **Hardware Keys**: Support for U2F hardware security keys

#### Password Policy
```python
# Password policy implementation
import re
from typing import List

class PasswordPolicy:
    """Enforces strong password policies."""

    MIN_LENGTH = 12
    MAX_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL = True
    FORBIDDEN_PATTERNS = [
        r'(.)\1{2,}',  # No 3+ repeating characters
        r'123456',     # No sequential numbers
        r'password',   # No common passwords
    ]

    @classmethod
    def validate_password(cls, password: str) -> List[str]:
        """Validate password against security policy."""
        errors = []

        # Length requirements
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters long")
        if len(password) > cls.MAX_LENGTH:
            errors.append(f"Password must not exceed {cls.MAX_LENGTH} characters")

        # Character requirements
        if cls.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")

        if cls.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")

        if cls.REQUIRE_DIGITS and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")

        if cls.REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")

        # Forbidden patterns
        for pattern in cls.FORBIDDEN_PATTERNS:
            if re.search(pattern, password, re.IGNORECASE):
                errors.append("Password contains forbidden patterns")

        return errors
```

#### Session Management
```python
# Secure session management
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

class SessionManager:
    """Manages user sessions with security controls."""

    def __init__(self):
        self.active_sessions: Dict[str, Dict] = {}
        self.session_timeout = timedelta(hours=2)
        self.max_sessions_per_user = 10

    async def create_session(self, user_id: str, ip_address: str, user_agent: str) -> str:
        """Create a new secure session."""
        session_id = str(uuid.uuid4())

        # Clean up old sessions for user
        await self._cleanup_user_sessions(user_id)

        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
            'is_active': True
        }

        self.active_sessions[session_id] = session_data
        return session_id

    async def validate_session(self, session_id: str, ip_address: str) -> Optional[str]:
        """Validate session and check for anomalies."""
        session = self.active_sessions.get(session_id)

        if not session or not session['is_active']:
            return None

        # Check session timeout
        if datetime.utcnow() - session['last_activity'] > self.session_timeout:
            await self.invalidate_session(session_id)
            return None

        # Check IP address consistency
        if session['ip_address'] != ip_address:
            await security_logger.log_session_anomaly(session_id, 'IP_ADDRESS_MISMATCH')
            # Could implement additional verification here

        # Update last activity
        session['last_activity'] = datetime.utcnow()

        return session['user_id']

    async def _cleanup_user_sessions(self, user_id: str):
        """Remove old sessions for user if they have too many."""
        user_sessions = [
            sid for sid, session in self.active_sessions.items()
            if session['user_id'] == user_id and session['is_active']
        ]

        if len(user_sessions) >= self.max_sessions_per_user:
            # Remove oldest sessions
            sessions_to_remove = sorted(
                user_sessions,
                key=lambda sid: self.active_sessions[sid]['created_at']
            )[:-self.max_sessions_per_user + 1]

            for session_id in sessions_to_remove:
                await self.invalidate_session(session_id)
```

### Authorization System

#### Role-Based Access Control (RBAC)

```python
# RBAC implementation
from enum import Enum
from typing import List, Set

class Permission(Enum):
    """System permissions."""
    READ_CHARACTER = "read_character"
    WRITE_CHARACTER = "write_character"
    DELETE_CHARACTER = "delete_character"
    READ_CAMPAIGN = "read_campaign"
    WRITE_CAMPAIGN = "write_campaign"
    DELETE_CAMPAIGN = "delete_campaign"
    MANAGE_USERS = "manage_users"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_BILLING = "manage_billing"

class Role(Enum):
    """User roles with associated permissions."""
    PLAYER = "player"
    DUNGEON_MASTER = "dungeon_master"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class RBACManager:
    """Manages role-based access control."""

    ROLE_PERMISSIONS = {
        Role.PLAYER: {
            Permission.READ_CHARACTER,
            Permission.WRITE_CHARACTER,
            Permission.READ_CAMPAIGN,
        },
        Role.DUNGEON_MASTER: {
            Permission.READ_CHARACTER,
            Permission.WRITE_CHARACTER,
            Permission.DELETE_CHARACTER,
            Permission.READ_CAMPAIGN,
            Permission.WRITE_CAMPAIGN,
            Permission.DELETE_CAMPAIGN,
            Permission.VIEW_ANALYTICS,
        },
        Role.MODERATOR: {
            Permission.READ_CHARACTER,
            Permission.WRITE_CHARACTER,
            Permission.READ_CAMPAIGN,
            Permission.VIEW_ANALYTICS,
        },
        Role.ADMIN: {
            # All permissions except user management
            Permission.READ_CHARACTER,
            Permission.WRITE_CHARACTER,
            Permission.DELETE_CHARACTER,
            Permission.READ_CAMPAIGN,
            Permission.WRITE_CAMPAIGN,
            Permission.DELETE_CAMPAIGN,
            Permission.VIEW_ANALYTICS,
            Permission.MANAGE_BILLING,
        },
        Role.SUPER_ADMIN: {
            # All permissions
            *Permission
        }
    }

    @classmethod
    def get_user_permissions(cls, user_roles: List[Role]) -> Set[Permission]:
        """Get all permissions for a user based on their roles."""
        permissions = set()

        for role in user_roles:
            permissions.update(cls.ROLE_PERMISSIONS.get(role, set()))

        return permissions

    @classmethod
    def has_permission(cls, user_permissions: Set[Permission],
                      required_permission: Permission) -> bool:
        """Check if user has required permission."""
        return required_permission in user_permissions
```

---

## Application Security

### Secure Coding Practices

#### Input Validation
```python
# Comprehensive input validation
import re
from typing import Any, Dict, List
from pydantic import BaseModel, validator

class SecureCharacterCreate(BaseModel):
    """Secure character creation model with validation."""

    name: str
    race: str
    character_class: str
    level: int
    backstory: str = None

    @validator('name')
    def validate_name(cls, v):
        """Validate character name for security."""
        # Length check
        if not 1 <= len(v) <= 100:
            raise ValueError("Name must be between 1 and 100 characters")

        # Script injection prevention
        if re.search(r'<script|javascript:|on\w+=', v, re.IGNORECASE):
            raise ValueError("Name contains invalid characters")

        # SQL injection prevention
        if re.search(r'["\';\\]|--|/\*|\*/', v):
            raise ValueError("Name contains invalid characters")

        return v.strip()

    @validator('level')
    def validate_level(cls, v):
        """Validate character level."""
        if not isinstance(v, int) or not 1 <= v <= 20:
            raise ValueError("Level must be an integer between 1 and 20")
        return v

    @validator('backstory')
    def validate_backstory(cls, v):
        """Validate backstory for content security."""
        if v is None:
            return v

        # Length limit
        if len(v) > 10000:
            raise ValueError("Backstory must not exceed 10,000 characters")

        # Content filtering
        forbidden_content = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*='
        ]

        for pattern in forbidden_content:
            if re.search(pattern, v, re.IGNORECASE | re.DOTALL):
                raise ValueError("Backstory contains invalid content")

        return v

# Usage in API endpoints
@router.post("/characters/")
async def create_character(character_data: SecureCharacterCreate,
                         current_user: User = Depends(get_current_user)):
    """Create character with secure validation."""
    return await character_service.create_character(
        character_data.dict(),
        user_id=current_user.id
    )
```

#### SQL Injection Prevention
```python
# Secure database query construction
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class SecureCharacterRepository:
    """Repository with SQL injection protection."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_characters_by_name(self, search_term: str) -> List[Character]:
        """Safely search characters by name."""
        # Using parameterized queries (SQLAlchemy handles this safely)
        query = text("""
            SELECT id, name, race, class, level
            FROM characters
            WHERE name ILIKE :search_term
            AND is_active = true
            ORDER BY name
            LIMIT 100
        """)

        result = await self.session.execute(
            query,
            {"search_term": f"%{search_term}%"}
        )

        return result.fetchall()

    async def get_character_campaigns(self, character_id: str) -> List[Campaign]:
        """Get campaigns for a character with validation."""
        # Validate character_id format
        if not self._is_valid_uuid(character_id):
            raise ValueError("Invalid character ID format")

        query = text("""
            SELECT c.id, c.name, c.description
            FROM campaigns c
            JOIN campaign_characters cc ON c.id = cc.campaign_id
            WHERE cc.character_id = :character_id
            AND c.is_active = true
        """)

        result = await self.session.execute(
            query,
            {"character_id": character_id}
        )

        return result.fetchall()

    @staticmethod
    def _is_valid_uuid(uuid_string: str) -> bool:
        """Validate UUID format."""
        import uuid
        try:
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False
```

#### XSS Prevention
```python
# XSS prevention utilities
import html
import markdown
from typing import Any

class XSSProtection:
    """Utilities for preventing XSS attacks."""

    @staticmethod
    def escape_html(text: str) -> str:
        """Escape HTML characters."""
        return html.escape(text, quote=True)

    @staticmethod
    def sanitize_markdown(content: str) -> str:
        """Sanitize markdown content."""
        # Convert markdown to HTML safely
        unsafe_html = markdown.markdown(content)

        # Sanitize HTML (using bleach library)
        try:
            import bleach
            clean_html = bleach.clean(
                unsafe_html,
                tags=['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'h1', 'h2', 'h3'],
                attributes={},
                strip=True
            )
            return clean_html
        except ImportError:
            # Fallback: escape all HTML
            return XSSProtection.escape_html(unsafe_html)

    @staticmethod
    def sanitize_user_input(text: str, allow_markdown: bool = False) -> str:
        """Sanitize user input for safe display."""
        if allow_markdown:
            return XSSProtection.sanitize_markdown(text)
        else:
            return XSSProtection.escape_html(text)

# Usage in templates and responses
class CharacterResponse(BaseModel):
    """Character response with XSS protection."""

    name: str
    backstory: str = None

    def get_safe_backstory(self) -> str:
        """Get backstory safe for display."""
        if self.backstory:
            return XSSProtection.sanitize_user_input(self.backstory, allow_markdown=True)
        return ""
```

### API Security

#### Rate Limiting
```python
# Advanced rate limiting implementation
import time
from collections import defaultdict, deque
from typing import Dict, Deque

class RateLimiter:
    """Advanced rate limiting with multiple strategies."""

    def __init__(self):
        self.requests: Dict[str, Deque] = defaultdict(deque)
        self.limits = {
            'default': {'requests': 100, 'window': 60},  # 100 requests per minute
            'auth': {'requests': 10, 'window': 60},        # 10 auth requests per minute
            'upload': {'requests': 5, 'window': 60},        # 5 uploads per minute
            'api': {'requests': 1000, 'window': 3600},     # 1000 API requests per hour
        }

    async def is_allowed(self, key: str, limit_type: str = 'default') -> bool:
        """Check if request is allowed based on rate limits."""
        current_time = time.time()
        limit_config = self.limits.get(limit_type, self.limits['default'])

        # Get or create request queue for this key
        request_queue = self.requests[key]

        # Remove old requests outside the time window
        window_start = current_time - limit_config['window']
        while request_queue and request_queue[0] < window_start:
            request_queue.popleft()

        # Check if under limit
        if len(request_queue) < limit_config['requests']:
            request_queue.append(current_time)
            return True

        return False

    async def check_rate_limit(self, request):
        """Middleware for rate limiting."""
        # Get client identifier
        client_key = self._get_client_key(request)

        # Determine limit type based on endpoint
        limit_type = self._determine_limit_type(request)

        # Check rate limit
        allowed = await self.is_allowed(client_key, limit_type)

        if not allowed:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(self.limits[limit_type]['window'])}
            )

    def _get_client_key(self, request) -> str:
        """Generate client key for rate limiting."""
        # Use combination of IP and user ID if available
        client_ip = request.client.host
        user_id = getattr(request.state, 'user_id', None)

        if user_id:
            return f"user:{user_id}"
        else:
            return f"ip:{client_ip}"

    def _determine_limit_type(self, request) -> str:
        """Determine rate limit type based on request."""
        path = request.url.path

        if '/auth/' in path:
            return 'auth'
        elif '/upload' in path:
            return 'upload'
        elif path.startswith('/api/'):
            return 'api'
        else:
            return 'default'
```

#### Request Validation Middleware
```python
# Security middleware for request validation
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for request validation."""

    async def dispatch(self, request: Request, call_next):
        # Security headers
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'"
        )

        return response

class RequestSizeMiddleware(BaseHTTPMiddleware):
    """Middleware to limit request size."""

    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")

        if content_length and int(content_length) > self.max_size:
            raise HTTPException(
                status_code=413,
                detail=f"Request too large. Maximum size is {self.max_size} bytes"
            )

        return await call_next(request)
```

---

## Infrastructure Security

### Cloud Security Configuration

#### AWS Security Configuration
```yaml
# AWS security configuration (CloudFormation template)
AWSTemplateFormatVersion: '2010-09-09'
Description: 'DMLog Security Infrastructure'

Resources:
  # VPC Configuration
  DMLogVPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: dmlog-vpc

  # Private Subnets
  PrivateSubnetA:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref DMLogVPC
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: !Select [0, !GetAZs '']
      Tags:
        - Key: Name
          Value: dmlog-private-a

  PrivateSubnetB:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref DMLogVPC
      CidrBlock: 10.0.2.0/24
      AvailabilityZone: !Select [1, !GetAZs '']
      Tags:
        - Key: Name
          Value: dmlog-private-b

  # Security Groups
  DatabaseSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for RDS database
      VpcId: !Ref DMLogVPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 5432
          ToPort: 5432
          SourceSecurityGroupId: !Ref ApplicationSecurityGroup
      Tags:
        - Key: Name
          Value: dmlog-db-sg

  ApplicationSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for application servers
      VpcId: !Ref DMLogVPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 8000
          ToPort: 8000
          CidrIp: 10.0.0.0/16
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0
      Tags:
        - Key: Name
          Value: dmlog-app-sg

  # KMS for encryption
  DMLogKMSKey:
    Type: AWS::KMS::Key
    Properties:
      Description: KMS key for DMLog encryption
      Enabled: true
      EnableKeyRotation: true
      KeyPolicy:
        Version: '2012-10-17'
        Statement:
          - Sid: Allow administration of the key
            Effect: Allow
            Principal:
              AWS: !Sub 'arn:aws:iam::${AWS::AccountId}:root'
            Action:
              - 'kms:*'
            Resource: '*'

  # S3 bucket with encryption
  DMLogS3Bucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub 'dmlog-secure-storage-${AWS::AccountId}'
      VersioningConfiguration:
        Status: Enabled
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: aws:kms
              KMSMasterKeyID: !Ref DMLogKMSKey
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
```

#### Docker Security
```dockerfile
# Secure Dockerfile for DMLog application
FROM python:3.11-slim as base

# Create non-root user
RUN groupadd -r dmlog && useradd -r -g dmlog dmlog

# Set security-related environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install security updates
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app
WORKDIR /app

# Set permissions
RUN chown -R dmlog:dmlog /app
USER dmlog

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/simple || exit 1

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "source_code.backend.api_server_new:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Network Security

#### Firewall Configuration
```bash
# UFW (Uncomplicated Firewall) configuration
#!/bin/bash

# Reset existing rules
ufw --force reset

# Default policies
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (with rate limiting)
ufw limit ssh

# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow application port (with IP restrictions for admin access)
ufw allow from 192.168.1.0/24 to any port 8000
ufw allow from 10.0.0.0/8 to any port 8000

# Allow database traffic only from application servers
ufw allow from 10.0.1.0/24 to any port 5432
ufw allow from 10.0.2.0/24 to any port 5432

# Enable firewall
ufw --force enable

# Show status
ufw status verbose
```

#### SSL/TLS Configuration
```nginx
# Nginx SSL configuration with best practices
server {
    listen 443 ssl http2;
    server_name dmlog.com www.dmlog.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/dmlog.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dmlog.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # Other security headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self';" always;

    # Application proxy
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Security
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

---

## Compliance Standards

### GDPR Compliance

#### Data Protection Impact Assessment (DPIA)
- **Regular Assessments**: Conduct DPIAs for new features and processing activities
- **Documentation**: Maintain comprehensive DPIA documentation
- **Review Process**: Regular review and update of assessments

#### Data Subject Rights Implementation
```python
# GDPR rights implementation
class GDPRCompliance:
    """Manages GDPR compliance for user data."""

    async def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export all user data (Right to Data Portability)."""
        user_data = {
            'personal_information': await self._get_personal_info(user_id),
            'characters': await self._get_user_characters(user_id),
            'campaigns': await self._get_user_campaigns(user_id),
            'sessions': await self._get_user_sessions(user_id),
            'analytics': await self._get_user_analytics(user_id),
            'export_date': datetime.utcnow().isoformat()
        }

        # Log export for audit trail
        await compliance_logger.log_data_export(user_id)

        return user_data

    async def delete_user_data(self, user_id: str, verification_code: str) -> bool:
        """Delete user data (Right to Erasure)."""
        # Verify deletion request
        if not await self._verify_deletion_request(user_id, verification_code):
            return False

        try:
            # Delete from all systems
            await self._delete_from_primary_db(user_id)
            await self._delete_from_analytics_db(user_id)
            await self._delete_from_backup_systems(user_id)
            await self._delete_from_third_party_services(user_id)

            # Log deletion
            await compliance_logger.log_data_deletion(user_id)

            return True

        except Exception as e:
            await compliance_logger.log_deletion_error(user_id, str(e))
            return False

    async def update_consent(self, user_id: str, consent_data: Dict[str, bool]) -> bool:
        """Update user consent preferences."""
        try:
            await self._update_consent_record(user_id, consent_data)
            await compliance_logger.log_consent_update(user_id, consent_data)
            return True
        except Exception as e:
            await compliance_logger.log_consent_error(user_id, str(e))
            return False
```

### CCPA Compliance

#### California Consumer Privacy Act Implementation
```python
# CCPA compliance implementation
class CCPACompliance:
    """Manages CCPA compliance for California residents."""

    async def handle_california_privacy_request(self, user_id: str, request_type: str) -> Dict[str, Any]:
        """Handle CCPA privacy requests."""
        # Verify California residency
        if not await self._is_california_resident(user_id):
            return {'error': 'Not eligible for CCPA rights'}

        if request_type == 'know':
            return await self._disclose_personal_info(user_id)
        elif request_type == 'delete':
            return await self._delete_personal_info(user_id)
        elif request_type == 'opt_out':
            return await self._opt_out_of_sale(user_id)
        else:
            return {'error': 'Invalid request type'}

    async def _disclose_personal_info(self, user_id: str) -> Dict[str, Any]:
        """Disclose personal information collected."""
        disclosure = {
            'categories_collected': [
                'Identifiers',
                'Personal Information',
                'Commercial Information',
                'Internet Activity'
            ],
            'data_sources': ['Direct from user', 'Website usage', 'Mobile app usage'],
            'business_purposes': ['Service provision', 'Analytics', 'Security'],
            'third_parties': ['Cloud providers', 'Analytics services'],
            'retention_period': 'As long as account is active plus 365 days'
        }

        return disclosure
```

### SOC 2 Type II Compliance

#### Security Controls Implementation
```python
# SOC 2 controls implementation
class SOC2Controls:
    """Implements SOC 2 Type II security controls."""

    async def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security events for audit trail."""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'details': details,
            'user_id': details.get('user_id'),
            'ip_address': details.get('ip_address'),
            'user_agent': details.get('user_agent')
        }

        # Store in secure logging system
        await security_logger.log_security_event(event)

        # Store in audit database
        await audit_db.create_audit_log(event)

    async def conduct_access_review(self):
        """Conduct regular access reviews."""
        # Get all active user accounts
        active_users = await user_db.get_active_users()

        for user in active_users:
            # Review access rights
            access_rights = await self._get_user_access_rights(user.id)

            # Check for unusual access patterns
            if self._has_unusual_access(user.id, access_rights):
                await self._flag_for_review(user.id, access_rights)

        # Generate review report
        await self._generate_access_review_report()

    async def perform_vulnerability_scan(self):
        """Perform regular vulnerability scanning."""
        # Scan application dependencies
        dependency_vulnerabilities = await self._scan_dependencies()

        # Scan infrastructure
        infrastructure_vulnerabilities = await self._scan_infrastructure()

        # Generate and prioritize remediation tasks
        await self._generate_remediation_tasks(
            dependency_vulnerabilities,
            infrastructure_vulnerabilities
        )
```

---

## Privacy Policy

### Data Collection and Use

#### Information We Collect
- **Account Information**: Name, email address, password, profile information
- **Character Data**: Character sheets, backstories, campaign participation
- **Usage Data**: Session information, feature usage, performance metrics
- **Technical Data**: IP address, browser information, device information
- **Communication Data**: Support requests, feedback, community interactions

#### How We Use Your Information
- **Service Provision**: Provide and maintain DMLog services
- **Personalization**: Customize user experience and recommendations
- **Communication**: Send service-related notifications and updates
- **Analytics**: Analyze usage patterns to improve our services
- **Security**: Protect against fraud and abuse
- **Legal Compliance**: Meet legal and regulatory obligations

### Data Sharing and Disclosure

#### When We Share Information
- **Service Providers**: With trusted third-party service providers
- **Legal Requirements**: When required by law or legal process
- **Business Transfers**: In case of merger, acquisition, or asset sale
- **Safety**: To protect rights, property, or safety of users or others
- **With Consent**: When you have given explicit consent

#### Data We Don't Share
- We don't sell personal information to third parties
- We don't share personal information for cross-context behavioral advertising
- We don't share more information than necessary for the stated purpose

### International Data Transfers

#### Data Transfer Mechanisms
- **Standard Contractual Clauses**: For transfers outside EEA/UK
- **Adequacy Decisions**: For countries with adequate data protection
- **Binding Corporate Rules**: For internal organization transfers
- **Consent**: When required for specific types of transfers

#### Data Location
- Primary storage: United States (with appropriate safeguards)
- European users: Option for EU-based storage
- Backup locations: Multiple secure locations with encryption

---

## Security Monitoring

### Real-time Monitoring

#### Security Information and Event Management (SIEM)
```python
# Security monitoring implementation
class SecurityMonitoring:
    """Real-time security monitoring and alerting."""

    def __init__(self):
        self.alert_thresholds = {
            'failed_logins': 5,  # 5 failed logins in 5 minutes
            'api_requests': 1000,  # 1000 requests per minute per user
            'data_exports': 3,  # 3 data exports per hour per user
            'password_resets': 3,  # 3 password resets per hour per user
        }

    async def monitor_failed_logins(self, event: Dict[str, Any]):
        """Monitor for suspicious login attempts."""
        user_id = event.get('user_id')
        ip_address = event.get('ip_address')

        # Count recent failed attempts
        recent_failures = await self._count_recent_failures(
            user_id, ip_address, minutes=5
        )

        if recent_failures >= self.alert_thresholds['failed_logins']:
            await self._trigger_security_alert('BRUTE_FORCE_ATTACK', {
                'user_id': user_id,
                'ip_address': ip_address,
                'failure_count': recent_failures
            })

            # Implement automatic blocking
            await self._block_ip_address(ip_address, duration=3600)  # 1 hour

    async def monitor_data_access(self, event: Dict[str, Any]):
        """Monitor for unusual data access patterns."""
        user_id = event.get('user_id')
        resource_type = event.get('resource_type')
        action = event.get('action')

        # Check for unusual access patterns
        if await self._is_unusual_access_pattern(user_id, resource_type, action):
            await self._trigger_security_alert('UNUSUAL_ACCESS', {
                'user_id': user_id,
                'resource_type': resource_type,
                'action': action,
                'risk_score': await self._calculate_risk_score(event)
            })

    async def _trigger_security_alert(self, alert_type: str, details: Dict[str, Any]):
        """Trigger security alert and notify appropriate teams."""
        alert = {
            'timestamp': datetime.utcnow().isoformat(),
            'alert_type': alert_type,
            'severity': self._determine_severity(alert_type),
            'details': details,
            'status': 'new'
        }

        # Store alert
        await security_db.create_security_alert(alert)

        # Notify security team
        await self._notify_security_team(alert)

        # Implement automated response if necessary
        await self._automated_response(alert_type, details)
```

### Log Management

#### Comprehensive Logging Strategy
```python
# Comprehensive logging implementation
class SecurityLogger:
    """Comprehensive security logging system."""

    def __init__(self):
        self.log_levels = {
            'CRITICAL': 50,
            'ERROR': 40,
            'WARNING': 30,
            'INFO': 20,
            'DEBUG': 10
        }

        self.log_categories = {
            'AUTHENTICATION': 'auth',
            'AUTHORIZATION': 'authz',
            'DATA_ACCESS': 'data',
            'CONFIGURATION': 'config',
            'NETWORK': 'network',
            'APPLICATION': 'app'
        }

    async def log_authentication_event(self, event_type: str, details: Dict[str, Any]):
        """Log authentication-related events."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'category': self.log_categories['AUTHENTICATION'],
            'event_type': event_type,
            'level': self._determine_log_level(event_type),
            'details': details,
            'source_ip': details.get('source_ip'),
            'user_agent': details.get('user_agent'),
            'user_id': details.get('user_id')
        }

        # Sanitize sensitive data
        log_entry = self._sanitize_log_data(log_entry)

        # Store in secure logging system
        await self._store_log_entry(log_entry)

    async def log_data_access(self, user_id: str, resource_type: str,
                             resource_id: str, action: str):
        """Log data access events."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'category': self.log_categories['DATA_ACCESS'],
            'event_type': 'DATA_ACCESS',
            'level': 'INFO',
            'details': {
                'user_id': user_id,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'action': action
            }
        }

        await self._store_log_entry(log_entry)

    def _sanitize_log_data(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from log entries."""
        sensitive_fields = ['password', 'token', 'api_key', 'ssn', 'credit_card']

        def sanitize_value(value):
            if isinstance(value, dict):
                return {k: sanitize_value(v) for k, v in value.items()
                       if k not in sensitive_fields}
            elif isinstance(value, str):
                # Mask potential sensitive data
                for field in sensitive_fields:
                    if field.lower() in value.lower():
                        return '[REDACTED]'
                return value
            return value

        return sanitize_value(log_entry)
```

---

## Incident Response

### Incident Response Plan

#### Response Team Structure
```
Incident Response Team
├── Incident Commander (IC)
├── Technical Lead
├── Communications Lead
├── Security Analysts
└── Subject Matter Experts
```

#### Incident Classification
```python
# Incident classification system
from enum import Enum

class IncidentSeverity(Enum):
    """Incident severity levels."""
    CRITICAL = 1    # System-wide outage, data breach
    HIGH = 2        # Significant service degradation
    MEDIUM = 3      # Limited impact
    LOW = 4         # Minimal impact

class IncidentType(Enum):
    """Types of security incidents."""
    DATA_BREACH = "data_breach"
    DENIAL_OF_SERVICE = "denial_of_service"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    MALWARE = "malware"
    SOCIAL_ENGINEERING = "social_engineering"
    PHYSICAL_SECURITY = "physical_security"

class IncidentResponse:
    """Incident response management."""

    def __init__(self):
        self.active_incidents = {}
        self.response_playbooks = self._load_response_playbooks()

    async def create_incident(self, incident_type: IncidentType,
                            severity: IncidentSeverity,
                            details: Dict[str, Any]) -> str:
        """Create and track a new security incident."""
        incident_id = str(uuid.uuid4())

        incident = {
            'id': incident_id,
            'type': incident_type,
            'severity': severity,
            'status': 'new',
            'created_at': datetime.utcnow(),
            'details': details,
            'timeline': [],
            'assigned_team': [],
            'communication_sent': []
        }

        self.active_incidents[incident_id] = incident

        # Initialize response based on playbook
        await self._initialize_response(incident_id)

        return incident_id

    async def update_incident_status(self, incident_id: str,
                                    status: str,
                                    update_details: Dict[str, Any]):
        """Update incident status and timeline."""
        if incident_id not in self.active_incidents:
            return False

        incident = self.active_incidents[incident_id]
        incident['status'] = status
        incident['timeline'].append({
            'timestamp': datetime.utcnow(),
            'status': status,
            'details': update_details
        })

        # Send notifications based on status change
        await self._send_status_notifications(incident_id, status)

        return True

    async def _initialize_response(self, incident_id: str):
        """Initialize incident response based on playbook."""
        incident = self.active_incidents[incident_id]
        playbook = self.response_playbooks.get(incident['type'])

        if playbook:
            # Execute initial response steps
            for step in playbook.get('initial_steps', []):
                await self._execute_response_step(incident_id, step)

            # Notify response team
            await self._notify_response_team(incident_id)
```

### Communication Procedures

#### Incident Communication
```python
# Incident communication management
class IncidentCommunications:
    """Manages internal and external incident communications."""

    def __init__(self):
        self.communication_templates = self._load_templates()
        self.stakeholders = self._load_stakeholders()

    async def send_internal_notification(self, incident_id: str,
                                      message_type: str,
                                      details: Dict[str, Any]):
        """Send internal notifications to response team."""
        template = self.communication_templates.get(message_type)

        if not template:
            return False

        message = template.format(**details)

        # Send to response team
        await self._send_to_team(incident_id, message)

        # Log communication
        await self._log_communication(incident_id, 'internal', message_type, message)

        return True

    async def send_external_notification(self, incident_id: str,
                                       audience: str,
                                       message: str):
        """Send external communications to users/public."""
        incident = self.get_incident(incident_id)

        if incident['severity'] in [IncidentSeverity.CRITICAL, IncidentSeverity.HIGH]:
            # Send to all users for critical incidents
            await self._send_to_all_users(message)
        else:
            # Send to affected users only
            affected_users = await self._get_affected_users(incident_id)
            await self._send_to_users(affected_users, message)

        # Log communication
        await self._log_communication(incident_id, 'external', audience, message)

    async def prepare_incident_report(self, incident_id: str) -> Dict[str, Any]:
        """Prepare comprehensive incident report."""
        incident = self.get_incident(incident_id)

        report = {
            'incident_id': incident['id'],
            'executive_summary': await self._generate_executive_summary(incident),
            'timeline': incident['timeline'],
            'impact_assessment': await self._assess_impact(incident),
            'root_cause_analysis': await self._analyze_root_cause(incident),
            'lessons_learned': await self._identify_lessons_learned(incident),
            'recommendations': await self._generate_recommendations(incident),
            'preventive_measures': await self._identify_preventive_measures(incident)
        }

        return report
```

---

## Third-Party Security

#### Vendor Security Assessment

```python
# Third-party vendor security assessment
class VendorSecurityAssessment:
    """Assesses security practices of third-party vendors."""

    def __init__(self):
        self.security_criteria = {
            'encryption': ['data_at_rest', 'data_in_transit', 'key_management'],
            'access_control': ['mfa', 'rbac', 'session_management'],
            'compliance': ['soc2', 'gdpr', 'hipaa'],
            'monitoring': ['siem', 'log_management', 'incident_response'],
            'infrastructure': ['penetration_testing', 'vulnerability_scanning']
        }

    async def assess_vendor(self, vendor_name: str, vendor_type: str) -> Dict[str, Any]:
        """Conduct security assessment of a vendor."""
        assessment = {
            'vendor_name': vendor_name,
            'vendor_type': vendor_type,
            'assessment_date': datetime.utcnow().isoformat(),
            'criteria_scores': {},
            'overall_score': 0,
            'risk_level': 'unknown',
            'recommendations': []
        }

        # Assess against security criteria
        total_score = 0
        total_criteria = 0

        for category, criteria in self.security_criteria.items():
            category_score = 0

            for criterion in criteria:
                score = await self._assess_criterion(vendor_name, category, criterion)
                assessment['criteria_scores'][f"{category}_{criterion}"] = score
                category_score += score
                total_criteria += 1

            assessment['criteria_scores'][f"{category}_overall"] = (
                category_score / len(criteria) if criteria else 0
            )
            total_score += category_score

        assessment['overall_score'] = total_score / total_criteria if total_criteria > 0 else 0
        assessment['risk_level'] = self._determine_risk_level(assessment['overall_score'])
        assessment['recommendations'] = await self._generate_recommendations(assessment)

        return assessment

    async def monitor_vendor_compliance(self, vendor_name: str):
        """Monitor ongoing vendor compliance."""
        # Schedule regular assessments
        # Monitor for security incidents
        # Review compliance documentation
        # Assess changes in security posture

        compliance_status = await self._check_current_compliance(vendor_name)

        if not compliance_status['compliant']:
            await self._trigger_vendor_compliance_alert(vendor_name, compliance_status)
```

---

## Security Metrics and KPIs

### Security Performance Metrics

#### Key Security Indicators
```python
# Security metrics tracking
class SecurityMetrics:
    """Tracks and analyzes security performance metrics."""

    async def calculate_security_scorecard(self, time_period: str) -> Dict[str, Any]:
        """Calculate comprehensive security scorecard."""
        metrics = {
            'period': time_period,
            'incident_metrics': await self._get_incident_metrics(time_period),
            'vulnerability_metrics': await self._get_vulnerability_metrics(time_period),
            'access_metrics': await self._get_access_metrics(time_period),
            'compliance_metrics': await self._get_compliance_metrics(time_period),
            'training_metrics': await self._get_training_metrics(time_period)
        }

        # Calculate overall security score
        metrics['overall_score'] = self._calculate_overall_score(metrics)

        return metrics

    async def _get_incident_metrics(self, time_period: str) -> Dict[str, Any]:
        """Get incident-related metrics."""
        incidents = await self._get_incidents_by_period(time_period)

        return {
            'total_incidents': len(incidents),
            'critical_incidents': len([i for i in incidents if i['severity'] == IncidentSeverity.CRITICAL]),
            'high_incidents': len([i for i in incidents if i['severity'] == IncidentSeverity.HIGH]),
            'mean_resolution_time': self._calculate_mean_resolution_time(incidents),
            'security_posture_score': self._calculate_posture_score(incidents)
        }

    async def generate_security_report(self, report_type: str,
                                     time_period: str) -> Dict[str, Any]:
        """Generate security reports for different audiences."""
        report_generators = {
            'executive': self._generate_executive_report,
            'technical': self._generate_technical_report,
            'compliance': self._generate_compliance_report
        }

        generator = report_generators.get(report_type)
        if not generator:
            raise ValueError(f"Unknown report type: {report_type}")

        return await generator(time_period)
```

---

This comprehensive security and compliance documentation demonstrates DMLog's commitment to protecting user data and maintaining the highest security standards. Our multi-layered security approach, combined with regular monitoring and incident response capabilities, ensures that user data remains protected while maintaining service availability and performance.

---

*Last updated: October 2024*
*For security concerns, please contact security@dmlog.com*
*For compliance questions, please contact compliance@dmlog.com*