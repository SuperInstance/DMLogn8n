"""
Mobile Authentication Service for DMLogn8n
Handles mobile-specific authentication including biometric auth, device management,
and secure token handling for mobile applications.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import secrets
import hashlib
import jwt
from flask import Flask, Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import redis
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask blueprint
auth_bp = Blueprint('mobile_auth', __name__, url_prefix='/api/mobile/auth')

# Enums
class AuthMethod(Enum):
    PASSWORD = "password"
    BIOMETRIC = "biometric"
    SOCIAL = "social"
    MAGIC_LINK = "magic_link"

class BiometricType(Enum):
    TOUCH_ID = "touchid"
    FACE_ID = "faceid"
    FINGERPRINT = "fingerprint"
    BIOMETRICS = "biometrics"

class Platform(Enum):
    IOS = "ios"
    ANDROID = "android"

@dataclass
class DeviceInfo:
    device_id: str
    platform: Platform
    app_version: str
    device_model: str
    os_version: str
    push_token: Optional[str] = None
    biometric_type: Optional[BiometricType] = None
    jailbroken: bool = False
    rooted: bool = False

@dataclass
class BiometricConfig:
    allow_device_credentials: bool = True
    authenticate_timeout: int = 10000
    max_attempts: int = 3
    reset_on_failure: bool = False
    require_biometric: bool = False

@dataclass
class AuthSession:
    session_id: str
    user_id: str
    device_id: str
    created_at: datetime
    expires_at: datetime
    last_accessed: datetime
    ip_address: str
    user_agent: str
    is_active: bool = True

@dataclass
class BiometricCredential:
    id: str
    user_id: str
    device_id: str
    biometric_type: BiometricType
    public_key: str
    credential_id: str
    created_at: datetime
    last_used: Optional[datetime] = None
    is_active: bool = True
    attempts: int = 0
    max_attempts: int = 5

class MobileAuthService:
    """Main mobile authentication service"""

    def __init__(self):
        # Configuration
        self.jwt_secret = os.environ.get('JWT_SECRET_KEY', 'your-super-secret-jwt-key')
        self.jwt_refresh_secret = os.environ.get('JWT_REFRESH_SECRET_KEY', 'your-super-secret-refresh-key')
        self.token_expiry = timedelta(hours=1)
        self.refresh_token_expiry = timedelta(days=30)
        self.session_timeout = timedelta(hours=24)
        self.max_sessions_per_user = 5
        self.max_devices_per_user = 10

        # Initialize Redis for session storage
        self.redis_client = redis.Redis(
            host=os.environ.get('REDIS_HOST', 'localhost'),
            port=int(os.environ.get('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True
        )

        # Initialize encryption
        self.encryption_key = self._generate_encryption_key()
        self.cipher = Fernet(self.encryption_key)

        # In-memory storage (replace with database in production)
        self.users: Dict[str, Dict[str, Any]] = {}
        self.devices: Dict[str, DeviceInfo] = {}
        self.sessions: Dict[str, AuthSession] = {}
        self.biometric_credentials: Dict[str, BiometricCredential] = {}

    def _generate_encryption_key(self) -> bytes:
        """Generate encryption key from password"""
        password = os.environ.get('ENCRYPTION_PASSWORD', 'default-encryption-password').encode()
        salt = b'mobile_auth_salt'  # In production, use a proper random salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key

    def register_user(self, email: str, password: str, username: str, display_name: str,
                     device_info: DeviceInfo) -> Dict[str, Any]:
        """Register a new user with device"""
        try:
            # Check if user already exists
            if email in self.users:
                raise Exception("User already exists")

            # Validate input
            if not self._validate_email(email):
                raise Exception("Invalid email address")
            if not self._validate_password(password):
                raise Exception("Password does not meet requirements")

            # Hash password
            password_hash = generate_password_hash(password)

            # Create user
            user_id = secrets.token_urlsafe(32)
            user = {
                'id': user_id,
                'email': email,
                'username': username,
                'display_name': display_name,
                'password_hash': password_hash,
                'created_at': datetime.utcnow().isoformat(),
                'last_login': None,
                'is_active': True,
                'email_verified': False,
                'devices': [device_info.device_id],
                'preferences': {},
                'security_settings': {
                    'require_biometric': False,
                    'session_timeout_hours': 24,
                    'max_sessions': 5
                }
            }

            self.users[email] = user
            self.devices[device_info.device_id] = device_info

            # Create initial session
            session = self._create_session(user_id, device_info.device_id, request.remote_addr)

            # Generate tokens
            access_token = self._generate_access_token(user_id, session.session_id, device_info.device_id)
            refresh_token = self._generate_refresh_token(user_id, device_info.device_id)

            logger.info(f"Registered new user: {email}")

            return {
                'user_id': user_id,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'session_id': session.session_id,
                'expires_in': int(self.token_expiry.total_seconds()),
                'user': {
                    'id': user_id,
                    'email': email,
                    'username': username,
                    'display_name': display_name,
                    'created_at': user['created_at']
                }
            }

        except Exception as e:
            logger.error(f"Registration failed: {str(e)}")
            raise

    def authenticate_user(self, email: str, password: str, device_info: DeviceInfo) -> Dict[str, Any]:
        """Authenticate user with password"""
        try:
            # Get user
            user = self.users.get(email)
            if not user:
                raise Exception("Invalid credentials")

            # Check password
            if not check_password_hash(user['password_hash'], password):
                raise Exception("Invalid credentials")

            # Check if user is active
            if not user['is_active']:
                raise Exception("Account is disabled")

            # Register device if new
            if device_info.device_id not in user['devices']:
                if len(user['devices']) >= self.max_devices_per_user:
                    raise Exception("Maximum devices reached")
                user['devices'].append(device_info.device_id)
                self.devices[device_info.device_id] = device_info

            # Clean up old sessions
            self._cleanup_old_sessions(user['id'])

            # Create new session
            session = self._create_session(user['id'], device_info.device_id, request.remote_addr)

            # Update last login
            user['last_login'] = datetime.utcnow().isoformat()

            # Generate tokens
            access_token = self._generate_access_token(user['id'], session.session_id, device_info.device_id)
            refresh_token = self._generate_refresh_token(user['id'], device_info.device_id)

            logger.info(f"User authenticated: {email}")

            return {
                'user_id': user['id'],
                'access_token': access_token,
                'refresh_token': refresh_token,
                'session_id': session.session_id,
                'expires_in': int(self.token_expiry.total_seconds()),
                'user': {
                    'id': user['id'],
                    'email': email,
                    'username': user['username'],
                    'display_name': user['display_name'],
                    'level': user.get('level', 1),
                    'experience': user.get('experience', 0)
                }
            }

        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise

    def setup_biometric_auth(self, user_id: str, device_id: str, biometric_type: BiometricType,
                           public_key: str, config: BiometricConfig) -> Dict[str, Any]:
        """Setup biometric authentication"""
        try:
            # Verify user exists and device is registered
            user = self._get_user_by_id(user_id)
            if not user:
                raise Exception("User not found")

            if device_id not in user['devices']:
                raise Exception("Device not registered")

            # Generate credential
            credential_id = secrets.token_urlsafe(32)
            credential = BiometricCredential(
                id=secrets.token_urlsafe(16),
                user_id=user_id,
                device_id=device_id,
                biometric_type=biometric_type,
                public_key=self._encrypt_data(public_key),
                credential_id=credential_id,
                created_at=datetime.utcnow()
            )

            # Store credential
            self.biometric_credentials[credential.id] = credential

            # Update device info
            if device_id in self.devices:
                self.devices[device_id].biometric_type = biometric_type

            # Update user security settings
            user['security_settings']['require_biometric'] = config.require_biometric

            logger.info(f"Biometric auth setup for user {user_id} on device {device_id}")

            return {
                'credential_id': credential_id,
                'biometric_type': biometric_type.value,
                'configured_at': credential.created_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Biometric setup failed: {str(e)}")
            raise

    def authenticate_with_biometric(self, credential_id: str, signature: str, challenge: str,
                                  device_info: DeviceInfo) -> Dict[str, Any]:
        """Authenticate using biometric credentials"""
        try:
            # Get credential
            credential = self.biometric_credentials.get(credential_id)
            if not credential:
                raise Exception("Invalid credentials")

            # Check if credential is active
            if not credential.is_active:
                raise Exception("Credentials are inactive")

            # Check attempts
            if credential.attempts >= credential.max_attempts:
                raise Exception("Too many failed attempts")

            # Verify device matches
            if credential.device_id != device_info.device_id:
                raise Exception("Device mismatch")

            # Verify signature (simplified - in production, use proper crypto)
            if not self._verify_biometric_signature(credential, signature, challenge):
                credential.attempts += 1
                if credential.attempts >= credential.max_attempts:
                    credential.is_active = False
                raise Exception("Invalid signature")

            # Reset attempts on success
            credential.attempts = 0
            credential.last_used = datetime.utcnow()

            # Get user
            user = self._get_user_by_id(credential.user_id)
            if not user:
                raise Exception("User not found")

            # Clean up old sessions
            self._cleanup_old_sessions(credential.user_id)

            # Create session
            session = self._create_session(credential.user_id, device_info.device_id, request.remote_addr)

            # Generate tokens
            access_token = self._generate_access_token(credential.user_id, session.session_id, device_info.device_id)
            refresh_token = self._generate_refresh_token(credential.user_id, device_info.device_id)

            logger.info(f"Biometric authentication successful for user {credential.user_id}")

            return {
                'user_id': credential.user_id,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'session_id': session.session_id,
                'expires_in': int(self.token_expiry.total_seconds())
            }

        except Exception as e:
            logger.error(f"Biometric authentication failed: {str(e)}")
            raise

    def refresh_token(self, refresh_token: str, device_id: str) -> Dict[str, Any]:
        """Refresh access token"""
        try:
            # Verify refresh token
            payload = self._decode_token(refresh_token, self.jwt_refresh_secret)
            user_id = payload.get('user_id')
            token_device_id = payload.get('device_id')

            if not user_id or token_device_id != device_id:
                raise Exception("Invalid refresh token")

            # Get user
            user = self._get_user_by_id(user_id)
            if not user or not user['is_active']:
                raise Exception("Invalid token")

            # Verify device is still registered
            if device_id not in user['devices']:
                raise Exception("Device not registered")

            # Create new session
            session = self._create_session(user_id, device_id, request.remote_addr)

            # Generate new tokens
            new_access_token = self._generate_access_token(user_id, session.session_id, device_id)
            new_refresh_token = self._generate_refresh_token(user_id, device_id)

            logger.info(f"Token refreshed for user {user_id}")

            return {
                'access_token': new_access_token,
                'refresh_token': new_refresh_token,
                'session_id': session.session_id,
                'expires_in': int(self.token_expiry.total_seconds())
            }

        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            raise

    def logout_user(self, session_id: str, device_id: str) -> bool:
        """Logout user and invalidate session"""
        try:
            # Get session
            session = self.sessions.get(session_id)
            if not session or session.device_id != device_id:
                return False

            # Invalidate session
            session.is_active = False

            # Remove from active sessions
            self.redis_client.delete(f"session:{session_id}")

            logger.info(f"User logged out: {session.user_id}")
            return True

        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            return False

    def logout_all_sessions(self, user_id: str) -> int:
        """Logout all sessions for a user"""
        try:
            count = 0
            for session in self.sessions.values():
                if session.user_id == user_id and session.is_active:
                    session.is_active = False
                    self.redis_client.delete(f"session:{session.session_id}")
                    count += 1

            logger.info(f"Logged out {count} sessions for user {user_id}")
            return count

        except Exception as e:
            logger.error(f"Logout all sessions failed: {str(e)}")
            return 0

    def revoke_biometric_credentials(self, user_id: str, device_id: str) -> bool:
        """Revoke biometric credentials for a device"""
        try:
            revoked_count = 0
            for credential in self.biometric_credentials.values():
                if credential.user_id == user_id and credential.device_id == device_id:
                    credential.is_active = False
                    revoked_count += 1

            logger.info(f"Revoked {revoked_count} biometric credentials for user {user_id}")
            return revoked_count > 0

        except Exception as e:
            logger.error(f"Revoke biometric credentials failed: {str(e)}")
            return False

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        try:
            session = self.sessions.get(session_id)
            if not session or not session.is_active:
                return None

            return asdict(session)

        except Exception as e:
            logger.error(f"Get session info failed: {str(e)}")
            return None

    def _create_session(self, user_id: str, device_id: str, ip_address: str) -> AuthSession:
        """Create new authentication session"""
        try:
            session_id = secrets.token_urlsafe(32)
            session = AuthSession(
                session_id=session_id,
                user_id=user_id,
                device_id=device_id,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + self.session_timeout,
                last_accessed=datetime.utcnow(),
                ip_address=ip_address,
                user_agent=request.headers.get('User-Agent', '')
            )

            self.sessions[session_id] = session

            # Store in Redis
            self.redis_client.setex(
                f"session:{session_id}",
                int(self.session_timeout.total_seconds()),
                json.dumps(asdict(session))
            )

            return session

        except Exception as e:
            logger.error(f"Create session failed: {str(e)}")
            raise

    def _generate_access_token(self, user_id: str, session_id: str, device_id: str) -> str:
        """Generate JWT access token"""
        try:
            payload = {
                'user_id': user_id,
                'session_id': session_id,
                'device_id': device_id,
                'type': 'access',
                'exp': datetime.utcnow() + self.token_expiry,
                'iat': datetime.utcnow()
            }

            return jwt.encode(payload, self.jwt_secret, algorithm='HS256')

        except Exception as e:
            logger.error(f"Generate access token failed: {str(e)}")
            raise

    def _generate_refresh_token(self, user_id: str, device_id: str) -> str:
        """Generate JWT refresh token"""
        try:
            payload = {
                'user_id': user_id,
                'device_id': device_id,
                'type': 'refresh',
                'exp': datetime.utcnow() + self.refresh_token_expiry,
                'iat': datetime.utcnow()
            }

            return jwt.encode(payload, self.jwt_refresh_secret, algorithm='HS256')

        except Exception as e:
            logger.error(f"Generate refresh token failed: {str(e)}")
            raise

    def _decode_token(self, token: str, secret: str) -> Dict[str, Any]:
        """Decode JWT token"""
        try:
            return jwt.decode(token, secret, algorithms=['HS256'])

        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.InvalidTokenError:
            raise Exception("Invalid token")

    def _encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            return self.cipher.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Data encryption failed: {str(e)}")
            raise

    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            return self.cipher.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Data decryption failed: {str(e)}")
            raise

    def _verify_biometric_signature(self, credential: BiometricCredential, signature: str, challenge: str) -> bool:
        """Verify biometric signature (simplified)"""
        try:
            # In a real implementation, this would use proper cryptographic verification
            # For now, we'll do a simple check
            public_key = self._decrypt_data(credential.public_key)

            # Simple verification logic
            expected_signature = hashlib.sha256(f"{public_key}:{challenge}".encode()).hexdigest()
            return signature == expected_signature

        except Exception as e:
            logger.error(f"Biometric signature verification failed: {str(e)}")
            return False

    def _get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            for user in self.users.values():
                if user['id'] == user_id:
                    return user
            return None

        except Exception as e:
            logger.error(f"Get user by ID failed: {str(e)}")
            return None

    def _cleanup_old_sessions(self, user_id: str):
        """Clean up expired sessions for a user"""
        try:
            current_time = datetime.utcnow()
            sessions_to_remove = []

            for session_id, session in self.sessions.items():
                if (session.user_id == user_id and
                    (session.expires_at < current_time or not session.is_active)):
                    sessions_to_remove.append(session_id)

            for session_id in sessions_to_remove:
                del self.sessions[session_id]
                self.redis_client.delete(f"session:{session_id}")

            if sessions_to_remove:
                logger.info(f"Cleaned up {len(sessions_to_remove)} old sessions for user {user_id}")

        except Exception as e:
            logger.error(f"Session cleanup failed: {str(e)}")

    def _validate_email(self, email: str) -> bool:
        """Validate email address"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def _validate_password(self, password: str) -> bool:
        """Validate password strength"""
        if len(password) < 8:
            return False
        if not any(c.isupper() for c in password):
            return False
        if not any(c.islower() for c in password):
            return False
        if not any(c.isdigit() for c in password):
            return False
        return True

    def get_user_devices(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all devices for a user"""
        try:
            user = self._get_user_by_id(user_id)
            if not user:
                return []

            devices = []
            for device_id in user['devices']:
                if device_id in self.devices:
                    device_info = self.devices[device_id]
                    devices.append({
                        'device_id': device_id,
                        'platform': device_info.platform.value,
                        'app_version': device_info.app_version,
                        'device_model': device_info.device_model,
                        'os_version': device_info.os_version,
                        'has_biometric': device_info.biometric_type is not None,
                        'biometric_type': device_info.biometric_type.value if device_info.biometric_type else None,
                        'is_jailbroken': device_info.jailbroken,
                        'is_rooted': device_info.rooted
                    })

            return devices

        except Exception as e:
            logger.error(f"Get user devices failed: {str(e)}")
            return []

    def get_active_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for a user"""
        try:
            sessions = []
            current_time = datetime.utcnow()

            for session in self.sessions.values():
                if (session.user_id == user_id and
                    session.is_active and
                    session.expires_at > current_time):
                    sessions.append({
                        'session_id': session.session_id,
                        'device_id': session.device_id,
                        'created_at': session.created_at.isoformat(),
                        'expires_at': session.expires_at.isoformat(),
                        'last_accessed': session.last_accessed.isoformat(),
                        'ip_address': session.ip_address,
                        'user_agent': session.user_agent
                    })

            return sessions

        except Exception as e:
            logger.error(f"Get active sessions failed: {str(e)}")
            return []

# Global auth service instance
auth_service = MobileAuthService()

# Flask API endpoints
@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.get_json()

        # Extract device info from headers
        device_info = DeviceInfo(
            device_id=request.headers.get('X-Device-ID', 'unknown'),
            platform=Platform(request.headers.get('X-Platform', 'android')),
            app_version=request.headers.get('X-App-Version', '1.0.0'),
            device_model=request.headers.get('X-Device-Model', 'unknown'),
            os_version=request.headers.get('X-OS-Version', 'unknown'),
            push_token=request.headers.get('X-Push-Token')
        )

        result = auth_service.register_user(
            email=data.get('email'),
            password=data.get('password'),
            username=data.get('username'),
            display_name=data.get('displayName'),
            device_info=device_info
        )

        return jsonify({
            'success': True,
            'data': result,
            'message': 'Registration successful'
        })

    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user"""
    try:
        data = request.get_json()

        # Extract device info from headers
        device_info = DeviceInfo(
            device_id=request.headers.get('X-Device-ID', 'unknown'),
            platform=Platform(request.headers.get('X-Platform', 'android')),
            app_version=request.headers.get('X-App-Version', '1.0.0'),
            device_model=request.headers.get('X-Device-Model', 'unknown'),
            os_version=request.headers.get('X-OS-Version', 'unknown'),
            push_token=request.headers.get('X-Push-Token')
        )

        result = auth_service.authenticate_user(
            email=data.get('email'),
            password=data.get('password'),
            device_info=device_info
        )

        return jsonify({
            'success': True,
            'data': result,
            'message': 'Authentication successful'
        })

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 401

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Refresh access token"""
    try:
        data = request.get_json()
        refresh_token = data.get('refreshToken')
        device_id = request.headers.get('X-Device-ID')

        if not refresh_token or not device_id:
            return jsonify({
                'success': False,
                'error': 'Refresh token and device ID required'
            }), 400

        result = auth_service.refresh_token(refresh_token, device_id)

        return jsonify({
            'success': True,
            'data': result,
            'message': 'Token refreshed successfully'
        })

    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user"""
    try:
        data = request.get_json()
        session_id = data.get('sessionId')
        device_id = request.headers.get('X-Device-ID')

        if not session_id or not device_id:
            return jsonify({
                'success': False,
                'error': 'Session ID and device ID required'
            }), 400

        success = auth_service.logout_user(session_id, device_id)

        if success:
            return jsonify({
                'success': True,
                'message': 'Logout successful'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid session'
            }), 400

    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Create Flask app for testing
    app = Flask(__name__)
    app.register_blueprint(auth_bp)

    app.run(host='0.0.0.0', port=3004, debug=True)