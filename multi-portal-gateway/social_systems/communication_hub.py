#!/usr/bin/env python3
"""
DMLogn8n Communication Hub - Comprehensive Chat and Messaging System

Handles real-time chat, voice communication, message boards, notifications,
private messaging, group communication, and social interactions.

Features:
- Real-time chat with multiple channel types
- Voice chat integration and management
- Private messaging system
- Group and party chat
- Guild communication channels
- Message boards and forums
- Notification system with priorities
- Proximity-based chat
- Cross-server communication
- Chat moderation and filtering
- Message history and search
- Emote and emoji support
- File sharing and media handling
"""

import asyncio
import json
import logging
import time
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import uuid
import base64
from collections import defaultdict, deque
import html

class ChannelType(Enum):
    """Types of communication channels"""
    GLOBAL = "global"           # Server-wide chat
    TRADE = "trade"             # Trading chat
    HELP = "help"               # Help and questions
    LFG = "lfg"                 # Looking for group
    PARTY = "party"             # Party chat
    GUILD = "guild"             # Guild chat
    OFFICER = "officer"         # Guild officer chat
    PRIVATE = "private"         # Private messages
    PROXIMITY = "proximity"     # Location-based chat
    SYSTEM = "system"           # System messages
    ANNOUNCEMENT = "announcement" # Server announcements
    WHISPER = "whisper"         # Direct whispers
    YELL = "yell"               # Area-wide messages
    EMOTE = "emote"             # Roleplay emotes
    ROLEPLAY = "roleplay"       # Roleplay channel

class MessageType(Enum):
    """Types of messages"""
    TEXT = "text"
    EMOTE = "emote"
    SYSTEM = "system"
    WHISPER = "whisper"
    PARTY = "party"
    GUILD = "guild"
    ANNOUNCEMENT = "announcement"
    FILE = "file"
    IMAGE = "image"
    VOICE = "voice"
    LINK = "link"
    COMMAND = "command"

class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5

class ModerationAction(Enum):
    """Moderation actions"""
    WARNING = "warning"
    MUTE = "mute"
    TIMEOUT = "timeout"
    KICK = "kick"
    BAN = "ban"
    DELETE_MESSAGE = "delete"
    FILTER = "filter"

@dataclass
class ChatMessage:
    """Individual chat message"""
    id: str
    sender_id: str
    sender_name: str
    channel_id: str
    channel_type: ChannelType
    message_type: MessageType
    content: str
    timestamp: datetime
    edited: bool = False
    edit_timestamp: Optional[datetime] = None
    deleted: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    mentions: List[str] = field(default_factory=list)
    reactions: Dict[str, Set[str]] = field(default_factory=dict)
    attachments: List[Dict] = field(default_factory=list)
    moderation_flags: List[str] = field(default_factory=list)
    read_by: Set[str] = field(default_factory=set)

@dataclass
class ChatChannel:
    """Chat channel configuration"""
    id: str
    name: str
    channel_type: ChannelType
    description: str
    members: Set[str] = field(default_factory=set)
    moderators: Set[str] = field(default_factory=set)
    permissions: Dict[str, List[str]] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    created_date: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    message_history: List[str] = field(default_factory=list)
    max_history: int = 1000
    is_private: bool = False
    password: Optional[str] = None
    temporary: bool = False
    expires_date: Optional[datetime] = None

@dataclass
class VoiceSession:
    """Voice chat session"""
    id: str
    channel_id: str
    participants: Dict[str, Dict] = field(default_factory=dict)
    leader_id: str
    quality: str = "standard"  # standard, high, ultra
    max_participants: int = 8
    created_date: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    is_recording: bool = False
    settings: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Notification:
    """System notification"""
    id: str
    recipient_id: str
    title: str
    message: str
    priority: NotificationPriority
    notification_type: str
    created_date: datetime = field(default_factory=datetime.now)
    read: bool = False
    read_date: Optional[datetime] = None
    expires_date: Optional[datetime] = None
    data: Dict[str, Any] = field(default_factory=dict)
    actions: List[Dict] = field(default_factory=list)

@dataclass
class MessageFilter:
    """Message filtering rule"""
    id: str
    name: str
    pattern: str
    action: ModerationAction
    enabled: bool = True
    priority: int = 0
    applies_to: List[ChannelType] = field(default_factory=list)
    created_by: str
    created_date: datetime = field(default_factory=datetime.now)
    match_count: int = 0

class CommunicationHub:
    """Main communication management system"""

    def __init__(self, database=None, config=None):
        self.logger = logging.getLogger(__name__)
        self.db = database
        self.config = config or self._default_config()

        # Core data structures
        self.messages: Dict[str, ChatMessage] = {}
        self.channels: Dict[str, ChatChannel] = {}
        self.voice_sessions: Dict[str, VoiceSession] = {}
        self.notifications: Dict[str, List[Notification]] = defaultdict(list)
        self.filters: Dict[str, MessageFilter] = {}

        # User sessions and connections
        self.user_sessions: Dict[str, Dict] = {}
        self.channel_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        self.voice_connections: Dict[str, str] = defaultdict(str)  # user_id -> voice_session_id

        # Proximity tracking
        self.user_locations: Dict[str, Tuple[float, float, str]] = {}  # user_id -> (x, y, zone_id)

        # Moderation data
        self.moderated_users: Dict[str, Dict] = {}
        self.reported_messages: Dict[str, List[Dict]] = defaultdict(list)

        # Background tasks
        self._running = False
        self._background_tasks: List[asyncio.Task] = []

    def _default_config(self) -> Dict:
        """Default configuration settings"""
        return {
            "max_message_length": 1000,
            "message_rate_limit": 10,  # messages per minute
            "max_channel_members": 1000,
            "voice_quality_levels": ["standard", "high", "ultra"],
            "default_voice_quality": "standard",
            "notification_retention_days": 30,
            "message_history_retention_days": 90,
            "proximity_chat_range": 50,
            "yell_range": 200,
            "whisper_range": 10,
            "max_voice_participants": 8,
            "auto_mute_threshold": 5,  # reports
            "profanity_filter_enabled": True,
            "link_filter_enabled": True,
            "emoji_enabled": True,
            "file_sharing_enabled": True,
            "max_file_size_mb": 10,
            "allowed_file_types": [".jpg", ".png", ".gif", ".txt", ".pdf"],
            "spam_detection_enabled": True,
            "spam_threshold": 10,  # similar messages in short time
            "spam_time_window": 60,  # seconds
            "channel_creation_cooldown": 300  # seconds
        }

    async def create_channel(self, creator_id: str, channel_data: Dict) -> Dict:
        """Create a new chat channel"""
        try:
            # Validate channel creation
            validation_result = await self._validate_channel_creation(creator_id, channel_data)
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["error"]}

            # Generate channel ID
            channel_id = str(uuid.uuid4())

            # Create channel
            channel = ChatChannel(
                id=channel_id,
                name=channel_data["name"],
                channel_type=ChannelType(channel_data["type"]),
                description=channel_data.get("description", ""),
                members=set([creator_id]),
                moderators=set([creator_id]),
                settings=channel_data.get("settings", {}),
                is_private=channel_data.get("private", False),
                password=self._hash_password(channel_data.get("password")) if channel_data.get("password") else None,
                temporary=channel_data.get("temporary", False),
                expires_date=datetime.fromisoformat(channel_data["expires_date"]) if channel_data.get("expires_date") else None
            )

            # Set default permissions based on channel type
            channel.permissions = await self._get_default_permissions(channel.channel_type, creator_id)

            # Store channel
            self.channels[channel_id] = channel
            self.channel_subscriptions[channel_id].add(creator_id)

            # Send system message to channel
            await self._send_system_message(
                channel_id,
                f"Channel '{channel.name}' created by {await self._get_player_name(creator_id)}",
                {"creator_id": creator_id}
            )

            self.logger.info(f"Channel '{channel.name}' created by {creator_id}")

            return {
                "success": True,
                "channel_id": channel_id,
                "channel": asdict(channel),
                "message": f"Channel '{channel.name}' created successfully"
            }

        except Exception as e:
            self.logger.error(f"Error creating channel: {e}")
            return {"success": False, "error": str(e)}

    async def send_message(self, sender_id: str, channel_id: str, content: str, message_type: MessageType = MessageType.TEXT,
                          metadata: Dict = None) -> Dict:
        """Send a message to a channel"""
        try:
            # Validate message
            validation_result = await self._validate_message(sender_id, channel_id, content)
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["error"]}

            channel = self.channels[channel_id]

            # Check rate limiting
            if not await self._check_rate_limit(sender_id):
                return {"success": False, "error": "Rate limit exceeded. Please wait before sending another message."}

            # Apply filters
            filter_result = await self._apply_message_filters(content, channel.channel_type)
            if filter_result["blocked"]:
                return {"success": False, "error": "Message blocked by content filter"}

            # Process content
            processed_content = await self._process_message_content(content, message_type)

            # Create message
            message = ChatMessage(
                id=str(uuid.uuid4()),
                sender_id=sender_id,
                sender_name=await self._get_player_name(sender_id),
                channel_id=channel_id,
                channel_type=channel.channel_type,
                message_type=message_type,
                content=processed_content["content"],
                timestamp=datetime.now(),
                metadata=metadata or {},
                mentions=processed_content["mentions"]
            )

            # Store message
            self.messages[message.id] = message
            channel.message_history.append(message.id)
            channel.last_activity = datetime.now()

            # Limit history size
            if len(channel.message_history) > channel.max_history:
                old_message_id = channel.message_history.pop(0)
                if old_message_id in self.messages:
                    del self.messages[old_message_id]

            # Mark as read by sender
            message.read_by.add(sender_id)

            # Broadcast to channel subscribers
            await self._broadcast_message(message, channel_id)

            # Handle special message types
            if message_type == MessageType.WHISPER:
                await self._handle_whisper_message(message)
            elif message_type == MessageType.YELL:
                await self._handle_yell_message(message)
            elif message_type == MessageType.EMOTE:
                await self._handle_emote_message(message)

            # Update user activity
            self._update_user_activity(sender_id)

            self.logger.info(f"Message sent to channel {channel_id} by {sender_id}")

            return {
                "success": True,
                "message_id": message.id,
                "message": asdict(message),
                "filtered": filter_result["filtered"]
            }

        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return {"success": False, "error": str(e)}

    async def send_private_message(self, sender_id: str, recipient_id: str, content: str, metadata: Dict = None) -> Dict:
        """Send a private message to another user"""
        try:
            # Validate recipients
            if not await self._player_exists(recipient_id):
                return {"success": False, "error": "Recipient not found"}

            if sender_id == recipient_id:
                return {"success": False, "error": "Cannot send private message to yourself"}

            # Check if sender is blocked by recipient
            if await self._is_blocked(sender_id, recipient_id):
                return {"success": False, "error": "Unable to send message"}

            # Create private channel (or get existing one)
            channel_id = await self._get_or_create_private_channel(sender_id, recipient_id)

            # Send message
            return await self.send_message(
                sender_id, channel_id, content, MessageType.PRIVATE, metadata
            )

        except Exception as e:
            self.logger.error(f"Error sending private message: {e}")
            return {"success": False, "error": str(e)}

    async def create_voice_session(self, creator_id: str, channel_id: str, settings: Dict = None) -> Dict:
        """Create a voice chat session"""
        try:
            # Validate voice session creation
            if channel_id not in self.channels:
                return {"success": False, "error": "Channel not found"}

            channel = self.channels[channel_id]
            if creator_id not in channel.members:
                return {"success": False, "error": "Not a member of this channel"}

            # Check if user is already in a voice session
            if creator_id in self.voice_connections:
                return {"success": False, "error": "Already in a voice session"}

            # Create voice session
            voice_session = VoiceSession(
                id=str(uuid.uuid4()),
                channel_id=channel_id,
                leader_id=creator_id,
                participants={
                    creator_id: {
                        "joined_date": datetime.now(),
                        "speaking": False,
                        "muted": False,
                        "deafened": False
                    }
                },
                quality=settings.get("quality", self.config["default_voice_quality"]),
                max_participants=settings.get("max_participants", self.config["max_voice_participants"]),
                settings=settings or {}
            )

            # Store voice session
            self.voice_sessions[voice_session.id] = voice_session
            self.voice_connections[creator_id] = voice_session.id

            # Send system message
            await self._send_system_message(
                channel_id,
                f"Voice session started by {await self._get_player_name(creator_id)}",
                {"session_id": voice_session.id, "leader": creator_id}
            )

            self.logger.info(f"Voice session {voice_session.id} created in channel {channel_id}")

            return {
                "success": True,
                "session_id": voice_session.id,
                "session": asdict(voice_session),
                "message": "Voice session created successfully"
            }

        except Exception as e:
            self.logger.error(f"Error creating voice session: {e}")
            return {"success": False, "error": str(e)}

    async def join_voice_session(self, user_id: str, session_id: str) -> Dict:
        """Join a voice chat session"""
        try:
            if session_id not in self.voice_sessions:
                return {"success": False, "error": "Voice session not found"}

            if user_id in self.voice_connections:
                return {"success": False, "error": "Already in a voice session"}

            voice_session = self.voice_sessions[session_id]
            channel = self.channels[voice_session.channel_id]

            # Check if user is channel member
            if user_id not in channel.members:
                return {"success": False, "error": "Not a member of this channel"}

            # Check session capacity
            if len(voice_session.participants) >= voice_session.max_participants:
                return {"success": False, "error": "Voice session is full"}

            # Add participant
            voice_session.participants[user_id] = {
                "joined_date": datetime.now(),
                "speaking": False,
                "muted": False,
                "deafened": False
            }
            self.voice_connections[user_id] = session_id

            # Send system message
            await self._send_system_message(
                voice_session.channel_id,
                f"{await self._get_player_name(user_id)} joined the voice session",
                {"session_id": session_id, "user_id": user_id}
            )

            self.logger.info(f"User {user_id} joined voice session {session_id}")

            return {
                "success": True,
                "session_id": session_id,
                "message": "Joined voice session successfully"
            }

        except Exception as e:
            self.logger.error(f"Error joining voice session: {e}")
            return {"success": False, "error": str(e)}

    async def leave_voice_session(self, user_id: str) -> Dict:
        """Leave current voice session"""
        try:
            if user_id not in self.voice_connections:
                return {"success": False, "error": "Not in a voice session"}

            session_id = self.voice_connections[user_id]
            voice_session = self.voice_sessions[session_id]

            # Remove participant
            if user_id in voice_session.participants:
                del voice_session.participants[user_id]

            del self.voice_connections[user_id]

            # Send system message
            await self._send_system_message(
                voice_session.channel_id,
                f"{await self._get_player_name(user_id)} left the voice session",
                {"session_id": session_id, "user_id": user_id}
            )

            # Clean up empty sessions
            if len(voice_session.participants) == 0:
                del self.voice_sessions[session_id]
                await self._send_system_message(
                    voice_session.channel_id,
                    "Voice session ended",
                    {"session_id": session_id}
                )

            self.logger.info(f"User {user_id} left voice session {session_id}")

            return {
                "success": True,
                "message": "Left voice session successfully"
            }

        except Exception as e:
            self.logger.error(f"Error leaving voice session: {e}")
            return {"success": False, "error": str(e)}

    async def send_notification(self, recipient_id: str, title: str, message: str, priority: NotificationPriority,
                               notification_type: str, data: Dict = None, actions: List[Dict] = None) -> Dict:
        """Send a notification to a user"""
        try:
            notification = Notification(
                id=str(uuid.uuid4()),
                recipient_id=recipient_id,
                title=title,
                message=message,
                priority=priority,
                notification_type=notification_type,
                data=data or {},
                actions=actions or [],
                expires_date=datetime.now() + timedelta(days=self.config["notification_retention_days"])
            )

            # Store notification
            self.notifications[recipient_id].append(notification)

            # Send to user if online
            if recipient_id in self.user_sessions:
                await self._send_notification_to_user(recipient_id, notification)

            self.logger.info(f"Notification sent to {recipient_id}: {title}")

            return {
                "success": True,
                "notification_id": notification.id,
                "message": "Notification sent successfully"
            }

        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")
            return {"success": False, "error": str(e)}

    async def subscribe_to_channel(self, user_id: str, channel_id: str) -> Dict:
        """Subscribe a user to a channel"""
        try:
            if channel_id not in self.channels:
                return {"success": False, "error": "Channel not found"}

            channel = self.channels[channel_id]

            # Check permissions
            if not await self._can_access_channel(user_id, channel):
                return {"success": False, "error": "No permission to access this channel"}

            # Add subscription
            self.channel_subscriptions[channel_id].add(user_id)

            self.logger.info(f"User {user_id} subscribed to channel {channel_id}")

            return {
                "success": True,
                "message": "Subscribed to channel successfully"
            }

        except Exception as e:
            self.logger.error(f"Error subscribing to channel: {e}")
            return {"success": False, "error": str(e)}

    async def unsubscribe_from_channel(self, user_id: str, channel_id: str) -> Dict:
        """Unsubscribe a user from a channel"""
        try:
            self.channel_subscriptions[channel_id].discard(user_id)

            self.logger.info(f"User {user_id} unsubscribed from channel {channel_id}")

            return {
                "success": True,
                "message": "Unsubscribed from channel successfully"
            }

        except Exception as e:
            self.logger.error(f"Error unsubscribing from channel: {e}")
            return {"success": False, "error": str(e)}

    async def edit_message(self, user_id: str, message_id: str, new_content: str) -> Dict:
        """Edit a message"""
        try:
            if message_id not in self.messages:
                return {"success": False, "error": "Message not found"}

            message = self.messages[message_id]

            # Check permissions
            if message.sender_id != user_id:
                return {"success": False, "error": "Can only edit your own messages"}

            # Check edit time limit (e.g., 15 minutes)
            if datetime.now() - message.timestamp > timedelta(minutes=15):
                return {"success": False, "error": "Message can no longer be edited"}

            # Process new content
            processed_content = await self._process_message_content(new_content, message.message_type)

            # Update message
            message.content = processed_content["content"]
            message.edited = True
            message.edit_timestamp = datetime.now()
            message.mentions = processed_content["mentions"]

            # Broadcast edit
            await self._broadcast_message_edit(message)

            self.logger.info(f"Message {message_id} edited by {user_id}")

            return {
                "success": True,
                "message": "Message edited successfully"
            }

        except Exception as e:
            self.logger.error(f"Error editing message: {e}")
            return {"success": False, "error": str(e)}

    async def delete_message(self, user_id: str, message_id: str, reason: str = "") -> Dict:
        """Delete a message"""
        try:
            if message_id not in self.messages:
                return {"success": False, "error": "Message not found"}

            message = self.messages[message_id]
            channel = self.channels[message.channel_id]

            # Check permissions
            is_sender = message.sender_id == user_id
            is_moderator = user_id in channel.moderators
            is_admin = await self._is_admin(user_id)

            if not (is_sender or is_moderator or is_admin):
                return {"success": False, "error": "No permission to delete this message"}

            # Mark as deleted
            message.deleted = True

            # Add moderation note if not sender
            if not is_sender:
                message.moderation_flags.append(f"Deleted by {await self._get_player_name(user_id)}: {reason}")

            # Broadcast deletion
            await self._broadcast_message_deletion(message)

            self.logger.info(f"Message {message_id} deleted by {user_id}")

            return {
                "success": True,
                "message": "Message deleted successfully"
            }

        except Exception as e:
            self.logger.error(f"Error deleting message: {e}")
            return {"success": False, "error": str(e)}

    async def get_channel_history(self, channel_id: str, user_id: str, limit: int = 50, before: str = None) -> Dict:
        """Get message history for a channel"""
        try:
            if channel_id not in self.channels:
                return {"success": False, "error": "Channel not found"}

            channel = self.channels[channel_id]

            # Check permissions
            if not await self._can_access_channel(user_id, channel):
                return {"success": False, "error": "No permission to access this channel"}

            # Get message IDs
            message_ids = channel.message_history.copy()
            if before:
                try:
                    before_index = message_ids.index(before)
                    message_ids = message_ids[:before_index]
                except ValueError:
                    pass

            # Limit and get messages
            message_ids = message_ids[-limit:]
            messages = []

            for msg_id in message_ids:
                if msg_id in self.messages:
                    msg = self.messages[msg_id]
                    if not msg.deleted:
                        messages.append(asdict(msg))

            return {
                "success": True,
                "messages": messages,
                "channel_id": channel_id,
                "total_count": len(messages)
            }

        except Exception as e:
            self.logger.error(f"Error getting channel history: {e}")
            return {"success": False, "error": str(e)}

    async def get_user_notifications(self, user_id: str, unread_only: bool = False, limit: int = 50) -> Dict:
        """Get notifications for a user"""
        try:
            notifications = self.notifications.get(user_id, [])

            # Filter
            if unread_only:
                notifications = [n for n in notifications if not n.read]

            # Sort by priority and date
            notifications.sort(key=lambda n: (n.priority.value, n.created_date), reverse=True)

            # Limit
            notifications = notifications[:limit]

            return {
                "success": True,
                "notifications": [asdict(n) for n in notifications],
                "total_count": len(notifications),
                "unread_count": len([n for n in notifications if not n.read])
            }

        except Exception as e:
            self.logger.error(f"Error getting notifications: {e}")
            return {"success": False, "error": str(e)}

    async def mark_notification_read(self, user_id: str, notification_id: str) -> Dict:
        """Mark a notification as read"""
        try:
            notifications = self.notifications.get(user_id, [])

            for notification in notifications:
                if notification.id == notification_id and not notification.read:
                    notification.read = True
                    notification.read_date = datetime.now()
                    break

            return {
                "success": True,
                "message": "Notification marked as read"
            }

        except Exception as e:
            self.logger.error(f"Error marking notification read: {e}")
            return {"success": False, "error": str(e)}

    async def update_user_location(self, user_id: str, x: float, y: float, zone_id: str):
        """Update user location for proximity chat"""
        self.user_locations[user_id] = (x, y, zone_id)

    async def get_nearby_users(self, user_id: str, range_distance: float = None) -> List[str]:
        """Get users within proximity chat range"""
        if user_id not in self.user_locations:
            return []

        user_x, user_y, user_zone = self.user_locations[user_id]
        range_distance = range_distance or self.config["proximity_chat_range"]

        nearby_users = []
        for other_id, (other_x, other_y, other_zone) in self.user_locations.items():
            if other_id != user_id and other_zone == user_zone:
                distance = math.sqrt((user_x - other_x)**2 + (user_y - other_y)**2)
                if distance <= range_distance:
                    nearby_users.append(other_id)

        return nearby_users

    async def get_channel_info(self, channel_id: str, user_id: str) -> Dict:
        """Get detailed channel information"""
        try:
            if channel_id not in self.channels:
                return {"success": False, "error": "Channel not found"}

            channel = self.channels[channel_id]

            # Check permissions
            if not await self._can_access_channel(user_id, channel):
                return {"success": False, "error": "No permission to access this channel"}

            # Get additional info
            member_count = len(channel.members)
            is_moderator = user_id in channel.moderators
            is_subscribed = user_id in self.channel_subscriptions[channel_id]

            # Get recent activity
            recent_messages = []
            for msg_id in channel.message_history[-5:]:
                if msg_id in self.messages:
                    recent_messages.append({
                        "id": msg_id,
                        "sender": self.messages[msg_id].sender_name,
                        "content": self.messages[msg_id].content[:100] + "..." if len(self.messages[msg_id].content) > 100 else self.messages[msg_id].content,
                        "timestamp": self.messages[msg_id].timestamp.isoformat()
                    })

            channel_info = {
                "id": channel.id,
                "name": channel.name,
                "type": channel.channel_type.value,
                "description": channel.description,
                "member_count": member_count,
                "created_date": channel.created_date.isoformat(),
                "last_activity": channel.last_activity.isoformat(),
                "is_private": channel.is_private,
                "is_moderator": is_moderator,
                "is_subscribed": is_subscribed,
                "recent_messages": recent_messages
            }

            return {
                "success": True,
                "channel": channel_info
            }

        except Exception as e:
            self.logger.error(f"Error getting channel info: {e}")
            return {"success": False, "error": str(e)}

    # Helper methods

    async def _validate_channel_creation(self, creator_id: str, channel_data: Dict) -> Dict:
        """Validate channel creation requirements"""
        try:
            # Check if player exists
            if not await self._player_exists(creator_id):
                return {"valid": False, "error": "Player not found"}

            # Validate channel type
            channel_type = channel_data.get("type")
            if not channel_type or channel_type not in [t.value for t in ChannelType]:
                return {"valid": False, "error": "Invalid channel type"}

            # Validate channel name
            name = channel_data.get("name", "").strip()
            if len(name) < 3:
                return {"valid": False, "error": "Channel name too short"}
            if len(name) > 50:
                return {"valid": False, "error": "Channel name too long"}

            # Check for name conflicts
            for channel in self.channels.values():
                if channel.name.lower() == name.lower():
                    return {"valid": False, "error": "Channel name already exists"}

            # Check cooldown
            user_channels = [c for c in self.channels.values() if creator_id in c.moderators]
            recent_channels = [
                c for c in user_channels
                if datetime.now() - c.created_date < timedelta(seconds=self.config["channel_creation_cooldown"])
            ]
            if recent_channels:
                return {"valid": False, "error": "Please wait before creating another channel"}

            return {"valid": True}

        except Exception as e:
            self.logger.error(f"Error validating channel creation: {e}")
            return {"valid": False, "error": str(e)}

    async def _validate_message(self, sender_id: str, channel_id: str, content: str) -> Dict:
        """Validate message before sending"""
        try:
            # Check if channel exists
            if channel_id not in self.channels:
                return {"valid": False, "error": "Channel not found"}

            channel = self.channels[channel_id]

            # Check if user can access channel
            if not await self._can_access_channel(sender_id, channel):
                return {"valid": False, "error": "No permission to access this channel"}

            # Check if user is muted
            if await self._is_muted(sender_id):
                return {"valid": False, "error": "You are muted"}

            # Validate content
            if len(content.strip()) == 0:
                return {"valid": False, "error": "Message cannot be empty"}

            if len(content) > self.config["max_message_length"]:
                return {"valid": False, "error": "Message too long"}

            return {"valid": True}

        except Exception as e:
            self.logger.error(f"Error validating message: {e}")
            return {"valid": False, "error": str(e)}

    async def _check_rate_limit(self, user_id: str) -> bool:
        """Check if user is within rate limits"""
        if not self.config["spam_detection_enabled"]:
            return True

        # Get recent messages from user
        now = datetime.now()
        recent_messages = [
            msg for msg in self.messages.values()
            if msg.sender_id == user_id and (now - msg.timestamp).total_seconds() < 60
        ]

        return len(recent_messages) < self.config["message_rate_limit"]

    async def _apply_message_filters(self, content: str, channel_type: ChannelType) -> Dict:
        """Apply content filters to message"""
        filtered = False
        blocked = False

        # Check profanity filter
        if self.config["profanity_filter_enabled"]:
            profanity_result = await self._check_profanity(content)
            if profanity_result["filtered"]:
                filtered = True
                content = profanity_result["content"]
                if profanity_result["blocked"]:
                    blocked = True

        # Check link filter
        if self.config["link_filter_enabled"] and channel_type not in [ChannelType.PRIVATE, ChannelType.SYSTEM]:
            link_result = await self._check_links(content)
            if link_result["blocked"]:
                blocked = True

        # Check custom filters
        for filter_rule in self.filters.values():
            if filter_rule.enabled and (not filter_rule.applies_to or channel_type in filter_rule.applies_to):
                if re.search(filter_rule.pattern, content, re.IGNORECASE):
                    filter_rule.match_count += 1
                    if filter_rule.action in [ModerationAction.DELETE_MESSAGE, ModerationAction.BAN]:
                        blocked = True
                    elif filter_rule.action == ModerationAction.FILTER:
                        filtered = True
                        content = re.sub(filter_rule.pattern, "***", content, flags=re.IGNORECASE)

        return {
            "filtered": filtered,
            "blocked": blocked,
            "content": content
        }

    async def _process_message_content(self, content: str, message_type: MessageType) -> Dict:
        """Process and format message content"""
        mentions = []

        # Extract mentions (@username)
        mention_pattern = r'@(\w+)'
        mention_matches = re.findall(mention_pattern, content)
        for username in mention_matches:
            user_id = await self._get_player_id_by_name(username)
            if user_id:
                mentions.append(user_id)

        # Process markdown if enabled
        processed_content = content

        # Escape HTML
        processed_content = html.escape(processed_content)

        # Convert line breaks
        processed_content = processed_content.replace('\n', '<br>')

        # Process mentions
        for username in mention_matches:
            user_id = await self._get_player_id_by_name(username)
            if user_id:
                processed_content = processed_content.replace(f"@{username}", f'<span class="mention" data-user="{user_id}">@{username}</span>')

        # Process emotes if enabled
        if self.config["emoji_enabled"]:
            processed_content = await self._process_emotes(processed_content)

        return {
            "content": processed_content,
            "mentions": mentions
        }

    async def _broadcast_message(self, message: ChatMessage, channel_id: str):
        """Broadcast message to channel subscribers"""
        subscribers = self.channel_subscriptions[channel_id].copy()

        for subscriber_id in subscribers:
            if subscriber_id in self.user_sessions:
                await self._send_message_to_user(subscriber_id, message)

    async def _broadcast_message_edit(self, message: ChatMessage):
        """Broadcast message edit to channel subscribers"""
        subscribers = self.channel_subscriptions[message.channel_id].copy()

        for subscriber_id in subscribers:
            if subscriber_id in self.user_sessions:
                await self._send_message_edit_to_user(subscriber_id, message)

    async def _broadcast_message_deletion(self, message: ChatMessage):
        """Broadcast message deletion to channel subscribers"""
        subscribers = self.channel_subscriptions[message.channel_id].copy()

        for subscriber_id in subscribers:
            if subscriber_id in self.user_sessions:
                await self._send_message_deletion_to_user(subscriber_id, message)

    async def _handle_whisper_message(self, message: ChatMessage):
        """Handle whisper/proximity chat"""
        # Send to nearby users
        nearby_users = await self.get_nearby_users(message.sender_id, self.config["whisper_range"])

        for user_id in nearby_users:
            if user_id in self.user_sessions:
                await self._send_message_to_user(user_id, message)

    async def _handle_yell_message(self, message: ChatMessage):
        """Handle yell messages"""
        # Send to users in extended range
        nearby_users = await self.get_nearby_users(message.sender_id, self.config["yell_range"])

        for user_id in nearby_users:
            if user_id in self.user_sessions:
                await self._send_message_to_user(user_id, message)

    async def _handle_emote_message(self, message: ChatMessage):
        """Handle emote messages"""
        # Send to nearby users with special formatting
        nearby_users = await self.get_nearby_users(message.sender_id)

        for user_id in nearby_users:
            if user_id in self.user_sessions:
                await self._send_emote_to_user(user_id, message)

    async def _send_system_message(self, channel_id: str, content: str, data: Dict = None):
        """Send a system message to a channel"""
        message = ChatMessage(
            id=str(uuid.uuid4()),
            sender_id="system",
            sender_name="System",
            channel_id=channel_id,
            channel_type=self.channels[channel_id].channel_type,
            message_type=MessageType.SYSTEM,
            content=content,
            timestamp=datetime.now(),
            metadata=data or {}
        )

        self.messages[message.id] = message
        self.channels[channel_id].message_history.append(message.id)
        await self._broadcast_message(message, channel_id)

    async def _can_access_channel(self, user_id: str, channel: ChatChannel) -> bool:
        """Check if user can access a channel"""
        # Public channels
        if not channel.is_private:
            return True

        # Private channels - check membership
        return user_id in channel.members

    async def _get_default_permissions(self, channel_type: ChannelType, creator_id: str) -> Dict:
        """Get default permissions for a channel type"""
        permissions = {
            creator_id: ["read", "write", "manage", "moderate"]
        }

        if channel_type in [ChannelType.GLOBAL, ChannelType.TRADE, ChannelType.HELP, ChannelType.LFG]:
            # Public channels - everyone can read and write
            permissions["everyone"] = ["read", "write"]
        elif channel_type in [ChannelType.GUILD, ChannelType.OFFICER]:
            # Guild channels - guild members can read
            permissions["guild_members"] = ["read"]
            if channel_type == ChannelType.GUILD:
                permissions["guild_members"].append("write")
            else:
                permissions["guild_officers"] = ["write"]
        elif channel_type == ChannelType.PARTY:
            # Party channels - party members can read and write
            permissions["party_members"] = ["read", "write"]

        return permissions

    async def _get_or_create_private_channel(self, user1_id: str, user2_id: str) -> str:
        """Get or create a private channel between two users"""
        # Look for existing private channel
        for channel in self.channels.values():
            if (channel.channel_type == ChannelType.PRIVATE and
                set([user1_id, user2_id]) == set(channel.members)):
                return channel.id

        # Create new private channel
        channel_id = str(uuid.uuid4())
        channel = ChatChannel(
            id=channel_id,
            name=f"Private: {user1_id} & {user2_id}",
            channel_type=ChannelType.PRIVATE,
            description="Private conversation",
            members=set([user1_id, user2_id]),
            is_private=True
        )

        self.channels[channel_id] = channel
        self.channel_subscriptions[channel_id].update([user1_id, user2_id])

        return channel_id

    def _hash_password(self, password: str) -> str:
        """Hash a password"""
        if not password:
            return None
        return hashlib.sha256(password.encode()).hexdigest()

    def _update_user_activity(self, user_id: str):
        """Update user's last activity timestamp"""
        if user_id in self.user_sessions:
            self.user_sessions[user_id]["last_activity"] = datetime.now()

    async def _player_exists(self, player_id: str) -> bool:
        """Check if player exists"""
        # This would integrate with your player database
        return True  # Placeholder

    async def _get_player_name(self, player_id: str) -> str:
        """Get player name by ID"""
        # This would integrate with your player database
        return f"Player_{player_id[:8]}"  # Placeholder

    async def _get_player_id_by_name(self, name: str) -> Optional[str]:
        """Get player ID by name"""
        # This would integrate with your player database
        return None  # Placeholder

    async def _is_blocked(self, sender_id: str, recipient_id: str) -> bool:
        """Check if sender is blocked by recipient"""
        # This would integrate with your block/mute system
        return False  # Placeholder

    async def _is_muted(self, user_id: str) -> bool:
        """Check if user is muted"""
        if user_id in self.moderated_users:
            mute_info = self.moderated_users[user_id]
            if mute_info.get("type") == "mute":
                expiry = mute_info.get("expires")
                if expiry and datetime.now() > expiry:
                    del self.moderated_users[user_id]
                    return False
                return True
        return False

    async def _is_admin(self, user_id: str) -> bool:
        """Check if user is an administrator"""
        # This would integrate with your permission system
        return False  # Placeholder

    async def _check_profanity(self, content: str) -> Dict:
        """Check content for profanity"""
        # This would integrate with a profanity filter
        return {"filtered": False, "blocked": False, "content": content}

    async def _check_links(self, content: str) -> Dict:
        """Check content for links"""
        # Simple URL detection
        url_pattern = r'https?://[^\s<>"{}|\\^`[\]]'
        if re.search(url_pattern, content):
            return {"blocked": True}
        return {"blocked": False}

    async def _process_emotes(self, content: str) -> str:
        """Process emote codes in content"""
        # This would integrate with your emote system
        return content

    async def _send_message_to_user(self, user_id: str, message: ChatMessage):
        """Send message to a specific user"""
        # This would integrate with your WebSocket/real-time system
        pass

    async def _send_message_edit_to_user(self, user_id: str, message: ChatMessage):
        """Send message edit to a specific user"""
        # This would integrate with your WebSocket/real-time system
        pass

    async def _send_message_deletion_to_user(self, user_id: str, message: ChatMessage):
        """Send message deletion to a specific user"""
        # This would integrate with your WebSocket/real-time system
        pass

    async def _send_emote_to_user(self, user_id: str, message: ChatMessage):
        """Send emote to a specific user"""
        # This would integrate with your WebSocket/real-time system
        pass

    async def _send_notification_to_user(self, user_id: str, notification: Notification):
        """Send notification to a specific user"""
        # This would integrate with your notification system
        pass

    async def start_background_tasks(self):
        """Start background maintenance tasks"""
        if self._running:
            return

        self._running = True

        # Cleanup tasks
        self._background_tasks.append(
            asyncio.create_task(self._cleanup_task())
        )

        # Proximity chat task
        self._background_tasks.append(
            asyncio.create_task(self._proximity_chat_task())
        )

    async def stop_background_tasks(self):
        """Stop background maintenance tasks"""
        self._running = False

        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._background_tasks.clear()

    async def _cleanup_task(self):
        """Periodic cleanup of old data"""
        while self._running:
            try:
                cutoff_date = datetime.now() - timedelta(days=self.config["message_history_retention_days"])

                # Clean up old messages
                for message_id, message in list(self.messages.items()):
                    if message.timestamp < cutoff_date:
                        del self.messages[message_id]

                # Clean up old notifications
                for user_id in list(self.notifications.keys()):
                    user_notifications = self.notifications[user_id]
                    self.notifications[user_id] = [
                        n for n in user_notifications
                        if not n.expires_date or n.expires_date > datetime.now()
                    ]

                # Clean up temporary channels
                for channel_id, channel in list(self.channels.items()):
                    if channel.temporary and channel.expires_date and datetime.now() > channel.expires_date:
                        del self.channels[channel_id]
                        if channel_id in self.channel_subscriptions:
                            del self.channel_subscriptions[channel_id]

                await asyncio.sleep(3600)  # Run hourly

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(300)

    async def _proximity_chat_task(self):
        """Handle proximity-based messaging"""
        while self._running:
            try:
                # This would handle proximity chat updates
                await asyncio.sleep(1)  # Check frequently for low latency

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in proximity chat task: {e}")
                await asyncio.sleep(5)

# Usage example
if __name__ == "__main__":
    async def main():
        # Initialize communication hub
        comm_hub = CommunicationHub()

        # Start background tasks
        await comm_hub.start_background_tasks()

        # Create some channels
        global_channel = await comm_hub.create_channel("system", {
            "name": "Global Chat",
            "type": "global",
            "description": "Server-wide chat channel"
        })
        print(f"Global channel created: {global_channel['channel_id']}")

        trade_channel = await comm_hub.create_channel("system", {
            "name": "Trade Chat",
            "type": "trade",
            "description": "Trading and marketplace chat"
        })
        print(f"Trade channel created: {trade_channel['channel_id']}")

        # Subscribe users to channels
        await comm_hub.subscribe_to_channel("player1", global_channel["channel_id"])
        await comm_hub.subscribe_to_channel("player2", global_channel["channel_id"])
        await comm_hub.subscribe_to_channel("player1", trade_channel["channel_id"])

        # Send some messages
        await comm_hub.send_message("player1", global_channel["channel_id"], "Hello everyone!")
        await comm_hub.send_message("player2", global_channel["channel_id"], "Hi there! How's it going?")
        await comm_hub.send_message("player1", trade_channel["channel_id"], "WTS: Dragon Sword 1000 gold")

        # Send private message
        await comm_hub.send_private_message("player1", "player2", "Want to party up?")

        # Send notification
        await comm_hub.send_notification(
            "player1",
            "New Message",
            "You have a new private message from Player2",
            NotificationPriority.NORMAL,
            "private_message"
        )

        # Create voice session
        voice_session = await comm_hub.create_voice_session("player1", global_channel["channel_id"])
        await comm_hub.join_voice_session("player2", voice_session["session_id"])

        # Get channel history
        history = await comm_hub.get_channel_history(global_channel["channel_id"], "player1")
        print(f"Global chat has {history['total_count']} messages")

        # Get notifications
        notifications = await comm_hub.get_user_notifications("player1")
        print(f"Player1 has {notifications['unread_count']} unread notifications")

        # Keep running for background tasks
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await comm_hub.stop_background_tasks()

    asyncio.run(main())