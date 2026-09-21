#!/usr/bin/env python3
"""
DMLogn8n Integration Manager
Central orchestration for all third-party integrations
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import redis
from cryptography.fernet import Fernet
import yaml
import os

# Integration modules
from .social_platforms import SocialPlatformsIntegration
from .streaming_services import StreamingServicesIntegration
from .payment_systems import PaymentSystemsIntegration
from .analytics_services import AnalyticsServicesIntegration
from .cdn_manager import CDNManager
from .ai_services import AIServicesIntegration
from .moderation_tools import ModerationToolsIntegration

class IntegrationStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    RATE_LIMITED = "rate_limited"

@dataclass
class IntegrationConfig:
    name: str
    enabled: bool
    api_keys: Dict[str, str]
    rate_limits: Dict[str, int]
    webhook_endpoints: List[str]
    retry_attempts: int
    timeout_seconds: int
    cache_ttl: int
    status: IntegrationStatus = IntegrationStatus.INACTIVE

@dataclass
class IntegrationMetrics:
    name: str
    requests_total: int
    requests_successful: int
    requests_failed: int
    average_response_time: float
    last_success: Optional[datetime]
    last_error: Optional[str]
    rate_limit_hits: int

class IntegrationManager:
    """Central orchestration system for all third-party integrations"""

    def __init__(self, config_path: str = "integrations_config.yaml"):
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.integrations: Dict[str, Any] = {}
        self.metrics: Dict[str, IntegrationMetrics] = {}
        self.redis_client = None
        self.encryption_key = os.environ.get('INTEGRATION_ENCRYPTION_KEY', Fernet.generate_key())
        self.cipher_suite = Fernet(self.encryption_key)
        self.session: Optional[aiohttp.ClientSession] = None

        # Initialize integration modules
        self._setup_integrations()

    def _setup_integrations(self):
        """Initialize all integration modules"""
        self.integrations = {
            'social_platforms': SocialPlatformsIntegration(self),
            'streaming_services': StreamingServicesIntegration(self),
            'payment_systems': PaymentSystemsIntegration(self),
            'analytics_services': AnalyticsServicesIntegration(self),
            'cdn_manager': CDNManager(self),
            'ai_services': AIServicesIntegration(self),
            'moderation_tools': ModerationToolsIntegration(self)
        }

    async def initialize(self):
        """Initialize the integration manager"""
        self.logger.info("Initializing Integration Manager")

        # Initialize HTTP session
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100)
        )

        # Initialize Redis for caching
        try:
            self.redis_client = redis.from_url(
                os.environ.get('REDIS_URL', 'redis://localhost:6379'),
                decode_responses=True
            )
            await self.redis_client.ping()
            self.logger.info("Redis connection established")
        except Exception as e:
            self.logger.warning(f"Redis connection failed: {e}")

        # Load configurations
        await self._load_configurations()

        # Initialize all integrations
        for name, integration in self.integrations.items():
            try:
                await integration.initialize()
                self.logger.info(f"Initialized integration: {name}")
            except Exception as e:
                self.logger.error(f"Failed to initialize {name}: {e}")

        # Start health monitoring
        asyncio.create_task(self._health_monitoring())

    async def _load_configurations(self):
        """Load integration configurations from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_data = yaml.safe_load(f)

                for integration_name, config in config_data.get('integrations', {}).items():
                    if integration_name in self.integrations:
                        # Decrypt API keys
                        if 'api_keys' in config:
                            config['api_keys'] = {
                                key: self._decrypt_value(value)
                                for key, value in config['api_keys'].items()
                            }

                        self.integrations[integration_name].config = config
            else:
                self.logger.warning(f"Configuration file not found: {self.config_path}")
                await self._create_default_config()
        except Exception as e:
            self.logger.error(f"Failed to load configurations: {e}")

    async def _create_default_config(self):
        """Create default configuration file"""
        default_config = {
            'integrations': {
                'social_platforms': {
                    'enabled': False,
                    'api_keys': {
                        'discord_bot_token': 'encrypted_token_here',
                        'twitter_api_key': 'encrypted_key_here',
                        'twitter_api_secret': 'encrypted_secret_here',
                        'reddit_client_id': 'encrypted_id_here',
                        'reddit_client_secret': 'encrypted_secret_here'
                    },
                    'rate_limits': {
                        'discord': 5,  # requests per second
                        'twitter': 300,  # requests per 15 minutes
                        'reddit': 60  # requests per minute
                    },
                    'webhook_endpoints': [],
                    'retry_attempts': 3,
                    'timeout_seconds': 30,
                    'cache_ttl': 300
                },
                'streaming_services': {
                    'enabled': False,
                    'api_keys': {
                        'twitch_client_id': 'encrypted_id_here',
                        'twitch_client_secret': 'encrypted_secret_here',
                        'youtube_api_key': 'encrypted_key_here'
                    },
                    'rate_limits': {
                        'twitch': 800,  # requests per minute
                        'youtube': 10000  # requests per day
                    },
                    'webhook_endpoints': [],
                    'retry_attempts': 3,
                    'timeout_seconds': 30,
                    'cache_ttl': 600
                },
                'payment_systems': {
                    'enabled': False,
                    'api_keys': {
                        'stripe_secret_key': 'encrypted_key_here',
                        'stripe_publishable_key': 'encrypted_key_here',
                        'paypal_client_id': 'encrypted_id_here',
                        'paypal_client_secret': 'encrypted_secret_here',
                        'coinbase_api_key': 'encrypted_key_here'
                    },
                    'rate_limits': {
                        'stripe': 100,
                        'paypal': 100,
                        'coinbase': 60
                    },
                    'webhook_endpoints': ['/webhook/stripe', '/webhook/paypal'],
                    'retry_attempts': 3,
                    'timeout_seconds': 60,
                    'cache_ttl': 300
                },
                'analytics_services': {
                    'enabled': False,
                    'api_keys': {
                        'google_analytics_measurement_id': 'encrypted_id_here',
                        'google_analytics_api_secret': 'encrypted_secret_here',
                        'mixpanel_token': 'encrypted_token_here',
                        'amplitude_api_key': 'encrypted_key_here'
                    },
                    'rate_limits': {
                        'google_analytics': 100000,
                        'mixpanel': 1000,
                        'amplitude': 1000
                    },
                    'webhook_endpoints': [],
                    'retry_attempts': 3,
                    'timeout_seconds': 30,
                    'cache_ttl': 3600
                },
                'cdn_manager': {
                    'enabled': False,
                    'api_keys': {
                        'cloudflare_api_token': 'encrypted_token_here',
                        'aws_access_key': 'encrypted_key_here',
                        'aws_secret_key': 'encrypted_key_here',
                        'fastly_api_key': 'encrypted_key_here'
                    },
                    'rate_limits': {
                        'cloudflare': 1200,
                        'aws': 100,
                        'fastly': 1000
                    },
                    'webhook_endpoints': [],
                    'retry_attempts': 3,
                    'timeout_seconds': 30,
                    'cache_ttl': 300
                },
                'ai_services': {
                    'enabled': False,
                    'api_keys': {
                        'huggingface_api_key': 'encrypted_key_here',
                        'stability_api_key': 'encrypted_key_here',
                        'openai_api_key': 'encrypted_key_here',
                        'anthropic_api_key': 'encrypted_key_here'
                    },
                    'rate_limits': {
                        'huggingface': 1000,
                        'stability': 100,
                        'openai': 3500,
                        'anthropic': 1000
                    },
                    'webhook_endpoints': [],
                    'retry_attempts': 3,
                    'timeout_seconds': 120,
                    'cache_ttl': 1800
                },
                'moderation_tools': {
                    'enabled': False,
                    'api_keys': {
                        'perspective_api_key': 'encrypted_key_here',
                        'content_safety_endpoint': 'encrypted_endpoint_here',
                        'sightengine_api_user': 'encrypted_user_here',
                        'sightengine_api_secret': 'encrypted_secret_here'
                    },
                    'rate_limits': {
                        'perspective': 100,
                        'content_safety': 100,
                        'sightengine': 500
                    },
                    'webhook_endpoints': [],
                    'retry_attempts': 3,
                    'timeout_seconds': 30,
                    'cache_ttl': 300
                }
            }
        }

        # Encrypt API keys for storage
        for integration_name, config in default_config['integrations'].items():
            if 'api_keys' in config:
                config['api_keys'] = {
                    key: self._encrypt_value(value)
                    for key, value in config['api_keys'].items()
                }

        with open(self.config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)

        self.logger.info(f"Created default configuration file: {self.config_path}")

    def _encrypt_value(self, value: str) -> str:
        """Encrypt sensitive configuration values"""
        return self.cipher_suite.encrypt(value.encode()).decode()

    def _decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt sensitive configuration values"""
        return self.cipher_suite.decrypt(encrypted_value.encode()).decode()

    async def get_integration(self, name: str):
        """Get integration instance by name"""
        return self.integrations.get(name)

    async def enable_integration(self, name: str):
        """Enable a specific integration"""
        if name in self.integrations:
            integration = self.integrations[name]
            integration.config['enabled'] = True
            await integration.enable()
            self.logger.info(f"Enabled integration: {name}")

    async def disable_integration(self, name: str):
        """Disable a specific integration"""
        if name in self.integrations:
            integration = self.integrations[name]
            integration.config['enabled'] = False
            await integration.disable()
            self.logger.info(f"Disabled integration: {name}")

    async def get_integration_status(self, name: str) -> IntegrationStatus:
        """Get status of a specific integration"""
        if name in self.integrations:
            return self.integrations[name].get_status()
        return IntegrationStatus.INACTIVE

    async def get_all_status(self) -> Dict[str, IntegrationStatus]:
        """Get status of all integrations"""
        return {
            name: integration.get_status()
            for name, integration in self.integrations.items()
        }

    async def execute_webhook(self, integration_name: str, event_type: str, data: Dict[str, Any]):
        """Execute webhook for specific integration"""
        if integration_name in self.integrations:
            integration = self.integrations[integration_name]
            if hasattr(integration, 'handle_webhook'):
                return await integration.handle_webhook(event_type, data)
        return None

    async def _health_monitoring(self):
        """Monitor health of all integrations"""
        while True:
            try:
                for name, integration in self.integrations.items():
                    if integration.config.get('enabled', False):
                        health = await integration.health_check()
                        if name not in self.metrics:
                            self.metrics[name] = IntegrationMetrics(
                                name=name,
                                requests_total=0,
                                requests_successful=0,
                                requests_failed=0,
                                average_response_time=0.0,
                                last_success=None,
                                last_error=None,
                                rate_limit_hits=0
                            )

                        # Update metrics based on health check
                        if health['status'] == 'healthy':
                            self.metrics[name].last_success = datetime.now()
                        else:
                            self.metrics[name].last_error = health.get('error')

                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)

    async def get_metrics(self, integration_name: Optional[str] = None) -> Union[Dict[str, IntegrationMetrics], IntegrationMetrics]:
        """Get metrics for integrations"""
        if integration_name:
            return self.metrics.get(integration_name)
        return self.metrics

    async def cache_get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if self.redis_client:
            try:
                value = await self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                self.logger.error(f"Cache get error: {e}")
        return None

    async def cache_set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache"""
        if self.redis_client:
            try:
                await self.redis_client.setex(key, ttl, json.dumps(value))
            except Exception as e:
                self.logger.error(f"Cache set error: {e}")

    async def make_api_request(self, url: str, method: str = 'GET',
                             headers: Optional[Dict] = None,
                             data: Optional[Dict] = None,
                             integration_name: str = 'unknown') -> Dict[str, Any]:
        """Make API request with rate limiting and error handling"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        start_time = datetime.now()

        try:
            # Check rate limits
            if integration_name in self.integrations:
                await self.integrations[integration_name].check_rate_limit()

            async with self.session.request(
                method, url, headers=headers, json=data
            ) as response:
                response_time = (datetime.now() - start_time).total_seconds()

                # Update metrics
                if integration_name in self.metrics:
                    self.metrics[integration_name].requests_total += 1
                    self.metrics[integration_name].average_response_time = (
                        (self.metrics[integration_name].average_response_time + response_time) / 2
                    )

                if response.status == 200:
                    if integration_name in self.metrics:
                        self.metrics[integration_name].requests_successful += 1
                        self.metrics[integration_name].last_success = datetime.now()
                    return await response.json()
                else:
                    if integration_name in self.metrics:
                        self.metrics[integration_name].requests_failed += 1
                        self.metrics[integration_name].last_error = f"HTTP {response.status}"
                    return {'error': f"HTTP {response.status}", 'status': response.status}

        except asyncio.TimeoutError:
            if integration_name in self.metrics:
                self.metrics[integration_name].requests_failed += 1
                self.metrics[integration_name].last_error = "Timeout"
            return {'error': 'Request timeout', 'status': 408}
        except Exception as e:
            if integration_name in self.metrics:
                self.metrics[integration_name].requests_failed += 1
                self.metrics[integration_name].last_error = str(e)
            return {'error': str(e), 'status': 500}

    async def shutdown(self):
        """Shutdown the integration manager"""
        self.logger.info("Shutting down Integration Manager")

        # Shutdown all integrations
        for name, integration in self.integrations.items():
            try:
                await integration.shutdown()
            except Exception as e:
                self.logger.error(f"Error shutting down {name}: {e}")

        # Close HTTP session
        if self.session:
            await self.session.close()

        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()

# Rate limiter class
class RateLimiter:
    """Rate limiting for API calls"""

    def __init__(self, requests_per_second: int):
        self.requests_per_second = requests_per_second
        self.requests = []

    async def acquire(self):
        """Acquire rate limit permit"""
        now = datetime.now()

        # Remove old requests
        self.requests = [req_time for req_time in self.requests
                        if (now - req_time).total_seconds() < 1]

        if len(self.requests) >= self.requests_per_second:
            sleep_time = 1 - (now - self.requests[0]).total_seconds()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        self.requests.append(now)