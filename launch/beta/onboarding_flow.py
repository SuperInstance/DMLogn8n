#!/usr/bin/env python3
"""
DMLogn8n Beta User Onboarding Flow System
Manages personalized onboarding experiences for different user segments and types
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import sqlite3
import aiohttp
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/activeloguser/DMLogn8n/launch/beta/logs/onboarding_flow.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OnboardingStatus(Enum):
    """Onboarding status stages"""
    NOT_STARTED = "not_started"
    PROFILE_STARTED = "profile_started"
    PROFILE_COMPLETED = "profile_completed"
    TUTORIAL_STARTED = "tutorial_started"
    TUTORIAL_COMPLETED = "tutorial_completed"
    FIRST_WORKFLOW_STARTED = "first_workflow_started"
    FIRST_WORKFLOW_COMPLETED = "first_workflow_completed"
    COMMUNITY_JOINED = "community_joined"
    INITIAL_SURVEY_STARTED = "initial_survey_started"
    INITIAL_SURVEY_COMPLETED = "initial_survey_completed"
    ONBOARDING_COMPLETED = "onboarding_completed"

class UserSegment(Enum):
    """Beta user segments"""
    GAMERS = "gamers"
    DEVELOPERS = "developers"
    EDUCATORS = "educators"
    ENTERPRISE = "enterprise"
    CONTENT_CREATORS = "content_creators"
    COMMUNITY_MANAGERS = "community_managers"

class UserType(Enum):
    """Types of beta users"""
    EARLY_ADOPTER = "early_adopter"
    POWER_USER = "power_user"
    CASUAL_USER = "casual_user"
    TECHNICAL_USER = "technical_user"
    CREATIVE_USER = "creative_user"

@dataclass
class OnboardingStep:
    """Individual onboarding step"""
    step_id: str
    title: str
    description: str
    step_type: str  # tutorial, action, survey, video, reading
    required: bool
    estimated_time_minutes: int
    content_url: Optional[str] = None
    completion_criteria: Optional[Dict[str, Any]] = None
    next_steps: List[str] = None

@dataclass
class OnboardingPath:
    """Complete onboarding path for a user segment"""
    path_id: str
    segment: UserSegment
    user_type: UserType
    name: str
    description: str
    steps: List[OnboardingStep]
    total_time_minutes: int
    required_steps: List[str]
    optional_steps: List[str]

@dataclass
class UserOnboardingProgress:
    """User's onboarding progress tracking"""
    user_id: str
    segment: UserSegment
    user_type: UserType
    path_id: str
    current_step: Optional[str] = None
    completed_steps: List[str] = None
    step_progress: Dict[str, Dict[str, Any]] = None
    start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    status: OnboardingStatus = OnboardingStatus.NOT_STARTED
    time_spent_minutes: int = 0
    skipped_steps: List[str] = None
    feedback: Dict[str, str] = None

    def __post_init__(self):
        if self.completed_steps is None:
            self.completed_steps = []
        if self.step_progress is None:
            self.step_progress = {}
        if self.skipped_steps is None:
            self.skipped_steps = []
        if self.feedback is None:
            self.feedback = {}

@dataclass
class OnboardingMetric:
    """Onboarding performance metrics"""
    total_users: int = 0
    started_onboarding: int = 0
    completed_onboarding: int = 0
    average_completion_time_minutes: float = 0.0
    step_completion_rates: Dict[str, float] = None
    segment_performance: Dict[str, float] = None
    drop_off_points: List[Tuple[str, int]] = None

    def __post_init__(self):
        if self.step_completion_rates is None:
            self.step_completion_rates = {}
        if self.segment_performance is None:
            self.segment_performance = {}
        if self.drop_off_points is None:
            self.drop_off_points = []

class OnboardingFlowSystem:
    """Beta user onboarding flow management system"""

    def __init__(self):
        self.db_path = "/home/activeloguser/DMLogn8n/launch/beta/data/onboarding_flow.db"
        self.config_path = "/home/activeloguser/DMLogn8n/launch/beta/config/onboarding_config.json"
        self.user_progress: Dict[str, UserOnboardingProgress] = {}
        self.onboarding_paths: Dict[str, OnboardingPath] = {}
        self.metrics = OnboardingMetric()
        self.init_database()
        self.load_onboarding_paths()

    def init_database(self):
        """Initialize SQLite database for onboarding"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # User progress table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_onboarding_progress (
                user_id TEXT PRIMARY KEY,
                segment TEXT NOT NULL,
                user_type TEXT NOT NULL,
                path_id TEXT NOT NULL,
                current_step TEXT,
                completed_steps TEXT,
                step_progress TEXT,
                start_date TIMESTAMP,
                completion_date TIMESTAMP,
                status TEXT DEFAULT 'not_started',
                time_spent_minutes INTEGER DEFAULT 0,
                skipped_steps TEXT,
                feedback TEXT
            )
        ''')

        # Onboarding paths table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS onboarding_paths (
                path_id TEXT PRIMARY KEY,
                segment TEXT NOT NULL,
                user_type TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                steps TEXT,
                total_time_minutes INTEGER,
                required_steps TEXT,
                optional_steps TEXT,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')

        # Step interactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS step_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                step_id TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                duration_seconds INTEGER,
                data TEXT,
                FOREIGN KEY (user_id) REFERENCES user_onboarding_progress (user_id)
            )
        ''')

        # Onboarding metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS onboarding_metrics (
                date DATE PRIMARY KEY,
                total_users INTEGER,
                started_onboarding INTEGER,
                completed_onboarding INTEGER,
                average_completion_time REAL,
                completion_rate REAL,
                segment_metrics TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def load_onboarding_paths(self):
        """Load or create onboarding paths for different user segments"""
        # Check if paths exist in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM onboarding_paths WHERE is_active = TRUE')
        rows = cursor.fetchall()
        conn.close()

        if rows:
            # Load existing paths from database
            for row in rows:
                path = self._row_to_onboarding_path(row)
                self.onboarding_paths[path.path_id] = path
        else:
            # Create default onboarding paths
            self.create_default_onboarding_paths()

    def _row_to_onboarding_path(self, row) -> OnboardingPath:
        """Convert database row to OnboardingPath"""
        return OnboardingPath(
            path_id=row[0],
            segment=UserSegment(row[1]),
            user_type=UserType(row[2]),
            name=row[3],
            description=row[4],
            steps=[self._dict_to_onboarding_step(step) for step in json.loads(row[5])],
            total_time_minutes=row[6],
            required_steps=json.loads(row[7]),
            optional_steps=json.loads(row[8])
        )

    def _dict_to_onboarding_step(self, step_dict: Dict[str, Any]) -> OnboardingStep:
        """Convert dictionary to OnboardingStep"""
        return OnboardingStep(
            step_id=step_dict['step_id'],
            title=step_dict['title'],
            description=step_dict['description'],
            step_type=step_dict['step_type'],
            required=step_dict['required'],
            estimated_time_minutes=step_dict['estimated_time_minutes'],
            content_url=step_dict.get('content_url'),
            completion_criteria=step_dict.get('completion_criteria'),
            next_steps=step_dict.get('next_steps', [])
        )

    def create_default_onboarding_paths(self):
        """Create default onboarding paths for each segment"""
        paths = [
            self.create_developer_path(),
            self.create_gamer_path(),
            self.create_educator_path(),
            self.create_enterprise_path(),
            self.create_content_creator_path(),
            self.create_community_manager_path()
        ]

        for path in paths:
            self.onboarding_paths[path.path_id] = path
            self.save_onboarding_path(path)

    def create_developer_path(self) -> OnboardingPath:
        """Create onboarding path for developers"""
        steps = [
            OnboardingStep(
                step_id="dev_profile",
                title="Complete Developer Profile",
                description="Set up your developer profile with skills and preferences",
                step_type="action",
                required=True,
                estimated_time_minutes=5,
                completion_criteria={"profile_completion": 0.9}
            ),
            OnboardingStep(
                step_id="dev_tutorial",
                title="DMLogn8n API Tutorial",
                description="Learn the DMLogn8n API and workflow creation basics",
                step_type="tutorial",
                required=True,
                estimated_time_minutes=20,
                content_url="/tutorials/developer-basics",
                completion_criteria={"tutorial_completion": 1.0}
            ),
            OnboardingStep(
                step_id="dev_first_workflow",
                title="Create Your First Workflow",
                description="Build a simple automated workflow using our API",
                step_type="action",
                required=True,
                estimated_time_minutes=15,
                completion_criteria={"workflow_created": True, "workflow_tested": True}
            ),
            OnboardingStep(
                step_id="dev_advanced_features",
                title="Explore Advanced Features",
                description="Discover advanced automation and integration capabilities",
                step_type="video",
                required=False,
                estimated_time_minutes=10,
                content_url="/videos/advanced-features"
            ),
            OnboardingStep(
                step_id="dev_community",
                title="Join Developer Community",
                description="Connect with other developers on Discord",
                step_type="action",
                required=True,
                estimated_time_minutes=5,
                completion_criteria={"discord_joined": True, "introductions_posted": True}
            ),
            OnboardingStep(
                step_id="dev_feedback",
                title="Initial Developer Feedback",
                description="Share your thoughts on the developer experience",
                step_type="survey",
                required=True,
                estimated_time_minutes=5,
                completion_criteria={"survey_completion": 1.0}
            )
        ]

        return OnboardingPath(
            path_id="developer_path",
            segment=UserSegment.DEVELOPERS,
            user_type=UserType.TECHNICAL_USER,
            name="Developer Onboarding Path",
            description="Comprehensive onboarding for developers and technical users",
            steps=steps,
            total_time_minutes=sum(step.estimated_time_minutes for step in steps),
            required_steps=[step.step_id for step in steps if step.required],
            optional_steps=[step.step_id for step in steps if not step.required]
        )

    def create_gamer_path(self) -> OnboardingPath:
        """Create onboarding path for gamers"""
        steps = [
            OnboardingStep(
                step_id="gamer_profile",
                title="Create Your Gaming Profile",
                description="Set up your profile with gaming preferences and experience",
                step_type="action",
                required=True,
                estimated_time_minutes=5,
                completion_criteria={"profile_completion": 0.9}
            ),
            OnboardingStep(
                step_id="gamer_tutorial",
                title="DMLogn8n Gaming Experience",
                description="Learn how DMLogn8n enhances tabletop and RPG gaming",
                step_type="tutorial",
                required=True,
                estimated_time_minutes=15,
                content_url="/tutorials/gamer-basics"
            ),
            OnboardingStep(
                step_id="gamer_first_session",
                title="Join Your First Game Session",
                description="Participate in a guided game session",
                step_type="action",
                required=True,
                estimated_time_minutes=20,
                completion_criteria={"session_joined": True, "session_completed": True}
            ),
            OnboardingStep(
                step_id="gamer_stories",
                title="Explore Story Creation",
                description="Learn to create and customize game stories",
                step_type="interactive",
                required=False,
                estimated_time_minutes=10,
                content_url="/interactive/story-creator"
            ),
            OnboardingStep(
                step_id="gamer_community",
                title="Join Gaming Community",
                description="Connect with other gamers and find groups",
                step_type="action",
                required=True,
                estimated_time_minutes=5,
                completion_criteria={"discord_joined": True, "gaming_intro_posted": True}
            ),
            OnboardingStep(
                step_id="gamer_feedback",
                title="Gaming Experience Feedback",
                description="Share your thoughts on the gaming features",
                step_type="survey",
                required=True,
                estimated_time_minutes=5,
                completion_criteria={"survey_completion": 1.0}
            )
        ]

        return OnboardingPath(
            path_id="gamer_path",
            segment=UserSegment.GAMERS,
            user_type=UserType.CREATIVE_USER,
            name="Gamer Onboarding Path",
            description="Fun and engaging onboarding for gamers and RPG enthusiasts",
            steps=steps,
            total_time_minutes=sum(step.estimated_time_minutes for step in steps),
            required_steps=[step.step_id for step in steps if step.required],
            optional_steps=[step.step_id for step in steps if not step.required]
        )

    def create_educator_path(self) -> OnboardingPath:
        """Create onboarding path for educators"""
        steps = [
            OnboardingStep(
                step_id="edu_profile",
                title="Complete Educator Profile",
                description="Set up your educational background and teaching focus",
                step_type="action",
                required=True,
                estimated_time_minutes=5,
                completion_criteria={"profile_completion": 0.9}
            ),
            OnboardingStep(
                step_id="edu_tutorial",
                title="DMLogn8n for Education",
                description="Learn how to use DMLogn8n in educational settings",
                step_type="tutorial",
                required=True,
                estimated_time_minutes=15,
                content_url="/tutorials/educator-basics"
            ),
            OnboardingStep(
                step_id="edu_first_lesson",
                title="Create Your First Lesson",
                description="Design an interactive lesson using DMLogn8n",
                step_type="action",
                required=True,
                estimated_time_minutes=20,
                completion_criteria={"lesson_created": True, "lesson_planned": True}
            ),
            OnboardingStep(
                step_id="edu_classroom",
                title="Classroom Integration",
                description="Learn best practices for classroom implementation",
                step_type="reading",
                required=False,
                estimated_time_minutes=10,
                content_url="/guides/classroom-integration"
            ),
            OnboardingStep(
                step_id="edu_community",
                title="Join Educator Community",
                description="Connect with other educators and share resources",
                step_type="action",
                required=True,
                estimated_time_minutes=5,
                completion_criteria={"discord_joined": True, "edu_intro_posted": True}
            ),
            OnboardingStep(
                step_id="edu_feedback",
                title="Educator Experience Survey",
                description="Provide feedback on educational features",
                step_type="survey",
                required=True,
                estimated_time_minutes=5,
                completion_criteria={"survey_completion": 1.0}
            )
        ]

        return OnboardingPath(
            path_id="educator_path",
            segment=UserSegment.EDUCATORS,
            user_type=UserType.CREATIVE_USER,
            name="Educator Onboarding Path",
            description="Specialized onboarding for teachers and educational professionals",
            steps=steps,
            total_time_minutes=sum(step.estimated_time_minutes for step in steps),
            required_steps=[step.step_id for step in steps if step.required],
            optional_steps=[step.step_id for step in steps if not step.required]
        )

    def create_enterprise_path(self) -> OnboardingPath:
        """Create onboarding path for enterprise users"""
        steps = [
            OnboardingStep(
                step_id="ent_profile",
                title="Complete Enterprise Profile",
                description="Set up your organization profile and team information",
                step_type="action",
                required=True,
                estimated_time_minutes=10,
                completion_criteria={"profile_completion": 0.9, "team_info": True}
            ),
            OnboardingStep(
                step_id="ent_tutorial",
                title="DMLogn8n Enterprise Features",
                description="Learn about enterprise-grade features and security",
                step_type="tutorial",
                required=True,
                estimated_time_minutes=20,
                content_url="/tutorials/enterprise-basics"
            ),
            OnboardingStep(
                step_id="ent_first_project",
                title="Set Up Your First Project",
                description="Create and configure your team's first project",
                step_type="action",
                required=True,
                estimated_time_minutes=15,
                completion_criteria={"project_created": True, "team_configured": True}
            ),
            OnboardingStep(
                step_id="ent_security",
                title="Security and Compliance",
                description="Review security settings and compliance features",
                step_type="reading",
                required=True,
                estimated_time_minutes=10,
                content_url="/docs/security-compliance"
            ),
            OnboardingStep(
                step_id="ent_community",
                title="Join Enterprise Community",
                description="Connect with other enterprise users and account managers",
                step_type="action",
                required=True,
                estimated_time_minutes=5,
                completion_criteria={"discord_joined": True, "enterprise_intro_posted": True}
            ),
            OnboardingStep(
                step_id="ent_feedback",
                title="Enterprise Requirements Feedback",
                description="Share your enterprise requirements and feedback",
                step_type="survey",
                required=True,
                estimated_time_minutes=10,
                completion_criteria={"survey_completion": 1.0, "requirements_detailed": True}
            )
        ]

        return OnboardingPath(
            path_id="enterprise_path",
            segment=UserSegment.ENTERPRISE,
            user_type=UserType.POWER_USER,
            name="Enterprise Onboarding Path",
            description="Comprehensive onboarding for enterprise and business users",
            steps=steps,
            total_time_minutes=sum(step.estimated_time_minutes for step in steps),
            required_steps=[step.step_id for step in steps if step.required],
            optional_steps=[step.step_id for step in steps if not step.required]
        )

    def create_content_creator_path(self) -> OnboardingPath:
        """Create onboarding path for content creators"""
        steps = [
            OnboardingStep(
                step_id="creator_profile",
                title="Create Creator Profile",
                description="Set up your creator profile with channels and content type",
                step_type="action",
                required=True,
                estimated_time_minutes=5,
                completion_criteria={"profile_completion": 0.9, "channels_linked": True}
            ),
            OnboardingStep(
                step_id="creator_tutorial",
                title="DMLogn8n for Content Creation",
                description="Learn how to use DMLogn8n for creating engaging content",
                step_type="tutorial",
                required=True,
                estimated_time_minutes=15,
                content_url="/tutorials/creator-basics"
            ),
            OnboardingStep(
                step_id="creator_first_content",
                title="Create Your First Content",
                description="Produce your first piece of content using DMLogn8n",
                step_type="action",
                required=True,
                estimated_time_minutes=20,
                completion_criteria={"content_created": True, "content_shared": True}
            ),
            OnboardingStep(
                step_id="creator_audience",
                title="Build Your Audience",
                description="Learn strategies for growing your audience",
                step_type="video",
                required=False,
                estimated_time_minutes=10,
                content_url="/videos/audience-growth"
            ),
            OnboardingStep(
                step_id="creator_community",
                title="Join Creator Community",
                description="Connect with other content creators",
                step_type="action",
                required=True,
                estimated_time_minutes=5,
                completion_criteria={"discord_joined": True, "creator_intro_posted": True}
            ),
            OnboardingStep(
                step_id="creator_feedback",
                title="Creator Experience Survey",
                description="Provide feedback on content creation features",
                step_type="survey",
                required=True,
                estimated_time_minutes=5,
                completion_criteria={"survey_completion": 1.0}
            )
        ]

        return OnboardingPath(
            path_id="content_creator_path",
            segment=UserSegment.CONTENT_CREATORS,
            user_type=UserType.CREATIVE_USER,
            name="Content Creator Onboarding Path",
            description="Tailored onboarding for content creators and influencers",
            steps=steps,
            total_time_minutes=sum(step.estimated_time_minutes for step in steps),
            required_steps=[step.step_id for step in steps if step.required],
            optional_steps=[step.step_id for step in steps if not step.required]
        )

    def create_community_manager_path(self) -> OnboardingPath:
        """Create onboarding path for community managers"""
        steps = [
            OnboardingStep(
                step_id="cm_profile",
                title="Complete Community Manager Profile",
                description="Set up your community management profile and experience",
                step_type="action",
                required=True,
                estimated_time_minutes=5,
                completion_criteria={"profile_completion": 0.9, "experience_verified": True}
            ),
            OnboardingStep(
                step_id="cm_tutorial",
                title="DMLogn8n Community Management",
                description="Learn community management features and best practices",
                step_type="tutorial",
                required=True,
                estimated_time_minutes=15,
                content_url="/tutorials/community-management"
            ),
            OnboardingStep(
                step_id="cm_first_community",
                title="Set Up Your First Community",
                description="Create and configure your community space",
                step_type="action",
                required=True,
                estimated_time_minutes=15,
                completion_criteria={"community_created": True, "rules_set": True}
            ),
            OnboardingStep(
                step_id="cm_moderation",
                title="Moderation Tools and Strategies",
                description="Master moderation tools and community guidelines",
                step_type="interactive",
                required=False,
                estimated_time_minutes=10,
                content_url="/interactive/moderation-simulator"
            ),
            OnboardingStep(
                step_id="cm_community",
                title="Join Community Manager Network",
                description="Connect with other community managers",
                step_type="action",
                required=True,
                estimated_time_minutes=5,
                completion_criteria={"discord_joined": True, "cm_network_joined": True}
            ),
            OnboardingStep(
                step_id="cm_feedback",
                title="Community Management Feedback",
                description="Share feedback on community management features",
                step_type="survey",
                required=True,
                estimated_time_minutes=5,
                completion_criteria={"survey_completion": 1.0}
            )
        ]

        return OnboardingPath(
            path_id="community_manager_path",
            segment=UserSegment.COMMUNITY_MANAGERS,
            user_type=UserType.POWER_USER,
            name="Community Manager Onboarding Path",
            description="Specialized onboarding for community management professionals",
            steps=steps,
            total_time_minutes=sum(step.estimated_time_minutes for step in steps),
            required_steps=[step.step_id for step in steps if step.required],
            optional_steps=[step.step_id for step in steps if not step.required]
        )

    async def start_user_onboarding(self, user_id: str, segment: UserSegment, user_type: UserType) -> Tuple[bool, str]:
        """Start onboarding for a new user"""
        try:
            # Find appropriate onboarding path
            path_id = self.find_onboarding_path(segment, user_type)
            if not path_id:
                return False, "No suitable onboarding path found"

            # Create user progress
            progress = UserOnboardingProgress(
                user_id=user_id,
                segment=segment,
                user_type=user_type,
                path_id=path_id,
                start_date=datetime.now(),
                status=OnboardingStatus.PROFILE_STARTED
            )

            # Save to database
            await self.save_user_progress(progress)
            self.user_progress[user_id] = progress

            # Get first step
            path = self.onboarding_paths[path_id]
            first_step = path.steps[0] if path.steps else None

            # Send welcome message
            await self.send_onboarding_welcome(user_id, progress, first_step)

            # Track metrics
            self.metrics.started_onboarding += 1

            logger.info(f"Started onboarding for user {user_id} - {segment.value}")
            return True, f"Onboarding started with path: {path.name}"

        except Exception as e:
            logger.error(f"Error starting onboarding for {user_id}: {e}")
            return False, f"Failed to start onboarding: {str(e)}"

    def find_onboarding_path(self, segment: UserSegment, user_type: UserType) -> Optional[str]:
        """Find the most appropriate onboarding path"""
        # Try exact match first
        for path_id, path in self.onboarding_paths.items():
            if path.segment == segment and path.user_type == user_type:
                return path_id

        # Try segment match (any user type)
        for path_id, path in self.onboarding_paths.items():
            if path.segment == segment:
                return path_id

        # Default to developer path if no match
        return "developer_path"

    async def save_user_progress(self, progress: UserOnboardingProgress):
        """Save user progress to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO user_onboarding_progress
            (user_id, segment, user_type, path_id, current_step, completed_steps,
             step_progress, start_date, completion_date, status, time_spent_minutes,
             skipped_steps, feedback)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            progress.user_id, progress.segment.value, progress.user_type.value,
            progress.path_id, progress.current_step, json.dumps(progress.completed_steps),
            json.dumps(progress.step_progress), progress.start_date, progress.completion_date,
            progress.status.value, progress.time_spent_minutes,
            json.dumps(progress.skipped_steps), json.dumps(progress.feedback)
        ))

        conn.commit()
        conn.close()

    async def send_onboarding_welcome(self, user_id: str, progress: UserOnboardingProgress, first_step: Optional[OnboardingStep]):
        """Send welcome message for onboarding"""
        try:
            path = self.onboarding_paths[progress.path_id]

            welcome_message = f"""
            🎉 Welcome to DMLogn8n Beta, User {user_id}!

            Your personalized onboarding journey begins now!

            📋 Your Onboarding Path: {path.name}
            ⏱️ Estimated Time: {path.total_time_minutes} minutes
            🎯 Required Steps: {len(path.required_steps)}

            Your first step: {first_step.title if first_step else 'Get Started!'}
            {first_step.description if first_step else 'Begin your onboarding journey'}

            Ready to start? [Click here to begin onboarding]
            {first_step.content_url if first_step and first_step.content_url else ''}

            Need help? Join our Discord #onboarding channel!
            """

            logger.info(f"Onboarding welcome sent to user {user_id}")

        except Exception as e:
            logger.error(f"Error sending onboarding welcome: {e}")

    async def complete_step(self, user_id: str, step_id: str, completion_data: Dict[str, Any] = None) -> Tuple[bool, str]:
        """Mark a step as completed for a user"""
        try:
            if user_id not in self.user_progress:
                return False, "User not found in onboarding system"

            progress = self.user_progress[user_id]
            path = self.onboarding_paths[progress.path_id]

            # Find the step
            step = next((s for s in path.steps if s.step_id == step_id), None)
            if not step:
                return False, "Step not found in onboarding path"

            # Validate completion criteria if specified
            if step.completion_criteria:
                if not self.validate_step_completion(step.completion_criteria, completion_data):
                    return False, "Step completion criteria not met"

            # Mark step as completed
            if step_id not in progress.completed_steps:
                progress.completed_steps.append(step_id)

            # Update step progress
            progress.step_progress[step_id] = {
                "completed": True,
                "completion_time": datetime.now().isoformat(),
                "time_spent": completion_data.get("time_spent", 0) if completion_data else 0,
                "data": completion_data or {}
            }

            # Find next step
            next_step = self.find_next_step(progress, path)

            # Update current step
            if next_step:
                progress.current_step = next_step.step_id
            else:
                # Onboarding completed
                progress.current_step = None
                progress.completion_date = datetime.now()
                progress.status = OnboardingStatus.ONBOARDING_COMPLETED
                self.metrics.completed_onboarding += 1

                # Send completion message
                await self.send_onboarding_completion(user_id, progress)

            # Save progress
            await self.save_user_progress(progress)

            # Log step interaction
            await self.log_step_interaction(user_id, step_id, "completed", completion_data)

            logger.info(f"Step {step_id} completed for user {user_id}")
            return True, f"Step completed. Next: {next_step.title if next_step else 'Onboarding Complete!'}"

        except Exception as e:
            logger.error(f"Error completing step {step_id} for user {user_id}: {e}")
            return False, f"Failed to complete step: {str(e)}"

    def validate_step_completion(self, criteria: Dict[str, Any], data: Optional[Dict[str, Any]]) -> bool:
        """Validate step completion criteria"""
        if not data:
            return not criteria  # No criteria means auto-complete

        for key, expected_value in criteria.items():
            if key not in data:
                return False

            actual_value = data[key]
            if isinstance(expected_value, bool):
                if actual_value != expected_value:
                    return False
            elif isinstance(expected_value, (int, float)):
                if actual_value < expected_value:
                    return False
            elif isinstance(expected_value, str):
                if actual_value != expected_value:
                    return False

        return True

    def find_next_step(self, progress: UserOnboardingProgress, path: OnboardingPath) -> Optional[OnboardingStep]:
        """Find the next step for user to complete"""
        for step in path.steps:
            if step.step_id not in progress.completed_steps and step.step_id not in progress.skipped_steps:
                # Check if prerequisites are met (simplified - assume linear progression)
                if not step.required or all(prev_step in progress.completed_steps
                                          for prev_step in path.required_steps[:path.required_steps.index(step.step_id)]):
                    return step
        return None

    async def send_onboarding_completion(self, user_id: str, progress: UserOnboardingProgress):
        """Send onboarding completion message"""
        try:
            completion_message = f"""
            🎊 Congratulations, User {user_id}!

            You've successfully completed your DMLogn8n onboarding!

            ✅ Onboarding Path: {progress.path_id}
            ⏱️ Time Spent: {progress.time_spent_minutes} minutes
            📅 Completion Date: {progress.completion_date.strftime('%Y-%m-%d %H:%M')}
            🏆 Beta Badge Earned: Early Adopter

            What's Next:
            - Explore advanced features
            - Join community discussions
            - Start creating amazing content
            - Share your feedback with us

            Thank you for being part of our beta program!
            """

            logger.info(f"Onboarding completion sent to user {user_id}")

        except Exception as e:
            logger.error(f"Error sending onboarding completion: {e}")

    async def skip_step(self, user_id: str, step_id: str, reason: str = "") -> Tuple[bool, str]:
        """Skip a step for a user"""
        try:
            if user_id not in self.user_progress:
                return False, "User not found in onboarding system"

            progress = self.user_progress[user_id]
            path = self.onboarding_paths[progress.path_id]

            # Find the step
            step = next((s for s in path.steps if s.step_id == step_id), None)
            if not step:
                return False, "Step not found"

            # Can't skip required steps
            if step.required:
                return False, "Cannot skip required steps"

            # Skip the step
            progress.skipped_steps.append(step_id)
            progress.step_progress[step_id] = {
                "skipped": True,
                "skip_time": datetime.now().isoformat(),
                "reason": reason
            }

            # Find next step
            next_step = self.find_next_step(progress, path)
            progress.current_step = next_step.step_id if next_step else None

            # Save progress
            await self.save_user_progress(progress)

            # Log step interaction
            await self.log_step_interaction(user_id, step_id, "skipped", {"reason": reason})

            logger.info(f"Step {step_id} skipped for user {user_id}")
            return True, f"Step skipped. Next: {next_step.title if next_step else 'Onboarding Complete!'}"

        except Exception as e:
            logger.error(f"Error skipping step {step_id} for user {user_id}: {e}")
            return False, f"Failed to skip step: {str(e)}"

    async def log_step_interaction(self, user_id: str, step_id: str, action: str, data: Dict[str, Any] = None):
        """Log step interaction for analytics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO step_interactions (user_id, step_id, action, data)
                VALUES (?, ?, ?, ?)
            ''', (user_id, step_id, action, json.dumps(data or {})))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error logging step interaction: {e}")

    async def get_user_progress(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed progress for a user"""
        try:
            if user_id not in self.user_progress:
                # Load from database
                progress = await self.load_user_progress(user_id)
                if not progress:
                    return None
                self.user_progress[user_id] = progress
            else:
                progress = self.user_progress[user_id]

            path = self.onboarding_paths[progress.path_id]

            return {
                "user_id": user_id,
                "segment": progress.segment.value,
                "path_name": path.name,
                "current_step": progress.current_step,
                "status": progress.status.value,
                "progress_percentage": len(progress.completed_steps) / len(path.steps) * 100,
                "completed_steps": progress.completed_steps,
                "skipped_steps": progress.skipped_steps,
                "total_steps": len(path.steps),
                "required_steps": len(path.required_steps),
                "start_date": progress.start_date.isoformat() if progress.start_date else None,
                "completion_date": progress.completion_date.isoformat() if progress.completion_date else None,
                "time_spent_minutes": progress.time_spent_minutes,
                "next_step_title": None,
                "estimated_remaining_time": self.calculate_remaining_time(progress, path)
            }

        except Exception as e:
            logger.error(f"Error getting user progress: {e}")
            return None

    async def load_user_progress(self, user_id: str) -> Optional[UserOnboardingProgress]:
        """Load user progress from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM user_onboarding_progress WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_user_progress(row)
        return None

    def _row_to_user_progress(self, row) -> UserOnboardingProgress:
        """Convert database row to UserOnboardingProgress"""
        return UserOnboardingProgress(
            user_id=row[0],
            segment=UserSegment(row[1]),
            user_type=UserType(row[2]),
            path_id=row[3],
            current_step=row[4],
            completed_steps=json.loads(row[5]) if row[5] else [],
            step_progress=json.loads(row[6]) if row[6] else {},
            start_date=datetime.fromisoformat(row[7]) if row[7] else None,
            completion_date=datetime.fromisoformat(row[8]) if row[8] else None,
            status=OnboardingStatus(row[9]),
            time_spent_minutes=row[10],
            skipped_steps=json.loads(row[11]) if row[11] else [],
            feedback=json.loads(row[12]) if row[12] else {}
        )

    def calculate_remaining_time(self, progress: UserOnboardingProgress, path: OnboardingPath) -> int:
        """Calculate estimated remaining time for onboarding"""
        remaining_steps = [step for step in path.steps
                          if step.step_id not in progress.completed_steps
                          and step.step_id not in progress.skipped_steps]

        return sum(step.estimated_time_minutes for step in remaining_steps)

    async def save_onboarding_path(self, path: OnboardingPath):
        """Save onboarding path to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO onboarding_paths
            (path_id, segment, user_type, name, description, steps,
             total_time_minutes, required_steps, optional_steps, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE)
        ''', (
            path.path_id, path.segment.value, path.user_type.value, path.name,
            path.description, json.dumps([asdict(step) for step in path.steps]),
            path.total_time_minutes, json.dumps(path.required_steps),
            json.dumps(path.optional_steps)
        ))

        conn.commit()
        conn.close()

    async def get_onboarding_analytics(self) -> Dict[str, Any]:
        """Get comprehensive onboarding analytics"""
        try:
            total_users = len(self.user_progress)
            completed_users = len([u for u in self.user_progress.values()
                                 if u.status == OnboardingStatus.ONBOARDING_COMPLETED])

            completion_rate = completed_users / total_users if total_users > 0 else 0

            # Calculate average completion time
            completed_times = [u.time_spent_minutes for u in self.user_progress.values()
                             if u.status == OnboardingStatus.ONBOARDING_COMPLETED]
            avg_completion_time = sum(completed_times) / len(completed_times) if completed_times else 0

            # Step completion rates
            step_completion_rates = {}
            for path_id, path in self.onboarding_paths.items():
                for step in path.steps:
                    step_users = [u for u in self.user_progress.values() if u.path_id == path_id]
                    step_completed = len([u for u in step_users if step.step_id in u.completed_steps])
                    rate = step_completed / len(step_users) if step_users else 0
                    step_completion_rates[step.step_id] = rate

            # Segment performance
            segment_performance = {}
            for segment in UserSegment:
                segment_users = [u for u in self.user_progress.values() if u.segment == segment]
                segment_completed = len([u for u in segment_users
                                       if u.status == OnboardingStatus.ONBOARDING_COMPLETED])
                rate = segment_completed / len(segment_users) if segment_users else 0
                segment_performance[segment.value] = rate

            # Drop-off points
            drop_off_points = []
            for path_id, path in self.onboarding_paths.items():
                for i, step in enumerate(path.steps):
                    step_users = [u for u in self.user_progress.values() if u.path_id == path_id]
                    next_step_users = len([u for u in step_users
                                         if (i + 1 < len(path.steps) and
                                             path.steps[i + 1].step_id in u.completed_steps)])
                    drop_off_count = len(step_users) - next_step_users
                    if drop_off_count > 0:
                        drop_off_points.append((step.step_id, drop_off_count))

            return {
                "total_users": total_users,
                "completed_users": completed_users,
                "completion_rate": f"{completion_rate:.2%}",
                "average_completion_time_minutes": round(avg_completion_time, 1),
                "step_completion_rates": {k: f"{v:.2%}" for k, v in step_completion_rates.items()},
                "segment_performance": {k: f"{v:.2%}" for k, v in segment_performance.items()},
                "drop_off_points": drop_off_points,
                "active_paths": len(self.onboarding_paths),
                "most_dropped_steps": sorted(drop_off_points, key=lambda x: x[1], reverse=True)[:5]
            }

        except Exception as e:
            logger.error(f"Error getting onboarding analytics: {e}")
            return {}

# Main execution
async def main():
    """Main execution for onboarding flow system"""
    onboarding = OnboardingFlowSystem()

    print("DMLogn8n Onboarding Flow System Initialized")
    print("=" * 50)

    # Get analytics
    analytics = await onboarding.get_onboarding_analytics()
    print(f"Total Users: {analytics.get('total_users', 0)}")
    print(f"Completion Rate: {analytics.get('completion_rate', '0%')}")
    print(f"Average Completion Time: {analytics.get('average_completion_time_minutes', 0)} minutes")

    # Path information
    print(f"\nAvailable Onboarding Paths:")
    for path_id, path in onboarding.onboarding_paths.items():
        print(f"  {path.name}: {len(path.steps)} steps, {path.total_time_minutes} minutes")

if __name__ == "__main__":
    asyncio.run(main())