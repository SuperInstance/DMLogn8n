#!/usr/bin/env python3
"""
DMLogn8n Beta Program Coordinator
Central management system for coordinating all aspects of the 10,000 user beta testing program
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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hashlib
import secrets
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/activeloguser/DMLogn8n/launch/beta/logs/beta_coordinator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BetaPhase(Enum):
    """Beta testing phases"""
    PREPARATION = "preparation"
    RECRUITMENT = "recruitment"
    ONBOARDING_WAVE_1 = "onboarding_wave_1"  # First 1000 users
    ONBOARDING_WAVE_2 = "onboarding_wave_2"  # Next 3000 users
    ONBOARDING_WAVE_3 = "onboarding_wave_3"  # Next 3000 users
    ONBOARDING_WAVE_4 = "onboarding_wave_4"  # Final 3000 users
    ACTIVE_TESTING = "active_testing"
    FEEDBACK_COLLECTION = "feedback_collection"
    OPTIMIZATION = "optimization"
    LAUNCH_PREPARATION = "launch_preparation"
    COMPLETED = "completed"

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
class BetaUser:
    """Beta user profile"""
    user_id: str
    email: str
    username: str
    segment: UserSegment
    user_type: UserType
    registration_date: datetime
    onboarding_date: Optional[datetime] = None
    last_active: Optional[datetime] = None
    activation_status: str = "pending"  # pending, active, inactive, churned
    beta_wave: int = 1
    feedback_score: float = 0.0
    bug_reports_count: int = 0
    feature_usage: Dict[str, int] = None
    communication_preferences: Dict[str, bool] = None

    def __post_init__(self):
        if self.feature_usage is None:
            self.feature_usage = {}
        if self.communication_preferences is None:
            self.communication_preferences = {
                "email": True,
                "discord": True,
                "in_app": True,
                "surveys": True
            }

@dataclass
class BetaMetrics:
    """Beta program metrics"""
    total_users: int = 0
    active_users: int = 0
    onboarding_completion_rate: float = 0.0
    retention_rate: float = 0.0
    feedback_count: int = 0
    bug_reports_count: int = 0
    satisfaction_score: float = 0.0
    feature_adoption_rate: float = 0.0
    community_engagement_rate: float = 0.0

class BetaCoordinator:
    """Central coordinator for DMLogn8n beta program"""

    def __init__(self):
        self.db_path = "/home/activeloguser/DMLogn8n/launch/beta/data/beta_coordinator.db"
        self.config_path = "/home/activeloguser/DMLogn8n/launch/beta/config/beta_config.json"
        self.current_phase = BetaPhase.PREPARATION
        self.beta_users: Dict[str, BetaUser] = {}
        self.metrics = BetaMetrics()
        self.wave_schedule = {
            1: {"start": None, "capacity": 1000, "segments": [UserSegment.GAMERS, UserSegment.DEVELOPERS]},
            2: {"start": None, "capacity": 3000, "segments": [UserSegment.EDUCATORS, UserSegment.CONTENT_CREATORS]},
            3: {"start": None, "capacity": 3000, "segments": [UserSegment.ENTERPRISE, UserSegment.COMMUNITY_MANAGERS]},
            4: {"start": None, "capacity": 3000, "segments": list(UserSegment)}  # Open to all
        }
        self.load_config()
        self.init_database()

    def load_config(self):
        """Load beta configuration"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = self.create_default_config()
            self.save_config()

    def create_default_config(self) -> Dict[str, Any]:
        """Create default beta configuration"""
        return {
            "beta_program": {
                "name": "DMLogn8n Beta Program",
                "version": "1.0.0",
                "target_users": 10000,
                "duration_weeks": 12,
                "phases": [phase.value for phase in BetaPhase],
                "waves": 4,
                "wave_capacity": [1000, 3000, 3000, 3000]
            },
            "onboarding": {
                "tutorial_duration_minutes": 30,
                "required_actions": [
                    "complete_profile",
                    "create_first_workflow",
                    "join_discord_community",
                    "complete_initial_survey"
                ],
                "completion_threshold": 0.8
            },
            "feedback": {
                "min_feedback_per_user": 3,
                "feedback_channels": ["in_app", "email", "discord", "surveys"],
                "response_time_hours": 24,
                "feedback_analysis_enabled": True
            },
            "communication": {
                "email_frequency_days": 3,
                "discord_channels": ["#announcements", "#beta-feedback", "#bug-reports", "#general"],
                "in_app_notifications": True,
                "weekly_digest": True
            },
            "success_criteria": {
                "min_retention_rate": 0.7,
                "min_satisfaction_score": 4.0,
                "max_critical_bugs": 5,
                "min_feature_adoption": 0.6,
                "min_community_engagement": 0.4
            },
            "rollout_strategy": {
                "gradual_increase": True,
                "capacity_buffer": 1.2,
                "monitoring_interval_minutes": 15,
                "auto_scaling": True
            }
        }

    def save_config(self):
        """Save beta configuration"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2, default=str)

    def init_database(self):
        """Initialize SQLite database for beta management"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS beta_users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                username TEXT NOT NULL,
                segment TEXT NOT NULL,
                user_type TEXT NOT NULL,
                registration_date TIMESTAMP,
                onboarding_date TIMESTAMP,
                last_active TIMESTAMP,
                activation_status TEXT DEFAULT 'pending',
                beta_wave INTEGER DEFAULT 1,
                feedback_score REAL DEFAULT 0.0,
                bug_reports_count INTEGER DEFAULT 0,
                feature_usage TEXT,
                communication_preferences TEXT
            )
        ''')

        # Phases table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS beta_phases (
                phase TEXT PRIMARY KEY,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                status TEXT DEFAULT 'pending',
                metrics TEXT
            )
        ''')

        # Metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS beta_metrics (
                date DATE PRIMARY KEY,
                total_users INTEGER,
                active_users INTEGER,
                new_users INTEGER,
                retention_rate REAL,
                satisfaction_score REAL,
                feedback_count INTEGER,
                bug_reports_count INTEGER
            )
        ''')

        # Communications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS communications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                type TEXT,
                subject TEXT,
                content TEXT,
                sent_date TIMESTAMP,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (user_id) REFERENCES beta_users (user_id)
            )
        ''')

        conn.commit()
        conn.close()

    async def register_beta_user(self, email: str, username: str, segment: str,
                                user_type: str, additional_info: Dict = None) -> Tuple[bool, str]:
        """Register a new beta user"""
        try:
            user_id = str(uuid.uuid4())

            # Check if user already exists
            if email in [user.email for user in self.beta_users.values()]:
                return False, "User already registered"

            # Validate segment and user type
            try:
                user_segment = UserSegment(segment.lower())
                user_type_enum = UserType(user_type.lower())
            except ValueError:
                return False, "Invalid segment or user type"

            # Determine beta wave based on segment and capacity
            wave = self.determine_beta_wave(user_segment)

            # Create beta user
            beta_user = BetaUser(
                user_id=user_id,
                email=email,
                username=username,
                segment=user_segment,
                user_type=user_type_enum,
                registration_date=datetime.now(),
                beta_wave=wave
            )

            # Store in database
            await self.save_user_to_db(beta_user)
            self.beta_users[user_id] = beta_user

            # Send welcome email
            await self.send_welcome_email(beta_user)

            # Update metrics
            self.metrics.total_users += 1

            logger.info(f"Registered new beta user: {username} ({email}) - Wave {wave}")
            return True, f"Successfully registered for beta wave {wave}"

        except Exception as e:
            logger.error(f"Error registering beta user: {e}")
            return False, f"Registration failed: {str(e)}"

    def determine_beta_wave(self, segment: UserSegment) -> int:
        """Determine which beta wave a user should be in"""
        for wave_num, wave_config in self.wave_schedule.items():
            if segment in wave_config["segments"]:
                # Check if wave has capacity
                current_count = len([u for u in self.beta_users.values() if u.beta_wave == wave_num])
                if current_count < wave_config["capacity"]:
                    return wave_num
        return 4  # Default to final wave if others are full

    async def save_user_to_db(self, user: BetaUser):
        """Save user to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO beta_users
            (user_id, email, username, segment, user_type, registration_date,
             onboarding_date, last_active, activation_status, beta_wave,
             feedback_score, bug_reports_count, feature_usage, communication_preferences)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user.user_id, user.email, user.username, user.segment.value, user.user_type.value,
            user.registration_date, user.onboarding_date, user.last_active, user.activation_status,
            user.beta_wave, user.feedback_score, user.bug_reports_count,
            json.dumps(user.feature_usage), json.dumps(user.communication_preferences)
        ))

        conn.commit()
        conn.close()

    async def send_welcome_email(self, user: BetaUser):
        """Send welcome email to new beta user"""
        try:
            subject = f"Welcome to DMLogn8n Beta Program - Wave {user.beta_wave}"

            body = f"""
            Dear {user.username},

            Welcome to the DMLogn8n Beta Program! We're excited to have you join us in Wave {user.beta_wave}.

            Your beta access details:
            - User ID: {user.user_id}
            - Email: {user.email}
            - Wave: {user.beta_wave}
            - Segment: {user.segment.value}

            Next Steps:
            1. Join our Discord community: [Discord Link]
            2. Complete your profile setup
            3. Watch the onboarding tutorial
            4. Join your wave's kickoff session

            Important Dates:
            - Wave {user.beta_wave} starts: {self.wave_schedule[user.beta_wave].get('start', 'TBD')}
            - Onboarding deadline: {self.wave_schedule[user.beta_wave].get('start', 'TBD')}

            You'll receive another email when your wave is ready to begin onboarding.

            Best regards,
            The DMLogn8n Team
            """

            # Store communication in database
            await self.store_communication(user.user_id, "email", subject, body)

            # In a real implementation, send via email service
            logger.info(f"Welcome email queued for {user.email}")

        except Exception as e:
            logger.error(f"Error sending welcome email: {e}")

    async def store_communication(self, user_id: str, comm_type: str, subject: str, content: str):
        """Store communication record in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO communications (user_id, type, subject, content, sent_date, status)
            VALUES (?, ?, ?, ?, ?, 'queued')
        ''', (user_id, comm_type, subject, content, datetime.now()))

        conn.commit()
        conn.close()

    async def start_beta_wave(self, wave_number: int):
        """Start a specific beta wave"""
        try:
            if wave_number not in self.wave_schedule:
                raise ValueError(f"Invalid wave number: {wave_number}")

            # Update wave schedule
            self.wave_schedule[wave_number]["start"] = datetime.now()

            # Update phase
            phase_map = {
                1: BetaPhase.ONBOARDING_WAVE_1,
                2: BetaPhase.ONBOARDING_WAVE_2,
                3: BetaPhase.ONBOARDING_WAVE_3,
                4: BetaPhase.ONBOARDING_WAVE_4
            }

            if wave_number in phase_map:
                self.current_phase = phase_map[wave_number]

            # Get users in this wave
            wave_users = [user for user in self.beta_users.values() if user.beta_wave == wave_number]

            # Send wave start notifications
            for user in wave_users:
                await self.send_wave_start_notification(user, wave_number)
                user.activation_status = "onboarding"
                await self.save_user_to_db(user)

            logger.info(f"Started beta wave {wave_number} with {len(wave_users)} users")
            return True, f"Wave {wave_number} started successfully"

        except Exception as e:
            logger.error(f"Error starting beta wave {wave_number}: {e}")
            return False, f"Failed to start wave: {str(e)}"

    async def send_wave_start_notification(self, user: BetaUser, wave_number: int):
        """Send wave start notification to user"""
        subject = f"DMLogn8n Beta Wave {wave_number} Has Started!"

        body = f"""
        Hi {user.username},

        Great news! Beta Wave {wave_number} has officially started. Your onboarding can now begin.

        Your Onboarding Checklist:
        1. Access the beta platform: [Platform Link]
        2. Complete your profile setup
        3. Watch the getting started tutorial
        4. Create your first workflow
        5. Join the Discord community
        6. Complete the initial feedback survey

        Resources:
        - Beta Handbook: [Handbook Link]
        - Video Tutorials: [Tutorials Link]
        - Support Discord: #wave-{wave_number}-support

        Your progress will be tracked, and you'll earn rewards for completing onboarding tasks.

        Need help? Reply to this email or join our Discord support channel.

        Happy testing!
        The DMLogn8n Team
        """

        await self.store_communication(user.user_id, "email", subject, body)
        logger.info(f"Wave start notification queued for {user.email}")

    async def update_user_activity(self, user_id: str, activity_type: str, details: Dict = None):
        """Update user activity and track engagement"""
        try:
            if user_id not in self.beta_users:
                return False, "User not found"

            user = self.beta_users[user_id]
            user.last_active = datetime.now()

            # Update feature usage
            if activity_type in user.feature_usage:
                user.feature_usage[activity_type] += 1
            else:
                user.feature_usage[activity_type] = 1

            # Update activation status based on activity
            if user.activation_status == "pending" and activity_type in ["login", "onboarding_complete"]:
                user.activation_status = "active"

            # Save to database
            await self.save_user_to_db(user)

            # Update metrics
            await self.calculate_metrics()

            return True, "Activity updated successfully"

        except Exception as e:
            logger.error(f"Error updating user activity: {e}")
            return False, f"Failed to update activity: {str(e)}"

    async def calculate_metrics(self):
        """Calculate current beta metrics"""
        try:
            total_users = len(self.beta_users)
            active_users = len([u for u in self.beta_users.values() if u.activation_status == "active"])

            # Calculate retention rate (users active in last 7 days)
            seven_days_ago = datetime.now() - timedelta(days=7)
            retained_users = len([
                u for u in self.beta_users.values()
                if u.last_active and u.last_active > seven_days_ago
            ])
            retention_rate = retained_users / total_users if total_users > 0 else 0

            # Calculate onboarding completion rate
            onboarded_users = len([u for u in self.beta_users.values() if u.onboarding_date])
            onboarding_rate = onboarded_users / total_users if total_users > 0 else 0

            # Calculate average satisfaction score
            feedback_scores = [u.feedback_score for u in self.beta_users.values() if u.feedback_score > 0]
            satisfaction_score = sum(feedback_scores) / len(feedback_scores) if feedback_scores else 0

            # Update metrics object
            self.metrics = BetaMetrics(
                total_users=total_users,
                active_users=active_users,
                onboarding_completion_rate=onboarding_rate,
                retention_rate=retention_rate,
                satisfaction_score=satisfaction_score,
                feedback_count=sum(u.bug_reports_count for u in self.beta_users.values()),
                bug_reports_count=sum(u.bug_reports_count for u in self.beta_users.values())
            )

            # Store daily metrics
            await self.store_daily_metrics()

        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")

    async def store_daily_metrics(self):
        """Store daily metrics in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        today = datetime.now().date()

        cursor.execute('''
            INSERT OR REPLACE INTO beta_metrics
            (date, total_users, active_users, retention_rate, satisfaction_score,
             feedback_count, bug_reports_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            today, self.metrics.total_users, self.metrics.active_users,
            self.metrics.retention_rate, self.metrics.satisfaction_score,
            self.metrics.feedback_count, self.metrics.bug_reports_count
        ))

        conn.commit()
        conn.close()

    async def get_beta_status(self) -> Dict[str, Any]:
        """Get comprehensive beta status"""
        return {
            "current_phase": self.current_phase.value,
            "total_users": self.metrics.total_users,
            "active_users": self.metrics.active_users,
            "retention_rate": f"{self.metrics.retention_rate:.2%}",
            "onboarding_completion": f"{self.metrics.onboarding_completion_rate:.2%}",
            "satisfaction_score": f"{self.metrics.satisfaction_score:.1f}/5.0",
            "feedback_count": self.metrics.feedback_count,
            "bug_reports_count": self.metrics.bug_reports_count,
            "wave_status": {
                wave: {
                    "capacity": config["capacity"],
                    "enrolled": len([u for u in self.beta_users.values() if u.beta_wave == wave]),
                    "started": config["start"] is not None,
                    "segments": [s.value for s in config["segments"]]
                }
                for wave, config in self.wave_schedule.items()
            },
            "user_segments": {
                segment.value: len([u for u in self.beta_users.values() if u.segment == segment])
                for segment in UserSegment
            }
        }

    async def generate_beta_report(self) -> str:
        """Generate comprehensive beta report"""
        status = await self.get_beta_status()

        report = f"""
# DMLogn8n Beta Program Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Current Status
- Phase: {status['current_phase'].replace('_', ' ').title()}
- Total Users: {status['total_users']} / {self.config['beta_program']['target_users']}
- Active Users: {status['active_users']} ({status['retention_rate']})
- Onboarding Completion: {status['onboarding_completion']}
- Satisfaction Score: {status['satisfaction_score']}

## Wave Status
"""

        for wave, wave_info in status['wave_status'].items():
            progress = (wave_info['enrolled'] / wave_info['capacity']) * 100
            report += f"""
### Wave {wave}
- Progress: {wave_info['enrolled']}/{wave_info['capacity']} ({progress:.1f}%)
- Status: {'Started' if wave_info['started'] else 'Pending'}
- Segments: {', '.join(wave_info['segments'])}
"""

        report += f"""
## User Segments
"""
        for segment, count in status['user_segments'].items():
            percentage = (count / status['total_users']) * 100 if status['total_users'] > 0 else 0
            report += f"- {segment.replace('_', ' ').title()}: {count} ({percentage:.1f}%)\n"

        report += f"""
## Feedback & Issues
- Total Feedback: {status['feedback_count']}
- Bug Reports: {status['bug_reports_count']}

## Success Criteria Progress
- Retention Target: {status['retention_rate']} / {self.config['success_criteria']['min_retention_rate']:.0%}
- Satisfaction Target: {status['satisfaction_score']} / {self.config['success_criteria']['min_satisfaction_score']}/5.0
"""

        return report

    async def prepare_for_launch(self) -> Tuple[bool, str]:
        """Evaluate launch readiness based on beta performance"""
        try:
            success_criteria = self.config['success_criteria']

            # Check all criteria
            checks = {
                "retention": self.metrics.retention_rate >= success_criteria['min_retention_rate'],
                "satisfaction": self.metrics.satisfaction_score >= success_criteria['min_satisfaction_score'],
                "feature_adoption": True,  # Would be calculated from actual usage
                "community_engagement": True,  # Would be calculated from Discord activity
                "critical_bugs": self.metrics.bug_reports_count <= success_criteria['max_critical_bugs']
            }

            all_passed = all(checks.values())

            if all_passed:
                self.current_phase = BetaPhase.LAUNCH_PREPARATION
                return True, "Beta program successful - Ready for launch preparation"
            else:
                failed_criteria = [k for k, v in checks.items() if not v]
                return False, f"Launch criteria not met: {', '.join(failed_criteria)}"

        except Exception as e:
            logger.error(f"Error evaluating launch readiness: {e}")
            return False, f"Error evaluating readiness: {str(e)}"

# Main execution
async def main():
    """Main execution for beta coordinator"""
    coordinator = BetaCoordinator()

    # Example usage
    print("DMLogn8n Beta Coordinator Initialized")
    print("=" * 50)

    # Get current status
    status = await coordinator.get_beta_status()
    print(f"Current Phase: {status['current_phase']}")
    print(f"Total Users: {status['total_users']}")
    print(f"Active Users: {status['active_users']}")

    # Generate report
    report = await coordinator.generate_beta_report()
    print("\nBeta Report Generated")
    print(report)

if __name__ == "__main__":
    asyncio.run(main())