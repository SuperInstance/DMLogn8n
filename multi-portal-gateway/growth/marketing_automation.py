"""
DMLogn8n Growth System - Comprehensive Go-to-Market Strategy
Automated marketing campaigns and lead generation engine
"""

import asyncio
import json
import logging
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from dataclasses import dataclass, asdict
import random
import uuid
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Lead:
    """Represents a marketing lead"""
    id: str
    email: str
    name: str
    company: Optional[str] = None
    source: str = ""
    score: int = 0
    status: str = "new"  # new, contacted, engaged, qualified, converted
    created_at: datetime = None
    last_contacted: Optional[datetime] = None
    interests: List[str] = None
    demographics: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.interests is None:
            self.interests = []
        if self.demographics is None:
            self.demographics = {}

@dataclass
class Campaign:
    """Represents a marketing campaign"""
    id: str
    name: str
    type: str  # email, social, content, paid, referral
    status: str  # draft, active, paused, completed
    target_audience: Dict[str, Any]
    content: Dict[str, Any]
    schedule: Dict[str, Any]
    budget: Optional[float] = None
    metrics: Dict[str, Any] = None

    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {
                "sent": 0,
                "delivered": 0,
                "opened": 0,
                "clicked": 0,
                "converted": 0,
                "cost": 0.0,
                "revenue": 0.0
            }

class ContentGenerator:
    """AI-powered content generation for marketing"""

    def __init__(self):
        self.templates = {
            "welcome_email": {
                "subject": "Welcome to DMLogn8n - Revolutionize Your D&D Games",
                "body": """
Hello {name},

Welcome to DMLogn8n! We're thrilled to have you join our community of innovative Dungeon Masters and game enthusiasts.

DMLogn8n is the ultimate platform that combines the power of AI automation with n8n workflows to create unforgettable gaming experiences. Whether you're running epic campaigns, managing complex character systems, or building immersive worlds, we've got you covered.

Here's what you can do right now:
• Start your first automated campaign
• Explore our library of pre-built workflows
• Join our community Discord server
• Check out our tutorials and guides

Ready to transform your games? Click here to get started!

Best regards,
The DMLogn8n Team
                """
            },
            "product_update": {
                "subject": "🎉 New Features in DMLogn8n - {feature_name}",
                "body": """
Hi {name},

We're excited to announce our latest update featuring {feature_name}! This new capability will revolutionize how you {benefit}.

What's new:
• {feature_1}
• {feature_2}
• {feature_3}

These improvements are based on your feedback and our commitment to making DMLogn8n the best platform for immersive storytelling.

Try it now and let us know what you think!

Happy Gaming,
The DMLogn8n Team
                """
            },
            "re_engagement": {
                "subject": "We Miss You! Here's What's New at DMLogn8n",
                "body": """
Hi {name},

It's been a while since we've seen you at DMLogn8n, and we've made some incredible updates that we think you'll love!

Recent highlights:
• {recent_update_1}
• {recent_update_2}
• {recent_update_3}

We've also added new workflows, improved performance, and expanded our community features.

Come back and check out what's new! As a welcome back gift, here's a special offer: {offer}

We can't wait to see you again!

Best regards,
The DMLogn8n Team
                """
            }
        }

    def generate_content(self, template_type: str, variables: Dict[str, Any]) -> Dict[str, str]:
        """Generate content from template with variables"""
        if template_type not in self.templates:
            raise ValueError(f"Unknown template type: {template_type}")

        template = self.templates[template_type]
        subject = template["subject"].format(**variables)
        body = template["body"].format(**variables)

        return {"subject": subject, "body": body}

    def personalize_content(self, content: Dict[str, str], lead: Lead) -> Dict[str, str]:
        """Personalize content based on lead data"""
        personalization_vars = {
            "name": lead.name.split()[0] if lead.name else "Adventurer",
            "company": lead.company or "your party",
            "interests": ", ".join(lead.interests[:3]) if lead.interests else "storytelling",
            "source": lead.source
        }

        personalized = content.copy()
        personalized["subject"] = personalized["subject"].format(**personalization_vars)
        personalized["body"] = personalized["body"].format(**personalization_vars)

        return personalized

class EmailMarketingEngine:
    """Email marketing automation engine"""

    def __init__(self, smtp_config: Dict[str, Any]):
        self.smtp_config = smtp_config
        self.content_generator = ContentGenerator()
        self.campaigns = {}
        self.sent_emails = []

    async def send_email(self, to_email: str, subject: str, body: str,
                        from_email: str = None) -> bool:
        """Send individual email"""
        try:
            from_email = from_email or self.smtp_config["from_email"]

            msg = MimeMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MimeText(body, 'html'))

            # Simulate email sending (in production, use actual SMTP)
            logger.info(f"Sending email to {to_email}: {subject}")

            # Record email
            self.sent_emails.append({
                "id": str(uuid.uuid4()),
                "to": to_email,
                "subject": subject,
                "sent_at": datetime.utcnow(),
                "status": "sent"
            })

            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    async def send_campaign_email(self, campaign: Campaign, lead: Lead) -> bool:
        """Send campaign email to lead"""
        try:
            # Generate and personalize content
            content = self.content_generator.generate_content(
                campaign.content["template_type"],
                campaign.content.get("variables", {})
            )
            personalized_content = self.content_generator.personalize_content(content, lead)

            # Send email
            success = await self.send_email(
                lead.email,
                personalized_content["subject"],
                personalized_content["body"]
            )

            if success:
                # Update campaign metrics
                campaign.metrics["sent"] += 1
                campaign.metrics["delivered"] += 1

                # Update lead status
                lead.last_contacted = datetime.utcnow()
                if lead.status == "new":
                    lead.status = "contacted"

            return success

        except Exception as e:
            logger.error(f"Failed to send campaign email to {lead.email}: {str(e)}")
            return False

    async def execute_campaign(self, campaign: Campaign, leads: List[Lead]) -> Dict[str, int]:
        """Execute campaign for list of leads"""
        results = {"sent": 0, "failed": 0}

        # Filter leads based on campaign criteria
        target_leads = self._filter_leads(campaign, leads)

        # Send emails in batches
        batch_size = 10
        for i in range(0, len(target_leads), batch_size):
            batch = target_leads[i:i + batch_size]

            tasks = []
            for lead in batch:
                task = self.send_campaign_email(campaign, lead)
                tasks.append(task)

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, bool) and result:
                    results["sent"] += 1
                else:
                    results["failed"] += 1

            # Small delay between batches to avoid overwhelming
            await asyncio.sleep(1)

        return results

    def _filter_leads(self, campaign: Campaign, leads: List[Lead]) -> List[Lead]:
        """Filter leads based on campaign target criteria"""
        target_criteria = campaign.target_audience
        filtered_leads = []

        for lead in leads:
            # Check lead status
            if "statuses" in target_criteria:
                if lead.status not in target_criteria["statuses"]:
                    continue

            # Check lead score
            if "min_score" in target_criteria:
                if lead.score < target_criteria["min_score"]:
                    continue

            # Check interests
            if "interests" in target_criteria:
                if not any(interest in lead.interests for interest in target_criteria["interests"]):
                    continue

            # Check source
            if "sources" in target_criteria:
                if lead.source not in target_criteria["sources"]:
                    continue

            filtered_leads.append(lead)

        return filtered_leads

class SocialMediaManager:
    """Social media marketing automation"""

    def __init__(self):
        self.platforms = {
            "twitter": {"character_limit": 280, "hashtags": ["DMLogn8n", "DnD", "TTRPG"]},
            "linkedin": {"character_limit": 1300, "hashtags": ["DungeonMaster", "Gaming", "AI"]},
            "facebook": {"character_limit": 500, "hashtags": ["TabletopGaming", "RPG"]},
            "reddit": {"character_limit": 1000, "subreddits": ["r/DMAcademy", "r/DnD", "r/rpg"]},
            "discord": {"character_limit": 2000, "channels": ["general", "announcements"]}
        }
        self.content_queue = []
        self.published_posts = []

    def create_post(self, platform: str, content_type: str, topic: str,
                   call_to_action: str = None) -> Dict[str, Any]:
        """Create social media post for platform"""
        if platform not in self.platforms:
            raise ValueError(f"Unsupported platform: {platform}")

        platform_config = self.platforms[platform]

        # Content templates
        templates = {
            "product_feature": {
                "twitter": "🎲 Level up your D&D game with {feature}! DMLogn8n makes it easy to {benefit}. Try it free! {cta} #{' #'.join(platform_config['hashtags'][:3])}",
                "linkedin": "Excited to share how DMLogn8n is transforming Dungeon Master experiences with our {feature}. Game masters can now {benefit}, resulting in more engaging campaigns and reduced preparation time. {cta} #{' #'.join(platform_config['hashtags'][:3])}",
                "facebook": "Tired of spending hours preparing for your D&D sessions? 🤔 DMLogn8n's {feature} helps you {benefit} so you can focus on what matters - creating amazing stories for your players! {cta} #{' #'.join(platform_config['hashtags'][:3])}",
                "reddit": "Hey fellow DMs! I've been using DMLogn8n for {feature} and it's been a game-changer. The ability to {benefit} has saved me hours of prep time. Thought you might find it useful! {cta}",
                "discord": "@everyone New feature alert! 🎉 {feature} is now live in DMLogn8n! You can now {benefit} with just a few clicks. Check it out and let me know what you think! {cta}"
            },
            "community_highlight": {
                "twitter": "🌟 Amazing campaign from @{user} using DMLogn8n! They created {achievement} using our workflows. Join our community! #{' #'.join(platform_config['hashtags'][:3])}",
                "linkedin": "Community success story: {user} leveraged DMLogn8n to {achievement}, demonstrating how AI-powered automation can enhance creative storytelling in tabletop gaming. #{' #'.join(platform_config['hashtags'][:3])}",
                "facebook": "Look what {user} accomplished with DMLogn8n! 🎭 They {achievement} and the results are incredible. Want to create amazing campaigns like this? Get started with DMLogn8n! #{' #'.join(platform_config['hashtags'][:3])}",
                "reddit": "Just wanted to share what {user} created using DMLogn8n - they managed to {achievement}! It's inspiring to see what our community can do with the right tools. {cta}",
                "discord": "Huge shoutout to {user} for this incredible achievement! 🏆 They used DMLogn8n to {achievement}. This is exactly why we built this platform - to empower amazing storytellers like you!"
            },
            "educational_content": {
                "twitter": "💡 DM Tip: Use AI automation to {tip}! DMLogn8n can help you implement this in seconds. Learn more: {link} #{' #'.join(platform_config['hashtags'][:3])}",
                "linkedin": "Professional development for Dungeon Masters: Implementing {tip} can significantly improve your game management. DMLogn8n provides tools to automate this process, allowing DMs to focus on narrative quality. #{' #'.join(platform_config['hashtags'][:3])}",
                "facebook": "Want to become a better DM? 📚 Here's a pro tip: {tip}. With DMLogn8n, you can set this up automatically and save hours of work. Your players will thank you! {cta} #{' #'.join(platform_config['hashtags'][:3])}",
                "reddit": "Pro tip for fellow DMs: {tip}. I've been using DMLogn8n to automate this and it's been incredibly helpful. If you're looking to level up your DM skills, definitely check it out. {cta}",
                "discord": "📚 Quick DM tip: {tip}. For those interested, I can show you how to set this up in DMLogn8n - it only takes a few minutes and makes a huge difference!"
            }
        }

        if content_type not in templates:
            raise ValueError(f"Unknown content type: {content_type}")

        template = templates[content_type][platform]
        post_content = template.format(
            feature=topic.get("feature", ""),
            benefit=topic.get("benefit", ""),
            user=topic.get("user", ""),
            achievement=topic.get("achievement", ""),
            tip=topic.get("tip", ""),
            link=topic.get("link", ""),
            cta=call_to_action or "Learn more at dmlogn8n.com"
        )

        # Truncate if necessary
        if len(post_content) > platform_config["character_limit"]:
            post_content = post_content[:platform_config["character_limit"]-3] + "..."

        post = {
            "id": str(uuid.uuid4()),
            "platform": platform,
            "content": post_content,
            "content_type": content_type,
            "topic": topic,
            "status": "draft",
            "created_at": datetime.utcnow(),
            "scheduled_at": None,
            "published_at": None,
            "metrics": {
                "views": 0,
                "likes": 0,
                "shares": 0,
                "comments": 0,
                "clicks": 0
            }
        }

        return post

    def schedule_post(self, post: Dict[str, Any], scheduled_time: datetime):
        """Schedule post for publication"""
        post["scheduled_at"] = scheduled_time
        post["status"] = "scheduled"
        self.content_queue.append(post)
        logger.info(f"Scheduled {post['platform']} post for {scheduled_time}")

    async def publish_post(self, post: Dict[str, Any]) -> bool:
        """Publish post to platform"""
        try:
            # Simulate publishing (in production, use actual social media APIs)
            logger.info(f"Publishing to {post['platform']}: {post['content'][:50]}...")

            post["status"] = "published"
            post["published_at"] = datetime.utcnow()
            self.published_posts.append(post)

            # Remove from queue
            if post in self.content_queue:
                self.content_queue.remove(post)

            return True

        except Exception as e:
            logger.error(f"Failed to publish post to {post['platform']}: {str(e)}")
            return False

    async def process_scheduled_posts(self):
        """Process and publish scheduled posts"""
        current_time = datetime.utcnow()
        ready_posts = [post for post in self.content_queue
                      if post["scheduled_at"] and post["scheduled_at"] <= current_time]

        for post in ready_posts:
            await self.publish_post(post)

    def generate_content_calendar(self, days: int = 7) -> List[Dict[str, Any]]:
        """Generate content calendar for specified days"""
        calendar = []
        content_types = ["product_feature", "community_highlight", "educational_content"]
        platforms = list(self.platforms.keys())

        for day in range(days):
            date = datetime.utcnow() + timedelta(days=day)

            # Generate 2-3 posts per day
            num_posts = random.randint(2, 3)
            for _ in range(num_posts):
                platform = random.choice(platforms)
                content_type = random.choice(content_types)

                # Generate topic based on content type
                if content_type == "product_feature":
                    topic = {
                        "feature": random.choice(["AI NPCs", "Dynamic Combat", "World Building", "Voice Integration"]),
                        "benefit": random.choice(["create immersive experiences", "save preparation time", "engage players better", "manage complex campaigns"])
                    }
                elif content_type == "community_highlight":
                    topic = {
                        "user": f"DM_{random.choice(['Legend', 'Master', 'Storyteller', 'Creator'])}",
                        "achievement": random.choice(["built an entire world", "ran a 6-month campaign", "created 50+ NPCs", "designed epic battles"])
                    }
                else:  # educational_content
                    topic = {
                        "tip": random.choice(["track player progress automatically", "generate random encounters", "manage campaign notes", "create balanced encounters"]),
                        "link": "dmlogn8n.com/blog"
                    }

                # Schedule at random time during business hours
                hour = random.randint(9, 17)
                minute = random.randint(0, 59)
                scheduled_time = date.replace(hour=hour, minute=minute, second=0, microsecond=0)

                post = self.create_post(platform, content_type, topic)
                self.schedule_post(post, scheduled_time)
                calendar.append(post)

        return calendar

class LeadScoringEngine:
    """Automated lead scoring system"""

    def __init__(self):
        self.scoring_rules = {
            "email_engagement": {
                "opened": 2,
                "clicked": 5,
                "replied": 10,
                "forwarded": 8
            },
            "website_activity": {
                "visited_pricing": 5,
                "visited_features": 3,
                "visited_demo": 8,
                "started_trial": 15,
                "completed_signup": 20
            },
            "demographics": {
                "has_company": 5,
                "gaming_experience": {
                    "beginner": 3,
                    "intermediate": 7,
                    "expert": 10
                },
                "group_size": {
                    "solo": 2,
                    "small": 5,
                    "medium": 8,
                    "large": 10
                }
            },
            "behavioral": {
                "visited_multiple_times": 5,
                "spent_time_on_site": {
                    "<1min": 1,
                    "1-5min": 3,
                    "5-15min": 6,
                    ">15min": 10
                },
                "downloaded_resources": 8,
                "attended_webinar": 12
            }
        }

    def calculate_lead_score(self, lead: Lead, activities: List[Dict[str, Any]]) -> int:
        """Calculate lead score based on activities and demographics"""
        score = 0

        for activity in activities:
            activity_type = activity.get("type")

            # Email engagement scoring
            if activity_type in self.scoring_rules["email_engagement"]:
                score += self.scoring_rules["email_engagement"][activity_type]

            # Website activity scoring
            elif activity_type in self.scoring_rules["website_activity"]:
                score += self.scoring_rules["website_activity"][activity_type]

            # Behavioral scoring
            elif activity_type in self.scoring_rules["behavioral"]:
                if isinstance(self.scoring_rules["behavioral"][activity_type], dict):
                    # Handle nested scoring rules
                    value = activity.get("value", "")
                    if value in self.scoring_rules["behavioral"][activity_type]:
                        score += self.scoring_rules["behavioral"][activity_type][value]
                else:
                    score += self.scoring_rules["behavioral"][activity_type]

        # Demographic scoring
        if lead.company:
            score += self.scoring_rules["demographics"]["has_company"]

        # Add demographic-based scoring from lead data
        if lead.demographics:
            for demo_key, demo_value in lead.demographics.items():
                if demo_key in self.scoring_rules["demographics"]:
                    if isinstance(self.scoring_rules["demographics"][demo_key], dict):
                        if demo_value in self.scoring_rules["demographics"][demo_key]:
                            score += self.scoring_rules["demographics"][demo_key][demo_value]

        return score

    def categorize_lead(self, score: int) -> str:
        """Categorize lead based on score"""
        if score >= 50:
            return "hot"
        elif score >= 25:
            return "warm"
        elif score >= 10:
            return "cool"
        else:
            return "cold"

class MarketingAutomation:
    """Main marketing automation orchestrator"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.email_engine = EmailMarketingEngine(config.get("smtp", {}))
        self.social_manager = SocialMediaManager()
        self.scoring_engine = LeadScoringEngine()
        self.leads = []
        self.campaigns = {}
        self.automation_rules = []

    def add_lead(self, lead: Lead):
        """Add new lead to system"""
        self.leads.append(lead)
        logger.info(f"Added new lead: {lead.email}")

    def create_campaign(self, name: str, campaign_type: str,
                       target_audience: Dict[str, Any],
                       content: Dict[str, Any],
                       schedule: Dict[str, Any] = None) -> Campaign:
        """Create new marketing campaign"""
        campaign = Campaign(
            id=str(uuid.uuid4()),
            name=name,
            type=campaign_type,
            status="draft",
            target_audience=target_audience,
            content=content,
            schedule=schedule or {}
        )

        self.campaigns[campaign.id] = campaign
        logger.info(f"Created campaign: {name}")
        return campaign

    async def execute_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Execute marketing campaign"""
        if campaign_id not in self.campaigns:
            raise ValueError(f"Campaign not found: {campaign_id}")

        campaign = self.campaigns[campaign_id]
        campaign.status = "active"

        if campaign.type == "email":
            results = await self.email_engine.execute_campaign(campaign, self.leads)
        else:
            # Handle other campaign types
            results = {"message": f"Campaign type {campaign.type} not yet implemented"}

        campaign.status = "completed"
        return results

    def add_automation_rule(self, rule: Dict[str, Any]):
        """Add marketing automation rule"""
        self.automation_rules.append(rule)
        logger.info(f"Added automation rule: {rule['name']}")

    async def process_automation_rules(self):
        """Process all automation rules"""
        for rule in self.automation_rules:
            try:
                await self._execute_rule(rule)
            except Exception as e:
                logger.error(f"Failed to execute rule {rule['name']}: {str(e)}")

    async def _execute_rule(self, rule: Dict[str, Any]):
        """Execute individual automation rule"""
        rule_type = rule["type"]

        if rule_type == "welcome_series":
            await self._execute_welcome_series(rule)
        elif rule_type == "lead_scoring":
            await self._execute_lead_scoring(rule)
        elif rule_type == "re_engagement":
            await self._execute_re_engagement(rule)
        elif rule_type == "social_posting":
            await self._execute_social_posting(rule)

    async def _execute_welcome_series(self, rule: Dict[str, Any]):
        """Execute welcome email series"""
        trigger = rule["trigger"]
        sequence = rule["sequence"]

        # Find leads that match trigger criteria
        for lead in self.leads:
            if self._matches_trigger(lead, trigger):
                # Send welcome sequence
                for i, email_config in enumerate(sequence):
                    delay_days = email_config.get("delay_days", 0)
                    scheduled_date = lead.created_at + timedelta(days=delay_days)

                    if datetime.utcnow() >= scheduled_date:
                        campaign = Campaign(
                            id=str(uuid.uuid4()),
                            name=f"Welcome Series - Step {i+1}",
                            type="email",
                            status="active",
                            target_audience={"emails": [lead.email]},
                            content=email_config["content"],
                            schedule={}
                        )

                        await self.email_engine.send_campaign_email(campaign, lead)

    async def _execute_lead_scoring(self, rule: Dict[str, Any]):
        """Execute lead scoring"""
        # Update lead scores based on recent activities
        for lead in self.leads:
            # Simulate fetching lead activities
            activities = self._get_lead_activities(lead)
            new_score = self.scoring_engine.calculate_lead_score(lead, activities)

            if new_score != lead.score:
                lead.score = new_score
                category = self.scoring_engine.categorize_lead(new_score)
                logger.info(f"Updated lead {lead.email} score to {new_score} ({category})")

    async def _execute_re_engagement(self, rule: Dict[str, Any]):
        """Execute re-engagement campaign"""
        inactive_days = rule.get("inactive_days", 30)
        threshold_date = datetime.utcnow() - timedelta(days=inactive_days)

        # Find inactive leads
        inactive_leads = [
            lead for lead in self.leads
            if (lead.last_contacted and lead.last_contacted < threshold_date) or
               (not lead.last_contacted and lead.created_at < threshold_date)
        ]

        for lead in inactive_leads:
            if lead.status in ["contacted", "engaged"] and lead.score >= 20:
                # Send re-engagement email
                campaign = Campaign(
                    id=str(uuid.uuid4()),
                    name="Re-engagement Campaign",
                    type="email",
                    status="active",
                    target_audience={"emails": [lead.email]},
                    content={
                        "template_type": "re_engagement",
                        "variables": {
                            "recent_update_1": "New AI-powered NPC system",
                            "recent_update_2": "Enhanced workflow automation",
                            "recent_update_3": "Community marketplace launch",
                            "offer": "Get 20% off your first month!"
                        }
                    },
                    schedule={}
                )

                await self.email_engine.send_campaign_email(campaign, lead)

    async def _execute_social_posting(self, rule: Dict[str, Any]):
        """Execute social media posting"""
        await self.social_manager.process_scheduled_posts()

    def _matches_trigger(self, lead: Lead, trigger: Dict[str, Any]) -> bool:
        """Check if lead matches trigger criteria"""
        trigger_type = trigger["type"]

        if trigger_type == "new_lead":
            return lead.status == "new"
        elif trigger_type == "lead_score":
            return lead.score >= trigger.get("min_score", 0)
        elif trigger_type == "lead_status":
            return lead.status in trigger.get("statuses", [])

        return False

    def _get_lead_activities(self, lead: Lead) -> List[Dict[str, Any]]:
        """Simulate fetching lead activities"""
        # In production, this would fetch from your analytics/tracking system
        activities = []

        if lead.last_contacted:
            days_since_contact = (datetime.utcnow() - lead.last_contacted).days

            if days_since_contact < 1:
                activities.append({"type": "opened", "timestamp": lead.last_contacted})
            elif days_since_contact < 7:
                activities.append({"type": "clicked", "timestamp": lead.last_contacted})

        # Add some simulated activities based on lead score
        if lead.score > 30:
            activities.append({"type": "visited_pricing"})
            activities.append({"type": "visited_demo"})

        if lead.score > 50:
            activities.append({"type": "started_trial"})

        return activities

    def get_analytics(self) -> Dict[str, Any]:
        """Get marketing analytics dashboard"""
        total_leads = len(self.leads)
        leads_by_status = {}
        leads_by_score = {"hot": 0, "warm": 0, "cool": 0, "cold": 0}

        for lead in self.leads:
            # Count by status
            leads_by_status[lead.status] = leads_by_status.get(lead.status, 0) + 1

            # Count by score category
            category = self.scoring_engine.categorize_lead(lead.score)
            leads_by_score[category] += 1

        # Campaign analytics
        campaign_analytics = {}
        for campaign_id, campaign in self.campaigns.items():
            campaign_analytics[campaign.name] = campaign.metrics

        # Social media analytics
        total_posts = len(self.social_manager.published_posts)
        total_engagement = sum(
            post["metrics"]["likes"] + post["metrics"]["shares"] + post["metrics"]["comments"]
            for post in self.social_manager.published_posts
        )

        return {
            "overview": {
                "total_leads": total_leads,
                "total_campaigns": len(self.campaigns),
                "total_social_posts": total_posts,
                "automation_rules": len(self.automation_rules)
            },
            "leads": {
                "by_status": leads_by_status,
                "by_score_category": leads_by_score,
                "average_score": sum(lead.score for lead in self.leads) / total_leads if total_leads > 0 else 0
            },
            "campaigns": campaign_analytics,
            "social_media": {
                "total_posts": total_posts,
                "total_engagement": total_engagement,
                "engagement_rate": total_engagement / total_posts if total_posts > 0 else 0
            }
        }

# Example usage and initialization
async def main():
    """Example usage of the marketing automation system"""

    # Configuration
    config = {
        "smtp": {
            "host": "smtp.gmail.com",
            "port": 587,
            "username": "your_email@gmail.com",
            "password": "your_password",
            "from_email": "noreply@dmlogn8n.com"
        }
    }

    # Initialize marketing automation
    marketing = MarketingAutomation(config)

    # Add sample leads
    sample_leads = [
        Lead(
            id=str(uuid.uuid4()),
            email="john.doe@example.com",
            name="John Doe",
            company="Gaming Club",
            source="website",
            interests=["D&D", "Storytelling", "Automation"],
            demographics={"gaming_experience": "intermediate", "group_size": "medium"}
        ),
        Lead(
            id=str(uuid.uuid4()),
            email="jane.smith@example.com",
            name="Jane Smith",
            source="linkedin",
            interests=["TTRPG", "World Building", "AI"],
            demographics={"gaming_experience": "expert", "group_size": "large"}
        )
    ]

    for lead in sample_leads:
        marketing.add_lead(lead)

    # Create welcome campaign
    welcome_campaign = marketing.create_campaign(
        name="Welcome Series",
        campaign_type="email",
        target_audience={"statuses": ["new"]},
        content={
            "template_type": "welcome_email",
            "variables": {}
        },
        schedule={"type": "triggered"}
    )

    # Add automation rules
    marketing.add_automation_rule({
        "name": "Welcome Email Series",
        "type": "welcome_series",
        "trigger": {"type": "new_lead"},
        "sequence": [
            {
                "delay_days": 0,
                "content": {
                    "template_type": "welcome_email",
                    "variables": {}
                }
            },
            {
                "delay_days": 3,
                "content": {
                    "template_type": "product_update",
                    "variables": {
                        "feature_name": "AI-Powered NPCs",
                        "feature_1": "Dynamic personality generation",
                        "feature_2": "Context-aware responses",
                        "feature_3": "Voice integration support"
                    }
                }
            }
        ]
    })

    marketing.add_automation_rule({
        "name": "Lead Scoring",
        "type": "lead_scoring",
        "trigger": {"type": "activity"},
        "schedule": {"frequency": "daily"}
    })

    marketing.add_automation_rule({
        "name": "Re-engagement Campaign",
        "type": "re_engagement",
        "inactive_days": 30,
        "schedule": {"frequency": "weekly"}
    })

    # Generate social media content calendar
    social_calendar = marketing.social_manager.generate_content_calendar(7)
    print(f"Generated {len(social_calendar)} social media posts for the next 7 days")

    # Process automation rules
    await marketing.process_automation_rules()

    # Get analytics
    analytics = marketing.get_analytics()
    print("\nMarketing Analytics Dashboard:")
    print(json.dumps(analytics, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())