#!/usr/bin/env python3
"""
Streaming Services Integration
Connects with Twitch, YouTube, and other streaming platforms
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import aiohttp
import websockets
from .integration_manager import IntegrationStatus

@dataclass
class StreamSession:
    platform: str
    stream_id: str
    title: str
    game: str
    viewer_count: int
    start_time: datetime
    is_live: bool
    thumbnail_url: str
    stream_url: str

@dataclass
class StreamAlert:
    type: str  # 'live', 'raid', 'follow', 'subscription', 'donation'
    platform: str
    user_name: str
    user_id: str
    message: str
    amount: Optional[float]
    timestamp: datetime

class StreamingServicesIntegration:
    """Integration with streaming platforms"""

    def __init__(self, integration_manager):
        self.manager = integration_manager
        self.logger = logging.getLogger(__name__)
        self.config = {}
        self.status = IntegrationStatus.INACTIVE

        # API clients
        self.twitch_token = None
        self.youtube_token = None

        # WebSocket connections
        self.twitch_websocket = None
        self.youtube_websocket = None

        # Active streams
        self.active_streams: Dict[str, StreamSession] = {}
        self.stream_alerts: List[StreamAlert] = []

        # Webhook callbacks
        self.webhook_callbacks = {}

    async def initialize(self):
        """Initialize the streaming services integration"""
        self.logger.info("Initializing Streaming Services Integration")

        # Initialize Twitch
        await self._initialize_twitch()

        # Initialize YouTube
        await self._initialize_youtube()

        # Start monitoring active streams
        asyncio.create_task(self._monitor_streams())

        self.status = IntegrationStatus.ACTIVE

    async def _initialize_twitch(self):
        """Initialize Twitch API integration"""
        try:
            client_id = self.config.get('api_keys', {}).get('twitch_client_id')
            client_secret = self.config.get('api_keys', {}).get('twitch_client_secret')

            if client_id and client_secret:
                # Get OAuth token
                await self._refresh_twitch_token(client_id, client_secret)
                self.logger.info("Twitch integration initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Twitch: {e}")

    async def _refresh_twitch_token(self, client_id: str, client_secret: str):
        """Refresh Twitch OAuth token"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://id.twitch.tv/oauth2/token',
                    params={
                        'client_id': client_id,
                        'client_secret': client_secret,
                        'grant_type': 'client_credentials'
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.twitch_token = data['access_token']
                        self.logger.info("Twitch token refreshed successfully")
                    else:
                        self.logger.error(f"Failed to get Twitch token: {response.status}")
        except Exception as e:
            self.logger.error(f"Error refreshing Twitch token: {e}")

    async def _initialize_youtube(self):
        """Initialize YouTube API integration"""
        try:
            api_key = self.config.get('api_keys', {}).get('youtube_api_key')
            if api_key:
                self.youtube_token = api_key
                self.logger.info("YouTube integration initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize YouTube: {e}")

    async def start_stream(self, platform: str, title: str, game: str = '',
                          tags: List[str] = None) -> Dict[str, Any]:
        """Start a stream on specified platform"""
        try:
            if platform == 'twitch':
                return await self._start_twitch_stream(title, game, tags or [])
            elif platform == 'youtube':
                return await self._start_youtube_stream(title, game, tags or [])
            else:
                return {'success': False, 'error': f'Unsupported platform: {platform}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _start_twitch_stream(self, title: str, game: str, tags: List[str]) -> Dict[str, Any]:
        """Start a Twitch stream"""
        try:
            if not self.twitch_token:
                return {'success': False, 'error': 'Twitch not authenticated'}

            # Get user info
            user_info = await self._get_twitch_user_info()
            if not user_info:
                return {'success': False, 'error': 'Failed to get user info'}

            # Update channel info
            await self._update_twitch_channel(title, game, tags)

            # Get game ID if game specified
            game_id = None
            if game:
                game_id = await self._get_twitch_game_id(game)

            stream_session = StreamSession(
                platform='twitch',
                stream_id=user_info['id'],
                title=title,
                game=game,
                viewer_count=0,
                start_time=datetime.now(),
                is_live=True,
                thumbnail_url='',
                stream_url=f"https://twitch.tv/{user_info['login']}"
            )

            self.active_streams[f"twitch_{user_info['id']}"] = stream_session

            return {
                'success': True,
                'stream_id': stream_session.stream_id,
                'stream_url': stream_session.stream_url,
                'title': title,
                'game': game,
                'start_time': stream_session.start_time.isoformat()
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _start_youtube_stream(self, title: str, game: str, tags: List[str]) -> Dict[str, Any]:
        """Start a YouTube stream"""
        try:
            if not self.youtube_token:
                return {'success': False, 'error': 'YouTube not authenticated'}

            # Create YouTube broadcast
            broadcast_data = {
                'snippet': {
                    'title': title,
                    'description': f"Stream: {title}\nGame: {game}",
                    'scheduledStartTime': datetime.now().isoformat() + 'Z',
                    'tags': tags + [game] if game else tags
                },
                'status': {
                    'privacyStatus': 'public',
                    'selfDeclaredMadeForKids': False
                },
                'contentDetails': {
                    'enableAutoStart': True,
                    'enableAutoStop': True
                }
            }

            # YouTube API call would go here
            # For now, return mock data
            stream_session = StreamSession(
                platform='youtube',
                stream_id='youtube_broadcast_' + str(int(datetime.now().timestamp())),
                title=title,
                game=game,
                viewer_count=0,
                start_time=datetime.now(),
                is_live=True,
                thumbnail_url='',
                stream_url='https://youtube.com/live/mock_stream_id'
            )

            self.active_streams[f"youtube_{stream_session.stream_id}"] = stream_session

            return {
                'success': True,
                'stream_id': stream_session.stream_id,
                'stream_url': stream_session.stream_url,
                'title': title,
                'game': game,
                'start_time': stream_session.start_time.isoformat()
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _get_twitch_user_info(self) -> Optional[Dict[str, Any]]:
        """Get Twitch user information"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Client-ID': self.config.get('api_keys', {}).get('twitch_client_id'),
                    'Authorization': f'Bearer {self.twitch_token}'
                }

                async with session.get(
                    'https://api.twitch.tv/helix/users',
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['data'][0] if data['data'] else None
                    else:
                        self.logger.error(f"Twitch user info error: {response.status}")
                        return None
        except Exception as e:
            self.logger.error(f"Error getting Twitch user info: {e}")
            return None

    async def _update_twitch_channel(self, title: str, game: str, tags: List[str]):
        """Update Twitch channel information"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Client-ID': self.config.get('api_keys', {}).get('twitch_client_id'),
                    'Authorization': f'Bearer {self.twitch_token}',
                    'Content-Type': 'application/json'
                }

                # Get game ID
                game_id = await self._get_twitch_game_id(game) if game else None

                data = {
                    'game_id': game_id,
                    'title': title,
                    'tags': tags[:5]  # Twitch limits to 5 tags
                }

                # Remove None values
                data = {k: v for k, v in data.items() if v is not None}

                async with session.patch(
                    'https://api.twitch.tv/helix/channels',
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 204:
                        self.logger.info("Twitch channel updated successfully")
                    else:
                        self.logger.error(f"Failed to update Twitch channel: {response.status}")
        except Exception as e:
            self.logger.error(f"Error updating Twitch channel: {e}")

    async def _get_twitch_game_id(self, game_name: str) -> Optional[str]:
        """Get Twitch game ID from game name"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Client-ID': self.config.get('api_keys', {}).get('twitch_client_id'),
                    'Authorization': f'Bearer {self.twitch_token}'
                }

                async with session.get(
                    'https://api.twitch.tv/helix/games',
                    headers=headers,
                    params={'name': game_name}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['data'][0]['id'] if data['data'] else None
                    else:
                        return None
        except Exception as e:
            self.logger.error(f"Error getting Twitch game ID: {e}")
            return None

    async def stop_stream(self, platform: str, stream_id: str) -> Dict[str, Any]:
        """Stop a stream"""
        try:
            stream_key = f"{platform}_{stream_id}"
            if stream_key in self.active_streams:
                stream = self.active_streams[stream_key]
                stream.is_live = False

                # Platform-specific stop actions
                if platform == 'twitch':
                    # Update stream info
                    await self._update_twitch_channel("Stream ended", "", [])

                # Remove from active streams after delay
                asyncio.create_task(self._remove_stream_after_delay(stream_key, 300))

                return {
                    'success': True,
                    'message': f'Stream {stream_id} stopped',
                    'duration': (datetime.now() - stream.start_time).total_seconds()
                }
            else:
                return {'success': False, 'error': 'Stream not found'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _remove_stream_after_delay(self, stream_key: str, delay: int):
        """Remove stream from active list after delay"""
        await asyncio.sleep(delay)
        if stream_key in self.active_streams:
            del self.active_streams[stream_key]

    async def get_stream_info(self, platform: str, stream_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a stream"""
        try:
            stream_key = f"{platform}_{stream_id}"
            if stream_key in self.active_streams:
                stream = self.active_streams[stream_key]

                # Update viewer count
                if platform == 'twitch':
                    await self._update_twitch_viewer_count(stream)
                elif platform == 'youtube':
                    await self._update_youtube_viewer_count(stream)

                return {
                    'platform': stream.platform,
                    'stream_id': stream.stream_id,
                    'title': stream.title,
                    'game': stream.game,
                    'viewer_count': stream.viewer_count,
                    'is_live': stream.is_live,
                    'start_time': stream.start_time.isoformat(),
                    'duration': (datetime.now() - stream.start_time).total_seconds(),
                    'stream_url': stream.stream_url
                }
            else:
                return None
        except Exception as e:
            self.logger.error(f"Error getting stream info: {e}")
            return None

    async def _update_twitch_viewer_count(self, stream: StreamSession):
        """Update Twitch stream viewer count"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Client-ID': self.config.get('api_keys', {}).get('twitch_client_id'),
                    'Authorization': f'Bearer {self.twitch_token}'
                }

                async with session.get(
                    f'https://api.twitch.tv/helix/streams?user_id={stream.stream_id}',
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data['data']:
                            stream.viewer_count = data['data'][0]['viewer_count']
                            stream.thumbnail_url = data['data'][0]['thumbnail_url'].replace('{width}', '320').replace('{height}', '180')
        except Exception as e:
            self.logger.error(f"Error updating Twitch viewer count: {e}")

    async def _update_youtube_viewer_count(self, stream: StreamSession):
        """Update YouTube stream viewer count"""
        try:
            # YouTube API call would go here
            # For now, simulate viewer count
            if stream.viewer_count == 0:
                stream.viewer_count = 1
        except Exception as e:
            self.logger.error(f"Error updating YouTube viewer count: {e}")

    async def get_active_streams(self) -> List[Dict[str, Any]]:
        """Get all active streams"""
        streams = []
        for stream_key, stream in self.active_streams.items():
            if stream.is_live:
                # Update viewer count
                if stream.platform == 'twitch':
                    await self._update_twitch_viewer_count(stream)
                elif stream.platform == 'youtube':
                    await self._update_youtube_viewer_count(stream)

                streams.append({
                    'platform': stream.platform,
                    'stream_id': stream.stream_id,
                    'title': stream.title,
                    'game': stream.game,
                    'viewer_count': stream.viewer_count,
                    'is_live': stream.is_live,
                    'start_time': stream.start_time.isoformat(),
                    'duration': (datetime.now() - stream.start_time).total_seconds(),
                    'stream_url': stream.stream_url,
                    'thumbnail_url': stream.thumbnail_url
                })

        return streams

    async def _monitor_streams(self):
        """Monitor active streams for updates"""
        while True:
            try:
                if self.active_streams:
                    for stream_key, stream in list(self.active_streams.items()):
                        if stream.is_live:
                            # Update viewer counts
                            if stream.platform == 'twitch':
                                await self._update_twitch_viewer_count(stream)
                            elif stream.platform == 'youtube':
                                await self._update_youtube_viewer_count(stream)

                            # Check for milestones
                            await self._check_stream_milestones(stream)

                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Error monitoring streams: {e}")
                await asyncio.sleep(60)

    async def _check_stream_milestones(self, stream: StreamSession):
        """Check for stream milestones and send alerts"""
        try:
            # Viewer count milestones
            milestones = [1, 5, 10, 25, 50, 100, 250, 500, 1000, 5000, 10000]
            for milestone in milestones:
                if stream.viewer_count >= milestone:
                    # Check if milestone already reached
                    milestone_key = f"{stream.stream_id}_viewers_{milestone}"
                    if not await self.manager.cache_get(milestone_key):
                        # Send milestone alert
                        await self._send_stream_alert({
                            'type': 'milestone',
                            'platform': stream.platform,
                            'stream_id': stream.stream_id,
                            'milestone_type': 'viewers',
                            'milestone_value': milestone,
                            'message': f"🎉 {milestone} viewers reached!",
                            'timestamp': datetime.now().isoformat()
                        })

                        # Mark milestone as reached
                        await self.manager.cache_set(milestone_key, True, ttl=86400)

            # Duration milestones
            duration_minutes = int((datetime.now() - stream.start_time).total_seconds() / 60)
            duration_milestones = [15, 30, 60, 120, 240, 480]
            for milestone in duration_milestones:
                if duration_minutes >= milestone:
                    milestone_key = f"{stream.stream_id}_duration_{milestone}"
                    if not await self.manager.cache_get(milestone_key):
                        await self._send_stream_alert({
                            'type': 'milestone',
                            'platform': stream.platform,
                            'stream_id': stream.stream_id,
                            'milestone_type': 'duration',
                            'milestone_value': milestone,
                            'message': f"⏰ Streamed for {milestone} minutes!",
                            'timestamp': datetime.now().isoformat()
                        })

                        await self.manager.cache_set(milestone_key, True, ttl=86400)

        except Exception as e:
            self.logger.error(f"Error checking stream milestones: {e}")

    async def _send_stream_alert(self, alert_data: Dict[str, Any]):
        """Send stream alert via webhooks"""
        try:
            # Send to social platforms
            await self.manager.execute_webhook('social_platforms', 'stream_alert', alert_data)

            # Send to analytics
            await self.manager.execute_webhook('analytics_services', 'stream_milestone', alert_data)

            self.logger.info(f"Stream alert sent: {alert_data['type']} - {alert_data.get('message', '')}")
        except Exception as e:
            self.logger.error(f"Error sending stream alert: {e}")

    async def schedule_stream(self, platform: str, title: str, game: str,
                            scheduled_time: datetime, tags: List[str] = None) -> Dict[str, Any]:
        """Schedule a stream for later"""
        try:
            stream_data = {
                'platform': platform,
                'title': title,
                'game': game,
                'scheduled_time': scheduled_time.isoformat(),
                'tags': tags or [],
                'status': 'scheduled'
            }

            # Store scheduled stream
            scheduled_streams = await self.manager.cache_get('scheduled_streams') or []
            stream_data['id'] = len(scheduled_streams) + 1
            scheduled_streams.append(stream_data)
            await self.manager.cache_set('scheduled_streams', scheduled_streams, ttl=86400 * 7)  # 7 days

            # Schedule stream start
            delay = (scheduled_time - datetime.now()).total_seconds()
            if delay > 0:
                asyncio.create_task(self._start_scheduled_stream(stream_data, delay))

            return {
                'success': True,
                'stream_id': stream_data['id'],
                'scheduled_time': scheduled_time.isoformat(),
                'platform': platform,
                'title': title
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _start_scheduled_stream(self, stream_data: Dict[str, Any], delay: float):
        """Start a scheduled stream"""
        await asyncio.sleep(delay)

        try:
            result = await self.start_stream(
                platform=stream_data['platform'],
                title=stream_data['title'],
                game=stream_data['game'],
                tags=stream_data['tags']
            )

            if result['success']:
                # Update scheduled stream status
                stream_data['status'] = 'started'
                stream_data['actual_start_time'] = datetime.now().isoformat()

                # Send notification
                await self._send_stream_alert({
                    'type': 'scheduled_start',
                    'platform': stream_data['platform'],
                    'stream_id': result['stream_id'],
                    'title': stream_data['title'],
                    'stream_url': result.get('stream_url', ''),
                    'message': f"🔴 Scheduled stream started: {stream_data['title']}",
                    'timestamp': datetime.now().isoformat()
                })

                self.logger.info(f"Scheduled stream started: {stream_data['title']}")

        except Exception as e:
            self.logger.error(f"Failed to start scheduled stream: {e}")
            stream_data['status'] = 'failed'
            stream_data['error'] = str(e)

    async def get_stream_analytics(self, platform: str, stream_id: str,
                                 start_date: datetime = None,
                                 end_date: datetime = None) -> Dict[str, Any]:
        """Get analytics for a specific stream"""
        try:
            stream_key = f"{platform}_{stream_id}"
            if stream_key in self.active_streams:
                stream = self.active_streams[stream_key]

                # Calculate basic analytics
                duration = (datetime.now() - stream.start_time).total_seconds()
                peak_viewers = stream.viewer_count  # Would need to track this properly

                analytics = {
                    'platform': platform,
                    'stream_id': stream_id,
                    'title': stream.title,
                    'game': stream.game,
                    'start_time': stream.start_time.isoformat(),
                    'duration_seconds': duration,
                    'duration_formatted': f"{int(duration // 3600)}h {int((duration % 3600) // 60)}m",
                    'current_viewers': stream.viewer_count,
                    'peak_viewers': peak_viewers,
                    'average_viewers': peak_viewers / 2 if peak_viewers > 0 else 0,  # Simplified
                    'is_live': stream.is_live
                }

                # Platform-specific analytics
                if platform == 'twitch':
                    analytics.update(await self._get_twitch_analytics(stream_id))
                elif platform == 'youtube':
                    analytics.update(await self._get_youtube_analytics(stream_id))

                return analytics
            else:
                return {'error': 'Stream not found'}

        except Exception as e:
            return {'error': str(e)}

    async def _get_twitch_analytics(self, stream_id: str) -> Dict[str, Any]:
        """Get Twitch-specific analytics"""
        try:
            # This would make actual Twitch API calls
            # For now, return mock data
            return {
                'followers': 1000,
                'subscribers': 50,
                'bits': 500,
                'chatters': 25
            }
        except Exception as e:
            return {'error': str(e)}

    async def _get_youtube_analytics(self, stream_id: str) -> Dict[str, Any]:
        """Get YouTube-specific analytics"""
        try:
            # This would make actual YouTube API calls
            # For now, return mock data
            return {
                'subscribers': 2000,
                'watch_time_minutes': 500,
                'likes': 100,
                'comments': 25
            }
        except Exception as e:
            return {'error': str(e)}

    async def get_status(self) -> IntegrationStatus:
        """Get integration status"""
        return self.status

    async def enable(self):
        """Enable the integration"""
        self.status = IntegrationStatus.ACTIVE
        self.logger.info("Streaming Services Integration enabled")

    async def disable(self):
        """Disable the integration"""
        self.status = IntegrationStatus.INACTIVE
        self.logger.info("Streaming Services Integration disabled")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'platforms': {},
            'active_streams': len(self.active_streams)
        }

        # Check Twitch
        if self.twitch_token:
            try:
                user_info = await self._get_twitch_user_info()
                health_status['platforms']['twitch'] = {
                    'status': 'connected' if user_info else 'disconnected',
                    'user': user_info['login'] if user_info else None
                }
            except Exception as e:
                health_status['platforms']['twitch'] = {'status': 'error', 'error': str(e)}

        # Check YouTube
        if self.youtube_token:
            health_status['platforms']['youtube'] = {
                'status': 'configured',
                'api_key': '***configured***'
            }

        return health_status

    async def check_rate_limit(self):
        """Check rate limits"""
        # Rate limiting would be implemented here
        pass

    async def handle_webhook(self, event_type: str, data: Dict[str, Any]):
        """Handle webhook events"""
        if event_type == 'start_stream':
            await self.start_stream(
                platform=data.get('platform', 'twitch'),
                title=data.get('title', 'Live Stream'),
                game=data.get('game', ''),
                tags=data.get('tags', [])
            )
        elif event_type == 'stop_stream':
            await self.stop_stream(
                platform=data.get('platform', 'twitch'),
                stream_id=data.get('stream_id')
            )
        elif event_type == 'schedule_stream':
            scheduled_time = datetime.fromisoformat(data.get('scheduled_time'))
            await self.schedule_stream(
                platform=data.get('platform', 'twitch'),
                title=data.get('title', 'Scheduled Stream'),
                game=data.get('game', ''),
                scheduled_time=scheduled_time,
                tags=data.get('tags', [])
            )

    async def shutdown(self):
        """Shutdown the integration"""
        if self.twitch_websocket:
            await self.twitch_websocket.close()
        if self.youtube_websocket:
            await self.youtube_websocket.close()
        self.logger.info("Streaming Services Integration shutdown")