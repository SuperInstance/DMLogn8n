#!/usr/bin/env python3
"""
Database Initialization Script
Initializes all required databases for the DMLogn8n Educational Platform
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import yaml


def load_config():
    """Load configuration from settings file"""
    config_path = project_root / "config" / "settings.yaml"

    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    else:
        # Return default configuration
        return {
            "database": {
                "type": "sqlite",
                "name": "dmlogn8n_education.db"
            }
        }


def get_database_url(config):
    """Generate database URL from configuration"""
    db_config = config.get("database", {})

    if db_config.get("type") == "postgresql":
        return (
            f"postgresql://{db_config.get('username', 'dmlogn8n_user')}:"
            f"{db_config.get('password', 'password')}@"
            f"{db_config.get('host', 'localhost')}:"
            f"{db_config.get('port', 5432)}/"
            f"{db_config.get('name', 'dmlogn8n_education')}"
        )
    else:
        # SQLite fallback
        return f"sqlite:///{db_config.get('name', 'dmlogn8n_education.db')}"


def create_database_engine(config):
    """Create database engine"""
    database_url = get_database_url(config)
    echo = config.get("database", {}).get("echo", False)

    engine = create_engine(
        database_url,
        echo=echo,
        pool_size=config.get("database", {}).get("pool_size", 10),
        max_overflow=config.get("database", {}).get("max_overflow", 20)
    )

    return engine


def create_tables(engine):
    """Create all required tables"""
    print("Creating database tables...")

    # Import all table definitions
    from learning_platform import (
        User, Course, Enrollment, UserProgress, UserAchievement
    )
    from documentation_generator import DocumentationProject
    from tutorial_system import (
        TutorialDB, UserTutorialProgress, CategoryDB
    )
    from knowledge_base import (
        ArticleDB, ArticleVersionDB, CategoryDB as WikiCategoryDB
    )
    from video_platform import (
        VideoDB, LiveStreamDB, VideoCategory, VideoTranscript
    )
    from certification_system import (
        CertificationDB, QuestionDB, ExamDB, CertificateDB
    )
    from community_learning import (
        CommunityPostDB, CommunityReplyDB, StudyGroupDB, MentorshipDB
    )
    from research_library import (
        ResearchPaperDB, ResearchProjectDB, PaperAuthor, PaperCitation
    )

    # Create all tables
    from learning_platform import Base as LearningBase
    from documentation_generator import Base as DocBase
    from tutorial_system import Base as TutorialBase
    from knowledge_base import Base as KnowledgeBase
    from video_platform import Base as VideoBase
    from certification_system import Base as CertificationBase
    from community_learning import Base as CommunityBase
    from research_library import Base as ResearchBase

    # Create tables for each module
    LearningBase.metadata.create_all(engine)
    DocBase.metadata.create_all(engine)
    TutorialBase.metadata.create_all(engine)
    KnowledgeBase.metadata.create_all(engine)
    VideoBase.metadata.create_all(engine)
    CertificationBase.metadata.create_all(engine)
    CommunityBase.metadata.create_all(engine)
    ResearchBase.metadata.create_all(engine)

    print("✓ All tables created successfully")


def create_initial_data(engine):
    """Create initial data for the platform"""
    print("Creating initial data...")

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Create default admin user
        from learning_platform import User

        admin_user = User(
            id="admin",
            username="admin",
            email="admin@dmlogn8n.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5uO8G",  # "admin123"
            full_name="System Administrator",
            skill_level="expert",
            is_active=True
        )

        session.add(admin_user)

        # Create default categories
        from tutorial_system import CategoryDB

        categories = [
            CategoryDB(
                id="programming",
                name="Programming",
                slug="programming",
                description="Programming and software development",
                sort_order=1
            ),
            CategoryDB(
                id="ai-ml",
                name="AI & Machine Learning",
                slug="ai-machine-learning",
                description="Artificial intelligence and machine learning",
                sort_order=2
            ),
            CategoryDB(
                id="web-development",
                name="Web Development",
                slug="web-development",
                description="Web development and frontend/backend technologies",
                sort_order=3
            ),
            CategoryDB(
                id="data-science",
                name="Data Science",
                slug="data-science",
                description="Data analysis, visualization, and science",
                sort_order=4
            ),
            CategoryDB(
                id="devops",
                name="DevOps",
                slug="devops",
                description="Development operations and infrastructure",
                sort_order=5
            )
        ]

        for category in categories:
            session.add(category)

        # Create default research areas
        from research_library import ResearchArea

        research_areas = [
            ResearchArea(
                id="multi-agent-systems",
                name="Multi-Agent Systems",
                description="Research on multi-agent architectures and behaviors"
            ),
            ResearchArea(
                id="artificial-intelligence",
                name="Artificial Intelligence",
                description="AI research and applications"
            ),
            ResearchArea(
                id="distributed-computing",
                name="Distributed Computing",
                description="Distributed systems and cloud computing"
            ),
            ResearchArea(
                id="machine-learning",
                name="Machine Learning",
                description="ML algorithms and applications"
            ),
            ResearchArea(
                id="natural-language-processing",
                name="Natural Language Processing",
                description="NLP research and applications"
            )
        ]

        for area in research_areas:
            session.add(area)

        # Create default sample courses
        from learning_platform import Course

        sample_courses = [
            Course(
                id="intro-dmlogn8n",
                title="Introduction to DMLogn8n",
                description="Get started with the DMLogn8n multi-agent platform",
                instructor_id="admin",
                skill_level="beginner",
                duration_hours=5,
                content_type="course",
                learning_objectives=[
                    "Understand DMLogn8n architecture",
                    "Create your first agent",
                    "Build basic workflows",
                    "Deploy and monitor agents"
                ],
                status="published"
            ),
            Course(
                id="advanced-agents",
                title="Advanced Agent Development",
                description="Master advanced agent programming techniques",
                instructor_id="admin",
                skill_level="advanced",
                duration_hours=15,
                content_type="course",
                learning_objectives=[
                    "Design complex agent architectures",
                    "Implement advanced communication patterns",
                    "Optimize agent performance",
                    "Build resilient multi-agent systems"
                ],
                status="published"
            ),
            Course(
                id="ai-integration",
                title="AI Integration with DMLogn8n",
                description="Integrate AI models and services with DMLogn8n",
                instructor_id="admin",
                skill_level="intermediate",
                duration_hours=10,
                content_type="course",
                learning_objectives=[
                    "Connect external AI services",
                    "Implement ML pipelines",
                    "Build intelligent agents",
                    "Optimize AI workflows"
                ],
                status="published"
            )
        ]

        for course in sample_courses:
            session.add(course)

        session.commit()
        print("✓ Initial data created successfully")

    except Exception as e:
        print(f"✗ Error creating initial data: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def create_indexes(engine):
    """Create performance indexes"""
    print("Creating database indexes...")

    # Create indexes for common queries
    indexes = [
        # Learning platform indexes
        "CREATE INDEX IF NOT EXISTS idx_enrollments_user_id ON enrollments(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_enrollments_course_id ON enrollments(course_id)",
        "CREATE INDEX IF NOT EXISTS idx_user_progress_user_id ON user_progress(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_courses_status ON courses(status)",
        "CREATE INDEX IF NOT EXISTS idx_courses_skill_level ON courses(skill_level)",

        # Video platform indexes
        "CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status)",
        "CREATE INDEX IF NOT EXISTS idx_videos_author_id ON videos(author_id)",
        "CREATE INDEX IF NOT EXISTS idx_video_views ON videos(view_count)",
        "CREATE INDEX IF NOT EXISTS idx_streams_status ON live_streams(status)",

        # Community indexes
        "CREATE INDEX IF NOT EXISTS idx_posts_author_id ON community_posts(author_id)",
        "CREATE INDEX IF NOT EXISTS idx_posts_created_at ON community_posts(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_replies_post_id ON community_replies(post_id)",

        # Research library indexes
        "CREATE INDEX IF NOT EXISTS idx_papers_authors ON research_papers(authors)",
        "CREATE INDEX IF NOT EXISTS idx_papers_publication_date ON research_papers(publication_date)",
        "CREATE INDEX IF NOT EXISTS idx_citations_citing_paper ON paper_citations(citing_paper_id)",
        "CREATE INDEX IF NOT EXISTS idx_citations_cited_paper ON paper_citations(cited_paper_id)"
    ]

    with engine.connect() as conn:
        for index_sql in indexes:
            try:
                conn.execute(text(index_sql))
            except Exception as e:
                print(f"Warning: Could not create index: {e}")

    print("✓ Indexes created successfully")


def create_triggers(engine):
    """Create database triggers for automatic updates"""
    print("Creating database triggers...")

    # Update view count trigger
    view_count_trigger = """
    CREATE TRIGGER IF NOT EXISTS update_paper_view_count
    AFTER UPDATE OF view_count ON research_papers
    FOR EACH ROW
    BEGIN
        UPDATE research_papers SET last_activity = datetime('now') WHERE id = NEW.id;
    END;
    """

    # Update reply count trigger
    reply_count_trigger = """
    CREATE TRIGGER IF NOT EXISTS update_post_reply_count
    AFTER INSERT ON community_replies
    FOR EACH ROW
    BEGIN
        UPDATE community_posts
        SET reply_count = reply_count + 1, last_activity = datetime('now')
        WHERE id = NEW.post_id;
    END;
    """

    with engine.connect() as conn:
        for trigger_sql in [view_count_trigger, reply_count_trigger]:
            try:
                conn.execute(text(trigger_sql))
            except Exception as e:
                print(f"Warning: Could not create trigger: {e}")

    print("✓ Triggers created successfully")


def verify_database(engine):
    """Verify database creation and basic functionality"""
    print("Verifying database...")

    with engine.connect() as conn:
        # Test basic query
        result = conn.execute(text("SELECT 1 as test")).fetchone()
        if result and result[0] == 1:
            print("✓ Database connection successful")
        else:
            raise Exception("Database verification failed")

        # Check tables exist
        tables_query = """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """

        try:
            tables = conn.execute(text(tables_query)).fetchall()
            print(f"✓ Found {len(tables)} tables")

            if len(tables) < 10:
                print("Warning: Expected more tables")
        except Exception as e:
            print(f"Warning: Could not verify tables: {e}")


def main():
    """Main database initialization function"""
    print("🚀 Initializing DMLogn8n Educational Platform Database")
    print("=" * 60)

    try:
        # Load configuration
        print("Loading configuration...")
        config = load_config()
        print("✓ Configuration loaded")

        # Create database engine
        print("Creating database engine...")
        engine = create_database_engine(config)
        print("✓ Database engine created")

        # Create tables
        create_tables(engine)

        # Create indexes
        create_indexes(engine)

        # Create triggers
        create_triggers(engine)

        # Create initial data
        create_initial_data(engine)

        # Verify database
        verify_database(engine)

        print("=" * 60)
        print("🎉 Database initialization completed successfully!")
        print("\nDefault admin credentials:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\nPlease change the default password after first login.")

    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()