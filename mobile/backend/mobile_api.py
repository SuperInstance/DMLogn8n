"""
Mobile API Service for DMLogn8n
Provides mobile-optimized API endpoints with support for push notifications,
offline sync, and mobile-specific features.
"""

from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, get_jwt
)
from datetime import datetime, timedelta
import hashlib
import secrets
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass
from enum import Enum
import json
import os
from werkzeug.exceptions import HTTPException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-here')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

# Initialize extensions
CORS(app)
jwt = JWTManager(app)

# Create mobile API blueprint
mobile_bp = Blueprint('mobile', __name__, url_prefix='/api/mobile')

# Enums and Data Classes
class Platform(Enum):
    IOS = "ios"
    ANDROID = "android"

class BiometricType(Enum):
    TOUCH_ID = "touchid"
    FACE_ID = "faceid"
    BIOMETRICS = "biometrics"

@dataclass
class DeviceInfo:
    device_id: str
    platform: Platform
    app_version: str
    push_token: Optional[str] = None
    biometric_type: Optional[BiometricType] = None

@dataclass
class BiometricConfig:
    allow_device_credentials: bool = True
    authenticate_timeout: int = 10000
    max_attempts: int = 3
    reset_on_failure: bool = False

# In-memory storage (replace with database in production)
users = {}
biometric_tokens = {}
device_tokens = {}
offline_queues = {}
cached_data = {}

# Helper Functions
def create_response(success: bool, data=None, error=None, message=None, status_code=200):
    """Create standardized API response"""
    response = {
        'success': success,
        'timestamp': datetime.utcnow().isoformat(),
    }

    if data is not None:
        response['data'] = data
    if error:
        response['error'] = error
    if message:
        response['message'] = message

    return jsonify(response), status_code

def get_device_info() -> DeviceInfo:
    """Extract device info from request headers"""
    headers = request.headers

    return DeviceInfo(
        device_id=headers.get('X-Device-ID', 'unknown'),
        platform=Platform(headers.get('X-Platform', 'android')),
        app_version=headers.get('X-App-Version', '1.0.0'),
        push_token=headers.get('X-Push-Token'),
        biometric_type=BiometricType(headers.get('X-Biometric-Type')) if headers.get('X-Biometric-Type') else None
    )

def generate_biometric_token(user_id: str, device_info: DeviceInfo) -> str:
    """Generate biometric authentication token"""
    timestamp = datetime.utcnow().timestamp()
    random_string = secrets.token_urlsafe(32)

    # Create token payload
    payload = f"{user_id}:{device_info.device_id}:{timestamp}:{random_string}"

    # Hash the payload
    token_hash = hashlib.sha256(payload.encode()).hexdigest()

    # Create final token
    token = f"bio_{token_hash[:32]}_{int(timestamp)}"

    # Store token
    biometric_tokens[token] = {
        'user_id': user_id,
        'device_id': device_info.device_id,
        'created_at': datetime.utcnow(),
        'expires_at': datetime.utcnow() + timedelta(days=365)
    }

    return token

def validate_biometric_token(token: str, device_info: DeviceInfo) -> Optional[str]:
    """Validate biometric token and return user_id"""
    if token not in biometric_tokens:
        return None

    token_data = biometric_tokens[token]

    # Check if token is expired
    if datetime.utcnow() > token_data['expires_at']:
        del biometric_tokens[token]
        return None

    # Check if device matches
    if token_data['device_id'] != device_info.device_id:
        return None

    return token_data['user_id']

def cache_response(key: str, data: Any, ttl_minutes: int = 5):
    """Cache response data"""
    expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
    cached_data[key] = {
        'data': data,
        'expires_at': expires_at
    }

def get_cached_response(key: str) -> Optional[Any]:
    """Get cached response data"""
    if key not in cached_data:
        return None

    cache_entry = cached_data[key]
    if datetime.utcnow() > cache_entry['expires_at']:
        del cached_data[key]
        return None

    return cache_entry['data']

# Authentication Endpoints
@mobile_bp.route('/auth/login', methods=['POST'])
def mobile_login():
    """Mobile-optimized login endpoint"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        remember_me = data.get('rememberMe', False)
        device_info_json = data.get('deviceInfo', {})

        if not email or not password:
            return create_response(False, error='Email and password are required', status_code=400)

        # Validate user credentials (replace with actual authentication)
        user = users.get(email)
        if not user or user['password'] != password:  # In production, use proper password hashing
            return create_response(False, error='Invalid credentials', status_code=401)

        # Create access token
        access_token = create_access_token(identity=email)
        refresh_token = secrets.token_urlsafe(32) if remember_me else None

        # Store refresh token
        if refresh_token:
            user['refresh_token'] = refresh_token

        # Update device info
        device_info = DeviceInfo(
            device_id=device_info_json.get('deviceId', 'unknown'),
            platform=Platform(device_info_json.get('platform', 'android')),
            app_version=device_info_json.get('appVersion', '1.0.0')
        )

        device_tokens[device_info.device_id] = {
            'user_id': email,
            'device_info': device_info,
            'last_login': datetime.utcnow()
        }

        response_data = {
            'token': access_token,
            'refreshToken': refresh_token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'username': user['username'],
                'displayName': user['displayName'],
                'level': user.get('level', 1),
                'experience': user.get('experience', 0)
            }
        }

        return create_response(True, data=response_data, message='Login successful')

    except Exception as e:
        logger.error(f"Mobile login error: {str(e)}")
        return create_response(False, error='Internal server error', status_code=500)

@mobile_bp.route('/auth/refresh', methods=['POST'])
def refresh_token():
    """Refresh access token"""
    try:
        data = request.get_json()
        refresh_token = data.get('refreshToken')

        if not refresh_token:
            return create_response(False, error='Refresh token required', status_code=400)

        # Find user with refresh token
        user_email = None
        for email, user_data in users.items():
            if user_data.get('refresh_token') == refresh_token:
                user_email = email
                break

        if not user_email:
            return create_response(False, error='Invalid refresh token', status_code=401)

        # Create new access token
        access_token = create_access_token(identity=user_email)

        return create_response(True, data={'token': access_token}, message='Token refreshed')

    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return create_response(False, error='Internal server error', status_code=500)

@mobile_bp.route('/auth/biometric/setup', methods=['POST'])
def setup_biometric():
    """Setup biometric authentication"""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        biometric_token = data.get('biometricToken')
        device_info_json = data.get('deviceInfo', {})
        config_data = data.get('config', {})

        if not user_id or not biometric_token:
            return create_response(False, error='User ID and biometric token required', status_code=400)

        # Validate biometric config
        config = BiometricConfig(**config_data)

        # Store biometric token
        device_info = DeviceInfo(
            device_id=device_info_json.get('deviceId', 'unknown'),
            platform=Platform(device_info_json.get('platform', 'android')),
            biometric_type=BiometricType(device_info_json.get('biometryType'))
        )

        # Generate server-side biometric token
        server_token = generate_biometric_token(user_id, device_info)

        # Store mapping
        if user_id not in users:
            users[user_id] = {}

        users[user_id]['biometric_tokens'] = users[user_id].get('biometric_tokens', [])
        users[user_id]['biometric_tokens'].append({
            'token': server_token,
            'device_id': device_info.device_id,
            'platform': device_info.platform.value,
            'biometric_type': device_info.biometric_type.value if device_info.biometric_type else None,
            'config': config_data,
            'created_at': datetime.utcnow().isoformat()
        })

        return create_response(True, data={'biometricToken': server_token}, message='Biometric authentication setup successful')

    except Exception as e:
        logger.error(f"Biometric setup error: {str(e)}")
        return create_response(False, error='Failed to setup biometric authentication', status_code=500)

@mobile_bp.route('/auth/biometric/verify', methods=['POST'])
def verify_biometric():
    """Verify biometric authentication"""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        biometric_token = data.get('biometricToken')
        device_info_json = data.get('deviceInfo', {})

        if not user_id or not biometric_token:
            return create_response(False, error='User ID and biometric token required', status_code=400)

        device_info = DeviceInfo(
            device_id=device_info_json.get('deviceId', 'unknown'),
            platform=Platform(device_info_json.get('platform', 'android')),
            biometric_type=BiometricType(device_info_json.get('biometryType'))
        )

        # Validate biometric token
        token_user_id = validate_biometric_token(biometric_token, device_info)

        if token_user_id != user_id:
            return create_response(False, error='Invalid biometric token', status_code=401)

        # Create access token
        access_token = create_access_token(identity=user_id)

        return create_response(True, data={'authToken': access_token}, message='Biometric authentication successful')

    except Exception as e:
        logger.error(f"Biometric verification error: {str(e)}")
        return create_response(False, error='Biometric verification failed', status_code=500)

@mobile_bp.route('/auth/biometric/remove', methods=['POST'])
def remove_biometric():
    """Remove biometric authentication"""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        device_info_json = data.get('deviceInfo', {})

        if not user_id:
            return create_response(False, error='User ID required', status_code=400)

        device_id = device_info_json.get('deviceId', 'unknown')

        # Remove biometric tokens for this device
        if user_id in users and 'biometric_tokens' in users[user_id]:
            users[user_id]['biometric_tokens'] = [
                token for token in users[user_id]['biometric_tokens']
                if token.get('device_id') != device_id
            ]

        # Remove biometric tokens from token store
        tokens_to_remove = []
        for token, token_data in biometric_tokens.items():
            if token_data['user_id'] == user_id and token_data['device_id'] == device_id:
                tokens_to_remove.append(token)

        for token in tokens_to_remove:
            del biometric_tokens[token]

        return create_response(True, message='Biometric authentication removed successfully')

    except Exception as e:
        logger.error(f"Biometric removal error: {str(e)}")
        return create_response(False, error='Failed to remove biometric authentication', status_code=500)

# User Data Endpoints
@mobile_bp.route('/user/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    """Get user profile with mobile optimizations"""
    try:
        current_user = get_jwt_identity()
        user = users.get(current_user)

        if not user:
            return create_response(False, error='User not found', status_code=404)

        # Cache key
        cache_key = f"user_profile_{current_user}"

        # Check cache first
        cached_profile = get_cached_response(cache_key)
        if cached_profile:
            return create_response(True, data=cached_profile, message='Profile retrieved from cache')

        # Build profile data
        profile_data = {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'displayName': user['displayName'],
            'level': user.get('level', 1),
            'experience': user.get('experience', 0),
            'achievements': user.get('achievements', []),
            'createdAt': user.get('createdAt'),
            'lastLoginAt': user.get('lastLoginAt'),
            'preferences': user.get('preferences', {})
        }

        # Cache the response
        cache_response(cache_key, profile_data, ttl_minutes=10)

        return create_response(True, data=profile_data, message='Profile retrieved successfully')

    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        return create_response(False, error='Failed to retrieve profile', status_code=500)

@mobile_bp.route('/user/characters', methods=['GET'])
@jwt_required()
def get_user_characters():
    """Get user characters with caching"""
    try:
        current_user = get_jwt_identity()
        user = users.get(current_user)

        if not user:
            return create_response(False, error='User not found', status_code=404)

        # Cache key
        cache_key = f"user_characters_{current_user}"

        # Check cache first
        cached_characters = get_cached_response(cache_key)
        if cached_characters:
            return create_response(True, data=cached_characters, message='Characters retrieved from cache')

        # Get characters (mock data)
        characters = user.get('characters', [])

        # Cache the response
        cache_response(cache_key, characters, ttl_minutes=5)

        return create_response(True, data=characters, message='Characters retrieved successfully')

    except Exception as e:
        logger.error(f"Get characters error: {str(e)}")
        return create_response(False, error='Failed to retrieve characters', status_code=500)

@mobile_bp.route('/user/achievements', methods=['GET'])
@jwt_required()
def get_user_achievements():
    """Get user achievements with progress"""
    try:
        current_user = get_jwt_identity()
        user = users.get(current_user)

        if not user:
            return create_response(False, error='User not found', status_code=404)

        # Cache key
        cache_key = f"user_achievements_{current_user}"

        # Check cache first
        cached_achievements = get_cached_response(cache_key)
        if cached_achievements:
            return create_response(True, data=cached_achievements, message='Achievements retrieved from cache')

        # Get achievements (mock data)
        achievements = user.get('achievements', [])

        # Cache the response
        cache_response(cache_key, achievements, ttl_minutes=15)

        return create_response(True, data=achievements, message='Achievements retrieved successfully')

    except Exception as e:
        logger.error(f"Get achievements error: {str(e)}")
        return create_response(False, error='Failed to retrieve achievements', status_code=500)

# Sync Endpoints
@mobile_bp.route('/sync/upload', methods=['POST'])
@jwt_required()
def upload_sync_data():
    """Upload offline data for sync"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()

        if not data:
            return create_response(False, error='No data provided', status_code=400)

        # Process sync data
        sync_data = {
            'user_id': current_user,
            'uploaded_at': datetime.utcnow().isoformat(),
            'data': data
        }

        # Store sync data (in production, save to database)
        if current_user not in offline_queues:
            offline_queues[current_user] = []

        offline_queues[current_user].append(sync_data)

        # Process queued actions
        pending_actions = data.get('pendingActions', [])
        processed_actions = []
        failed_actions = []

        for action in pending_actions:
            try:
                # Process each action based on type
                result = process_offline_action(current_user, action)
                if result['success']:
                    processed_actions.append(action['id'])
                else:
                    failed_actions.append({
                        'id': action['id'],
                        'error': result['error']
                    })
            except Exception as e:
                failed_actions.append({
                    'id': action['id'],
                    'error': str(e)
                })

        response_data = {
            'processedActions': processed_actions,
            'failedActions': failed_actions,
            'syncId': secrets.token_urlsafe(16)
        }

        return create_response(True, data=response_data, message='Sync data uploaded successfully')

    except Exception as e:
        logger.error(f"Sync upload error: {str(e)}")
        return create_response(False, error='Failed to upload sync data', status_code=500)

@mobile_bp.route('/sync/download', methods=['GET'])
@jwt_required()
def download_sync_data():
    """Download latest data for offline use"""
    try:
        current_user = get_jwt_identity()
        user = users.get(current_user)

        if not user:
            return create_response(False, error='User not found', status_code=404)

        # Get all user data for offline sync
        sync_data = {
            'characters': user.get('characters', []),
            'inventory': user.get('inventory', []),
            'achievements': user.get('achievements', []),
            'gameSessions': user.get('gameSessions', []),
            'chatMessages': user.get('chatMessages', []),
            'lastSyncTime': datetime.utcnow().isoformat(),
            'pendingActions': []
        }

        return create_response(True, data=sync_data, message='Sync data downloaded successfully')

    except Exception as e:
        logger.error(f"Sync download error: {str(e)}")
        return create_response(False, error='Failed to download sync data', status_code=500)

@mobile_bp.route('/sync/status', methods=['GET'])
@jwt_required()
def get_sync_status():
    """Get sync status"""
    try:
        current_user = get_jwt_identity()

        # Get sync status
        pending_count = len(offline_queues.get(current_user, []))
        last_sync = users.get(current_user, {}).get('lastSyncAt')

        status_data = {
            'pendingActions': pending_count,
            'lastSyncTime': last_sync,
            'isOnline': True,  # In production, check actual connectivity
            'conflicts': []  # In production, check for actual conflicts
        }

        return create_response(True, data=status_data, message='Sync status retrieved')

    except Exception as e:
        logger.error(f"Sync status error: {str(e)}")
        return create_response(False, error='Failed to get sync status', status_code=500)

# Helper Functions
def process_offline_action(user_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
    """Process offline action"""
    try:
        action_type = action.get('type')
        resource = action.get('resource')
        data = action.get('data', {})

        # Process different action types
        if action_type == 'create':
            return handle_create_action(user_id, resource, data)
        elif action_type == 'update':
            return handle_update_action(user_id, resource, data)
        elif action_type == 'delete':
            return handle_delete_action(user_id, resource, data)
        else:
            return {'success': False, 'error': f'Unknown action type: {action_type}'}

    except Exception as e:
        return {'success': False, 'error': str(e)}

def handle_create_action(user_id: str, resource: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle create action"""
    # Mock implementation - in production, save to database
    logger.info(f"Creating {resource} for user {user_id}: {data}")
    return {'success': True}

def handle_update_action(user_id: str, resource: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle update action"""
    # Mock implementation - in production, update in database
    logger.info(f"Updating {resource} for user {user_id}: {data}")
    return {'success': True}

def handle_delete_action(user_id: str, resource: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle delete action"""
    # Mock implementation - in production, delete from database
    logger.info(f"Deleting {resource} for user {user_id}: {data}")
    return {'success': True}

# Error Handlers
@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Handle HTTP exceptions"""
    return create_response(False, error=e.description, status_code=e.code)

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle generic exceptions"""
    logger.error(f"Unhandled exception: {str(e)}")
    return create_response(False, error='Internal server error', status_code=500)

# Register blueprint
app.register_blueprint(mobile_bp)

# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint"""
    return create_response(True, data={'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

if __name__ == '__main__':
    # Initialize with some test data
    users['test@example.com'] = {
        'id': 'user123',
        'email': 'test@example.com',
        'username': 'testuser',
        'displayName': 'Test User',
        'password': 'password123',  # In production, use proper password hashing
        'level': 5,
        'experience': 2500,
        'achievements': [
            {
                'id': 'ach1',
                'name': 'First Character',
                'description': 'Create your first character',
                'completedAt': '2024-01-01T00:00:00Z'
            }
        ],
        'characters': [
            {
                'id': 'char1',
                'name': 'Aragorn',
                'class': 'Ranger',
                'level': 3,
                'health': 45,
                'maxHealth': 50
            }
        ],
        'createdAt': '2024-01-01T00:00:00Z',
        'lastLoginAt': datetime.utcnow().isoformat()
    }

    # Run the app
    app.run(
        host='0.0.0.0',
        port=3001,
        debug=True
    )