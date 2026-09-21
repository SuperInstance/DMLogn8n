"""
DMLogn8n Advertising System - Non-Intrusive Advertising Integration

This module manages advertising integration that respects user experience and privacy,
providing ethical advertising options and brand partnerships.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
from decimal import Decimal
import pandas as pd
import numpy as np
from collections import defaultdict
import redis
import aiohttp
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import aioredis
import hashlib
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class AdType(Enum):
    """Advertisement types"""
    BANNER = "banner"
    VIDEO = "video"
    SPONSORED_CONTENT = "sponsored_content"
    PRODUCT_PLACEMENT = "product_placement"
    BRAND_PARTNERSHIP = "brand_partnership"
    AFFILIATE_LINK = "affiliate_link"
    NATIVE_AD = "native_ad"

class AdFormat(Enum):
    """Advertisement formats"""
    IMAGE = "image"
    VIDEO = "video"
    TEXT = "text"
    INTERACTIVE = "interactive"
    AUDIO = "audio"
    RICH_MEDIA = "rich_media"

class AdPosition(Enum):
    """Advertisement positions"""
    HEADER = "header"
    SIDEBAR = "sidebar"
    FOOTER = "footer"
    IN_CONTENT = "in_content"
    BETWEEN_SESSIONS = "between_sessions"
    LOADING_SCREEN = "loading_screen"
    PAUSE_MENU = "pause_menu"

class UserAdPreference(Enum):
    """User ad preferences"""
    ALL_ADS = "all_ads"
    MINIMAL_ADS = "minimal_ads"
    NO_ADS = "no_ads"
    PERSONALIZED_ADS = "personalized_ads"
    CONTEXT_RELEVANT_ONLY = "context_relevant_only"

class AdCategory(Enum):
    """Advertisement categories"""
    GAMING = "gaming"
    TECHNOLOGY = "technology"
    ENTERTAINMENT = "entertainment"
    EDUCATION = "education"
    LIFESTYLE = "lifestyle"
    FINANCE = "finance"
    TRAVEL = "travel"
    FOOD = "food"
    HEALTH = "health"
    FITNESS = "fitness"

@dataclass
class AdCampaign:
    """Advertisement campaign definition"""
    id: str
    name: str
    advertiser_id: str
    ad_type: AdType
    format: AdFormat
    category: AdCategory
    content: Dict[str, Any]
    target_audience: Dict[str, Any] = field(default_factory=dict)
    budget: Decimal = Decimal('0.00')
    bid_amount: Decimal = Decimal('0.00')
    start_date: datetime = field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None
    active: bool = True
    frequency_cap: int = 5  # max impressions per user per day
    geo_targeting: List[str] = field(default_factory=list)
    device_targeting: List[str] = field(default_factory=list)
    age_targeting: Optional[Tuple[int, int]] = None
    gender_targeting: Optional[str] = None
    interests: List[str] = field(default_factory=list)
    metrics: Dict[str, int] = field(default_factory=dict)

@dataclass
class AdImpression:
    """Advertisement impression record"""
    id: str
    campaign_id: str
    user_id: str
    ad_type: AdType
    position: AdPosition
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ip_address: str = ""
    user_agent: str = ""
    country: str = ""
    device_type: str = ""
    clicked: bool = False
    conversion_value: Decimal = Decimal('0.00')
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UserAdProfile:
    """User advertising profile (privacy-respecting)"""
    user_id: str
    preferences: UserAdPreference = UserAdPreference.MINIMAL_ADS
    blocked_categories: List[AdCategory] = field(default_factory=list)
    blocked_advertisers: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    demographics: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    consent_given: bool = False
    gdpr_compliant: bool = True

class AdvertisingSystem:
    """Main advertising system manager"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_client = None
        self.db_engine = None
        self.session_factory = None
        self.campaigns: Dict[str, AdCampaign] = {}
        self.ad_networks: Dict[str, Dict] = {}
        self.user_profiles: Dict[str, UserAdProfile] = {}
        self.revenue_tracker = {}
        self.privacy_settings = config.get('privacy', {})

    async def initialize(self):
        """Initialize advertising system"""
        logger.info("Initializing DMLogn8n Advertising System...")

        # Initialize Redis
        self.redis_client = aioredis.from_url(
            self.config.get('redis_url', 'redis://localhost:6379')
        )

        # Initialize database
        db_url = self.config.get('database_url', 'postgresql://localhost/dmlog_ads')
        self.db_engine = create_engine(db_url)
        self.session_factory = sessionmaker(bind=self.db_engine)

        # Load ad networks
        await self._load_ad_networks()

        # Load campaigns
        await self._load_campaigns()

        # Initialize privacy settings
        await self._initialize_privacy_settings()

        # Start background tasks
        asyncio.create_task(self._campaign_monitor())
        asyncio.create_task(self._revenue_reporter())
        asyncio.create_task(self._ad_quality_monitor())

        logger.info("Advertising System initialized successfully")

    async def _load_ad_networks(self):
        """Load advertising network configurations"""
        default_networks = {
            "google_adsense": {
                "name": "Google AdSense",
                "enabled": True,
                "revenue_share": 0.68,  # 68% to publisher
                "formats": ["banner", "video", "native"],
                "categories": ["technology", "gaming", "entertainment"],
                "min_bid": 0.10,
                "config": {
                    "publisher_id": "ca-pub-xxxxxxxxxxx",
                    "ad_unit_id": "xxxxxxxxxxx"
                }
            },
            "amazon_associates": {
                "name": "Amazon Associates",
                "enabled": True,
                "revenue_share": 0.04,  # 4% commission
                "formats": ["affiliate_link", "product_placement"],
                "categories": ["technology", "gaming", "books"],
                "min_bid": 0.05,
                "config": {
                    "associate_id": "dmlogn8n-20"
                }
            },
            "ethical_ads": {
                "name": "Ethical Ads Network",
                "enabled": True,
                "revenue_share": 0.70,  # 70% to publisher
                "formats": ["banner", "native", "sponsored_content"],
                "categories": ["technology", "education", "sustainability"],
                "min_bid": 0.15,
                "config": {
                    "network_id": "ethical-ads-001"
                }
            }
        }

        for network_id, network_config in default_networks.items():
            self.ad_networks[network_id] = network_config
            await self.redis_client.setex(
                f"ad_network:{network_id}",
                86400 * 365,  # 1 year
                json.dumps(network_config)
            )

    async def _load_campaigns(self):
        """Load advertising campaigns"""
        default_campaigns = [
            AdCampaign(
                id="game_dev_tools",
                name="Game Development Tools",
                advertiser_id="dev_tools_inc",
                ad_type=AdType.BANNER,
                format=AdFormat.IMAGE,
                category=AdCategory.TECHNOLOGY,
                content={
                    "title": "Professional Game Development Suite",
                    "description": "Build amazing games with our professional tools",
                    "image_url": "https://example.com/ad1.jpg",
                    "landing_url": "https://example.com/dev-tools",
                    "cta_text": "Try Free Demo"
                },
                budget=Decimal('10000.00'),
                bid_amount=Decimal('0.50'),
                end_date=datetime.utcnow() + timedelta(days=30),
                frequency_cap=3,
                target_audience={"game_developers": True, "experience_level": "intermediate_plus"}
            ),
            AdCampaign(
                id="rpg_books_sale",
                name="RPG Books Collection",
                advertiser_id="fantasy_books",
                ad_type=AdType.SPONSORED_CONTENT,
                format=AdFormat.TEXT,
                category=AdCategory.ENTERTAINMENT,
                content={
                    "title": "Expand Your RPG Library",
                    "description": "Discover amazing new tabletop RPG books and resources",
                    "landing_url": "https://example.com/rpg-books",
                    "cta_text": "Browse Collection"
                },
                budget=Decimal('5000.00'),
                bid_amount=Decimal('0.30'),
                end_date=datetime.utcnow() + timedelta(days=60),
                frequency_cap=5,
                interests=["tabletop_rpg", "fantasy", "storytelling"]
            ),
            AdCampaign(
                id="gaming_chair",
                name="Premium Gaming Chair",
                advertiser_id="comfort_gaming",
                ad_type=AdType.PRODUCT_PLACEMENT,
                format=AdFormat.IMAGE,
                category=AdCategory.GAMING,
                content={
                    "title": "Level Up Your Comfort",
                    "description": "The ultimate gaming chair for long sessions",
                    "image_url": "https://example.com/chair.jpg",
                    "landing_url": "https://example.com/gaming-chair",
                    "cta_text": "Shop Now"
                },
                budget=Decimal('7500.00'),
                bid_amount=Decimal('0.75'),
                end_date=datetime.utcnow() + timedelta(days=45),
                frequency_cap=2,
                target_audience={"pc_gamers": True, "session_length": "long"}
            )
        ]

        for campaign in default_campaigns:
            self.campaigns[campaign.id] = campaign
            await self._cache_campaign(campaign)

    async def _cache_campaign(self, campaign: AdCampaign):
        """Cache campaign data"""
        campaign_data = {
            'id': campaign.id,
            'name': campaign.name,
            'advertiser_id': campaign.advertiser_id,
            'ad_type': campaign.ad_type.value,
            'format': campaign.format.value,
            'category': campaign.category.value,
            'content': campaign.content,
            'budget': float(campaign.budget),
            'bid_amount': float(campaign.bid_amount),
            'start_date': campaign.start_date.isoformat(),
            'end_date': campaign.end_date.isoformat() if campaign.end_date else None,
            'active': campaign.active,
            'frequency_cap': campaign.frequency_cap,
            'target_audience': campaign.target_audience,
            'interests': campaign.interests
        }

        await self.redis_client.setex(
            f"campaign:{campaign.id}",
            86400 * 30,  # 30 days
            json.dumps(campaign_data)
        )

    async def _initialize_privacy_settings(self):
        """Initialize privacy and GDPR compliance settings"""
        default_settings = {
            'gdpr_compliance': True,
            'cookie_consent_required': True,
            'data_retention_days': 365,
            'anonymize_ip_addresses': True,
            'allow_personalization': False,
            'respect_do_not_track': True,
            'min_data_collection': True,
            'transparency_reports': True
        }

        for key, value in default_settings.items():
            await self.redis_client.hset("privacy_settings", key, str(value))

    async def get_user_ad_profile(self, user_id: str) -> UserAdProfile:
        """Get user's advertising profile"""
        try:
            # Try to get from cache
            cached_profile = await self.redis_client.get(f"ad_profile:{user_id}")
            if cached_profile:
                data = json.loads(cached_profile)
                return UserAdProfile(
                    user_id=data['user_id'],
                    preferences=UserAdPreference(data['preferences']),
                    blocked_categories=[AdCategory(cat) for cat in data['blocked_categories']],
                    blocked_advertisers=data['blocked_advertisers'],
                    interests=data['interests'],
                    demographics=data['demographics'],
                    last_updated=datetime.fromisoformat(data['last_updated']),
                    consent_given=data['consent_given'],
                    gdpr_compliant=data['gdpr_compliant']
                )

            # Create default profile
            profile = UserAdProfile(
                user_id=user_id,
                preferences=UserAdPreference.MINIMAL_ADS,
                consent_given=False
            )

            await self._cache_user_profile(profile)
            return profile

        except Exception as e:
            logger.error(f"Error getting user ad profile: {e}")
            return UserAdProfile(user_id=user_id)

    async def _cache_user_profile(self, profile: UserAdProfile):
        """Cache user profile"""
        profile_data = {
            'user_id': profile.user_id,
            'preferences': profile.preferences.value,
            'blocked_categories': [cat.value for cat in profile.blocked_categories],
            'blocked_advertisers': profile.blocked_advertisers,
            'interests': profile.interests,
            'demographics': profile.demographics,
            'last_updated': profile.last_updated.isoformat(),
            'consent_given': profile.consent_given,
            'gdpr_compliant': profile.gdpr_compliant
        }

        await self.redis_client.setex(
            f"ad_profile:{profile.user_id}",
            86400 * 7,  # 7 days
            json.dumps(profile_data)
        )

    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user advertising preferences"""
        try:
            profile = await self.get_user_ad_profile(user_id)

            # Update preferences
            if 'ad_preference' in preferences:
                profile.preferences = UserAdPreference(preferences['ad_preference'])

            if 'blocked_categories' in preferences:
                profile.blocked_categories = [AdCategory(cat) for cat in preferences['blocked_categories']]

            if 'blocked_advertisers' in preferences:
                profile.blocked_advertisers = preferences['blocked_advertisers']

            if 'interests' in preferences:
                profile.interests = preferences['interests']

            if 'consent_given' in preferences:
                profile.consent_given = preferences['consent_given']

            profile.last_updated = datetime.utcnow()

            await self._cache_user_profile(profile)
            return True

        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return False

    async def get_advertisement(self, user_id: str, position: AdPosition,
                              context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Get appropriate advertisement for user and context"""
        try:
            # Get user profile
            profile = await self.get_user_ad_profile(user_id)

            # Check if user has opted out of ads
            if profile.preferences == UserAdPreference.NO_ADS:
                return None

            # Check consent
            if not profile.consent_given and self.privacy_settings.get('cookie_consent_required', True):
                return None

            # Get eligible campaigns
            eligible_campaigns = await self._get_eligible_campaigns(user_id, profile, position, context)

            if not eligible_campaigns:
                return None

            # Select best campaign (simplified auction)
            selected_campaign = await self._run_ad_auction(eligible_campaigns, user_id, context)

            if not selected_campaign:
                return None

            # Check frequency cap
            if await self._check_frequency_cap(user_id, selected_campaign.id):
                return None

            # Record impression
            impression_id = await self._record_impression(user_id, selected_campaign, position, context)

            # Return ad data
            return {
                'campaign_id': selected_campaign.id,
                'impression_id': impression_id,
                'ad_type': selected_campaign.ad_type.value,
                'format': selected_campaign.format.value,
                'content': selected_campaign.content,
                'position': position.value,
                'tracking': {
                    'impression_id': impression_id,
                    'click_url': f"/api/ads/click/{impression_id}",
                    'view_url': f"/api/ads/view/{impression_id}"
                }
            }

        except Exception as e:
            logger.error(f"Error getting advertisement: {e}")
            return None

    async def _get_eligible_campaigns(self, user_id: str, profile: UserAdProfile,
                                   position: AdPosition, context: Dict[str, Any]) -> List[AdCampaign]:
        """Get campaigns eligible for user and context"""
        eligible = []

        for campaign in self.campaigns.values():
            if not campaign.active:
                continue

            # Check date range
            if campaign.end_date and datetime.utcnow() > campaign.end_date:
                continue

            # Check budget
            if campaign.budget <= 0:
                continue

            # Check blocked categories
            if campaign.category in profile.blocked_categories:
                continue

            # Check blocked advertisers
            if campaign.advertiser_id in profile.blocked_advertisers:
                continue

            # Check position compatibility
            if not await self._is_position_compatible(campaign, position):
                continue

            # Check targeting
            if not await self._matches_targeting(campaign, user_id, profile, context):
                continue

            eligible.append(campaign)

        return eligible

    async def _is_position_compatible(self, campaign: AdCampaign, position: AdPosition) -> bool:
        """Check if campaign is compatible with position"""
        # Simple compatibility check
        compatible_positions = {
            AdType.BANNER: [AdPosition.HEADER, AdPosition.SIDEBAR, AdPosition.FOOTER],
            AdType.VIDEO: [AdPosition.IN_CONTENT, AdPosition.BETWEEN_SESSIONS],
            AdType.SPONSORED_CONTENT: [AdPosition.IN_CONTENT, AdPosition.FOOTER],
            AdType.PRODUCT_PLACEMENT: [AdPosition.IN_CONTENT, AdPosition.LOADING_SCREEN],
            AdType.NATIVE_AD: [AdPosition.IN_CONTENT, AdPosition.SIDEBAR],
            AdType.AFFILIATE_LINK: [AdPosition.IN_CONTENT, AdPosition.FOOTER],
            AdType.BRAND_PARTNERSHIP: [AdPosition.HEADER, AdPosition.SIDEBAR]
        }

        return position in compatible_positions.get(campaign.ad_type, [])

    async def _matches_targeting(self, campaign: AdCampaign, user_id: str,
                               profile: UserAdProfile, context: Dict[str, Any]) -> bool:
        """Check if user matches campaign targeting"""
        # Check interest targeting
        if campaign.interests:
            user_interests = set(profile.interests)
            campaign_interests = set(campaign.interests)
            if not user_interests.intersection(campaign_interests):
                return False

        # Check demographics (if available and consented)
        if profile.consent_given and profile.demographics:
            if campaign.age_targeting:
                user_age = profile.demographics.get('age')
                if user_age:
                    min_age, max_age = campaign.age_targeting
                    if not (min_age <= user_age <= max_age):
                        return False

            if campaign.gender_targeting:
                user_gender = profile.demographics.get('gender')
                if user_gender and user_gender != campaign.gender_targeting:
                    return False

        # Check context relevance
        if context and 'campaign_type' in context:
            context_category = context.get('category')
            if context_category and campaign.category.value != context_category:
                # Allow some flexibility for related categories
                related_categories = {
                    AdCategory.GAMING: [AdCategory.TECHNOLOGY, AdCategory.ENTERTAINMENT],
                    AdCategory.TECHNOLOGY: [AdCategory.GAMING, AdCategory.EDUCATION],
                    AdCategory.EDUCATION: [AdCategory.TECHNOLOGY, AdCategory.LIFESTYLE],
                    AdCategory.ENTERTAINMENT: [AdCategory.GAMING, AdCategory.LIFESTYLE]
                }

                if campaign.category not in related_categories.get(AdCategory(context_category), []):
                    return False

        return True

    async def _run_ad_auction(self, campaigns: List[AdCampaign], user_id: str,
                            context: Dict[str, Any]) -> Optional[AdCampaign]:
        """Run ad auction to select best campaign"""
        if not campaigns:
            return None

        # Simple auction: select highest bid
        # In real implementation, would consider quality score, relevance, etc.
        best_campaign = max(campaigns, key=lambda c: c.bid_amount)

        # Check if bid meets minimum threshold
        min_bid = self.config.get('min_bid_threshold', 0.10)
        if best_campaign.bid_amount < Decimal(str(min_bid)):
            return None

        return best_campaign

    async def _check_frequency_cap(self, user_id: str, campaign_id: str) -> bool:
        """Check if user has exceeded frequency cap for campaign"""
        today = datetime.utcnow().strftime('%Y-%m-%d')
        key = f"ad_frequency:{user_id}:{campaign_id}:{today}"

        current_count = await self.redis_client.get(key)
        if current_count and int(current_count) >= 5:  # Default frequency cap
            return True

        return False

    async def _record_impression(self, user_id: str, campaign: AdCampaign,
                               position: AdPosition, context: Dict[str, Any]) -> str:
        """Record ad impression"""
        impression_id = str(uuid.uuid4())

        # Create impression record
        impression = AdImpression(
            id=impression_id,
            campaign_id=campaign.id,
            user_id=self._anonymize_user_id(user_id),
            ad_type=campaign.ad_type,
            position=position,
            metadata={
                'context': context,
                'bid_amount': float(campaign.bid_amount)
            }
        )

        # Store impression
        impression_data = {
            'id': impression.id,
            'campaign_id': impression.campaign_id,
            'user_id': impression.user_id,
            'ad_type': impression.ad_type.value,
            'position': impression.position.value,
            'timestamp': impression.timestamp.isoformat(),
            'clicked': impression.clicked,
            'metadata': impression.metadata
        }

        await self.redis_client.setex(
            f"impression:{impression_id}",
            86400 * 7,  # 7 days
            json.dumps(impression_data)
        )

        # Update frequency counter
        today = datetime.utcnow().strftime('%Y-%m-%d')
        freq_key = f"ad_frequency:{user_id}:{campaign.id}:{today}"
        await self.redis_client.incr(freq_key)
        await self.redis_client.expire(freq_key, 86400)

        # Update campaign metrics
        await self.redis_client.hincrby(f"campaign_metrics:{campaign.id}", "impressions", 1)
        await self.redis_client.hincrbyfloat(f"campaign_revenue:{campaign.id}", "spent", float(campaign.bid_amount))

        return impression_id

    def _anonymize_user_id(self, user_id: str) -> str:
        """Anonymize user ID for privacy"""
        # Use hash for anonymity while maintaining consistency
        hash_object = hashlib.sha256(user_id.encode())
        return hash_object.hexdigest()[:16]

    async def record_click(self, impression_id: str, click_data: Dict[str, Any] = None) -> bool:
        """Record ad click"""
        try:
            # Get impression data
            impression_data = await self.redis_client.get(f"impression:{impression_id}")
            if not impression_data:
                return False

            impression_info = json.loads(impression_data)

            # Update impression
            impression_info['clicked'] = True
            if click_data:
                impression_info['metadata']['click_data'] = click_data

            await self.redis_client.setex(
                f"impression:{impression_id}",
                86400 * 7,
                json.dumps(impression_info)
            )

            # Update campaign metrics
            campaign_id = impression_info['campaign_id']
            await self.redis_client.hincrby(f"campaign_metrics:{campaign_id}", "clicks", 1)

            # Calculate revenue (typically higher than impression)
            campaign = self.campaigns.get(campaign_id)
            if campaign:
                click_revenue = campaign.bid_amount * Decimal('2.0')  # 2x bid for clicks
                await self.redis_client.hincrbyfloat(
                    f"campaign_revenue:{campaign_id}",
                    "revenue",
                    float(click_revenue)
                )

            return True

        except Exception as e:
            logger.error(f"Error recording click: {e}")
            return False

    async def record_conversion(self, impression_id: str, conversion_value: Decimal,
                              conversion_data: Dict[str, Any] = None) -> bool:
        """Record ad conversion"""
        try:
            # Get impression data
            impression_data = await self.redis_client.get(f"impression:{impression_id}")
            if not impression_data:
                return False

            impression_info = json.loads(impression_data)

            # Update impression with conversion
            impression_info['conversion_value'] = float(conversion_value)
            if conversion_data:
                impression_info['metadata']['conversion_data'] = conversion_data

            await self.redis_client.setex(
                f"impression:{impression_id}",
                86400 * 7,
                json.dumps(impression_info)
            )

            # Update campaign metrics
            campaign_id = impression_info['campaign_id']
            await self.redis_client.hincrby(f"campaign_metrics:{campaign_id}", "conversions", 1)
            await self.redis_client.hincrbyfloat(
                f"campaign_revenue:{campaign_id}",
                "revenue",
                float(conversion_value)
            )

            return True

        except Exception as e:
            logger.error(f"Error recording conversion: {e}")
            return False

    async def get_ad_performance(self, campaign_id: str = None,
                               start_date: datetime = None,
                               end_date: datetime = None) -> Dict[str, Any]:
        """Get advertising performance metrics"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()

            performance = {
                'total_impressions': 0,
                'total_clicks': 0,
                'total_conversions': 0,
                'total_revenue': Decimal('0.00'),
                'ctr': 0.0,  # Click-through rate
                'conversion_rate': 0.0,
                'cpm': 0.0,  # Cost per mille
                'cpc': 0.0,  # Cost per click
                'campaigns': {}
            }

            if campaign_id:
                campaign_ids = [campaign_id]
            else:
                campaign_ids = list(self.campaigns.keys())

            for cid in campaign_ids:
                metrics = await self.redis_client.hgetall(f"campaign_metrics:{cid}")
                revenue = await self.redis_client.hgetall(f"campaign_revenue:{cid}")

                if metrics:
                    campaign_metrics = {
                        'impressions': int(metrics.get(b'impressions', 0)),
                        'clicks': int(metrics.get(b'clicks', 0)),
                        'conversions': int(metrics.get(b'conversions', 0))
                    }

                    campaign_revenue = Decimal(
                        revenue.get(b'revenue', revenue.get(b'spent', b'0')).decode()
                    )

                    # Calculate rates
                    ctr = campaign_metrics['clicks'] / campaign_metrics['impressions'] if campaign_metrics['impressions'] > 0 else 0
                    conversion_rate = campaign_metrics['conversions'] / campaign_metrics['clicks'] if campaign_metrics['clicks'] > 0 else 0
                    cpm = (campaign_revenue / campaign_metrics['impressions']) * 1000 if campaign_metrics['impressions'] > 0 else 0
                    cpc = campaign_revenue / campaign_metrics['clicks'] if campaign_metrics['clicks'] > 0 else 0

                    campaign_performance = {
                        **campaign_metrics,
                        'revenue': float(campaign_revenue),
                        'ctr': ctr,
                        'conversion_rate': conversion_rate,
                        'cpm': float(cpm),
                        'cpc': float(cpc)
                    }

                    performance['campaigns'][cid] = campaign_performance

                    # Aggregate totals
                    performance['total_impressions'] += campaign_metrics['impressions']
                    performance['total_clicks'] += campaign_metrics['clicks']
                    performance['total_conversions'] += campaign_metrics['conversions']
                    performance['total_revenue'] += campaign_revenue

            # Calculate overall rates
            if performance['total_impressions'] > 0:
                performance['ctr'] = performance['total_clicks'] / performance['total_impressions']
                performance['cpm'] = float((performance['total_revenue'] / performance['total_impressions']) * 1000)

            if performance['total_clicks'] > 0:
                performance['conversion_rate'] = performance['total_conversions'] / performance['total_clicks']
                performance['cpc'] = float(performance['total_revenue'] / performance['total_clicks'])

            return performance

        except Exception as e:
            logger.error(f"Error getting ad performance: {e}")
            return {}

    async def _campaign_monitor(self):
        """Background task to monitor campaigns"""
        while True:
            try:
                logger.info("Running campaign monitor...")

                # Check campaign status
                for campaign_id, campaign in self.campaigns.items():
                    if campaign.end_date and datetime.utcnow() > campaign.end_date:
                        campaign.active = False
                        await self._cache_campaign(campaign)

                # Check budget depletion
                for campaign_id in self.campaigns.keys():
                    revenue_data = await self.redis_client.hgetall(f"campaign_revenue:{campaign_id}")
                    if revenue_data:
                        spent = Decimal(revenue_data.get(b'spent', b'0').decode())
                        campaign = self.campaigns.get(campaign_id)
                        if campaign and spent >= campaign.budget:
                            campaign.active = False
                            await self._cache_campaign(campaign)

                await asyncio.sleep(3600)  # Check every hour

            except Exception as e:
                logger.error(f"Error in campaign monitor: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def _revenue_reporter(self):
        """Background task to report advertising revenue"""
        while True:
            try:
                logger.info("Generating revenue report...")

                # Get daily revenue
                today = datetime.utcnow().strftime('%Y-%m-%d')
                daily_revenue = Decimal('0.00')

                for campaign_id in self.campaigns.keys():
                    revenue_data = await self.redis_client.hgetall(f"campaign_revenue:{campaign_id}")
                    if revenue_data:
                        daily_revenue += Decimal(revenue_data.get(b'revenue', b'0').decode())

                # Store daily revenue
                await self.redis_client.hset(
                    "ad_revenue_daily",
                    today,
                    str(daily_revenue)
                )

                # Generate weekly report
                if datetime.utcnow().weekday() == 0:  # Monday
                    await self._generate_weekly_report()

                await asyncio.sleep(86400)  # Run daily

            except Exception as e:
                logger.error(f"Error in revenue reporter: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error

    async def _generate_weekly_report(self):
        """Generate weekly advertising revenue report"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)

            weekly_revenue = Decimal('0.00')
            campaign_breakdown = {}

            for campaign_id in self.campaigns.keys():
                campaign_revenue = Decimal('0.00')

                # Get impressions for the week
                impression_keys = await self.redis_client.keys(f"impression:*")
                for key in impression_keys:
                    impression_data = await self.redis_client.get(key)
                    if impression_data:
                        impression_info = json.loads(impression_data)
                        impression_date = datetime.fromisoformat(impression_info['timestamp'])

                        if (impression_info['campaign_id'] == campaign_id and
                            start_date <= impression_date <= end_date):
                            campaign_revenue += Decimal(impression_info.get('conversion_value', 0))

                if campaign_revenue > 0:
                    campaign_breakdown[campaign_id] = float(campaign_revenue)
                    weekly_revenue += campaign_revenue

            # Store weekly report
            report = {
                'week_start': start_date.isoformat(),
                'week_end': end_date.isoformat(),
                'total_revenue': float(weekly_revenue),
                'campaign_breakdown': campaign_breakdown,
                'generated_at': datetime.utcnow().isoformat()
            }

            await self.redis_client.lpush(
                "ad_revenue_weekly_reports",
                json.dumps(report)
            )

            logger.info(f"Weekly ad revenue report generated: ${weekly_revenue}")

        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")

    async def _ad_quality_monitor(self):
        """Background task to monitor ad quality and user experience"""
        while True:
            try:
                logger.info("Running ad quality monitor...")

                # Check for low-performing campaigns
                for campaign_id in self.campaigns.keys():
                    metrics = await self.redis_client.hgetall(f"campaign_metrics:{campaign_id}")
                    if metrics:
                        impressions = int(metrics.get(b'impressions', 0))
                        clicks = int(metrics.get(b'clicks', 0))

                        if impressions > 1000:  # Minimum impressions for evaluation
                            ctr = clicks / impressions
                            if ctr < 0.001:  # Very low CTR (< 0.1%)
                                # Flag for review
                                await self.redis_client.sadd("low_performing_campaigns", campaign_id)

                # Monitor user complaints (simplified)
                complaints = await self.redis_client.get("ad_complaints_count")
                if complaints and int(complaints) > 10:
                    logger.warning("High number of ad complaints detected")
                    # Would trigger review process

                await asyncio.sleep(86400)  # Run daily

            except Exception as e:
                logger.error(f"Error in ad quality monitor: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error

    async def get_ad_suggestions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get personalized ad suggestions based on user interests"""
        try:
            profile = await self.get_user_ad_profile(user_id)

            if not profile.interests:
                return []

            suggestions = []
            for interest in profile.interests:
                # Find relevant campaigns
                relevant_campaigns = [
                    campaign for campaign in self.campaigns.values()
                    if campaign.active and interest in campaign.interests
                ]

                for campaign in relevant_campaigns[:2]:  # Top 2 per interest
                    suggestions.append({
                        'campaign_id': campaign.id,
                        'title': campaign.content.get('title', campaign.name),
                        'description': campaign.content.get('description', ''),
                        'category': campaign.category.value,
                        'relevance_score': 0.85  # Simplified relevance score
                    })

            return suggestions[:5]  # Return top 5 suggestions

        except Exception as e:
            logger.error(f"Error getting ad suggestions: {e}")
            return []

# Database models
class AdCampaignDB(Base):
    """Ad campaign database model"""
    __tablename__ = 'ad_campaigns'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    advertiser_id = Column(String, nullable=False)
    ad_type = Column(String, nullable=False)
    format = Column(String, nullable=False)
    category = Column(String, nullable=False)
    content = Column(JSON, nullable=False)
    budget = Column(Float, nullable=False)
    bid_amount = Column(Float, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    active = Column(Boolean, default=True)
    frequency_cap = Column(Integer, default=5)
    target_audience = Column(JSON)
    interests = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class AdImpressionDB(Base):
    """Ad impression database model"""
    __tablename__ = 'ad_impressions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(String, nullable=False)
    user_id_hash = Column(String, nullable=False)  # Hashed for privacy
    ad_type = Column(String, nullable=False)
    position = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    clicked = Column(Boolean, default=False)
    conversion_value = Column(Float, default=0.0)
    metadata = Column(JSON)

if __name__ == "__main__":
    # Example usage
    async def main():
        config = {
            'redis_url': 'redis://localhost:6379',
            'database_url': 'postgresql://localhost/dmlog_ads',
            'privacy': {
                'gdpr_compliance': True,
                'cookie_consent_required': True,
                'anonymize_ip_addresses': True
            }
        }

        ad_system = AdvertisingSystem(config)
        await ad_system.initialize()

        # Update user preferences
        result = await ad_system.update_user_preferences(
            "user_123",
            {
                'ad_preference': 'minimal_ads',
                'blocked_categories': ['finance'],
                'consent_given': True
            }
        )
        print(f"Updated preferences: {result}")

        # Get advertisement
        ad = await ad_system.get_advertisement(
            "user_123",
            AdPosition.SIDEBAR,
            {'campaign_type': 'gaming'}
        )
        print(f"Got advertisement: {ad}")

        # Get performance metrics
        performance = await ad_system.get_ad_performance()
        print(f"Ad performance: {performance}")

    asyncio.run(main())