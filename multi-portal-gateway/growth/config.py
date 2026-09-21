"""
DMLogn8n Growth System Configuration
Central configuration management for the growth system
"""

import os
from typing import Dict, Any
from datetime import timedelta

class GrowthConfig:
    """Central configuration class for DMLogn8n Growth System"""

    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = self.environment == "development"

        # Database Configuration
        self.database = {
            "url": os.getenv("DATABASE_URL", "sqlite:///growth.db"),
            "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20"))
        }

        # Email Configuration
        self.email = {
            "provider": os.getenv("EMAIL_PROVIDER", "sendgrid"),
            "api_key": os.getenv("EMAIL_API_KEY"),
            "from_email": os.getenv("FROM_EMAIL", "noreply@dmlogn8n.com"),
            "from_name": os.getenv("FROM_NAME", "DMLogn8n Team"),
            "reply_to": os.getenv("REPLY_TO", "support@dmlogn8n.com")
        }

        # Social Media Configuration
        self.social = {
            "twitter": {
                "api_key": os.getenv("TWITTER_API_KEY"),
                "api_secret": os.getenv("TWITTER_API_SECRET"),
                "access_token": os.getenv("TWITTER_ACCESS_TOKEN"),
                "access_token_secret": os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
                "bearer_token": os.getenv("TWITTER_BEARER_TOKEN")
            },
            "facebook": {
                "app_id": os.getenv("FACEBOOK_APP_ID"),
                "app_secret": os.getenv("FACEBOOK_APP_SECRET"),
                "access_token": os.getenv("FACEBOOK_ACCESS_TOKEN"),
                "page_id": os.getenv("FACEBOOK_PAGE_ID")
            },
            "linkedin": {
                "client_id": os.getenv("LINKEDIN_CLIENT_ID"),
                "client_secret": os.getenv("LINKEDIN_CLIENT_SECRET"),
                "access_token": os.getenv("LINKEDIN_ACCESS_TOKEN")
            },
            "reddit": {
                "client_id": os.getenv("REDDIT_CLIENT_ID"),
                "client_secret": os.getenv("REDDIT_CLIENT_SECRET"),
                "user_agent": os.getenv("REDDIT_USER_AGENT", "DMLogn8n Bot/1.0")
            }
        }

        # Discord Configuration
        self.discord = {
            "bot_token": os.getenv("DISCORD_BOT_TOKEN"),
            "server_id": os.getenv("DISCORD_SERVER_ID"),
            "webhook_url": os.getenv("DISCORD_WEBHOOK_URL"),
            "admin_roles": os.getenv("DISCORD_ADMIN_ROLES", "Admin,Moderator").split(","),
            "channels": {
                "announcements": os.getenv("DISCORD_ANNOUNCEMENTS_CHANNEL"),
                "general": os.getenv("DISCORD_GENERAL_CHANNEL"),
                "welcome": os.getenv("DISCORD_WELCOME_CHANNEL")
            }
        }

        # Analytics Configuration
        self.analytics = {
            "google_analytics": {
                "tracking_id": os.getenv("GA_TRACKING_ID"),
                "enable_demo": self.debug
            },
            "mixpanel": {
                "token": os.getenv("MIXPANEL_TOKEN"),
                "enable_demo": self.debug
            },
            "custom": {
                "events": ["sign_up", "feature_use", "conversion", "referral"],
                "properties": ["source", "medium", "campaign", "content"]
            }
        }

        # Redis Configuration (for caching and queues)
        self.redis = {
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "db": int(os.getenv("REDIS_DB", "0")),
            "password": os.getenv("REDIS_PASSWORD"),
            "decode_responses": True
        }

        # Growth System Settings
        self.growth = {
            "referral_programs": {
                "default_incentive": {
                    "referrer": {"type": "account_credits", "amount": 10.0},
                    "referred": {"type": "free_trial", "days": 14}
                },
                "cookie_duration": 30,  # days
                "attribution_window": 90  # days
            },
            "marketing_automation": {
                "email_batch_size": 100,
                "send_interval": 1,  # seconds between batches
                "max_retry_attempts": 3,
                "retry_delay": 300  # seconds
            },
            "social_media": {
                "post_interval": 3600,  # seconds between posts
                "max_daily_posts": 10,
                "auto_reply_enabled": True,
                "mention_response_time": 300  # seconds
            },
            "community": {
                "automated_welcome": True,
                "engagement_campaigns": True,
                "content_moderation": True,
                "member_milestones": [1, 10, 50, 100, 500, 1000]
            },
            "experiments": {
                "min_sample_size": 100,
                "confidence_level": 0.95,
                "max_duration_days": 30,
                "auto_termination": True
            }
        }

        # Brand Configuration
        self.brand = {
            "name": "DMLogn8n",
            "tagline": "AI-Powered Dungeon Master Automation",
            "website": "https://dmlogn8n.com",
            "support_email": "support@dmlogn8n.com",
            "social_profiles": {
                "twitter": "https://twitter.com/dmlogn8n",
                "discord": "https://discord.gg/dmlogn8n",
                "youtube": "https://youtube.com/dmlogn8n",
                "reddit": "https://reddit.com/r/dmlogn8n"
            },
            "colors": {
                "primary": "#6366F1",
                "secondary": "#8B5CF6",
                "accent": "#EC4899"
            },
            "voice": {
                "personality": ["innovative", "helpful", "approachable", "creative"],
                "tone": "helpful and encouraging",
                "formality": "conversational"
            }
        }

        # Security Configuration
        self.security = {
            "secret_key": os.getenv("SECRET_KEY", "your-secret-key-here"),
            "jwt_expiration": timedelta(hours=24),
            "api_rate_limit": os.getenv("API_RATE_LIMIT", "100/hour"),
            "cors_origins": os.getenv("CORS_ORIGINS", "*").split(","),
            "require_https": not self.debug
        }

        # Feature Flags
        self.features = {
            "advanced_analytics": os.getenv("FEATURE_ADVANCED_ANALYTICS", "true").lower() == "true",
            "ai_powered_content": os.getenv("FEATURE_AI_CONTENT", "false").lower() == "true",
            "real_time_notifications": os.getenv("FEATURE_REAL_TIME", "true").lower() == "true",
            "multi_language": os.getenv("FEATURE_MULTI_LANG", "false").lower() == "true",
            "enterprise_features": os.getenv("FEATURE_ENTERPRISE", "false").lower() == "true"
        }

        # Logging Configuration
        self.logging = {
            "level": "DEBUG" if self.debug else "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": os.getenv("LOG_FILE", "growth.log"),
            "max_file_size": int(os.getenv("LOG_MAX_SIZE", "10485760")),  # 10MB
            "backup_count": int(os.getenv("LOG_BACKUP_COUNT", "5"))
        }

        # API Configuration
        self.api = {
            "base_url": os.getenv("API_BASE_URL", "https://api.dmlogn8n.com"),
            "version": "v1",
            "timeout": int(os.getenv("API_TIMEOUT", "30")),
            "retry_attempts": int(os.getenv("API_RETRY_ATTEMPTS", "3")),
            "retry_delay": int(os.getenv("API_RETRY_DELAY", "1"))
        }

        # Third-party Integrations
        self.integrations = {
            "stripe": {
                "public_key": os.getenv("STRIPE_PUBLIC_KEY"),
                "secret_key": os.getenv("STRIPE_SECRET_KEY"),
                "webhook_secret": os.getenv("STRIPE_WEBHOOK_SECRET")
            },
            "sendgrid": {
                "api_key": os.getenv("SENDGRID_API_KEY"),
                "templates": {
                    "welcome": "d-1234567890abcdef1234567890abcdef",
                    "newsletter": "d-abcdef1234567890abcdef1234567890"
                }
            },
            "google_ads": {
                "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
                "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
                "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN")
            },
            "facebook_ads": {
                "app_id": os.getenv("FACEBOOK_ADS_APP_ID"),
                "app_secret": os.getenv("FACEBOOK_ADS_APP_SECRET"),
                "access_token": os.getenv("FACEBOOK_ADS_ACCESS_TOKEN"),
                "ad_account_id": os.getenv("FACEBOOK_ADS_ACCOUNT_ID")
            }
        }

# Global configuration instance
config = GrowthConfig()

def get_config() -> GrowthConfig:
    """Get the global configuration instance"""
    return config

def is_development() -> bool:
    """Check if running in development mode"""
    return config.environment == "development"

def is_production() -> bool:
    """Check if running in production mode"""
    return config.environment == "production"

def get_database_url() -> str:
    """Get database URL with environment handling"""
    return os.getenv("DATABASE_URL", config.database["url"])

def get_redis_config() -> Dict[str, Any]:
    """Get Redis configuration"""
    return config.redis

def get_email_config() -> Dict[str, Any]:
    """Get email configuration"""
    return config.email

def get_social_config(platform: str) -> Dict[str, Any]:
    """Get social media platform configuration"""
    return config.social.get(platform, {})

def is_feature_enabled(feature: str) -> bool:
    """Check if a feature flag is enabled"""
    return config.features.get(feature, False)