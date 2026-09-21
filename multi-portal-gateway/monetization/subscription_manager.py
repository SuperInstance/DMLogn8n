"""
DMLogn8n Subscription Manager - Comprehensive Subscription Tiers and Benefits Management

This module handles all subscription-related functionality including tier management,
billing cycles, benefit allocation, upgrades/downgrades, and subscription analytics.
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
import stripe
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import aioredis
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class SubscriptionTier(Enum):
    """Subscription tier levels"""
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"

class BillingCycle(Enum):
    """Billing cycle options"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    LIFETIME = "lifetime"

class SubscriptionStatus(Enum):
    """Subscription status states"""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    PENDING_CANCELLATION = "pending_cancellation"
    PENDING_UPGRADE = "pending_upgrade"
    PENDING_DOWNGRADE = "pending_downgrade"

@dataclass
class SubscriptionPlan:
    """Subscription plan definition"""
    id: str
    name: str
    tier: SubscriptionTier
    price: Decimal
    currency: str = "USD"
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    features: Dict[str, Any] = field(default_factory=dict)
    limits: Dict[str, int] = field(default_factory=dict)
    trial_days: int = 0
    setup_fee: Decimal = Decimal('0.00')
    cancellation_policy: str = "standard"
    refund_policy: str = "30_day_money_back"
    upgrade_discount: float = 0.0
    downgrade_proration: bool = True
    priority_support: bool = False
    custom_domain: bool = False
    api_access: bool = False
    white_label: bool = False

@dataclass
class SubscriptionBenefit:
    """Individual subscription benefit"""
    id: str
    name: str
    description: str
    type: str  # feature, limit, service, content
    value: Any
    tier_requirements: List[SubscriptionTier]
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UserSubscription:
    """User's subscription information"""
    user_id: str
    plan_id: str
    status: SubscriptionStatus
    start_date: datetime
    end_date: Optional[datetime]
    trial_end_date: Optional[datetime]
    auto_renew: bool = True
    payment_method_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    billing_cycle_anchor: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class SubscriptionManager:
    """Main subscription management system"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_client = None
        self.db_engine = None
        self.session_factory = None
        self.stripe_client = None
        self.plans: Dict[str, SubscriptionPlan] = {}
        self.benefits: Dict[str, SubscriptionBenefit] = {}
        self.email_config = config.get('email', {})

    async def initialize(self):
        """Initialize subscription manager"""
        logger.info("Initializing DMLogn8n Subscription Manager...")

        # Initialize Redis
        self.redis_client = aioredis.from_url(
            self.config.get('redis_url', 'redis://localhost:6379')
        )

        # Initialize database
        db_url = self.config.get('database_url', 'postgresql://localhost/dmlog_subscriptions')
        self.db_engine = create_engine(db_url)
        self.session_factory = sessionmaker(bind=self.db_engine)

        # Initialize Stripe
        stripe.api_key = self.config.get('stripe_secret_key')

        # Load subscription plans
        await self._load_subscription_plans()

        # Load benefits
        await self._load_subscription_benefits()

        # Start background tasks
        asyncio.create_task(self._subscription_monitor())
        asyncio.create_task(self._billing_processor())

        logger.info("Subscription Manager initialized successfully")

    async def _load_subscription_plans(self):
        """Load subscription plan configurations"""
        default_plans = [
            SubscriptionPlan(
                id="free_tier",
                name="Free Tier",
                tier=SubscriptionTier.FREE,
                price=Decimal('0.00'),
                billing_cycle=BillingCycle.MONTHLY,
                features={
                    'basic_campaigns': True,
                    'up_to_3_campaigns': True,
                    'email_support': True,
                    'community_access': True
                },
                limits={
                    'campaigns': 3,
                    'players_per_campaign': 10,
                    'storage_mb': 100,
                    'api_calls_per_day': 100
                },
                trial_days=0
            ),
            SubscriptionPlan(
                id="basic_monthly",
                name="Basic Plan",
                tier=SubscriptionTier.BASIC,
                price=Decimal('9.99'),
                billing_cycle=BillingCycle.MONTHLY,
                features={
                    'advanced_campaigns': True,
                    'up_to_10_campaigns': True,
                    'email_support': True,
                    'community_access': True,
                    'basic_analytics': True
                },
                limits={
                    'campaigns': 10,
                    'players_per_campaign': 50,
                    'storage_mb': 500,
                    'api_calls_per_day': 1000
                },
                trial_days=14,
                priority_support=False
            ),
            SubscriptionPlan(
                id="professional_monthly",
                name="Professional Plan",
                tier=SubscriptionTier.PROFESSIONAL,
                price=Decimal('29.99'),
                billing_cycle=BillingCycle.MONTHLY,
                features={
                    'unlimited_campaigns': True,
                    'advanced_campaigns': True,
                    'priority_support': True,
                    'community_access': True,
                    'advanced_analytics': True,
                    'custom_themes': True,
                    'api_access': True
                },
                limits={
                    'campaigns': -1,  # Unlimited
                    'players_per_campaign': 500,
                    'storage_mb': 5000,
                    'api_calls_per_day': 10000
                },
                trial_days=14,
                priority_support=True,
                api_access=True
            ),
            SubscriptionPlan(
                id="enterprise_monthly",
                name="Enterprise Plan",
                tier=SubscriptionTier.ENTERPRISE,
                price=Decimal('99.99'),
                billing_cycle=BillingCycle.MONTHLY,
                features={
                    'unlimited_everything': True,
                    'dedicated_support': True,
                    'custom_domain': True,
                    'white_label': True,
                    'advanced_analytics': True,
                    'api_access': True,
                    'custom_integrations': True,
                    'sla_guarantee': True
                },
                limits={
                    'campaigns': -1,
                    'players_per_campaign': -1,
                    'storage_mb': -1,
                    'api_calls_per_day': -1
                },
                trial_days=30,
                priority_support=True,
                custom_domain=True,
                white_label=True
            ),
            SubscriptionPlan(
                id="professional_annual",
                name="Professional Annual",
                tier=SubscriptionTier.PROFESSIONAL,
                price=Decimal('299.99'),
                billing_cycle=BillingCycle.ANNUAL,
                features={
                    'unlimited_campaigns': True,
                    'advanced_campaigns': True,
                    'priority_support': True,
                    'community_access': True,
                    'advanced_analytics': True,
                    'custom_themes': True,
                    'api_access': True
                },
                limits={
                    'campaigns': -1,
                    'players_per_campaign': 500,
                    'storage_mb': 5000,
                    'api_calls_per_day': 10000
                },
                upgrade_discount=0.20,  # 20% discount for annual
                priority_support=True,
                api_access=True
            )
        ]

        for plan in default_plans:
            self.plans[plan.id] = plan

    async def _load_subscription_benefits(self):
        """Load subscription benefits"""
        default_benefits = [
            SubscriptionBenefit(
                id="campaign_creation",
                name="Campaign Creation",
                description="Create and manage campaigns",
                type="feature",
                value=True,
                tier_requirements=[SubscriptionTier.BASIC, SubscriptionTier.PROFESSIONAL, SubscriptionTier.ENTERPRISE]
            ),
            SubscriptionBenefit(
                id="player_limit",
                name="Player Limit",
                description="Maximum players per campaign",
                type="limit",
                value={"basic": 50, "professional": 500, "enterprise": -1},
                tier_requirements=[SubscriptionTier.BASIC, SubscriptionTier.PROFESSIONAL, SubscriptionTier.ENTERPRISE]
            ),
            SubscriptionBenefit(
                id="priority_support",
                name="Priority Support",
                description="24/7 priority customer support",
                type="service",
                value=True,
                tier_requirements=[SubscriptionTier.PROFESSIONAL, SubscriptionTier.ENTERPRISE]
            ),
            SubscriptionBenefit(
                id="custom_domain",
                name="Custom Domain",
                description="Use your own domain",
                type="feature",
                value=True,
                tier_requirements=[SubscriptionTier.ENTERPRISE]
            ),
            SubscriptionBenefit(
                id="api_access",
                name="API Access",
                description="Full API access for integrations",
                type="feature",
                value=True,
                tier_requirements=[SubscriptionTier.PROFESSIONAL, SubscriptionTier.ENTERPRISE]
            ),
            SubscriptionBenefit(
                id="white_label",
                name="White Label",
                description="Remove DMLog branding",
                type="feature",
                value=True,
                tier_requirements=[SubscriptionTier.ENTERPRISE]
            )
        ]

        for benefit in default_benefits:
            self.benefits[benefit.id] = benefit

    async def create_subscription(self, user_id: str, plan_id: str,
                                 payment_method_id: Optional[str] = None,
                                 trial: bool = False) -> Dict[str, Any]:
        """Create a new subscription for user"""
        try:
            logger.info(f"Creating subscription for user {user_id}, plan {plan_id}")

            # Validate plan
            plan = self.plans.get(plan_id)
            if not plan:
                raise ValueError(f"Unknown plan: {plan_id}")

            # Check if user already has active subscription
            existing_sub = await self.get_user_subscription(user_id)
            if existing_sub and existing_sub.status == SubscriptionStatus.ACTIVE:
                raise ValueError("User already has active subscription")

            # Calculate trial end date
            trial_end_date = None
            if trial and plan.trial_days > 0:
                trial_end_date = datetime.utcnow() + timedelta(days=plan.trial_days)

            # Calculate end date based on billing cycle
            end_date = self._calculate_end_date(plan.billing_cycle, trial_end_date)

            # Create subscription object
            subscription = UserSubscription(
                user_id=user_id,
                plan_id=plan_id,
                status=SubscriptionStatus.ACTIVE if not trial else SubscriptionStatus.ACTIVE,  # Trials are active
                start_date=datetime.utcnow(),
                end_date=end_date,
                trial_end_date=trial_end_date,
                auto_renew=True,
                payment_method_id=payment_method_id
            )

            # Process payment if not free trial
            stripe_subscription_id = None
            if plan.price > 0 and (not trial or trial_end_date is None):
                stripe_result = await self._create_stripe_subscription(
                    user_id, plan, payment_method_id, trial_end_date
                )
                stripe_subscription_id = stripe_result['id']
                subscription.stripe_subscription_id = stripe_subscription_id

            # Store subscription
            await self._store_subscription(subscription)

            # Grant subscription benefits
            await self._grant_subscription_benefits(user_id, plan)

            # Send welcome email
            await self._send_subscription_email(user_id, plan, 'welcome', trial)

            # Schedule monitoring
            await self._schedule_subscription_monitoring(user_id)

            return {
                'success': True,
                'subscription_id': subscription.user_id,  # Using user_id as subscription ID for simplicity
                'plan_id': plan_id,
                'status': subscription.status.value,
                'trial_end_date': trial_end_date.isoformat() if trial_end_date else None,
                'next_billing_date': end_date.isoformat(),
                'amount': float(plan.price),
                'currency': plan.currency
            }

        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _calculate_end_date(self, billing_cycle: BillingCycle, trial_end_date: Optional[datetime]) -> datetime:
        """Calculate subscription end date"""
        if trial_end_date:
            base_date = trial_end_date
        else:
            base_date = datetime.utcnow()

        if billing_cycle == BillingCycle.MONTHLY:
            return base_date + timedelta(days=30)
        elif billing_cycle == BillingCycle.QUARTERLY:
            return base_date + timedelta(days=90)
        elif billing_cycle == BillingCycle.ANNUAL:
            return base_date + timedelta(days=365)
        elif billing_cycle == BillingCycle.LIFETIME:
            return datetime(2100, 12, 31)  # Far future date
        else:
            return base_date + timedelta(days=30)

    async def _create_stripe_subscription(self, user_id: str, plan: SubscriptionPlan,
                                        payment_method_id: str, trial_end_date: Optional[datetime]) -> Dict[str, Any]:
        """Create Stripe subscription"""
        try:
            # Get or create Stripe customer
            customer = await self._get_or_create_stripe_customer(user_id, payment_method_id)

            # Create subscription
            subscription_data = {
                'customer': customer.id,
                'items': [{
                    'price': await self._get_or_create_stripe_price(plan)
                }],
                'payment_behavior': 'default_incomplete',
                'expand': ['latest_invoice.payment_intent'],
                'metadata': {
                    'user_id': user_id,
                    'plan_id': plan.id,
                    'plan_tier': plan.tier.value
                }
            }

            # Add trial period if applicable
            if trial_end_date:
                trial_days = (trial_end_date - datetime.utcnow()).days
                if trial_days > 0:
                    subscription_data['trial_period_days'] = trial_days

            # Add setup fee if applicable
            if plan.setup_fee > 0:
                subscription_data['add_invoice_items'] = [{
                    'price_data': {
                        'currency': plan.currency.lower(),
                        'unit_amount': int(plan.setup_fee * 100),
                        'product_data': {
                            'name': f'{plan.name} Setup Fee',
                            'description': 'One-time setup fee'
                        }
                    }
                }]

            stripe_subscription = await stripe.Subscription.create(**subscription_data)

            return stripe_subscription

        except Exception as e:
            logger.error(f"Error creating Stripe subscription: {e}")
            raise

    async def _get_or_create_stripe_customer(self, user_id: str, payment_method_id: str) -> stripe.Customer:
        """Get or create Stripe customer"""
        # Check if customer exists
        existing_customer_id = await self.redis_client.get(f"stripe_customer:{user_id}")

        if existing_customer_id:
            try:
                customer = await stripe.Customer.retrieve(existing_customer_id.decode())
                return customer
            except stripe.error.InvalidRequestError:
                # Customer doesn't exist, create new one
                pass

        # Get user data (simplified - would fetch from user service)
        user_data = {
            'email': f'user_{user_id}@example.com',
            'name': f'User {user_id}'
        }

        # Create customer
        customer = await stripe.Customer.create(
            email=user_data['email'],
            name=user_data['name'],
            metadata={'user_id': user_id}
        )

        # Attach payment method
        if payment_method_id:
            await stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer.id
            )

            # Set as default payment method
            await stripe.Customer.modify(
                customer.id,
                invoice_settings={'default_payment_method': payment_method_id}
            )

        # Store customer ID
        await self.redis_client.setex(
            f"stripe_customer:{user_id}",
            86400 * 365,  # 1 year
            customer.id
        )

        return customer

    async def _get_or_create_stripe_price(self, plan: SubscriptionPlan) -> str:
        """Get or create Stripe price for plan"""
        price_key = f"stripe_price:{plan.id}:{plan.billing_cycle.value}"

        existing_price_id = await self.redis_client.get(price_key)
        if existing_price_id:
            return existing_price_id.decode()

        # Create new price
        recurring = None
        if plan.billing_cycle != BillingCycle.LIFETIME:
            interval_map = {
                BillingCycle.MONTHLY: 'month',
                BillingCycle.QUARTERLY: 'month',  # Stripe doesn't have quarterly, use 3 months
                BillingCycle.ANNUAL: 'year'
            }
            interval_count = 1
            if plan.billing_cycle == BillingCycle.QUARTERLY:
                interval_count = 3

            recurring = {
                'interval': interval_map[plan.billing_cycle],
                'interval_count': interval_count
            }

        price_data = {
            'currency': plan.currency.lower(),
            'unit_amount': int(plan.price * 100),
            'product_data': {
                'name': plan.name,
                'description': f'{plan.tier.value.title()} subscription plan'
            },
            'metadata': {
                'plan_id': plan.id,
                'tier': plan.tier.value
            }
        }

        if recurring:
            price_data['recurring'] = recurring

        price = await stripe.Price.create(**price_data)

        # Store price ID
        await self.redis_client.setex(
            price_key,
            86400 * 365,  # 1 year
            price.id
        )

        return price.id

    async def _store_subscription(self, subscription: UserSubscription):
        """Store subscription in database and cache"""
        # Store in Redis for quick access
        subscription_data = {
            'user_id': subscription.user_id,
            'plan_id': subscription.plan_id,
            'status': subscription.status.value,
            'start_date': subscription.start_date.isoformat(),
            'end_date': subscription.end_date.isoformat() if subscription.end_date else None,
            'trial_end_date': subscription.trial_end_date.isoformat() if subscription.trial_end_date else None,
            'auto_renew': subscription.auto_renew,
            'payment_method_id': subscription.payment_method_id,
            'stripe_subscription_id': subscription.stripe_subscription_id,
            'metadata': json.dumps(subscription.metadata)
        }

        await self.redis_client.setex(
            f"subscription:{subscription.user_id}",
            86400 * 30,  # 30 days
            json.dumps(subscription_data)
        )

        # Store in database
        session = self.session_factory()
        try:
            # Create database record (simplified)
            db_subscription = SubscriptionDB(
                user_id=subscription.user_id,
                plan_id=subscription.plan_id,
                status=subscription.status.value,
                start_date=subscription.start_date,
                end_date=subscription.end_date,
                trial_end_date=subscription.trial_end_date,
                auto_renew=subscription.auto_renew,
                stripe_subscription_id=subscription.stripe_subscription_id,
                metadata=subscription.metadata
            )
            session.add(db_subscription)
            session.commit()
        finally:
            session.close()

    async def _grant_subscription_benefits(self, user_id: str, plan: SubscriptionPlan):
        """Grant subscription benefits to user"""
        benefits_key = f"subscription_benefits:{user_id}"

        # Clear existing benefits
        await self.redis_client.delete(benefits_key)

        # Add benefits based on plan tier
        for benefit_id, benefit in self.benefits.items():
            if plan.tier in benefit.tier_requirements:
                await self.redis_client.hset(
                    benefits_key,
                    benefit_id,
                    json.dumps({
                        'name': benefit.name,
                        'type': benefit.type,
                        'value': benefit.value,
                        'granted_at': datetime.utcnow().isoformat()
                    })
                )

        # Add plan limits
        limits_key = f"user_limits:{user_id}"
        for limit_name, limit_value in plan.limits.items():
            await self.redis_client.hset(limits_key, limit_name, str(limit_value))

        # Set expiration
        await self.redis_client.expire(benefits_key, 86400 * 30)
        await self.redis_client.expire(limits_key, 86400 * 30)

    async def _send_subscription_email(self, user_id: str, plan: SubscriptionPlan,
                                     email_type: str, is_trial: bool = False):
        """Send subscription-related email"""
        try:
            # Get user email (simplified)
            user_email = f"user_{user_id}@example.com"

            # Prepare email content
            if email_type == 'welcome':
                subject = f"Welcome to DMLogn8n {plan.name}!"
                if is_trial:
                    body = f"""
                    Welcome to DMLogn8n!

                    Your {plan.name} trial is now active. You have {plan.trial_days} days to explore all the features.

                    Your trial includes:
                    {', '.join([k for k, v in plan.features.items() if v])}

                    No payment is required during the trial period. You can cancel anytime.

                    Best regards,
                    The DMLogn8n Team
                    """
                else:
                    body = f"""
                    Welcome to DMLogn8n!

                    Your {plan.name} subscription is now active.

                    Your subscription includes:
                    {', '.join([k for k, v in plan.features.items() if v])}

                    Thank you for choosing DMLogn8n!

                    Best regards,
                    The DMLogn8n Team
                    """
            elif email_type == 'payment_failed':
                subject = "Payment Failed - DMLogn8n Subscription"
                body = """
                We were unable to process your subscription payment.

                Please update your payment method to ensure uninterrupted service.

                Update your payment method here: [LINK]

                Best regards,
                The DMLogn8n Team
                """
            elif email_type == 'cancelled':
                subject = "Subscription Cancelled - DMLogn8n"
                body = f"""
                Your {plan.name} subscription has been cancelled.

                You will continue to have access until {plan.end_date}.

                We're sorry to see you go! You can reactivate your subscription anytime.

                Best regards,
                The DMLogn8n Team
                """
            else:
                return

            # Send email (simplified - would use proper email service)
            await self._send_email(user_email, subject, body)

        except Exception as e:
            logger.error(f"Error sending subscription email: {e}")

    async def _send_email(self, to_email: str, subject: str, body: str):
        """Send email using SMTP"""
        try:
            # This is a simplified email sending implementation
            # In production, use a proper email service like SendGrid, Mailgun, etc.

            smtp_config = self.email_config.get('smtp', {})
            smtp_host = smtp_config.get('host', 'localhost')
            smtp_port = smtp_config.get('port', 587)
            smtp_username = smtp_config.get('username', '')
            smtp_password = smtp_config.get('password', '')

            if smtp_host != 'localhost':
                server = smtplib.SMTP(smtp_host, smtp_port)
                server.starttls()
                server.login(smtp_username, smtp_password)

                msg = MIMEMultipart()
                msg['From'] = smtp_config.get('from_email', 'noreply@dmlogn8n.com')
                msg['To'] = to_email
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain'))

                server.send_message(msg)
                server.quit()

            logger.info(f"Email sent to {to_email}: {subject}")

        except Exception as e:
            logger.error(f"Error sending email: {e}")

    async def _schedule_subscription_monitoring(self, user_id: str):
        """Schedule subscription monitoring for user"""
        monitoring_key = f"subscription_monitoring:{user_id}"
        await self.redis_client.setex(
            monitoring_key,
            86400,  # 24 hours
            'active'
        )

    async def get_user_subscription(self, user_id: str) -> Optional[UserSubscription]:
        """Get user's current subscription"""
        try:
            subscription_data = await self.redis_client.get(f"subscription:{user_id}")
            if subscription_data:
                data = json.loads(subscription_data)
                return UserSubscription(
                    user_id=data['user_id'],
                    plan_id=data['plan_id'],
                    status=SubscriptionStatus(data['status']),
                    start_date=datetime.fromisoformat(data['start_date']),
                    end_date=datetime.fromisoformat(data['end_date']) if data['end_date'] else None,
                    trial_end_date=datetime.fromisoformat(data['trial_end_date']) if data['trial_end_date'] else None,
                    auto_renew=data['auto_renew'],
                    payment_method_id=data['payment_method_id'],
                    stripe_subscription_id=data['stripe_subscription_id'],
                    metadata=json.loads(data['metadata'])
                )
        except Exception as e:
            logger.error(f"Error getting user subscription: {e}")

        return None

    async def upgrade_subscription(self, user_id: str, new_plan_id: str) -> Dict[str, Any]:
        """Upgrade user's subscription"""
        try:
            current_sub = await self.get_user_subscription(user_id)
            if not current_sub:
                raise ValueError("No active subscription found")

            current_plan = self.plans.get(current_sub.plan_id)
            new_plan = self.plans.get(new_plan_id)

            if not new_plan:
                raise ValueError(f"Unknown plan: {new_plan_id}")

            # Check if this is actually an upgrade
            if not self._is_upgrade(current_plan, new_plan):
                raise ValueError("New plan must be higher tier than current plan")

            # Update Stripe subscription
            if current_sub.stripe_subscription_id:
                new_price_id = await self._get_or_create_stripe_price(new_plan)
                await stripe.Subscription.modify(
                    current_sub.stripe_subscription_id,
                    items=[{
                        'id': current_sub.stripe_subscription_id,  # This would be the item ID in real implementation
                        'price': new_price_id
                    }],
                    proration_behavior='create_prorations'
                )

            # Update local subscription
            current_sub.plan_id = new_plan_id
            current_sub.status = SubscriptionStatus.ACTIVE
            await self._store_subscription(current_sub)

            # Grant new benefits
            await self._grant_subscription_benefits(user_id, new_plan)

            # Send upgrade confirmation
            await self._send_subscription_email(user_id, new_plan, 'upgrade')

            return {
                'success': True,
                'new_plan_id': new_plan_id,
                'new_plan_name': new_plan.name,
                'effective_immediately': True
            }

        except Exception as e:
            logger.error(f"Error upgrading subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def downgrade_subscription(self, user_id: str, new_plan_id: str) -> Dict[str, Any]:
        """Downgrade user's subscription (effective next billing cycle)"""
        try:
            current_sub = await self.get_user_subscription(user_id)
            if not current_sub:
                raise ValueError("No active subscription found")

            current_plan = self.plans.get(current_sub.plan_id)
            new_plan = self.plans.get(new_plan_id)

            if not new_plan:
                raise ValueError(f"Unknown plan: {new_plan_id}")

            # Check if this is actually a downgrade
            if not self._is_downgrade(current_plan, new_plan):
                raise ValueError("New plan must be lower tier than current plan")

            # Schedule downgrade for next billing cycle
            await self.redis_client.setex(
                f"pending_downgrade:{user_id}",
                86400 * 30,  # 30 days
                json.dumps({
                    'new_plan_id': new_plan_id,
                    'effective_date': current_sub.end_date.isoformat() if current_sub.end_date else None
                })
            )

            # Update status
            current_sub.status = SubscriptionStatus.PENDING_DOWNGRADE
            await self._store_subscription(current_sub)

            # Send downgrade confirmation
            await self._send_subscription_email(user_id, new_plan, 'downgrade')

            return {
                'success': True,
                'new_plan_id': new_plan_id,
                'new_plan_name': new_plan.name,
                'effective_date': current_sub.end_date.isoformat() if current_sub.end_date else None
            }

        except Exception as e:
            logger.error(f"Error downgrading subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _is_upgrade(self, current_plan: SubscriptionPlan, new_plan: SubscriptionPlan) -> bool:
        """Check if new plan is an upgrade"""
        tier_hierarchy = {
            SubscriptionTier.FREE: 0,
            SubscriptionTier.BASIC: 1,
            SubscriptionTier.PROFESSIONAL: 2,
            SubscriptionTier.ENTERPRISE: 3,
            SubscriptionTier.CUSTOM: 4
        }

        return tier_hierarchy[new_plan.tier] > tier_hierarchy[current_plan.tier]

    def _is_downgrade(self, current_plan: SubscriptionPlan, new_plan: SubscriptionPlan) -> bool:
        """Check if new plan is a downgrade"""
        tier_hierarchy = {
            SubscriptionTier.FREE: 0,
            SubscriptionTier.BASIC: 1,
            SubscriptionTier.PROFESSIONAL: 2,
            SubscriptionTier.ENTERPRISE: 3,
            SubscriptionTier.CUSTOM: 4
        }

        return tier_hierarchy[new_plan.tier] < tier_hierarchy[current_plan.tier]

    async def cancel_subscription(self, user_id: str, reason: str = "") -> Dict[str, Any]:
        """Cancel user's subscription"""
        try:
            current_sub = await self.get_user_subscription(user_id)
            if not current_sub:
                raise ValueError("No active subscription found")

            # Cancel Stripe subscription
            if current_sub.stripe_subscription_id:
                await stripe.Subscription.delete(current_sub.stripe_subscription_id)

            # Update local subscription
            current_sub.status = SubscriptionStatus.CANCELLED
            current_sub.auto_renew = False
            await self._store_subscription(current_sub)

            # Store cancellation reason
            await self.redis_client.setex(
                f"cancellation_reason:{user_id}",
                86400 * 365,  # 1 year
                reason
            )

            # Send cancellation confirmation
            plan = self.plans.get(current_sub.plan_id)
            if plan:
                await self._send_subscription_email(user_id, plan, 'cancelled')

            return {
                'success': True,
                'cancellation_date': datetime.utcnow().isoformat(),
                'access_until': current_sub.end_date.isoformat() if current_sub.end_date else None
            }

        except Exception as e:
            logger.error(f"Error cancelling subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def reactivate_subscription(self, user_id: str) -> Dict[str, Any]:
        """Reactivate cancelled subscription"""
        try:
            current_sub = await self.get_user_subscription(user_id)
            if not current_sub or current_sub.status != SubscriptionStatus.CANCELLED:
                raise ValueError("No cancelled subscription found")

            # Check if subscription can be reactivated (within grace period)
            grace_period_days = 7
            if current_sub.end_date and (datetime.utcnow() - current_sub.end_date).days > grace_period_days:
                raise ValueError("Subscription is past grace period for reactivation")

            # Reactivate Stripe subscription
            if current_sub.stripe_subscription_id:
                await stripe.Subscription.modify(
                    current_sub.stripe_subscription_id,
                    cancel_at_period_end=False
                )

            # Update local subscription
            current_sub.status = SubscriptionStatus.ACTIVE
            current_sub.auto_renew = True
            await self._store_subscription(current_sub)

            # Grant benefits again
            plan = self.plans.get(current_sub.plan_id)
            if plan:
                await self._grant_subscription_benefits(user_id, plan)

            return {
                'success': True,
                'reactivation_date': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error reactivating subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def get_subscription_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get subscription metrics for analytics"""
        metrics = {
            'total_subscriptions': 0,
            'active_subscriptions': 0,
            'churned_subscriptions': 0,
            'new_subscriptions': 0,
            'revenue': defaultdict(Decimal),
            'revenue_by_tier': defaultdict(Decimal),
            'revenue_by_cycle': defaultdict(Decimal),
            'mrr': Decimal('0.00'),  # Monthly Recurring Revenue
            'arr': Decimal('0.00'),  # Annual Recurring Revenue
            'churn_rate': 0.0,
            'ltv': Decimal('0.00'),  # Lifetime Value
            'arpu': Decimal('0.00')  # Average Revenue Per User
        }

        # Get all subscriptions from database
        session = self.session_factory()
        try:
            # Query subscriptions in date range (simplified)
            subscriptions = session.query(SubscriptionDB).filter(
                SubscriptionDB.created_at >= start_date,
                SubscriptionDB.created_at <= end_date
            ).all()

            for sub in subscriptions:
                plan = self.plans.get(sub.plan_id)
                if not plan:
                    continue

                metrics['total_subscriptions'] += 1

                if sub.status == 'active':
                    metrics['active_subscriptions'] += 1

                    # Calculate MRR
                    if plan.billing_cycle == BillingCycle.MONTHLY:
                        metrics['mrr'] += plan.price
                    elif plan.billing_cycle == BillingCycle.ANNUAL:
                        metrics['mrr'] += plan.price / 12
                    elif plan.billing_cycle == BillingCycle.QUARTERLY:
                        metrics['mrr'] += plan.price / 3

                elif sub.status in ['cancelled', 'expired']:
                    metrics['churned_subscriptions'] += 1

                # Calculate revenue
                if sub.status != 'cancelled':
                    metrics['revenue'][plan.currency] += plan.price
                    metrics['revenue_by_tier'][plan.tier.value] += plan.price
                    metrics['revenue_by_cycle'][plan.billing_cycle.value] += plan.price

            # Calculate ARR
            metrics['arr'] = metrics['mrr'] * 12

            # Calculate churn rate
            if metrics['total_subscriptions'] > 0:
                metrics['churn_rate'] = metrics['churned_subscriptions'] / metrics['total_subscriptions']

            # Calculate ARPU
            if metrics['active_subscriptions'] > 0:
                total_revenue = sum(metrics['revenue'].values())
                metrics['arpu'] = total_revenue / metrics['active_subscriptions']

        finally:
            session.close()

        return {
            'total_subscriptions': metrics['total_subscriptions'],
            'active_subscriptions': metrics['active_subscriptions'],
            'churned_subscriptions': metrics['churned_subscriptions'],
            'mrr': float(metrics['mrr']),
            'arr': float(metrics['arr']),
            'churn_rate': metrics['churn_rate'],
            'arpu': float(metrics['arpu']),
            'revenue_by_tier': {k: float(v) for k, v in metrics['revenue_by_tier'].items()},
            'revenue_by_cycle': {k: float(v) for k, v in metrics['revenue_by_cycle'].items()}
        }

    async def _subscription_monitor(self):
        """Background task to monitor subscription status"""
        while True:
            try:
                logger.info("Running subscription monitor...")

                # Get all active subscriptions that need monitoring
                monitoring_keys = await self.redis_client.keys("subscription_monitoring:*")

                for key in monitoring_keys:
                    user_id = key.decode().split(':')[-1]
                    await self._check_subscription_status(user_id)

                await asyncio.sleep(3600)  # Check every hour

            except Exception as e:
                logger.error(f"Error in subscription monitor: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def _check_subscription_status(self, user_id: str):
        """Check and update subscription status"""
        try:
            subscription = await self.get_user_subscription(user_id)
            if not subscription:
                return

            now = datetime.utcnow()

            # Check if trial is ending
            if subscription.trial_end_date and now >= subscription.trial_end_date:
                await self._handle_trial_end(user_id, subscription)

            # Check if subscription is ending
            if subscription.end_date and now >= subscription.end_date:
                await self._handle_subscription_end(user_id, subscription)

            # Check for pending downgrades
            pending_downgrade = await self.redis_client.get(f"pending_downgrade:{user_id}")
            if pending_downgrade and subscription.end_date and now >= subscription.end_date:
                await self._process_pending_downgrade(user_id, pending_downgrade)

        except Exception as e:
            logger.error(f"Error checking subscription status for {user_id}: {e}")

    async def _handle_trial_end(self, user_id: str, subscription: UserSubscription):
        """Handle trial ending"""
        plan = self.plans.get(subscription.plan_id)
        if plan and plan.price > 0:
            # Trial ending for paid plan - attempt to charge
            await self._process_trial_payment(user_id, subscription)
        else:
            # Free trial ending - move to free plan
            await self._convert_to_free_plan(user_id, subscription)

    async def _handle_subscription_end(self, user_id: str, subscription: UserSubscription):
        """Handle subscription ending"""
        if subscription.auto_renew:
            # Attempt to renew
            await self._renew_subscription(user_id, subscription)
        else:
            # Cancel subscription
            subscription.status = SubscriptionStatus.EXPIRED
            await self._store_subscription(subscription)
            await self._revoke_subscription_benefits(user_id)

    async def _revoke_subscription_benefits(self, user_id: str):
        """Revoke subscription benefits"""
        benefits_key = f"subscription_benefits:{user_id}"
        limits_key = f"user_limits:{user_id}"

        await self.redis_client.delete(benefits_key)
        await self.redis_client.delete(limits_key)

    async def _billing_processor(self):
        """Background task to process billing"""
        while True:
            try:
                logger.info("Running billing processor...")

                # Process daily billing tasks
                await self._process_daily_billing()

                # Wait until next day
                now = datetime.utcnow()
                next_day = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                sleep_seconds = (next_day - now).total_seconds()
                await asyncio.sleep(sleep_seconds)

            except Exception as e:
                logger.error(f"Error in billing processor: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def _process_daily_billing(self):
        """Process daily billing tasks"""
        # This would handle daily billing operations
        # Like generating invoices, sending payment reminders, etc.
        logger.info("Processing daily billing tasks")

# Database models
class SubscriptionDB(Base):
    """Subscription database model"""
    __tablename__ = 'subscriptions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, unique=True)
    plan_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    trial_end_date = Column(DateTime)
    auto_renew = Column(Boolean, default=True)
    stripe_subscription_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON)

class SubscriptionPaymentDB(Base):
    """Subscription payment records"""
    __tablename__ = 'subscription_payments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False)
    subscription_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    payment_method = Column(String)
    stripe_payment_intent_id = Column(String)
    status = Column(String, default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)

if __name__ == "__main__":
    # Example usage
    async def main():
        config = {
            'redis_url': 'redis://localhost:6379',
            'database_url': 'postgresql://localhost/dmlog_subscriptions',
            'stripe_secret_key': 'sk_test_...',
            'email': {
                'smtp': {
                    'host': 'smtp.gmail.com',
                    'port': 587,
                    'username': 'your_email@gmail.com',
                    'password': 'your_password',
                    'from_email': 'noreply@dmlogn8n.com'
                }
            }
        }

        manager = SubscriptionManager(config)
        await manager.initialize()

        # Create a test subscription
        result = await manager.create_subscription(
            user_id="test_user_123",
            plan_id="professional_monthly",
            trial=True
        )
        print(f"Subscription creation result: {result}")

        # Get subscription metrics
        metrics = await manager.get_subscription_metrics(
            datetime.utcnow() - timedelta(days=30),
            datetime.utcnow()
        )
        print(f"Subscription metrics: {metrics}")

    asyncio.run(main())