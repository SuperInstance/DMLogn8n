#!/usr/bin/env python3
"""
DMLogn8n Integration System
Comprehensive third-party integration management for external services and APIs
"""

__version__ = "1.0.0"
__author__ = "DMLogn8n Development Team"
__description__ = "Multi-portal integration system for DMLogn8n platform"

from .integration_manager import IntegrationManager, IntegrationStatus, IntegrationConfig, IntegrationMetrics
from .social_platforms import SocialPlatformsIntegration, SocialPost
from .streaming_services import StreamingServicesIntegration, StreamSession, StreamAlert
from .payment_systems import PaymentSystemsIntegration, PaymentTransaction, Subscription, PaymentMethod
from .analytics_services import AnalyticsServicesIntegration, AnalyticsEvent, UserProperties, FunnelData
from .cdn_manager import CDNManager, CDNAsset, CDNZone
from .ai_services import AIServicesIntegration, AIModel, AIRequest
from .moderation_tools import ModerationToolsIntegration, ModerationResult, ModerationRule

# Integration registry
INTEGRATION_MODULES = {
    'social_platforms': SocialPlatformsIntegration,
    'streaming_services': StreamingServicesIntegration,
    'payment_systems': PaymentSystemsIntegration,
    'analytics_services': AnalyticsServicesIntegration,
    'cdn_manager': CDNManager,
    'ai_services': AIServicesIntegration,
    'moderation_tools': ModerationToolsIntegration
}

# Supported platforms and providers
SUPPORTED_SOCIAL_PLATFORMS = ['discord', 'twitter', 'reddit', 'facebook', 'instagram', 'linkedin']
SUPPORTED_STREAMING_PLATFORMS = ['twitch', 'youtube', 'facebook_live', 'tiktok']
SUPPORTED_PAYMENT_PROVIDERS = ['stripe', 'paypal', 'coinbase', 'square', 'adyen']
SUPPORTED_ANALYTICS_PLATFORMS = ['google_analytics', 'mixpanel', 'amplitude', 'segment']
SUPPORTED_CDN_PROVIDERS = ['cloudflare', 'aws_cloudfront', 'fastly', 'akamai']
SUPPORTED_AI_PROVIDERS = ['openai', 'anthropic', 'huggingface', 'stability_ai', 'cohere']
SUPPORTED_MODERATION_PROVIDERS = ['perspective_api', 'content_safety', 'sightengine', 'aws_rekognition']

# Integration capabilities
INTEGRATION_CAPABILITIES = {
    'social_platforms': [
        'cross_platform_posting',
        'content_scheduling',
        'audience_analytics',
        'engagement_tracking',
        'community_management',
        'social_monitoring'
    ],
    'streaming_services': [
        'live_streaming',
        'stream_scheduling',
        'audience_interaction',
        'stream_analytics',
        'multi_streaming',
        'recording_management'
    ],
    'payment_systems': [
        'payment_processing',
        'subscription_management',
        'refund_processing',
        'payment_analytics',
        'multi_currency',
        'recurring_billing'
    ],
    'analytics_services': [
        'event_tracking',
        'user_analytics',
        'funnel_analysis',
        'conversion_tracking',
        'custom_dashboards',
        'behavior_analysis'
    ],
    'cdn_manager': [
        'asset_upload',
        'cache_management',
        'global_delivery',
        'performance_optimization',
        'bandwidth_analytics',
        'purge_management'
    ],
    'ai_services': [
        'text_generation',
        'image_generation',
        'content_analysis',
        'sentiment_analysis',
        'translation',
        'summarization'
    ],
    'moderation_tools': [
        'content_filtering',
        'toxicity_detection',
        'spam_detection',
        'hate_speech_detection',
        'personal_info_detection',
        'custom_rules'
    ]
}

# Webhook event types
WEBHOOK_EVENTS = {
    'social_platforms': [
        'share_content',
        'schedule_post',
        'social_activity',
        'stream_alert',
        'payment_notification'
    ],
    'streaming_services': [
        'start_stream',
        'stop_stream',
        'schedule_stream',
        'stream_milestone',
        'viewer_alert'
    ],
    'payment_systems': [
        'payment_completed',
        'payment_failed',
        'subscription_started',
        'subscription_ended',
        'refund_processed'
    ],
    'analytics_services': [
        'track_event',
        'update_user_properties',
        'funnel_step_completed',
        'payment_event',
        'moderation_event'
    ],
    'cdn_manager': [
        'upload_asset',
        'purge_asset',
        'cdn_upload',
        'cdn_zone_created'
    ],
    'ai_services': [
        'generate_text',
        'generate_image',
        'analyze_content',
        'process_request'
    ],
    'moderation_tools': [
        'moderate_content',
        'content_flagged',
        'content_approved',
        'content_rejected'
    ]
}

# Rate limiting configurations
DEFAULT_RATE_LIMITS = {
    'social_platforms': {
        'discord': 5,  # requests per second
        'twitter': 300,  # requests per 15 minutes
        'reddit': 60,  # requests per minute
        'facebook': 200,  # requests per hour
        'instagram': 200,  # requests per hour
        'linkedin': 100  # requests per hour
    },
    'streaming_services': {
        'twitch': 800,  # requests per minute
        'youtube': 10000,  # requests per day
        'facebook_live': 200,  # requests per hour
        'tiktok': 1000  # requests per day
    },
    'payment_systems': {
        'stripe': 100,  # requests per second
        'paypal': 100,  # requests per second
        'coinbase': 60,  # requests per minute
        'square': 100,  # requests per second
        'adyen': 100  # requests per second
    },
    'analytics_services': {
        'google_analytics': 100000,  # requests per day
        'mixpanel': 1000,  # requests per minute
        'amplitude': 1000,  # requests per minute
        'segment': 1000  # requests per minute
    },
    'cdn_manager': {
        'cloudflare': 1200,  # requests per minute
        'aws_cloudfront': 100,  # requests per second
        'fastly': 1000,  # requests per minute
        'akamai': 500  # requests per minute
    },
    'ai_services': {
        'openai': 3500,  # requests per minute
        'anthropic': 1000,  # requests per minute
        'huggingface': 1000,  # requests per minute
        'stability_ai': 100,  # requests per minute
        'cohere': 1000  # requests per minute
    },
    'moderation_tools': {
        'perspective_api': 100,  # requests per minute
        'content_safety': 100,  # requests per second
        'sightengine': 500,  # requests per minute
        'aws_rekognition': 100  # requests per second
    }
}

# Error codes
INTEGRATION_ERROR_CODES = {
    'CONFIG_MISSING': 'E001',
    'API_KEY_INVALID': 'E002',
    'RATE_LIMIT_EXCEEDED': 'E003',
    'SERVICE_UNAVAILABLE': 'E004',
    'AUTHENTICATION_FAILED': 'E005',
    'PERMISSION_DENIED': 'E006',
    'REQUEST_TIMEOUT': 'E007',
    'INVALID_REQUEST': 'E008',
    'QUOTA_EXCEEDED': 'E009',
    'SERVICE_ERROR': 'E010'
}

# Security configurations
SECURITY_SETTINGS = {
    'encryption_required': True,
    'api_key_rotation_days': 90,
    'webhook_signature_verification': True,
    'request_logging_enabled': True,
    'sensitive_data_masking': True,
    'rate_limiting_enabled': True,
    'ip_whitelist_enabled': False,
    'audit_logging_enabled': True
}

# Cache settings
CACHE_SETTINGS = {
    'default_ttl': 300,  # 5 minutes
    'analytics_ttl': 3600,  # 1 hour
    'user_data_ttl': 1800,  # 30 minutes
    'config_ttl': 86400,  # 24 hours
    'max_cache_size': 10000,  # maximum number of items
    'cleanup_interval': 300  # cleanup interval in seconds
}

def get_integration_info():
    """Get comprehensive integration system information"""
    return {
        'version': __version__,
        'description': __description__,
        'supported_modules': list(INTEGRATION_MODULES.keys()),
        'supported_platforms': {
            'social': SUPPORTED_SOCIAL_PLATFORMS,
            'streaming': SUPPORTED_STREAMING_PLATFORMS,
            'payment': SUPPORTED_PAYMENT_PROVIDERS,
            'analytics': SUPPORTED_ANALYTICS_PLATFORMS,
            'cdn': SUPPORTED_CDN_PROVIDERS,
            'ai': SUPPORTED_AI_PROVIDERS,
            'moderation': SUPPORTED_MODERATION_PROVIDERS
        },
        'capabilities': INTEGRATION_CAPABILITIES,
        'webhook_events': WEBHOOK_EVENTS,
        'rate_limits': DEFAULT_RATE_LIMITS,
        'error_codes': INTEGRATION_ERROR_CODES,
        'security_settings': SECURITY_SETTINGS,
        'cache_settings': CACHE_SETTINGS
    }

def create_integration_manager(config_path: str = "integrations_config.yaml"):
    """Create and return an integration manager instance"""
    return IntegrationManager(config_path=config_path)

def list_available_integrations():
    """List all available integration modules"""
    return list(INTEGRATION_MODULES.keys())

def get_integration_capabilities(integration_name: str):
    """Get capabilities for a specific integration"""
    return INTEGRATION_CAPABILITIES.get(integration_name, [])

def get_supported_platforms(service_type: str):
    """Get supported platforms for a service type"""
    platform_map = {
        'social': SUPPORTED_SOCIAL_PLATFORMS,
        'streaming': SUPPORTED_STREAMING_PLATFORMS,
        'payment': SUPPORTED_PAYMENT_PROVIDERS,
        'analytics': SUPPORTED_ANALYTICS_PLATFORMS,
        'cdn': SUPPORTED_CDN_PROVIDERS,
        'ai': SUPPORTED_AI_PROVIDERS,
        'moderation': SUPPORTED_MODERATION_PROVIDERS
    }
    return platform_map.get(service_type, [])

# Export main classes and functions
__all__ = [
    # Main classes
    'IntegrationManager',
    'IntegrationStatus',
    'IntegrationConfig',
    'IntegrationMetrics',

    # Integration modules
    'SocialPlatformsIntegration',
    'StreamingServicesIntegration',
    'PaymentSystemsIntegration',
    'AnalyticsServicesIntegration',
    'CDNManager',
    'AIServicesIntegration',
    'ModerationToolsIntegration',

    # Data models
    'SocialPost',
    'StreamSession',
    'StreamAlert',
    'PaymentTransaction',
    'Subscription',
    'PaymentMethod',
    'AnalyticsEvent',
    'UserProperties',
    'FunnelData',
    'CDNAsset',
    'CDNZone',
    'AIModel',
    'AIRequest',
    'ModerationResult',
    'ModerationRule',

    # Constants and configurations
    'INTEGRATION_MODULES',
    'SUPPORTED_SOCIAL_PLATFORMS',
    'SUPPORTED_STREAMING_PLATFORMS',
    'SUPPORTED_PAYMENT_PROVIDERS',
    'SUPPORTED_ANALYTICS_PLATFORMS',
    'SUPPORTED_CDN_PROVIDERS',
    'SUPPORTED_AI_PROVIDERS',
    'SUPPORTED_MODERATION_PROVIDERS',
    'INTEGRATION_CAPABILITIES',
    'WEBHOOK_EVENTS',
    'DEFAULT_RATE_LIMITS',
    'INTEGRATION_ERROR_CODES',
    'SECURITY_SETTINGS',
    'CACHE_SETTINGS',

    # Utility functions
    'get_integration_info',
    'create_integration_manager',
    'list_available_integrations',
    'get_integration_capabilities',
    'get_supported_platforms'
]