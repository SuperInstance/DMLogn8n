"""
DMLogn8n Growth System - Viral Referral and Ambassador Programs
Comprehensive referral system for exponential growth and user advocacy
"""

import asyncio
import json
import logging
import random
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import uuid
import secrets

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ReferralProgram:
    """Represents a referral program configuration"""
    id: str
    name: str
    program_type: str  # one_sided, two_sided, multi_tier, gamified
    status: str  # active, paused, inactive
    incentives: Dict[str, Any]
    sharing_mechanisms: List[Dict[str, Any]]
    tracking_settings: Dict[str, Any]
    eligibility_criteria: Dict[str, Any]
    gamification: Dict[str, Any]
    analytics: Dict[str, Any]

    def __post_init__(self):
        if self.incentives is None:
            self.incentives = {}
        if self.sharing_mechanisms is None:
            self.sharing_mechanisms = []
        if self.tracking_settings is None:
            self.tracking_settings = {}
        if self.eligibility_criteria is None:
            self.eligibility_criteria = {}
        if self.gamification is None:
            self.gamification = {}
        if self.analytics is None:
            self.analytics = {}

@dataclass
class ReferralLink:
    """Represents an individual referral link"""
    id: str
    user_id: str
    referral_code: str
    program_id: str
    created_at: datetime
    expires_at: Optional[datetime]
    click_count: int
    conversion_count: int
    status: str  # active, expired, paused
    custom_slug: Optional[str]
    utm_parameters: Dict[str, Any]

    def __post_init__(self):
        if self.utm_parameters is None:
            self.utm_parameters = {}

@dataclass
class ReferralConversion:
    """Represents a successful referral conversion"""
    id: str
    referral_link_id: str
    referrer_id: str
    referred_user_id: str
    conversion_date: datetime
    conversion_type: str  # signup, trial, purchase, premium
    conversion_value: float
    reward_status: str  # pending, processed, paid, expired
    reward_amount: float
    tracking_data: Dict[str, Any]

    def __post_init__(self):
        if self.tracking_data is None:
            self.tracking_data = {}

@dataclass
class Ambassador:
    """Represents a brand ambassador"""
    id: str
    user_id: str
    tier: str  # bronze, silver, gold, platinum
    status: str  # active, inactive, suspended
    join_date: datetime
    performance_metrics: Dict[str, Any]
    rewards: Dict[str, Any]
    content_created: List[str]
    special_permissions: List[str]

    def __post_init__(self):
        if self.performance_metrics is None:
            self.performance_metrics = {}
        if self.rewards is None:
            self.rewards = {}
        if self.content_created is None:
            self.content_created = []
        if self.special_permissions is None:
            self.special_permissions = []

class ReferralLinkGenerator:
    """Generate and manage referral links"""

    def __init__(self):
        self.base_url = "https://dmlogn8n.com"
        self.link_tracking = {}

    def generate_referral_code(self, user_id: str, custom_slug: str = None) -> str:
        """Generate unique referral code"""
        if custom_slug:
            # Validate custom slug
            if self._is_slug_available(custom_slug):
                return custom_slug
            else:
                # Generate alternative if slug taken
                base_slug = custom_slug.lower().replace(' ', '-')
                counter = 1
                while not self._is_slug_available(f"{base_slug}-{counter}"):
                    counter += 1
                return f"{base_slug}-{counter}"
        else:
            # Generate random code
            return secrets.token_urlsafe(8)

    def _is_slug_available(self, slug: str) -> bool:
        """Check if custom slug is available"""
        # Simulate availability check
        existing_slugs = ["join", "signup", "referral", "free", "trial", "premium"]
        return slug.lower() not in existing_slugs

    def create_referral_link(self, user_id: str, program_id: str,
                           custom_slug: str = None,
                           utm_parameters: Dict[str, Any] = None) -> ReferralLink:
        """Create new referral link"""
        referral_code = self.generate_referral_code(user_id, custom_slug)

        # Default UTM parameters
        default_utm = {
            "utm_source": "referral",
            "utm_medium": "organic",
            "utm_campaign": f"program_{program_id}",
            "utm_content": referral_code
        }

        if utm_parameters:
            default_utm.update(utm_parameters)

        referral_link = ReferralLink(
            id=str(uuid.uuid4()),
            user_id=user_id,
            referral_code=referral_code,
            program_id=program_id,
            created_at=datetime.utcnow(),
            expires_at=None,  # No expiration by default
            click_count=0,
            conversion_count=0,
            status="active",
            custom_slug=custom_slug,
            utm_parameters=default_utm
        )

        # Generate full URL
        referral_url = f"{self.base_url}/ref/{referral_code}"
        utm_string = "&".join([f"{k}={v}" for k, v in default_utm.items()])
        referral_link.full_url = f"{referral_url}?{utm_string}"

        return referral_link

    def track_link_click(self, referral_code: str, click_data: Dict[str, Any]) -> bool:
        """Track referral link click"""
        if referral_code not in self.link_tracking:
            self.link_tracking[referral_code] = {
                "clicks": [],
                "conversions": [],
                "unique_visitors": set()
            }

        click_record = {
            "timestamp": datetime.utcnow(),
            "ip_address": click_data.get("ip_address"),
            "user_agent": click_data.get("user_agent"),
            "referer": click_data.get("referer"),
            "country": click_data.get("country"),
            "device": click_data.get("device")
        }

        self.link_tracking[referral_code]["clicks"].append(click_record)
        return True

class IncentiveManager:
    """Manage referral incentives and rewards"""

    def __init__(self):
        self.incentive_types = {
            "monetary": {
                "cash": {"direct_payment", "paypal", "bank_transfer"},
                "credits": {"account_credits", "store_credits", "service_credits"},
                "discounts": {"percentage_discount", "fixed_amount_discount", "free_trial_extension"}
            },
            "non_monetary": {
                "recognition": {"badge", "leaderboard_rank", "special_status"},
                "access": {"premium_features", "beta_access", "exclusive_content"},
                "experiences": {"events", "workshops", "consulting_sessions"}
            }
        }
        self.reward_calculations = {}

    def create_incentive_structure(self, program_type: str) -> Dict[str, Any]:
        """Create incentive structure for referral program"""
        structures = {
            "one_sided": {
                "referrer_rewards": [
                    {
                        "trigger": "signup",
                        "reward_type": "account_credits",
                        "amount": 10.00,
                        "description": "$10 account credit for each successful signup"
                    },
                    {
                        "trigger": "premium_conversion",
                        "reward_type": "cash",
                        "amount": 25.00,
                        "description": "$25 cash for each premium conversion"
                    }
                ],
                "referred_rewards": [],
                "bonus_tiers": [
                    {
                        "milestone": 5,
                        "bonus_type": "account_credits",
                        "amount": 50.00,
                        "description": "$50 bonus for 5 successful referrals"
                    },
                    {
                        "milestone": 10,
                        "bonus_type": "percentage_discount",
                        "amount": 0.20,
                        "description": "20% lifetime discount after 10 referrals"
                    }
                ]
            },
            "two_sided": {
                "referrer_rewards": [
                    {
                        "trigger": "signup",
                        "reward_type": "account_credits",
                        "amount": 5.00,
                        "description": "$5 account credit for each signup"
                    },
                    {
                        "trigger": "premium_conversion",
                        "reward_type": "cash",
                        "amount": 20.00,
                        "description": "$20 cash for each premium conversion"
                    }
                ],
                "referred_rewards": [
                    {
                        "trigger": "signup",
                        "reward_type": "free_trial_extension",
                        "amount": 14,  # days
                        "description": "14 extra days of premium trial"
                    },
                    {
                        "trigger": "first_purchase",
                        "reward_type": "percentage_discount",
                        "amount": 0.15,
                        "description": "15% discount on first purchase"
                    }
                ],
                "mutual_bonuses": [
                    {
                        "condition": "both_premium_within_30_days",
                        "referrer_bonus": 10.00,
                        "referred_bonus": 10.00,
                        "description": "$10 bonus each when both convert within 30 days"
                    }
                ]
            },
            "multi_tier": {
                "tiers": [
                    {
                        "name": "Bronze Referrer",
                        "min_referrals": 1,
                        "max_referrals": 5,
                        "per_referral_bonus": 5.00,
                        "additional_benefits": ["basic_analytics", "referral_dashboard"]
                    },
                    {
                        "name": "Silver Referrer",
                        "min_referrals": 6,
                        "max_referrals": 20,
                        "per_referral_bonus": 7.50,
                        "additional_benefits": ["advanced_analytics", "custom_referral_pages", "priority_support"]
                    },
                    {
                        "name": "Gold Referrer",
                        "min_referrals": 21,
                        "max_referrals": 50,
                        "per_referral_bonus": 10.00,
                        "additional_benefits": ["premium_features_access", "exclusive_content", "monthly_consultation"]
                    },
                    {
                        "name": "Platinum Ambassador",
                        "min_referrals": 51,
                        "per_referral_bonus": 15.00,
                        "additional_benefits": ["revenue_sharing", "co_marketing_opportunities", "input_on_features"]
                    }
                ]
            },
            "gamified": {
                "points_system": {
                    "signup": 10,
                    "trial_activation": 25,
                    "premium_conversion": 100,
                    "friend_of_friend": 50
                },
                "leaderboards": [
                    {
                        "name": "Weekly Top Referrer",
                        "period": 7,
                        "prizes": ["$100 bonus", "exclusive badge", "feature_highlight"]
                    },
                    {
                        "name": "Monthly Champion",
                        "period": 30,
                        "prizes": ["$500 bonus", "premium features lifetime", "ambassador_status"]
                    }
                ],
                "achievements": [
                    {
                        "name": "First Steps",
                        "requirement": "first_successful_referral",
                        "reward": "special_badge"
                    },
                    {
                        "name": "Social Butterfly",
                        "requirement": "10_referrals_via_social",
                        "reward": "social_media_kit"
                    },
                    {
                        "name": "Conversion Master",
                        "requirement": "5_premium_conversions",
                        "reward": "advanced_analytics_access"
                    }
                ]
            }
        }

        return structures.get(program_type, structures["one_sided"])

    def calculate_reward(self, conversion: ReferralConversion,
                        incentive_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate reward for referral conversion"""
        reward_calculation = {
            "conversion_id": conversion.id,
            "reward_amount": 0.0,
            "reward_type": "",
            "bonus_rewards": [],
            "total_value": 0.0
        }

        # Find matching reward based on conversion type
        conversion_type = conversion.conversion_type

        if "referrer_rewards" in incentive_structure:
            for reward in incentive_structure["referrer_rewards"]:
                if reward["trigger"] == conversion_type:
                    reward_calculation["reward_amount"] = reward["amount"]
                    reward_calculation["reward_type"] = reward["reward_type"]
                    break

        # Check for bonus tiers
        if "bonus_tiers" in incentive_structure:
            # This would require tracking total referrals per user
            # Simulated for now
            total_referrals = random.randint(1, 50)
            for bonus in incentive_structure["bonus_tiers"]:
                if total_referrals >= bonus["milestone"]:
                    reward_calculation["bonus_rewards"].append({
                        "type": bonus["bonus_type"],
                        "amount": bonus["amount"],
                        "description": bonus["description"]
                    })

        # Calculate total value
        total_bonus_value = sum(b["amount"] for b in reward_calculation["bonus_rewards"])
        reward_calculation["total_value"] = reward_calculation["reward_amount"] + total_bonus_value

        return reward_calculation

class AmbassadorProgram:
    """Manage brand ambassador programs"""

    def __init__(self):
        self.ambassadors = {}
        self.tier_requirements = {
            "bronze": {
                "min_referrals": 10,
                "min_revenue": 500,
                "content_requirements": ["1 tutorial", "2 social posts"],
                "community_participation": "active"
            },
            "silver": {
                "min_referrals": 25,
                "min_revenue": 1500,
                "content_requirements": ["3 tutorials", "5 social posts", "1 case study"],
                "community_participation": "moderator"
            },
            "gold": {
                "min_referrals": 50,
                "min_revenue": 5000,
                "content_requirements": ["5 tutorials", "10 social posts", "2 case studies", "1 video"],
                "community_participation": "leader"
            },
            "platinum": {
                "min_referrals": 100,
                "min_revenue": 15000,
                "content_requirements": ["10 tutorials", "20 social posts", "3 case studies", "3 videos"],
                "community_participation": "strategic_partner"
            }
        }
        self.benefit_packages = {}

    def create_ambassador(self, user_id: str, initial_tier: str = "bronze") -> Ambassador:
        """Create new brand ambassador"""
        ambassador = Ambassador(
            id=str(uuid.uuid4()),
            user_id=user_id,
            tier=initial_tier,
            status="active",
            join_date=datetime.utcnow(),
            performance_metrics={
                "total_referrals": 0,
                "total_revenue": 0.0,
                "conversion_rate": 0.0,
                "content_pieces_created": 0,
                "community_engagement_score": 0
            },
            rewards={
                "total_earned": 0.0,
                "current_month": 0.0,
                "pending": 0.0
            },
            content_created=[],
            special_permissions=[]
        )

        # Assign tier-specific permissions
        ambassador.special_permissions = self._get_tier_permissions(initial_tier)

        self.ambassadors[ambassador.id] = ambassador
        logger.info(f"Created ambassador: {user_id} at {initial_tier} tier")
        return ambassador

    def _get_tier_permissions(self, tier: str) -> List[str]:
        """Get permissions for ambassador tier"""
        permissions = {
            "bronze": ["referral_dashboard", "basic_analytics"],
            "silver": ["referral_dashboard", "basic_analytics", "content_creation_tools", "early_access"],
            "gold": ["referral_dashboard", "advanced_analytics", "content_creation_tools", "early_access", "beta_features"],
            "platinum": ["all_features", "strategic_input", "revenue_sharing", "dedicated_support"]
        }
        return permissions.get(tier, [])

    def evaluate_ambassador_performance(self, ambassador_id: str) -> Dict[str, Any]:
        """Evaluate ambassador performance and potential tier changes"""
        if ambassador_id not in self.ambassadors:
            raise ValueError(f"Ambassador not found: {ambassador_id}")

        ambassador = self.ambassadors[ambassador_id]
        current_tier = ambassador.tier
        performance = ambassador.performance_metrics

        evaluation = {
            "ambassador_id": ambassador_id,
            "current_tier": current_tier,
            "performance_review": {
                "referrals": performance["total_referrals"],
                "revenue": performance["total_revenue"],
                "conversion_rate": performance["conversion_rate"],
                "content_score": performance["content_pieces_created"],
                "engagement_score": performance["community_engagement_score"]
            },
            "tier_requirements_met": {},
            "recommendation": "maintain_current",
            "next_review_date": datetime.utcnow() + timedelta(days=30)
        }

        # Check each tier requirement
        for tier, requirements in self.tier_requirements.items():
            tier_met = all([
                performance["total_referrals"] >= requirements["min_referrals"],
                performance["total_revenue"] >= requirements["min_revenue"],
                performance["content_pieces_created"] >= len(requirements["content_requirements"])
            ])
            evaluation["tier_requirements_met"][tier] = tier_met

        # Determine tier recommendation
        if current_tier != "platinum":
            next_tier = self._get_next_tier(current_tier)
            if next_tier and evaluation["tier_requirements_met"].get(next_tier, False):
                evaluation["recommendation"] = f"upgrade_to_{next_tier}"
            elif performance["total_referrals"] < self.tier_requirements[current_tier]["min_referrals"] * 0.5:
                evaluation["recommendation"] = "needs_improvement"

        return evaluation

    def _get_next_tier(self, current_tier: str) -> Optional[str]:
        """Get next tier in hierarchy"""
        tier_order = ["bronze", "silver", "gold", "platinum"]
        try:
            current_index = tier_order.index(current_tier)
            if current_index < len(tier_order) - 1:
                return tier_order[current_index + 1]
        except ValueError:
            pass
        return None

    def create_ambassador_support_package(self, tier: str) -> Dict[str, Any]:
        """Create support package for ambassador tier"""
        packages = {
            "bronze": {
                "financial": {
                    "base_commission": 0.20,  # 20%
                    "performance_bonus": 0.05,  # Additional 5%
                    "payment_schedule": "monthly"
                },
                "resources": {
                    "brand_kit": True,
                    "content_templates": True,
                    "tracking_dashboard": True,
                    "monthly_newsletter": True
                },
                "support": {
                    "email_support": True,
                    "monthly_checkins": True,
                    "community_access": True
                },
                "recognition": {
                    "profile_badge": True,
                    "leaderboard_inclusion": True,
                    "monthly_highlights": True
                }
            },
            "silver": {
                "financial": {
                    "base_commission": 0.25,  # 25%
                    "performance_bonus": 0.07,  # Additional 7%
                    "content_creation_bonus": 50.00,  # Per approved content
                    "payment_schedule": "monthly"
                },
                "resources": {
                    "brand_kit": True,
                    "content_templates": True,
                    "tracking_dashboard": True,
                    "monthly_newsletter": True,
                    "advanced_analytics": True,
                    "custom_referral_pages": True
                },
                "support": {
                    "email_support": True,
                    "monthly_checkins": True,
                    "community_access": True,
                    "priority_support": True,
                    "monthly_strategy_calls": True
                },
                "recognition": {
                    "profile_badge": True,
                    "leaderboard_inclusion": True,
                    "monthly_highlights": True,
                    "blog_features": True,
                    "social_media_shoutouts": True
                }
            },
            "gold": {
                "financial": {
                    "base_commission": 0.30,  # 30%
                    "performance_bonus": 0.10,  # Additional 10%
                    "content_creation_bonus": 100.00,  # Per approved content
                    "revenue_sharing": True,
                    "payment_schedule": "bi_monthly"
                },
                "resources": {
                    "brand_kit": True,
                    "content_templates": True,
                    "tracking_dashboard": True,
                    "monthly_newsletter": True,
                    "advanced_analytics": True,
                    "custom_referral_pages": True,
                    "api_access": True,
                    "beta_feature_access": True
                },
                "support": {
                    "email_support": True,
                    "monthly_checkins": True,
                    "community_access": True,
                    "priority_support": True,
                    "monthly_strategy_calls": True,
                    "dedicated_manager": True
                },
                "recognition": {
                    "profile_badge": True,
                    "leaderboard_inclusion": True,
                    "monthly_highlights": True,
                    "blog_features": True,
                    "social_media_shoutouts": True,
                    "case_study_opportunities": True,
                    "speaking_opportunities": True
                }
            },
            "platinum": {
                "financial": {
                    "base_commission": 0.35,  # 35%
                    "performance_bonus": 0.15,  # Additional 15%
                    "content_creation_bonus": 200.00,  # Per approved content
                    "revenue_sharing": True,
                    "equity_opportunities": True,
                    "payment_schedule": "monthly"
                },
                "resources": {
                    "all_resources": True,
                    "custom_development": True,
                    "early_product_input": True,
                    "strategic_partnership": True
                },
                "support": {
                    "vip_support": True,
                    "dedicated_manager": True,
                    "quarterly_strategy_retreats": True,
                    "direct_founder_access": True
                },
                "recognition": {
                    "all_recognition": True,
                    "brand_ambassador_title": True,
                    "exclusive_events": True,
                    "industry_recognition": True
                }
            }
        }

        return packages.get(tier, packages["bronze"])

class ReferralSystem:
    """Main referral system orchestrator"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.link_generator = ReferralLinkGenerator()
        self.incentive_manager = IncentiveManager()
        self.ambassador_program = AmbassadorProgram()
        self.referral_programs = {}
        self.referral_links = {}
        self.conversions = []
        self.analytics = {}

    def create_referral_program(self, name: str, program_type: str,
                              settings: Dict[str, Any] = None) -> ReferralProgram:
        """Create new referral program"""
        incentive_structure = self.incentive_manager.create_incentive_structure(program_type)

        program = ReferralProgram(
            id=str(uuid.uuid4()),
            name=name,
            program_type=program_type,
            status="active",
            incentives=incentive_structure,
            sharing_mechanisms=[
                {
                    "type": "direct_link",
                    "description": "Share unique referral link",
                    "channels": ["email", "social", "messaging"]
                },
                {
                    "type": "email_invitation",
                    "description": "Send personalized email invitations",
                    "templates": ["casual", "professional", "benefit_focused"]
                },
                {
                    "type": "social_sharing",
                    "description": "Share on social media platforms",
                    "platforms": ["twitter", "facebook", "linkedin", "reddit"]
                }
            ],
            tracking_settings={
                "attribution_window": 30,  # days
                "cookie_duration": 90,  # days
                "multi_device_tracking": True,
                "fraud_detection": True
            },
            eligibility_criteria={
                "minimum_age": 18,
                "account_status": "active",
                "no_self_referral": True,
                "geographic_restrictions": []
            },
            gamification=settings.get("gamification", {}),
            analytics={
                "track_metrics": ["clicks", "conversions", "revenue", "retention"],
                "reporting_frequency": "weekly",
                "real_time_dashboard": True
            }
        )

        self.referral_programs[program.id] = program
        logger.info(f"Created referral program: {name}")
        return program

    def create_user_referral_links(self, user_id: str, program_id: str) -> List[ReferralLink]:
        """Create referral links for user in multiple formats"""
        links = []

        # Primary referral link
        primary_link = self.link_generator.create_referral_link(
            user_id=user_id,
            program_id=program_id
        )
        links.append(primary_link)

        # Social media optimized links
        social_utm = {
            "utm_campaign": "social_referral",
            "utm_content": "social_share"
        }

        twitter_link = self.link_generator.create_referral_link(
            user_id=user_id,
            program_id=program_id,
            utm_parameters=social_utm
        )
        links.append(twitter_link)

        # Custom branded link (if user qualifies)
        if random.random() > 0.7:  # 30% chance for custom link
            custom_slug = f"join-{user_id.split('_')[-1]}".lower()
            custom_link = self.link_generator.create_referral_link(
                user_id=user_id,
                program_id=program_id,
                custom_slug=custom_slug
            )
            links.append(custom_link)

        # Store links
        for link in links:
            self.referral_links[link.id] = link

        return links

    def track_referral_conversion(self, referral_code: str,
                                referred_user_id: str,
                                conversion_type: str,
                                conversion_value: float = 0.0) -> Optional[ReferralConversion]:
        """Track and process referral conversion"""
        # Find referral link
        referral_link = None
        for link in self.referral_links.values():
            if link.referral_code == referral_code:
                referral_link = link
                break

        if not referral_link:
            logger.error(f"Referral link not found for code: {referral_code}")
            return None

        # Create conversion record
        conversion = ReferralConversion(
            id=str(uuid.uuid4()),
            referral_link_id=referral_link.id,
            referrer_id=referral_link.user_id,
            referred_user_id=referred_user_id,
            conversion_date=datetime.utcnow(),
            conversion_type=conversion_type,
            conversion_value=conversion_value,
            reward_status="pending",
            reward_amount=0.0,
            tracking_data={
                "ip_address": "192.168.1.1",  # Would be actual IP
                "user_agent": "Mozilla/5.0...",  # Would be actual user agent
                "conversion_page": "/signup/complete"
            }
        )

        # Update referral link metrics
        referral_link.conversion_count += 1

        # Calculate reward
        program = self.referral_programs.get(referral_link.program_id)
        if program:
            reward_calculation = self.incentive_manager.calculate_reward(
                conversion, program.incentives
            )
            conversion.reward_amount = reward_calculation["total_value"]

        self.conversions.append(conversion)
        logger.info(f"Tracked conversion: {conversion.id} for referrer: {referral_link.user_id}")

        return conversion

    def generate_referral_analytics(self, program_id: str = None) -> Dict[str, Any]:
        """Generate comprehensive referral analytics"""
        if program_id:
            # Analytics for specific program
            program = self.referral_programs.get(program_id)
            if not program:
                return {}

            program_conversions = [c for c in self.conversions
                                if any(l.id == c.referral_link_id and l.program_id == program_id
                                     for l in self.referral_links.values())]

            return self._calculate_program_analytics(program, program_conversions)
        else:
            # Overall analytics
            return self._calculate_overall_analytics()

    def _calculate_program_analytics(self, program: ReferralProgram,
                                   conversions: List[ReferralConversion]) -> Dict[str, Any]:
        """Calculate analytics for specific program"""
        total_conversions = len(conversions)
        total_revenue = sum(c.conversion_value for c in conversions)
        total_rewards = sum(c.reward_amount for c in conversions)

        # Conversion breakdown
        conversion_breakdown = {}
        for conversion in conversions:
            conversion_type = conversion.conversion_type
            conversion_breakdown[conversion_type] = conversion_breakdown.get(conversion_type, 0) + 1

        # Top referrers
        referrer_performance = {}
        for conversion in conversions:
            referrer_id = conversion.referrer_id
            if referrer_id not in referrer_performance:
                referrer_performance[referrer_id] = {
                    "conversions": 0,
                    "revenue": 0.0,
                    "rewards": 0.0
                }
            referrer_performance[referrer_id]["conversions"] += 1
            referrer_performance[referrer_id]["revenue"] += conversion.conversion_value
            referrer_performance[referrer_id]["rewards"] += conversion.reward_amount

        # Sort by conversions
        top_referrers = sorted(referrer_performance.items(),
                             key=lambda x: x[1]["conversions"],
                             reverse=True)[:10]

        return {
            "program_id": program.id,
            "program_name": program.name,
            "program_type": program.program_type,
            "performance": {
                "total_conversions": total_conversions,
                "total_revenue": total_revenue,
                "total_rewards_paid": total_rewards,
                "roi": (total_revenue - total_rewards) / total_rewards if total_rewards > 0 else 0,
                "average_conversion_value": total_revenue / total_conversions if total_conversions > 0 else 0
            },
            "conversion_breakdown": conversion_breakdown,
            "top_referrers": [
                {
                    "referrer_id": referrer_id,
                    "conversions": metrics["conversions"],
                    "revenue": metrics["revenue"],
                    "rewards": metrics["rewards"]
                }
                for referrer_id, metrics in top_referrers
            ],
            "metrics_by_period": self._calculate_time_series_metrics(conversions)
        }

    def _calculate_overall_analytics(self) -> Dict[str, Any]:
        """Calculate overall referral system analytics"""
        total_links = len(self.referral_links)
        total_conversions = len(self.conversions)
        active_programs = len([p for p in self.referral_programs.values() if p.status == "active"])

        # Calculate viral metrics
        if total_links > 0:
            conversion_rate = total_conversions / total_links
        else:
            conversion_rate = 0

        total_revenue = sum(c.conversion_value for c in self.conversions)
        total_rewards = sum(c.reward_amount for c in self.conversions)

        return {
            "overview": {
                "total_programs": len(self.referral_programs),
                "active_programs": active_programs,
                "total_referral_links": total_links,
                "total_conversions": total_conversions,
                "conversion_rate": conversion_rate,
                "total_revenue_generated": total_revenue,
                "total_rewards_paid": total_rewards
            },
            "program_performance": {
                program_id: self.generate_referral_analytics(program_id)
                for program_id in self.referral_programs.keys()
            },
            "ambassador_program": {
                "total_ambassadors": len(self.ambassador_program.ambassadors),
                "tier_distribution": self._calculate_ambassador_tier_distribution()
            },
            "growth_metrics": {
                "monthly_growth": random.uniform(0.15, 0.35),
                "viral_coefficient": random.uniform(0.2, 0.4),
                "customer_acquisition_cost": random.uniform(15.0, 35.0),
                "referral_percentage": random.uniform(0.25, 0.45)
            }
        }

    def _calculate_time_series_metrics(self, conversions: List[ReferralConversion]) -> Dict[str, Any]:
        """Calculate time series metrics for conversions"""
        # Group conversions by month
        monthly_data = {}
        for conversion in conversions:
            month_key = conversion.conversion_date.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "conversions": 0,
                    "revenue": 0.0,
                    "rewards": 0.0
                }
            monthly_data[month_key]["conversions"] += 1
            monthly_data[month_key]["revenue"] += conversion.conversion_value
            monthly_data[month_key]["rewards"] += conversion.reward_amount

        return monthly_data

    def _calculate_ambassador_tier_distribution(self) -> Dict[str, int]:
        """Calculate distribution of ambassadors across tiers"""
        tier_counts = {"bronze": 0, "silver": 0, "gold": 0, "platinum": 0}
        for ambassador in self.ambassador_program.ambassadors.values():
            tier_counts[ambassador.tier] = tier_counts.get(ambassador.tier, 0) + 1
        return tier_counts

    def create_viral_referral_campaign(self) -> Dict[str, Any]:
        """Create viral referral campaign for maximum growth"""
        campaign = {
            "id": str(uuid.uuid4()),
            "name": "DMLogn8n Viral Launch Campaign",
            "duration_days": 60,
            "viral_mechanics": [
                {
                    "name": "Double Rewards Week",
                    "description": "2x rewards for referrals during launch week",
                    "start_day": 1,
                    "duration": 7,
                    "mechanic": "reward_multiplier",
                    "multiplier": 2.0
                },
                {
                    "name": "Team Challenge",
                    "description": "Teams compete for most referrals",
                    "start_day": 8,
                    "duration": 14,
                    "mechanic": "team_competition",
                    "team_size": 5,
                    "prizes": ["premium_lifetime", "merchandise_pack", "custom_workflow"]
                },
                {
                    "name": "Content Creator Bonus",
                    "description": "Extra rewards for sharing creation process",
                    "start_day": 15,
                    "duration": 30,
                    "mechanic": "content_bonus",
                    "requirements": ["screenshot_proof", "tutorial_creation", "social_sharing"],
                    "bonus_per_content": 25.00
                },
                {
                    "name": "Milestone Celebration",
                    "description": "Community-wide rewards for reaching milestones",
                    "start_day": 22,
                    "duration": 38,
                    "mechanic": "milestone_rewards",
                    "milestones": [
                        {"users": 1000, "reward": "site_wide_discount"},
                        {"users": 5000, "reward": "feature_unlock"},
                        {"users": 10000, "reward": "free_premium_day"}
                    ]
                }
            ],
            "amplification_channels": [
                "discord_community",
                "twitter_campaign",
                "reddit_engagement",
                "youtube_creator_partnerships",
                "twitch_streamer_spotlight",
                "dnd_community_forums"
            ],
            "success_metrics": [
                "viral_coefficient > 0.3",
                "50% of new users from referrals",
                "1000+ active referrers",
                "50+ ambassadors recruited"
            ],
            "budget_allocation": {
                "rewards": 0.40,  # 40% for rewards
                "marketing": 0.30,  # 30% for marketing
                "operations": 0.20,  # 20% for operations
                "contingency": 0.10  # 10% contingency
            }
        }

        return campaign

# Example usage
async def main():
    """Example usage of the referral system"""

    # Initialize referral system
    referral_system = ReferralSystem({})

    # Create referral programs
    standard_program = referral_system.create_referral_program(
        name="Standard Referral Program",
        program_type="two_sided",
        settings={"gamification": True}
    )

    ambassador_program = referral_system.create_referral_program(
        name="Ambassador Program",
        program_type="multi_tier",
        settings={"gamification": True}
    )

    viral_program = referral_system.create_referral_program(
        name="Viral Growth Program",
        program_type="gamified",
        settings={"gamification": True}
    )

    print(f"Created {len(referral_system.referral_programs)} referral programs")

    # Create sample referral links
    user_links = referral_system.create_user_referral_links(
        user_id="user_001",
        program_id=standard_program.id
    )

    print(f"Created {len(user_links)} referral links for user")

    # Track sample conversions
    conversions = []
    for i in range(10):
        conversion = referral_system.track_referral_conversion(
            referral_code=user_links[0].referral_code,
            referred_user_id=f"referred_{i}",
            conversion_type=random.choice(["signup", "trial", "premium_conversion"]),
            conversion_value=random.uniform(0, 99.99)
        )
        if conversion:
            conversions.append(conversion)

    print(f"Tracked {len(conversions)} conversions")

    # Create ambassador
    ambassador = referral_system.ambassador_program.create_ambassador(
        user_id="user_001",
        initial_tier="silver"
    )

    # Evaluate ambassador performance
    performance = referral_system.ambassador_program.evaluate_ambassador_performance(
        ambassador.id
    )
    print(f"Ambassador performance: {performance['recommendation']}")

    # Generate analytics
    analytics = referral_system.generate_referral_analytics()
    print(f"\nReferral System Analytics:")
    print(json.dumps(analytics, indent=2, default=str))

    # Create viral campaign
    viral_campaign = referral_system.create_viral_referral_campaign()
    print(f"\nViral Campaign Created: {viral_campaign['name']}")

if __name__ == "__main__":
    asyncio.run(main())