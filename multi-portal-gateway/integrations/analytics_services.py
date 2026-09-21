#!/usr/bin/env python3
"""
Analytics Services Integration
Connects with Google Analytics, Mixpanel, Amplitude, and other analytics platforms
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import aiohttp
import uuid
from .integration_manager import IntegrationStatus

@dataclass
class AnalyticsEvent:
    event_name: str
    user_id: Optional[str]
    anonymous_id: str
    properties: Dict[str, Any]
    timestamp: datetime
    platform: str
    source: str
    campaign: Optional[str]

@dataclass
class UserProperties:
    user_id: str
    properties: Dict[str, Any]
    timestamp: datetime
    platform: str

@dataclass
class FunnelData:
    funnel_name: str
    steps: List[Dict[str, Any]]
    conversion_rates: Dict[str, float]
    total_users: int
    time_period: str

class AnalyticsServicesIntegration:
    """Integration with analytics platforms"""

    def __init__(self, integration_manager):
        self.manager = integration_manager
        self.logger = logging.getLogger(__name__)
        self.config = {}
        self.status = IntegrationStatus.INACTIVE

        # Analytics clients
        self.google_analytics = None
        self.mixpanel = None
        self.amplitude = None

        # Event queue for batching
        self.event_queue: List[AnalyticsEvent] = []
        self.batch_size = 50
        self.batch_timeout = 30  # seconds

        # User tracking
        self.user_profiles: Dict[str, Dict[str, Any]] = {}
        self.session_data: Dict[str, Dict[str, Any]] = {}

    async def initialize(self):
        """Initialize the analytics services integration"""
        self.logger.info("Initializing Analytics Services Integration")

        # Initialize Google Analytics
        await self._initialize_google_analytics()

        # Initialize Mixpanel
        await self._initialize_mixpanel()

        # Initialize Amplitude
        await self._initialize_amplitude()

        # Start event batching
        asyncio.create_task(self._event_batch_processor())

        # Start session cleanup
        asyncio.create_task(self._session_cleanup())

        self.status = IntegrationStatus.ACTIVE

    async def _initialize_google_analytics(self):
        """Initialize Google Analytics 4"""
        try:
            measurement_id = self.config.get('api_keys', {}).get('google_analytics_measurement_id')
            api_secret = self.config.get('api_keys', {}).get('google_analytics_api_secret')

            if measurement_id and api_secret:
                self.google_analytics = {
                    'measurement_id': measurement_id,
                    'api_secret': api_secret,
                    'base_url': 'https://www.google-analytics.com/mp/collect'
                }
                self.logger.info("Google Analytics initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Google Analytics: {e}")

    async def _initialize_mixpanel(self):
        """Initialize Mixpanel"""
        try:
            token = self.config.get('api_keys', {}).get('mixpanel_token')
            if token:
                self.mixpanel = {
                    'token': token,
                    'base_url': 'https://api.mixpanel.com'
                }
                self.logger.info("Mixpanel initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Mixpanel: {e}")

    async def _initialize_amplitude(self):
        """Initialize Amplitude"""
        try:
            api_key = self.config.get('api_keys', {}).get('amplitude_api_key')
            if api_key:
                self.amplitude = {
                    'api_key': api_key,
                    'base_url': 'https://api2.amplitude.com/2/httpapi'
                }
                self.logger.info("Amplitude initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Amplitude: {e}")

    async def track_event(self, event_name: str,
                         user_id: Optional[str] = None,
                         anonymous_id: Optional[str] = None,
                         properties: Dict[str, Any] = None,
                         platform: str = 'web',
                         source: str = 'dmlogn8n',
                         campaign: Optional[str] = None) -> Dict[str, Any]:
        """Track an analytics event"""
        try:
            # Generate anonymous ID if not provided
            if not anonymous_id:
                anonymous_id = str(uuid.uuid4())

            event = AnalyticsEvent(
                event_name=event_name,
                user_id=user_id,
                anonymous_id=anonymous_id,
                properties=properties or {},
                timestamp=datetime.now(),
                platform=platform,
                source=source,
                campaign=campaign
            )

            # Add to queue for batching
            self.event_queue.append(event)

            # Track in real-time for critical events
            critical_events = ['payment_completed', 'user_signup', 'subscription_started']
            if event_name in critical_events:
                await self._send_event_immediately(event)

            # Update session data
            await self._update_session_data(event)

            return {
                'success': True,
                'event_id': str(uuid.uuid4()),
                'event_name': event_name,
                'timestamp': event.timestamp.isoformat()
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _send_event_immediately(self, event: AnalyticsEvent):
        """Send event immediately without batching"""
        try:
            # Send to all configured platforms
            if self.google_analytics:
                await self._send_to_google_analytics(event)
            if self.mixpanel:
                await self._send_to_mixpanel(event)
            if self.amplitude:
                await self._send_to_amplitude(event)
        except Exception as e:
            self.logger.error(f"Error sending immediate event: {e}")

    async def _event_batch_processor(self):
        """Process events in batches"""
        while True:
            try:
                if len(self.event_queue) >= self.batch_size:
                    await self._process_batch()
                else:
                    await asyncio.sleep(self.batch_timeout)
                    if self.event_queue:  # Process remaining events
                        await self._process_batch()
            except Exception as e:
                self.logger.error(f"Error in batch processor: {e}")
                await asyncio.sleep(10)

    async def _process_batch(self):
        """Process a batch of events"""
        if not self.event_queue:
            return

        # Take a batch of events
        batch = self.event_queue[:self.batch_size]
        self.event_queue = self.event_queue[self.batch_size:]

        try:
            # Send to all platforms concurrently
            tasks = []
            if self.google_analytics:
                tasks.append(self._send_batch_to_google_analytics(batch))
            if self.mixpanel:
                tasks.append(self._send_batch_to_mixpanel(batch))
            if self.amplitude:
                tasks.append(self._send_batch_to_amplitude(batch))

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            self.logger.info(f"Processed batch of {len(batch)} events")

        except Exception as e:
            self.logger.error(f"Error processing batch: {e}")
            # Re-add failed events to queue
            self.event_queue = batch + self.event_queue

    async def _send_to_google_analytics(self, event: AnalyticsEvent):
        """Send event to Google Analytics"""
        try:
            client_id = event.user_id or event.anonymous_id

            event_data = {
                'client_id': client_id,
                'user_properties': {
                    'platform': {'value': event.platform},
                    'source': {'value': event.source}
                },
                'events': [{
                    'name': event.event_name,
                    'params': {
                        'timestamp_micros': int(event.timestamp.timestamp() * 1000000),
                        **event.properties
                    }
                }]
            }

            # Add campaign info if available
            if event.campaign:
                event_data['user_properties']['campaign'] = {'value': event.campaign}

            params = {
                'measurement_id': self.google_analytics['measurement_id'],
                'api_secret': self.google_analytics['api_secret']
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.google_analytics['base_url'],
                    params=params,
                    json=event_data
                ) as response:
                    if response.status != 204:
                        error_text = await response.text()
                        self.logger.error(f"Google Analytics error: {error_text}")

        except Exception as e:
            self.logger.error(f"Error sending to Google Analytics: {e}")

    async def _send_batch_to_google_analytics(self, events: List[AnalyticsEvent]):
        """Send batch of events to Google Analytics"""
        try:
            # Group events by client_id
            events_by_client = {}
            for event in events:
                client_id = event.user_id or event.anonymous_id
                if client_id not in events_by_client:
                    events_by_client[client_id] = []
                events_by_client[client_id].append(event)

            # Send each client's events
            for client_id, client_events in events_by_client.items():
                event_data = {
                    'client_id': client_id,
                    'events': []
                }

                for event in client_events:
                    event_data['events'].append({
                        'name': event.event_name,
                        'params': {
                            'timestamp_micros': int(event.timestamp.timestamp() * 1000000),
                            **event.properties
                        }
                    })

                params = {
                    'measurement_id': self.google_analytics['measurement_id'],
                    'api_secret': self.google_analytics['api_secret']
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.google_analytics['base_url'],
                        params=params,
                        json=event_data
                    ) as response:
                        if response.status != 204:
                            error_text = await response.text()
                            self.logger.error(f"Google Analytics batch error: {error_text}")

        except Exception as e:
            self.logger.error(f"Error sending batch to Google Analytics: {e}")

    async def _send_to_mixpanel(self, event: AnalyticsEvent):
        """Send event to Mixpanel"""
        try:
            event_data = {
                'event': event.event_name,
                'properties': {
                    'token': self.mixpanel['token'],
                    'time': int(event.timestamp.timestamp()),
                    'distinct_id': event.user_id or event.anonymous_id,
                    'platform': event.platform,
                    'source': event.source,
                    **event.properties
                }
            }

            if event.campaign:
                event_data['properties']['campaign'] = event.campaign

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.mixpanel['base_url']}/track",
                    json=event_data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Mixpanel error: {error_text}")

        except Exception as e:
            self.logger.error(f"Error sending to Mixpanel: {e}")

    async def _send_batch_to_mixpanel(self, events: List[AnalyticsEvent]):
        """Send batch of events to Mixpanel"""
        try:
            batch_data = []
            for event in events:
                event_data = {
                    'event': event.event_name,
                    'properties': {
                        'token': self.mixpanel['token'],
                        'time': int(event.timestamp.timestamp()),
                        'distinct_id': event.user_id or event.anonymous_id,
                        'platform': event.platform,
                        'source': event.source,
                        **event.properties
                    }
                }
                if event.campaign:
                    event_data['properties']['campaign'] = event.campaign
                batch_data.append(event_data)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.mixpanel['base_url']}/track",
                    json=batch_data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Mixpanel batch error: {error_text}")

        except Exception as e:
            self.logger.error(f"Error sending batch to Mixpanel: {e}")

    async def _send_to_amplitude(self, event: AnalyticsEvent):
        """Send event to Amplitude"""
        try:
            event_data = {
                'api_key': self.amplitude['api_key'],
                'events': [{
                    'user_id': event.user_id,
                    'device_id': event.anonymous_id,
                    'event_type': event.event_name,
                    'timestamp': int(event.timestamp.timestamp() * 1000),
                    'event_properties': event.properties,
                    'user_properties': {
                        'platform': event.platform,
                        'source': event.source
                    },
                    'platform': event.platform
                }]
            }

            if event.campaign:
                event_data['events'][0]['user_properties']['campaign'] = event.campaign

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.amplitude['base_url'],
                    json=event_data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Amplitude error: {error_text}")

        except Exception as e:
            self.logger.error(f"Error sending to Amplitude: {e}")

    async def _send_batch_to_amplitude(self, events: List[AnalyticsEvent]):
        """Send batch of events to Amplitude"""
        try:
            amplitude_events = []
            for event in events:
                amplitude_event = {
                    'user_id': event.user_id,
                    'device_id': event.anonymous_id,
                    'event_type': event.event_name,
                    'timestamp': int(event.timestamp.timestamp() * 1000),
                    'event_properties': event.properties,
                    'user_properties': {
                        'platform': event.platform,
                        'source': event.source
                    },
                    'platform': event.platform
                }
                if event.campaign:
                    amplitude_event['user_properties']['campaign'] = event.campaign
                amplitude_events.append(amplitude_event)

            event_data = {
                'api_key': self.amplitude['api_key'],
                'events': amplitude_events
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.amplitude['base_url'],
                    json=event_data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Amplitude batch error: {error_text}")

        except Exception as e:
            self.logger.error(f"Error sending batch to Amplitude: {e}")

    async def update_user_properties(self, user_id: str,
                                   properties: Dict[str, Any],
                                   platform: str = 'web') -> Dict[str, Any]:
        """Update user properties across all platforms"""
        try:
            user_props = UserProperties(
                user_id=user_id,
                properties=properties,
                timestamp=datetime.now(),
                platform=platform
            )

            # Update local user profile
            if user_id not in self.user_profiles:
                self.user_profiles[user_id] = {}
            self.user_profiles[user_id].update(properties)

            # Send to all platforms
            if self.mixpanel:
                await self._update_mixpanel_user_properties(user_props)
            if self.amplitude:
                await self._update_amplitude_user_properties(user_props)

            return {
                'success': True,
                'user_id': user_id,
                'updated_properties': list(properties.keys()),
                'timestamp': user_props.timestamp.isoformat()
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _update_mixpanel_user_properties(self, user_props: UserProperties):
        """Update user properties in Mixpanel"""
        try:
            profile_data = {
                '$token': self.mixpanel['token'],
                '$distinct_id': user_props.user_id,
                '$set': user_props.properties,
                '$time': int(user_props.timestamp.timestamp())
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.mixpanel['base_url']}/engage",
                    json=profile_data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Mixpanel user properties error: {error_text}")

        except Exception as e:
            self.logger.error(f"Error updating Mixpanel user properties: {e}")

    async def _update_amplitude_user_properties(self, user_props: UserProperties):
        """Update user properties in Amplitude"""
        try:
            identify_data = {
                'api_key': self.amplitude['api_key'],
                'identifications': [{
                    'user_id': user_props.user_id,
                    'user_properties': user_props.properties
                }]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.amplitude['base_url']}/identify",
                    json=identify_data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Amplitude user properties error: {error_text}")

        except Exception as e:
            self.logger.error(f"Error updating Amplitude user properties: {e}")

    async def create_funnel(self, funnel_name: str,
                          steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create and track a conversion funnel"""
        try:
            funnel_data = {
                'funnel_name': funnel_name,
                'steps': steps,
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }

            # Store funnel definition
            await self.manager.cache_set(f"funnel_{funnel_name}", funnel_data, ttl=86400 * 30)

            # Track funnel creation event
            await self.track_event(
                event_name='funnel_created',
                properties={
                    'funnel_name': funnel_name,
                    'steps_count': len(steps),
                    'steps': [step['event_name'] for step in steps]
                }
            )

            return {
                'success': True,
                'funnel_name': funnel_name,
                'steps': steps,
                'created_at': funnel_data['created_at']
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def track_funnel_step(self, funnel_name: str,
                              step_index: int,
                              user_id: str,
                              properties: Dict[str, Any] = None) -> Dict[str, Any]:
        """Track user progress through funnel steps"""
        try:
            funnel_data = await self.manager.cache_get(f"funnel_{funnel_name}")
            if not funnel_data:
                return {'success': False, 'error': 'Funnel not found'}

            if step_index >= len(funnel_data['steps']):
                return {'success': False, 'error': 'Invalid step index'}

            step = funnel_data['steps'][step_index]

            # Track funnel step event
            await self.track_event(
                event_name='funnel_step_completed',
                user_id=user_id,
                properties={
                    'funnel_name': funnel_name,
                    'step_name': step['event_name'],
                    'step_index': step_index,
                    'total_steps': len(funnel_data['steps']),
                    **(properties or {})
                }
            )

            # Update user's funnel progress
            user_progress_key = f"funnel_progress_{user_id}_{funnel_name}"
            progress = await self.manager.cache_get(user_progress_key) or {
                'current_step': -1,
                'completed_steps': [],
                'started_at': datetime.now().isoformat()
            }

            progress['current_step'] = step_index
            progress['completed_steps'].append(step_index)
            await self.manager.cache_set(user_progress_key, progress, ttl=86400 * 7)

            return {
                'success': True,
                'funnel_name': funnel_name,
                'step_index': step_index,
                'step_name': step['event_name'],
                'progress': f"{step_index + 1}/{len(funnel_data['steps'])}"
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def get_funnel_analytics(self, funnel_name: str,
                                 start_date: datetime = None,
                                 end_date: datetime = None) -> Dict[str, Any]:
        """Get funnel analytics and conversion rates"""
        try:
            # This would typically query the analytics platforms
            # For now, return mock data based on cached progress

            funnel_data = await self.manager.cache_get(f"funnel_{funnel_name}")
            if not funnel_data:
                return {'error': 'Funnel not found'}

            # Mock analytics data
            mock_analytics = {
                'funnel_name': funnel_name,
                'total_users': 1000,
                'conversion_rates': {
                    'overall': 0.25,
                    'step_1': 0.8,
                    'step_2': 0.6,
                    'step_3': 0.4,
                    'step_4': 0.25
                },
                'step_analytics': [
                    {
                        'step_name': step['event_name'],
                        'step_index': idx,
                        'users_entered': 1000 - (idx * 200),
                        'users_completed': (1000 - (idx * 200)) * 0.8,
                        'conversion_rate': 0.8,
                        'average_time_to_complete': 300  # seconds
                    }
                    for idx, step in enumerate(funnel_data['steps'])
                ],
                'time_period': f"{start_date} to {end_date}" if start_date and end_date else "Last 30 days"
            }

            return mock_analytics

        except Exception as e:
            return {'error': str(e)}

    async def _update_session_data(self, event: AnalyticsEvent):
        """Update session data based on events"""
        try:
            session_id = event.user_id or event.anonymous_id

            if session_id not in self.session_data:
                self.session_data[session_id] = {
                    'session_start': event.timestamp,
                    'last_activity': event.timestamp,
                    'event_count': 0,
                    'platform': event.platform,
                    'source': event.source,
                    'campaign': event.campaign
                }

            session = self.session_data[session_id]
            session['last_activity'] = event.timestamp
            session['event_count'] += 1

        except Exception as e:
            self.logger.error(f"Error updating session data: {e}")

    async def _session_cleanup(self):
        """Clean up expired sessions"""
        while True:
            try:
                current_time = datetime.now()
                expired_sessions = []

                for session_id, session in self.session_data.items():
                    # Remove sessions inactive for more than 30 minutes
                    if (current_time - session['last_activity']).total_seconds() > 1800:
                        expired_sessions.append(session_id)

                for session_id in expired_sessions:
                    del self.session_data[session_id]

                self.logger.debug(f"Cleaned up {len(expired_sessions)} expired sessions")
                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                self.logger.error(f"Error in session cleanup: {e}")
                await asyncio.sleep(60)

    async def get_user_analytics(self, user_id: str,
                               start_date: datetime = None,
                               end_date: datetime = None) -> Dict[str, Any]:
        """Get analytics for a specific user"""
        try:
            # Get user profile
            user_profile = self.user_profiles.get(user_id, {})

            # Get session data
            session_data = self.session_data.get(user_id, {})

            # Mock analytics data
            analytics = {
                'user_id': user_id,
                'profile': user_profile,
                'session_data': {
                    'session_start': session_data.get('session_start').isoformat() if session_data.get('session_start') else None,
                    'last_activity': session_data.get('last_activity').isoformat() if session_data.get('last_activity') else None,
                    'total_events': session_data.get('event_count', 0),
                    'platform': session_data.get('platform', 'unknown'),
                    'source': session_data.get('source', 'unknown')
                },
                'engagement_metrics': {
                    'total_events': session_data.get('event_count', 0),
                    'session_duration': (session_data.get('last_activity') - session_data.get('session_start')).total_seconds() if session_data.get('session_start') and session_data.get('last_activity') else 0,
                    'events_per_session': session_data.get('event_count', 0)
                },
                'time_period': f"{start_date} to {end_date}" if start_date and end_date else "All time"
            }

            return analytics

        except Exception as e:
            return {'error': str(e)}

    async def get_platform_analytics(self, platform: str,
                                   start_date: datetime = None,
                                   end_date: datetime = None) -> Dict[str, Any]:
        """Get analytics for a specific platform"""
        try:
            # This would query the analytics platforms
            # For now, return mock data
            mock_analytics = {
                'platform': platform,
                'total_users': 5000,
                'active_users': 1200,
                'new_users': 150,
                'total_events': 45000,
                'event_types': {
                    'page_view': 20000,
                    'user_signup': 150,
                    'payment_completed': 75,
                    'content_interaction': 24775
                },
                'engagement': {
                    'average_session_duration': 450,  # seconds
                    'events_per_user': 9.0,
                    'retention_rate': 0.65
                },
                'time_period': f"{start_date} to {end_date}" if start_date and end_date else "Last 30 days"
            }

            return mock_analytics

        except Exception as e:
            return {'error': str(e)}

    async def get_status(self) -> IntegrationStatus:
        """Get integration status"""
        return self.status

    async def enable(self):
        """Enable the integration"""
        self.status = IntegrationStatus.ACTIVE
        self.logger.info("Analytics Services Integration enabled")

    async def disable(self):
        """Disable the integration"""
        self.status = IntegrationStatus.INACTIVE
        self.logger.info("Analytics Services Integration disabled")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'platforms': {},
            'metrics': {
                'events_queued': len(self.event_queue),
                'active_sessions': len(self.session_data),
                'user_profiles': len(self.user_profiles)
            }
        }

        # Check Google Analytics
        if self.google_analytics:
            health_status['platforms']['google_analytics'] = {
                'status': 'configured',
                'measurement_id': self.google_analytics['measurement_id']
            }

        # Check Mixpanel
        if self.mixpanel:
            health_status['platforms']['mixpanel'] = {
                'status': 'configured',
                'token': '***configured***'
            }

        # Check Amplitude
        if self.amplitude:
            health_status['platforms']['amplitude'] = {
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
        if event_type == 'track_event':
            await self.track_event(
                event_name=data.get('event_name'),
                user_id=data.get('user_id'),
                properties=data.get('properties', {}),
                platform=data.get('platform', 'web'),
                source=data.get('source', 'webhook')
            )
        elif event_type == 'update_user_properties':
            await self.update_user_properties(
                user_id=data.get('user_id'),
                properties=data.get('properties', {}),
                platform=data.get('platform', 'web')
            )

    async def shutdown(self):
        """Shutdown the integration"""
        # Process remaining events
        while self.event_queue:
            await self._process_batch()
            await asyncio.sleep(1)

        self.logger.info("Analytics Services Integration shutdown")