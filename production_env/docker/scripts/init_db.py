#!/usr/bin/env python3
"""
Database initialization script for Docker containers
This script sets up the DMLog database with initial schema and data
"""

import asyncio
import sys
import os
import logging
from pathlib import Path
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.append('/app')

async def initialize_database():
    """Initialize the database with schema and initial data"""

    logger.info("🚀 Initializing DMLog database...")

    try:
        # Import database components
        from database.connection import Database
        from database.models import Base
        from config.settings import get_settings

        # Get settings
        settings = get_settings()
        logger.info(f"Connecting to database: {settings.database_url.split('@')[-1]}")

        # Initialize database
        database = Database()
        database.initialize()

        # Create tables
        logger.info("Creating database tables...")
        async with database._async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created")

        # Create initial data if needed
        await create_initial_data(database)

        # Run health check
        is_healthy = await database.health_check()
        if is_healthy:
            logger.info("✅ Database is healthy and ready")
        else:
            logger.error("❌ Database health check failed")
            return False

        return True

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def create_initial_data(database):
    """Create initial data for development"""

    # Check if we should create sample data
    create_sample = os.getenv('CREATE_SAMPLE_DATA', 'false').lower() == 'true'

    if not create_sample:
        logger.info("Skipping sample data creation (set CREATE_SAMPLE_DATA=true to enable)")
        return

    logger.info("Creating initial sample data...")

    from database.models import Character, Campaign, Session, Memory, Decision, SessionParticipant

    async with database.get_session() as session:
        # Create sample campaign
        campaign = Campaign(
            name="The Lost Mine of Phandelver",
            description="A beginner's adventure in the Forgotten Realms where the party searches for a lost mine.",
            dm_id="dm_001",
            world_lore={
                "setting": "Forgotten Realms",
                "region": "Sword Coast North",
                "starting_location": "Neverwinter",
                "current_year": "1491 DR"
            },
            house_rules=[
                "No evil alignments without DM approval",
                "Collaborative storytelling encouraged",
                "Critical successes/fails on natural 20/1"
            ],
            is_active=True
        )
        session.add(campaign)
        await session.commit()
        await session.refresh(campaign)
        logger.info(f"✅ Created campaign: {campaign.name}")

        # Create sample characters
        characters_data = [
            {
                "name": "Thorin Ironforge",
                "race": "dwarf",
                "character_class": "fighter",
                "level": 1,
                "strength": 16,
                "dexterity": 12,
                "constitution": 14,
                "intelligence": 10,
                "wisdom": 13,
                "charisma": 8,
                "personality_traits": [
                    "I'm fiercely loyal to my friends and clan",
                    "I face problems head-on, no matter how daunting",
                    "I have a weakness for gold and treasure"
                ],
                "backstory": "Thorin comes from the noble Ironforge clan of the dwarves. After his family's mine was lost to a dragon, he adventures to earn enough gold to reclaim his home.",
                "alignment": "Lawful Good",
                "is_active": True
            },
            {
                "name": "Elena Starweaver",
                "race": "high elf",
                "character_class": "wizard",
                "level": 1,
                "strength": 8,
                "dexterity": 14,
                "constitution": 12,
                "intelligence": 16,
                "wisdom": 13,
                "charisma": 11,
                "personality_traits": [
                    "I'm fascinated by ancient magic and artifacts",
                    "I can be lost in thought for hours",
                    "I believe knowledge is the greatest treasure"
                ],
                "backstory": "Elena studied at the prestigious Academy of Silverymoon before setting out to find the legendary Spellbook of the Ancients. Her quest for knowledge drives her to explore dangerous ruins.",
                "alignment": "Neutral Good",
                "is_active": True
            },
            {
                "name": "Rook Shadowstep",
                "race": "human",
                "character_class": "rogue",
                "level": 1,
                "strength": 10,
                "dexterity": 16,
                "constitution": 12,
                "intelligence": 12,
                "wisdom": 11,
                "charisma": 14,
                "personality_traits": [
                    "I always have an escape plan",
                    "I trust no one completely",
                    "I have a soft spot for the downtrodden"
                ],
                "backstory": "Orphaned on the streets of Waterdeep, Rook learned survival through cunning and stealth. Now he uses his skills for good, helping those who can't help themselves while always looking for the big score.",
                "alignment": "Chaotic Neutral",
                "is_active": True
            }
        ]

        created_characters = []
        for char_data in characters_data:
            character = Character(**char_data)
            session.add(character)
            await session.commit()
            await session.refresh(character)
            created_characters.append(character)
            logger.info(f"✅ Created character: {character.name} (Level {character.level} {character.race} {character.character_class})")

        # Create first session
        session_obj = Session(
            campaign_id=campaign.id,
            session_number=1,
            title="A Fateful Meeting in Neverwinter",
            phase="active",
            start_time=datetime.utcnow(),
            session_notes="The party meets in Neverwinter's Yawning Portal inn. A dwarf named Gundren Rockseeker hires them to escort supplies to the town of Phandalin.",
            game_state={
                "location": "Neverwinter",
                "time_of_day": "morning",
                "weather": "clear",
                "party_morale": "high"
            },
            total_decisions=0,
            total_reward=0.0
        )
        session.add(session_obj)
        await session.commit()
        await session.refresh(session_obj)
        logger.info(f"✅ Created session: {session_obj.title}")

        # Add characters to session
        for character in created_characters:
            participant = SessionParticipant(
                session_id=session_obj.id,
                character_id=character.id,
                joined_at=datetime.utcnow()
            )
            session.add(participant)
        await session.commit()

        # Create initial memories for each character
        memories_by_character = {
            created_characters[0]: [  # Thorin
                {
                    "memory_type": "episodic",
                    "content": "Met my new companions in the Yawning Portal inn. They seem capable, though the elf is a bit dreamy and the human looks shifty.",
                    "context": {
                        "location": "Neverwinter - Yawning Portal",
                        "people": ["Elena Starweaver", "Rook Shadowstep"],
                        "event": "first_meeting"
                    },
                    "importance": 0.8,
                    "emotional_valence": 0.3,
                    "retrieval_count": 0
                },
                {
                    "memory_type": "semantic",
                    "content": "Gundren Rockseeker offered 10 gold pieces each to escort supplies to Phandalin. It's a two-day journey along the Triboar Trail.",
                    "context": {
                        "quest_giver": "Gundren Rockseeker",
                        "destination": "Phandalin",
                        "payment": "10 gold each",
                        "route": "Triboar Trail"
                    },
                    "importance": 0.9,
                    "emotional_valence": 0.5,
                    "retrieval_count": 0
                }
            ],
            created_characters[1]: [  # Elena
                {
                    "memory_type": "episodic",
                    "content": "The dwarf warrior seems honorable and reliable. The rogue has nimble fingers but shifty eyes. This could be an interesting party dynamic.",
                    "context": {
                        "location": "Neverwinter - Yawning Portal",
                        "companions": ["Thorin Ironforge", "Rook Shadowstep"],
                        "observation": "party_assessment"
                    },
                    "importance": 0.7,
                    "emotional_valence": 0.1,
                    "retrieval_count": 0
                },
                {
                    "memory_type": "procedural",
                    "content": "Remember to prepare Detect Magic before entering any ruins. Always check for magical traps and auras.",
                    "context": {
                        "type": "wizard_preparation",
                        "priority": "high",
                        "reminder": "daily_preparation"
                    },
                    "importance": 0.85,
                    "emotional_valence": 0.0,
                    "retrieval_count": 0
                }
            ],
            created_characters[2]: [  # Rook
                {
                    "memory_type": "episodic",
                    "content": "The dwarf is straightforward and honest - easy to read. The elf is lost in her books. This could work to my advantage.",
                    "context": {
                        "location": "Neverwinter - Yawning Portal",
                        "companions": ["Thorin Ironforge", "Elena Starweaver"],
                        "assessment": "party_weaknesses"
                    },
                    "importance": 0.75,
                    "emotional_valence": 0.4,
                    "retrieval_count": 0
                },
                {
                    "memory_type": "episodic",
                    "content": "Gundren's cart was unusually heavy for supplies. He seemed nervous about something. Might be more to this job than he's saying.",
                    "context": {
                        "observation": "gundrens_behavior",
                        "suspicion": "hidden_agenda",
                        "detail": "heavy_cart"
                    },
                    "importance": 0.8,
                    "emotional_valence": -0.2,
                    "retrieval_count": 0
                }
            ]
        }

        for character, memories in memories_by_character.items():
            for memory_data in memories:
                memory = Memory(
                    character_id=character.id,
                    **memory_data
                )
                session.add(memory)
            await session.commit()
            logger.info(f"✅ Created {len(memories)} memories for {character.name}")

        # Create initial decisions
        decisions = [
            {
                "character": created_characters[0],  # Thorin
                "decision_type": "social",
                "description": "Volunteered to take first watch during the night",
                "reasoning": "As a dwarf, I'm naturally hardy and vigilant. My companions need their rest, and I can spot trouble coming from far away.",
                "source": "human",
                "confidence": 0.95,
                "time_taken_ms": 500,
                "success": True,
                "outcome_description": "Successfully kept watch through the night, spotting a wolf pack that was deterred by the campfire.",
                "reward_signals": [
                    {"type": "survival", "value": 0.5},
                    {"type": "leadership", "value": 0.3},
                    {"type": "party_safety", "value": 0.7}
                ],
                "quality_score": 0.85
            },
            {
                "character": created_characters[1],  # Elena
                "decision_type": "exploration",
                "description": "Examined the strange markings on the old road marker",
                "reasoning": "These aren't common dwarven runes. They might be ancient Netherese, which could indicate magical wards or traps in the area.",
                "source": "bot",
                "confidence": 0.75,
                "time_taken_ms": 1200,
                "success": True,
                "outcome_description": "Successfully identified the markings as protection wards against goblinoids. They're old but still active.",
                "reward_signals": [
                    {"type": "knowledge", "value": 0.8},
                    {"type": "investigation", "value": 0.6},
                    {"type": "party_safety", "value": 0.5}
                ],
                "quality_score": 0.9
            },
            {
                "character": created_characters[2],  # Rook
                "decision_type": "social",
                "description": "Convinced the merchant to give us a discount on trail rations",
                "reasoning": "I noticed the merchant was overcharging and used a bit of friendly persuasion - and maybe a subtle threat about reporting to the city guard.",
                "source": "bot",
                "confidence": 0.8,
                "time_taken_ms": 800,
                "success": True,
                "outcome_description": "Secured a 20% discount on supplies, saving the party 2 gold pieces total.",
                "reward_signals": [
                    {"type": "resourcefulness", "value": 0.7},
                    {"type": "party_benefit", "value": 0.4},
                    {"type": "negotiation", "value": 0.6}
                ],
                "quality_score": 0.75
            }
        ]

        for decision_data in decisions:
            decision = Decision(
                character_id=decision_data["character"].id,
                session_id=session_obj.id,
                **{k: v for k, v in decision_data.items() if k != "character"}
            )
            session.add(decision)
            await session.commit()
            logger.info(f"✅ Created decision for {decision_data['character'].name}: {decision_data['description'][:50]}...")

        # Update session with decision count
        session_obj.total_decisions = len(decisions)
        await session.commit()

        logger.info("\n✅ Sample data creation complete!")
        logger.info(f"Created {len(created_characters)} characters, 1 campaign, 1 session")
        logger.info(f"Total memories: {sum(len(m) for m in memories_by_character.values())}")
        logger.info(f"Total decisions: {len(decisions)}")

async def main():
    """Main initialization function"""
    logger.info("🎲 DMLog Database Initialization")
    logger.info("================================")

    success = await initialize_database()

    if success:
        logger.info("\n🎉 Database initialization completed successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Verify tables were created: \\dt")
        logger.info("2. Check sample data: SELECT COUNT(*) FROM characters;")
        logger.info("3. Test API endpoints: curl http://localhost:8000/api/v1/health")
    else:
        logger.error("\n❌ Database initialization failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())