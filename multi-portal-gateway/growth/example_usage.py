"""
DMLogn8n Growth System - Example Usage
Demonstrates how to use the comprehensive growth system
"""

import asyncio
import json
from datetime import datetime, timedelta
from growth.marketing_automation import MarketingAutomation
from growth.user_acquisition import UserAcquisitionEngine
from growth.community_builder import CommunityBuilder
from growth.growth_hacking import GrowthHacker
from growth.referral_system import ReferralSystem
from growth.launch_coordinator import LaunchCoordinator
from growth.analytics_growth import GrowthAnalytics
from growth.brand_manager import BrandManager

# Import configuration
from config import get_config

async def main():
    """Main example demonstrating the growth system capabilities"""

    print("🚀 DMLogn8n Growth System - Example Usage")
    print("=" * 50)

    # Get configuration
    config = get_config()

    # Initialize all system components
    print("\n📦 Initializing Growth System Components...")

    # 1. Marketing Automation
    print("  • Marketing Automation")
    marketing_config = {
        "smtp": {
            "host": "smtp.gmail.com",
            "port": 587,
            "username": config.email["from_email"],
            "from_email": config.email["from_email"]
        }
    }
    marketing = MarketingAutomation(marketing_config)

    # 2. User Acquisition
    print("  • User Acquisition Engine")
    acquisition = UserAcquisitionEngine({})

    # 3. Community Building
    print("  • Community Builder")
    community = CommunityBuilder({})

    # 4. Growth Hacking
    print("  • Growth Hacking")
    growth_hacker = GrowthHacker({})

    # 5. Referral System
    print("  • Referral System")
    referral_system = ReferralSystem({})

    # 6. Launch Coordination
    print("  • Launch Coordinator")
    launch_coordinator = LaunchCoordinator({})

    # 7. Growth Analytics
    print("  • Growth Analytics")
    analytics = GrowthAnalytics({})

    # 8. Brand Management
    print("  • Brand Manager")
    brand_manager = BrandManager({})

    print("✅ All components initialized successfully!")

    # Example 1: Set up Marketing Automation
    print("\n" + "="*50)
    print("📧 MARKETING AUTOMATION EXAMPLE")
    print("="*50)

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
                        "feature_2": "Context-aware responses"
                    }
                }
            }
        ]
    })

    # Create sample leads
    sample_leads = [
        {
            "id": "lead_001",
            "email": "john.doe@example.com",
            "name": "John Doe",
            "source": "website",
            "interests": ["D&D", "Storytelling", "Automation"]
        },
        {
            "id": "lead_002",
            "email": "jane.smith@example.com",
            "name": "Jane Smith",
            "source": "referral",
            "interests": ["TTRPG", "World Building", "AI"]
        }
    ]

    for lead_data in sample_leads:
        marketing.add_lead(type('Lead', (object,), {
            'id': lead_data['id'],
            'email': lead_data['email'],
            'name': lead_data['name'],
            'source': lead_data['source'],
            'interests': lead_data['interests'],
            'status': 'new',
            'score': 0
        }))

    # Process automation rules
    await marketing.process_automation_rules()

    # Get analytics
    marketing_analytics = marketing.get_analytics()
    print(f"📊 Marketing Analytics:")
    print(f"  Total leads: {marketing_analytics['overview']['total_leads']}")
    print(f"  Total campaigns: {marketing_analytics['overview']['total_campaigns']}")

    # Example 2: Set up User Acquisition
    print("\n" + "="*50)
    print("🎯 USER ACQUISITION EXAMPLE")
    print("="*50)

    # Create acquisition channels
    google_search = acquisition.create_acquisition_channel(
        channel_type="paid",
        platform="google_ads",
        name="Google Search - DMLogn8n Keywords",
        budget=5000.0,
        targeting={
            "keywords": ["DMLogn8n", "D&D automation", "AI dungeon master"],
            "locations": ["US", "CA", "UK"],
            "languages": ["en"]
        }
    )

    facebook_social = acquisition.create_acquisition_channel(
        channel_type="paid",
        platform="facebook_ads",
        name="Facebook - D&D Community Targeting",
        budget=3000.0,
        targeting={
            "interests": ["Dungeons & Dragons", "Tabletop RPG"],
            "age_range": "18-45",
            "behaviors": ["engaged_shoppers"]
        }
    )

    # Create landing pages
    homepage = acquisition.create_landing_page(
        name="Homepage",
        url="https://dmlogn8n.com",
        template="homepage_v2",
        conversion_goal="signup",
        traffic_sources=["google_search", "facebook_social", "organic_search"]
    )

    # Implement growth pipeline
    growth_pipeline = await acquisition.implement_growth_pipeline()

    print(f"📈 Acquisition Pipeline Results:")
    print(f"  Experiments created: {len(growth_pipeline['experiments'])}")
    print(f"  Viral mechanics: {len(growth_pipeline['viral_mechanics'])}")
    print(f"  Growth hacks: {growth_pipeline['growth_hacks']['total_created']}")

    # Example 3: Set up Community Building
    print("\n" + "="*50)
    print("👥 COMMUNITY BUILDING EXAMPLE")
    print("="*50)

    # Initialize community platforms
    community_results = await community.initialize_community_platforms()

    # Create sample community members
    sample_members = [
        {
            "user_id": "user_001",
            "username": "DragonbornDave",
            "email": "dave@example.com",
            "preferences": {"notifications": "all", "privacy": "public"}
        },
        {
            "user_id": "user_002",
            "username": "ElaraElf",
            "email": "elara@example.com",
            "preferences": {"notifications": "mentions", "privacy": "friends"}
        }
    ]

    for member_data in sample_members:
        member = community.create_member(member_data)
        print(f"  Created community member: {member.username}")

    # Run engagement campaigns
    welcome_campaign = await community.run_engagement_campaign(
        "welcome_campaign", "new_members", 7
    )

    # Analyze community health
    health = community.analyze_community_health()
    print(f"🏥 Community Health Score: {health['health_score']}/100")

    # Example 4: Set up Growth Hacking
    print("\n" + "="*50)
    print("🧪 GROWTH HACKING EXAMPLE")
    print("="*50)

    # Create A/B test experiment
    landing_page_experiment = growth_hacker.experiment_manager.create_experiment(
        name="Landing Page Hero Test",
        hypothesis="Benefit-focused hero increases signups",
        experiment_type="a_b_test",
        target_metric="signup_conversion_rate",
        baseline_value=0.08,
        expected_improvement=0.25
    )

    # Create viral mechanics
    viral_mechanic = growth_hacker.viral_engine.create_viral_mechanic(
        name="Collaborative Workflow Sharing",
        mechanic_type="collaboration",
        description="Users share and collaborate on DMLogn8n workflows",
        implementation={
            "sharing_method": "link_based",
            "collaboration_features": ["real_time_editing", "version_control"],
            "ease_of_sharing": "high"
        }
    )

    # Run growth pipeline
    growth_results = await growth_hacker.implement_growth_pipeline()

    print(f"🚀 Growth Pipeline Results:")
    print(f"  A/B Tests: {len(growth_results['experiments'])}")
    print(f"  Viral K-factor: {growth_results['viral_mechanics']['collaborative_sharing']['viral_metrics']['viral_coefficient']:.2f}")

    # Example 5: Set up Referral System
    print("\n" + "="*50)
    print("🎁 REFERRAL SYSTEM EXAMPLE")
    print("="*50)

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

    # Create referral links for user
    user_links = referral_system.create_user_referral_links(
        user_id="user_001",
        program_id=standard_program.id
    )

    # Track sample conversions
    for i in range(5):
        conversion = referral_system.track_referral_conversion(
            referral_code=user_links[0].referral_code,
            referred_user_id=f"referred_{i}",
            conversion_type="signup",
            conversion_value=random.uniform(0, 99.99)
        )

    print(f"📊 Referral System Results:")
    print(f"  Programs created: {len(referral_system.referral_programs)}")
    print(f"  Referral links: {len(user_links)}")

    # Example 6: Launch Coordination
    print("\n" + "="*50)
    print("🚀 LAUNCH COORDINATION EXAMPLE")
    print("="*50)

    # Create launch plan
    launch_date = datetime.utcnow() + timedelta(days=30)
    launch_plan = launch_coordinator.create_launch_plan(
        product_name="DMLogn8n AI Assistant",
        launch_date=launch_date,
        product_type="new_product"
    )

    print(f"📋 Launch Plan Created:")
    print(f"  Product: {launch_plan['product_name']}")
    print(f"  Launch Date: {launch_plan['launch_date']}")
    print(f"  Timeline Phases: {len(launch_plan['timeline']['phases'])}")
    print(f"  Marketing Campaigns: {sum(len(campaigns) for campaigns in launch_plan['campaigns'].values())}")

    # Example 7: Growth Analytics
    print("\n" + "="*50)
    print("📊 GROWTH ANALYTICS EXAMPLE")
    print("="*50)

    # Generate growth dashboard
    date_range = {
        "start": datetime.utcnow() - timedelta(days=30),
        "end": datetime.utcnow()
    }

    dashboard = analytics.generate_growth_dashboard(date_range)

    print(f"📈 Growth Dashboard Results:")
    print(f"  Overall Growth Score: {dashboard['growth_score']['overall_score']:.1f}")
    print(f"  Rating: {dashboard['growth_score']['rating']}")
    print(f"  Total Alerts: {len(dashboard['alerts'])}")
    print(f"  Recommendations: {len(dashboard['recommendations'])}")

    # Create reports
    weekly_report = analytics.create_growth_report("weekly", date_range)
    monthly_report = analytics.create_growth_report("monthly", date_range)

    print(f"📑 Reports Generated:")
    print(f"  Weekly: {len(weekly_report['key_metrics'])} metrics")
    print(f"  Monthly: {len(monthly_report['detailed_metrics'])} metrics")

    # Example 8: Brand Management
    print("\n" + "="*50)
    print("🎨 BRAND MANAGEMENT EXAMPLE")
    print("="*50)

    # Build brand identity
    brand_identity = brand_manager.build_brand_identity()

    # Develop content strategy
    content_strategy = brand_manager.develop_content_strategy()

    # Launch brand campaigns
    campaign_plan = brand_manager.launch_brand_campaigns()

    print(f"🎯 Brand Management Results:")
    print(f"  Brand: {brand_identity['brand_name']}")
    print(f"  Tagline: {brand_identity['tagline']}")
    print(f"  Content Pillars: {len(content_strategy['content_pillars'])}")
    print(f"  Active Campaigns: {len(campaign_plan['active_campaigns'])}")

    # Get brand analytics
    brand_analytics = brand_manager.get_brand_analytics()
    print(f"📊 Brand Analytics:")
    print(f"  Brand Awareness Score: {brand_analytics['brand_health']['awareness_score']:.1%}")
    print(f"  Content Engagement Rate: {brand_analytics['content_performance']['engagement_rate']:.1%}")

    print("\n" + "="*50)
    print("🎉 GROWTH SYSTEM DEMO COMPLETE!")
    print("="*50)
    print("✅ All 8 components demonstrated successfully!")
    print("🚀 Your DMLogn8n growth engine is ready to scale!")
    print("\nNext Steps:")
    print("1. Configure your API keys and credentials")
    print("2. Customize settings for your specific needs")
    print("3. Launch your first campaigns")
    print("4. Monitor analytics and optimize")
    print("5. Scale successful initiatives")

    # Save configuration example
    config_example = {
        "demo_timestamp": datetime.utcnow().isoformat(),
        "components_initialized": 8,
        "campaigns_created": len(marketing.campaigns) + len(campaign_plan['active_campaigns']),
        "users_created": len(sample_leads) + len(sample_members),
        "experiments_running": 1,
        "growth_score": dashboard['growth_score']['overall_score']
    }

    with open("demo_results.json", "w") as f:
        json.dump(config_example, f, indent=2, default=str)

    print(f"\n📄 Demo results saved to: demo_results.json")

if __name__ == "__main__":
    # Add some randomness for realistic demo data
    import random

    # Set random seed for reproducible demo
    random.seed(42)

    # Run the example
    asyncio.run(main())