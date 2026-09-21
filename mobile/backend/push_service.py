"""
Push Notification Service for DMLogn8n Mobile
Handles Firebase Cloud Messaging (FCM) for Android and Apple Push Notification Service (APNs) for iOS.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import requests
from flask import Flask, Blueprint, request, jsonify
import firebase_admin
from firebase_admin import credentials, messaging
import jwt
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask blueprint
push_bp = Blueprint('push', __name__, url_prefix='/api/push')

# Enums
class NotificationPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class NotificationType(Enum):
    GAME_INVITE = "game_invite"
    FRIEND_REQUEST = "friend_request"
    ACHIEVEMENT = "achievement"
    SYSTEM = "system"
    CHAT_MESSAGE = "chat_message"
    GAME_EVENT = "game_event"

@dataclass
class PushToken:
    user_id: str
    token: str
    platform: str  # 'ios' or 'android'
    device_id: str
    app_version: str
    created_at: datetime
    is_active: bool = True

@dataclass
class NotificationData:
    title: str
    body: str
    data: Dict[str, Any]
    type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    sound: str = "default"
    badge: Optional[int] = None
    image_url: Optional[str] = None
    actions: Optional[List[Dict[str, str]]] = None

@dataclass
class NotificationRequest:
    user_ids: List[str]
    notification: NotificationData
    scheduled_for: Optional[datetime] = None

class PushNotificationService:
    """Main push notification service"""

    def __init__(self):
        self.firebase_app = None
        self.tokens: Dict[str, List[PushToken]] = {}  # user_id -> list of tokens
        self.apns_key = os.environ.get('APNS_KEY_PATH')
        self.apns_key_id = os.environ.get('APNS_KEY_ID')
        self.apns_team_id = os.environ.get('APNS_TEAM_ID')
        self.initialize_firebase()

    def initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if already initialized
            if not firebase_admin._apps:
                # Initialize with service account
                cred_path = os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH')
                if cred_path and os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    self.firebase_app = firebase_admin.initialize_app(cred)
                    logger.info("Firebase Admin SDK initialized successfully")
                else:
                    # Initialize with environment variables (for deployment)
                    if os.environ.get('FIREBASE_PROJECT_ID'):
                        config = {
                            'type': 'service_account',
                            'project_id': os.environ.get('FIREBASE_PROJECT_ID'),
                            'private_key_id': os.environ.get('FIREBASE_PRIVATE_KEY_ID'),
                            'private_key': os.environ.get('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n'),
                            'client_email': os.environ.get('FIREBASE_CLIENT_EMAIL'),
                            'client_id': os.environ.get('FIREBASE_CLIENT_ID'),
                            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                            'token_uri': 'https://oauth2.googleapis.com/token'
                        }
                        cred = credentials.Certificate(config)
                        self.firebase_app = firebase_admin.initialize_app(cred)
                        logger.info("Firebase Admin SDK initialized from environment")
                    else:
                        logger.warning("Firebase credentials not found - push notifications disabled")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")

    def register_token(self, user_id: str, token: str, platform: str, device_id: str, app_version: str) -> bool:
        """Register a new push token"""
        try:
            # Create new push token
            push_token = PushToken(
                user_id=user_id,
                token=token,
                platform=platform,
                device_id=device_id,
                app_version=app_version,
                created_at=datetime.utcnow()
            )

            # Remove existing token for this device if any
            self.remove_device_token(device_id)

            # Add new token
            if user_id not in self.tokens:
                self.tokens[user_id] = []

            self.tokens[user_id].append(push_token)

            logger.info(f"Registered push token for user {user_id} on {platform}")
            return True

        except Exception as e:
            logger.error(f"Failed to register push token: {str(e)}")
            return False

    def remove_token(self, user_id: str, token: str) -> bool:
        """Remove a specific push token"""
        try:
            if user_id in self.tokens:
                self.tokens[user_id] = [
                    t for t in self.tokens[user_id] if t.token != token
                ]
                if not self.tokens[user_id]:
                    del self.tokens[user_id]

            logger.info(f"Removed push token for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove push token: {str(e)}")
            return False

    def remove_device_token(self, device_id: str) -> bool:
        """Remove token for specific device"""
        try:
            for user_id, token_list in self.tokens.items():
                self.tokens[user_id] = [
                    t for t in token_list if t.device_id != device_id
                ]

            logger.info(f"Removed push token for device {device_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove device token: {str(e)}")
            return False

    def send_notification(self, notification_request: NotificationRequest) -> Dict[str, Any]:
        """Send push notification to specified users"""
        try:
            results = {
                'success': 0,
                'failed': 0,
                'tokens_used': 0,
                'errors': []
            }

            for user_id in notification_request.user_ids:
                user_tokens = self.tokens.get(user_id, [])
                active_tokens = [t for t in user_tokens if t.is_active]

                if not active_tokens:
                    results['errors'].append(f"No active tokens found for user {user_id}")
                    continue

                for token in active_tokens:
                    try:
                        success = self._send_to_token(token.token, token.platform, notification_request.notification)
                        if success:
                            results['success'] += 1
                        else:
                            results['failed'] += 1
                            # Mark token as inactive if it failed
                            token.is_active = False

                        results['tokens_used'] += 1

                    except Exception as e:
                        logger.error(f"Failed to send to token {token.token[:10]}...: {str(e)}")
                        results['failed'] += 1
                        results['errors'].append(f"Token error: {str(e)}")

            return results

        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            return {
                'success': 0,
                'failed': 0,
                'tokens_used': 0,
                'errors': [str(e)]
            }

    def _send_to_token(self, token: str, platform: str, notification_data: NotificationData) -> bool:
        """Send notification to a specific token"""
        try:
            if platform == 'android':
                return self._send_android_notification(token, notification_data)
            elif platform == 'ios':
                return self._send_ios_notification(token, notification_data)
            else:
                logger.error(f"Unsupported platform: {platform}")
                return False

        except Exception as e:
            logger.error(f"Failed to send notification to token: {str(e)}")
            return False

    def _send_android_notification(self, token: str, notification_data: NotificationData) -> bool:
        """Send Android notification via FCM"""
        try:
            if not self.firebase_app:
                logger.error("Firebase not initialized - cannot send Android notification")
                return False

            # Create message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=notification_data.title,
                    body=notification_data.body,
                    image_url=notification_data.image_url
                ),
                data=notification_data.data,
                token=token,
                android=messaging.AndroidConfig(
                    priority=self._get_android_priority(notification_data.priority),
                    notification=messaging.AndroidNotification(
                        sound=notification_data.sound,
                        badge=notification_data.badge,
                        icon='ic_notification',
                        color='#6200EE',
                        click_action='FLUTTER_NOTIFICATION_CLICK',
                        default_sound=True,
                        default_vibrate_timings=True
                    ),
                    data=notification_data.data
                )
            )

            # Add actions if provided
            if notification_data.actions:
                message.android.notification.actions = [
                    messaging.AndroidNotificationAction(
                        action['action'],
                        action['title']
                    ) for action in notification_data.actions
                ]

            # Send message
            result = messaging.send(message)
            logger.info(f"Android notification sent successfully: {result}")
            return True

        except Exception as e:
            logger.error(f"Failed to send Android notification: {str(e)}")
            return False

    def _send_ios_notification(self, token: str, notification_data: NotificationData) -> bool:
        """Send iOS notification via APNs"""
        try:
            if not self.firebase_app:
                logger.error("Firebase not initialized - cannot send iOS notification")
                return False

            # Create message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=notification_data.title,
                    body=notification_data.body,
                    image_url=notification_data.image_url
                ),
                data=notification_data.data,
                token=token,
                apns=messaging.APNSConfig(
                    headers={
                        'apns-priority': self._get_apns_priority(notification_data.priority),
                        'apns-expiration': str(int((datetime.utcnow() + timedelta(days=1)).timestamp()))
                    },
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            alert=messaging.ApsAlert(
                                title=notification_data.title,
                                body=notification_data.body
                            ),
                            badge=notification_data.badge,
                            sound=notification_data.sound,
                            content_available=True,
                            mutable_content=True,
                            category=notification_data.type.value
                        ),
                        custom_data=notification_data.data
                    )
                )
            )

            # Send message
            result = messaging.send(message)
            logger.info(f"iOS notification sent successfully: {result}")
            return True

        except Exception as e:
            logger.error(f"Failed to send iOS notification: {str(e)}")
            return False

    def _get_android_priority(self, priority: NotificationPriority) -> str:
        """Get Android priority string"""
        priority_map = {
            NotificationPriority.LOW: 'normal',
            NotificationPriority.NORMAL: 'normal',
            NotificationPriority.HIGH: 'high',
            NotificationPriority.CRITICAL: 'high'
        }
        return priority_map.get(priority, 'normal')

    def _get_apns_priority(self, priority: NotificationPriority) -> str:
        """Get APNs priority string"""
        priority_map = {
            NotificationPriority.LOW: '5',
            NotificationPriority.NORMAL: '5',
            NotificationPriority.HIGH: '10',
            NotificationPriority.CRITICAL: '10'
        }
        return priority_map.get(priority, '5')

    def send_game_invite_notification(self, inviter_name: str, session_name: str, user_ids: List[str], session_id: str) -> bool:
        """Send game invitation notification"""
        try:
            notification = NotificationData(
                title="Game Invitation",
                body=f"{inviter_name} invited you to join \"{session_name}\"",
                data={
                    'type': NotificationType.GAME_INVITE.value,
                    'session_id': session_id,
                    'session_name': session_name,
                    'inviter_name': inviter_name
                },
                type=NotificationType.GAME_INVITE,
                priority=NotificationPriority.HIGH,
                sound='game_invite.wav'
            )

            request = NotificationRequest(
                user_ids=user_ids,
                notification=notification
            )

            result = self.send_notification(request)
            return result['success'] > 0

        except Exception as e:
            logger.error(f"Failed to send game invite notification: {str(e)}")
            return False

    def send_friend_request_notification(self, from_user: str, user_ids: List[str], from_user_id: str) -> bool:
        """Send friend request notification"""
        try:
            notification = NotificationData(
                title="Friend Request",
                body=f"{from_user} sent you a friend request",
                data={
                    'type': NotificationType.FRIEND_REQUEST.value,
                    'from_user': from_user,
                    'from_user_id': from_user_id
                },
                type=NotificationType.FRIEND_REQUEST,
                priority=NotificationPriority.NORMAL,
                sound='friend_request.wav'
            )

            request = NotificationRequest(
                user_ids=user_ids,
                notification=notification
            )

            result = self.send_notification(request)
            return result['success'] > 0

        except Exception as e:
            logger.error(f"Failed to send friend request notification: {str(e)}")
            return False

    def send_achievement_notification(self, achievement_name: str, description: str, user_ids: List[str]) -> bool:
        """Send achievement unlocked notification"""
        try:
            notification = NotificationData(
                title="Achievement Unlocked!",
                body=f"{achievement_name}: {description}",
                data={
                    'type': NotificationType.ACHIEVEMENT.value,
                    'achievement_name': achievement_name,
                    'description': description
                },
                type=NotificationType.ACHIEVEMENT,
                priority=NotificationPriority.HIGH,
                sound='achievement.wav'
            )

            request = NotificationRequest(
                user_ids=user_ids,
                notification=notification
            )

            result = self.send_notification(request)
            return result['success'] > 0

        except Exception as e:
            logger.error(f"Failed to send achievement notification: {str(e)}")
            return False

    def send_chat_notification(self, channel_name: str, sender_name: str, message: str, user_ids: List[str], channel_id: str) -> bool:
        """Send chat message notification"""
        try:
            # Truncate message if too long
            truncated_message = message[:100] + ("..." if len(message) > 100 else "")

            notification = NotificationData(
                title=channel_name,
                body=f"{sender_name}: {truncated_message}",
                data={
                    'type': NotificationType.CHAT_MESSAGE.value,
                    'channel_name': channel_name,
                    'sender_name': sender_name,
                    'channel_id': channel_id,
                    'message': message
                },
                type=NotificationType.CHAT_MESSAGE,
                priority=NotificationPriority.LOW,
                sound='chat_message.wav'
            )

            request = NotificationRequest(
                user_ids=user_ids,
                notification=notification
            )

            result = self.send_notification(request)
            return result['success'] > 0

        except Exception as e:
            logger.error(f"Failed to send chat notification: {str(e)}")
            return False

    def send_game_event_notification(self, session_name: str, event: str, user_ids: List[str], session_id: str) -> bool:
        """Send game event notification"""
        try:
            notification = NotificationData(
                title="Game Event",
                body=f"{session_name}: {event}",
                data={
                    'type': NotificationType.GAME_EVENT.value,
                    'session_name': session_name,
                    'event': event,
                    'session_id': session_id
                },
                type=NotificationType.GAME_EVENT,
                priority=NotificationPriority.NORMAL,
                sound='game_event.wav'
            )

            request = NotificationRequest(
                user_ids=user_ids,
                notification=notification
            )

            result = self.send_notification(request)
            return result['success'] > 0

        except Exception as e:
            logger.error(f"Failed to send game event notification: {str(e)}")
            return False

    def cleanup_inactive_tokens(self, days: int = 30) -> int:
        """Clean up inactive tokens older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            removed_count = 0

            for user_id, token_list in self.tokens.items():
                original_count = len(token_list)
                self.tokens[user_id] = [
                    token for token in token_list
                    if token.created_at > cutoff_date or token.is_active
                ]
                removed_count += original_count - len(self.tokens[user_id])

                # Remove user entry if no tokens left
                if not self.tokens[user_id]:
                    del self.tokens[user_id]

            logger.info(f"Cleaned up {removed_count} inactive tokens")
            return removed_count

        except Exception as e:
            logger.error(f"Failed to cleanup inactive tokens: {str(e)}")
            return 0

    def get_user_tokens(self, user_id: str) -> List[PushToken]:
        """Get all tokens for a user"""
        return self.tokens.get(user_id, [])

    def get_token_stats(self) -> Dict[str, Any]:
        """Get token statistics"""
        try:
            total_tokens = sum(len(tokens) for tokens in self.tokens.values())
            active_tokens = sum(
                len([t for t in tokens if t.is_active])
                for tokens in self.tokens.values()
            )
            android_tokens = sum(
                len([t for t in tokens if t.platform == 'android' and t.is_active])
                for tokens in self.tokens.values()
            )
            ios_tokens = sum(
                len([t for t in tokens if t.platform == 'ios' and t.is_active])
                for tokens in self.tokens.values()
            )

            return {
                'total_users': len(self.tokens),
                'total_tokens': total_tokens,
                'active_tokens': active_tokens,
                'android_tokens': android_tokens,
                'ios_tokens': ios_tokens,
                'inactive_tokens': total_tokens - active_tokens
            }

        except Exception as e:
            logger.error(f"Failed to get token stats: {str(e)}")
            return {}

# Global push service instance
push_service = PushNotificationService()

# API Endpoints
@push_bp.route('/register', methods=['POST'])
def register_push_token():
    """Register a new push token"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        token = data.get('token')
        platform = data.get('platform')
        device_id = data.get('device_id')
        app_version = data.get('app_version', '1.0.0')

        if not all([user_id, token, platform, device_id]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400

        success = push_service.register_token(user_id, token, platform, device_id, app_version)

        if success:
            return jsonify({
                'success': True,
                'message': 'Push token registered successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to register push token'
            }), 500

    except Exception as e:
        logger.error(f"Register token error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@push_bp.route('/unregister', methods=['POST'])
def unregister_push_token():
    """Unregister a push token"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        token = data.get('token')

        if not all([user_id, token]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400

        success = push_service.remove_token(user_id, token)

        if success:
            return jsonify({
                'success': True,
                'message': 'Push token unregistered successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to unregister push token'
            }), 500

    except Exception as e:
        logger.error(f"Unregister token error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@push_bp.route('/stats', methods=['GET'])
def get_push_stats():
    """Get push notification statistics"""
    try:
        stats = push_service.get_token_stats()
        return jsonify({
            'success': True,
            'data': stats
        })

    except Exception as e:
        logger.error(f"Get stats error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@push_bp.route('/cleanup', methods=['POST'])
def cleanup_tokens():
    """Clean up inactive tokens"""
    try:
        data = request.get_json() or {}
        days = data.get('days', 30)

        removed_count = push_service.cleanup_inactive_tokens(days)

        return jsonify({
            'success': True,
            'data': {
                'removed_tokens': removed_count
            },
            'message': f'Cleaned up {removed_count} inactive tokens'
        })

    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

# Test endpoints
@push_bp.route('/test', methods=['POST'])
def test_notification():
    """Send test notification"""
    try:
        data = request.get_json()
        user_ids = data.get('user_ids', [])
        title = data.get('title', 'Test Notification')
        body = data.get('body', 'This is a test notification')

        if not user_ids:
            return jsonify({
                'success': False,
                'error': 'No user IDs provided'
            }), 400

        notification = NotificationData(
            title=title,
            body=body,
            data={'test': 'true'},
            type=NotificationType.SYSTEM,
            priority=NotificationPriority.NORMAL
        )

        request = NotificationRequest(
            user_ids=user_ids,
            notification=notification
        )

        result = push_service.send_notification(request)

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        logger.error(f"Test notification error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

if __name__ == '__main__':
    # Create Flask app for testing
    app = Flask(__name__)
    app.register_blueprint(push_bp)

    # Add some test data
    push_service.register_token(
        'test_user_1',
        'test_token_1_android',
        'android',
        'device_1',
        '1.0.0'
    )
    push_service.register_token(
        'test_user_2',
        'test_token_1_ios',
        'ios',
        'device_2',
        '1.0.0'
    )

    app.run(host='0.0.0.0', port=3002, debug=True)