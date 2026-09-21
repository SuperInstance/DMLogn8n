#!/usr/bin/env python3
"""
DMLogn8n Beta Feedback Collection System
Comprehensive feedback collection and analysis for beta testing program
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import sqlite3
import aiohttp
import nltk
from textblob import TextBlob
from collections import Counter, defaultdict
import statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/activeloguser/DMLogn8n/launch/beta/logs/feedback_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FeedbackType(Enum):
    """Types of feedback collected"""
    GENERAL = "general"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    USABILITY = "usability"
    PERFORMANCE = "performance"
    SATISFACTION = "satisfaction"
    ONBOARDING = "onboarding"
    COMMUNITY = "community"
    DOCUMENTATION = "documentation"
    TECHNICAL = "technical"

class FeedbackChannel(Enum):
    """Feedback collection channels"""
    IN_APP = "in_app"
    EMAIL = "email"
    DISCORD = "discord"
    SURVEY = "survey"
    INTERVIEW = "interview"
    FORUM = "forum"
    SUPPORT_TICKET = "support_ticket"
    SOCIAL_MEDIA = "social_media"

class FeedbackPriority(Enum):
    """Feedback priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    URGENT = "urgent"

class FeedbackStatus(Enum):
    """Feedback processing status"""
    NEW = "new"
    REVIEWING = "reviewing"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REJECTED = "rejected"

class UserSegment(Enum):
    """Beta user segments"""
    GAMERS = "gamers"
    DEVELOPERS = "developers"
    EDUCATORS = "educators"
    ENTERPRISE = "enterprise"
    CONTENT_CREATORS = "content_creators"
    COMMUNITY_MANAGERS = "community_managers"

@dataclass
class FeedbackSubmission:
    """Individual feedback submission"""
    feedback_id: str
    user_id: str
    user_segment: UserSegment
    feedback_type: FeedbackType
    channel: FeedbackChannel
    title: str
    content: str
    rating: Optional[float] = None  # 1-5 scale
    priority: FeedbackPriority = FeedbackPriority.MEDIUM
    status: FeedbackStatus = FeedbackStatus.NEW
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    submission_date: datetime = None
    last_updated: datetime = None
    assigned_to: Optional[str] = None
    response: Optional[str] = None
    resolution_date: Optional[datetime] = None
    sentiment_score: Optional[float] = None
    action_items: List[str] = None

    def __post_init__(self):
        if self.submission_date is None:
            self.submission_date = datetime.now()
        if self.last_updated is None:
            self.last_updated = datetime.now()
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
        if self.action_items is None:
            self.action_items = []

@dataclass
class FeedbackSurvey:
    """Feedback survey definition"""
    survey_id: str
    name: str
    description: str
    target_segments: List[UserSegment]
    questions: List[Dict[str, Any]]
    is_active: bool = True
    created_date: datetime = None
    expiry_date: Optional[datetime] = None

    def __post_init__(self):
        if self.created_date is None:
            self.created_date = datetime.now()

@dataclass
class FeedbackAnalysis:
    """Feedback analysis results"""
    total_submissions: int
    submissions_by_type: Dict[str, int]
    submissions_by_channel: Dict[str, int]
    submissions_by_segment: Dict[str, int]
    average_rating: float
    sentiment_distribution: Dict[str, int]
    top_issues: List[Tuple[str, int]]
    top_suggestions: List[Tuple[str, int]]
    response_times: Dict[str, float]
    resolution_rates: Dict[str, float]
    trends: Dict[str, List[float]]

class FeedbackCollector:
    """Comprehensive feedback collection and analysis system"""

    def __init__(self):
        self.db_path = "/home/activeloguser/DMLogn8n/launch/beta/data/feedback_collector.db"
        self.config_path = "/home/activeloguser/DMLogn8n/launch/beta/config/feedback_config.json"
        self.feedback_submissions: Dict[str, FeedbackSubmission] = {}
        self.surveys: Dict[str, FeedbackSurvey] = {}
        self.init_database()
        self.load_surveys()

    def init_database(self):
        """Initialize SQLite database for feedback collection"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Feedback submissions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback_submissions (
                feedback_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                user_segment TEXT NOT NULL,
                feedback_type TEXT NOT NULL,
                channel TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                rating REAL,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'new',
                tags TEXT,
                metadata TEXT,
                submission_date TIMESTAMP,
                last_updated TIMESTAMP,
                assigned_to TEXT,
                response TEXT,
                resolution_date TIMESTAMP,
                sentiment_score REAL,
                action_items TEXT
            )
        ''')

        # Surveys table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback_surveys (
                survey_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                target_segments TEXT,
                questions TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_date TIMESTAMP,
                expiry_date TIMESTAMP
            )
        ''')

        # Survey responses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS survey_responses (
                response_id TEXT PRIMARY KEY,
                survey_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                user_segment TEXT NOT NULL,
                responses TEXT,
                submission_date TIMESTAMP,
                completed BOOLEAN DEFAULT FALSE
            )
        ''')

        # Feedback analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback_analytics (
                date DATE PRIMARY KEY,
                total_submissions INTEGER,
                average_rating REAL,
                sentiment_score REAL,
                response_time_avg REAL,
                resolution_rate REAL,
                submissions_by_type TEXT,
                submissions_by_channel TEXT,
                submissions_by_segment TEXT
            )
        ''')

        # Feedback tags table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback_tags (
                tag TEXT PRIMARY KEY,
                usage_count INTEGER DEFAULT 1,
                category TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def load_surveys(self):
        """Load existing surveys or create default ones"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM feedback_surveys WHERE is_active = TRUE')
        rows = cursor.fetchall()
        conn.close()

        if rows:
            for row in rows:
                survey = self._row_to_survey(row)
                self.surveys[survey.survey_id] = survey
        else:
            self.create_default_surveys()

    def _row_to_survey(self, row) -> FeedbackSurvey:
        """Convert database row to FeedbackSurvey"""
        return FeedbackSurvey(
            survey_id=row[0],
            name=row[1],
            description=row[2],
            target_segments=[UserSegment(seg) for seg in json.loads(row[3])],
            questions=json.loads(row[4]),
            is_active=bool(row[5]),
            created_date=datetime.fromisoformat(row[6]) if row[6] else None,
            expiry_date=datetime.fromisoformat(row[7]) if row[7] else None
        )

    def create_default_surveys(self):
        """Create default feedback surveys"""
        surveys = [
            self.create_initial_experience_survey(),
            self.create_feature_satisfaction_survey(),
            self.create_usability_survey(),
            self.create_bug_report_survey(),
            self.create_weekly_checkin_survey()
        ]

        for survey in surveys:
            self.surveys[survey.survey_id] = survey
            self.save_survey(survey)

    def create_initial_experience_survey(self) -> FeedbackSurvey:
        """Create initial experience survey"""
        questions = [
            {
                "id": "overall_satisfaction",
                "type": "rating",
                "question": "Overall, how satisfied are you with your DMLogn8n beta experience?",
                "scale": 5,
                "required": True
            },
            {
                "id": "ease_of_use",
                "type": "rating",
                "question": "How easy was it to get started with DMLogn8n?",
                "scale": 5,
                "required": True
            },
            {
                "id": "features_discovered",
                "type": "rating",
                "question": "How well did you discover and understand the available features?",
                "scale": 5,
                "required": True
            },
            {
                "id": "onboarding_helpful",
                "type": "rating",
                "question": "How helpful was the onboarding process?",
                "scale": 5,
                "required": True
            },
            {
                "id": "favorite_feature",
                "type": "text",
                "question": "What's your favorite feature so far and why?",
                "required": False
            },
            {
                "id": "improvement_suggestion",
                "type": "text",
                "question": "What's one thing you would improve about DMLogn8n?",
                "required": False
            },
            {
                "id": "additional_feedback",
                "type": "textarea",
                "question": "Any additional feedback or suggestions?",
                "required": False
            }
        ]

        return FeedbackSurvey(
            survey_id="initial_experience_survey",
            name="Initial Beta Experience Survey",
            description="Survey to collect initial impressions and feedback from beta users",
            target_segments=list(UserSegment),
            questions=questions,
            expiry_date=datetime.now() + timedelta(days=14)
        )

    def create_feature_satisfaction_survey(self) -> FeedbackSurvey:
        """Create feature satisfaction survey"""
        questions = [
            {
                "id": "workflow_creation",
                "type": "rating",
                "question": "How satisfied are you with the workflow creation features?",
                "scale": 5,
                "required": True
            },
            {
                "id": "ai_integration",
                "type": "rating",
                "question": "How satisfied are you with the AI integration and automation?",
                "scale": 5,
                "required": True
            },
            {
                "id": "user_interface",
                "type": "rating",
                "question": "How satisfied are you with the user interface design?",
                "scale": 5,
                "required": True
            },
            {
                "id": "performance",
                "type": "rating",
                "question": "How satisfied are you with the system performance?",
                "scale": 5,
                "required": True
            },
            {
                "id": "most_useful_feature",
                "type": "multiple_choice",
                "question": "Which feature do you find most useful?",
                "options": [
                    "Workflow Automation",
                    "AI Story Generation",
                    "Character Management",
                    "Community Features",
                    "Analytics Dashboard",
                    "Other"
                ],
                "required": True
            },
            {
                "id": "feature_improvements",
                "type": "checkbox",
                "question": "Which features need improvement? (Select all that apply)",
                "options": [
                    "Workflow Creation",
                    "AI Integration",
                    "User Interface",
                    "Performance",
                    "Documentation",
                    "Community Features",
                    "Mobile Experience"
                ],
                "required": False
            },
            {
                "id": "missing_features",
                "type": "text",
                "question": "What features are missing that you would like to see?",
                "required": False
            }
        ]

        return FeedbackSurvey(
            survey_id="feature_satisfaction_survey",
            name="Feature Satisfaction Survey",
            description="Detailed feedback on specific features and functionality",
            target_segments=list(UserSegment),
            questions=questions
        )

    def create_usability_survey(self) -> FeedbackSurvey:
        """Create usability survey"""
        questions = [
            {
                "id": "navigation_ease",
                "type": "rating",
                "question": "How easy is it to navigate the platform?",
                "scale": 5,
                "required": True
            },
            {
                "id": "learning_curve",
                "type": "rating",
                "question": "How steep was the learning curve?",
                "scale": 5,
                "required": True,
                "reverse": True  # Lower score is better for learning curve
            },
            {
                "id": "documentation_clarity",
                "type": "rating",
                "question": "How clear and helpful is the documentation?",
                "scale": 5,
                "required": True
            },
            {
                "id": "error_handling",
                "type": "rating",
                "question": "How helpful are error messages and troubleshooting guidance?",
                "scale": 5,
                "required": True
            },
            {
                "id": "confusing_points",
                "type": "text",
                "question": "What parts of the platform did you find confusing?",
                "required": False
            },
            {
                "id": "usability_improvements",
                "type": "textarea",
                "question": "What improvements would make the platform more user-friendly?",
                "required": False
            }
        ]

        return FeedbackSurvey(
            survey_id="usability_survey",
            name="Usability Survey",
            description="Focus on user experience and ease of use",
            target_segments=list(UserSegment),
            questions=questions
        )

    def create_bug_report_survey(self) -> FeedbackSurvey:
        """Create bug report survey"""
        questions = [
            {
                "id": "bug_frequency",
                "type": "rating",
                "question": "How often do you encounter bugs or issues?",
                "scale": 5,
                "required": True,
                "labels": ["Never", "Rarely", "Sometimes", "Often", "Very Often"]
            },
            {
                "id": "bug_severity",
                "type": "rating",
                "question": "How severe are the bugs you encounter?",
                "scale": 5,
                "required": True,
                "labels": ["Not Severe", "Minor", "Moderate", "Severe", "Critical"]
            },
            {
                "id": "bug_types",
                "type": "checkbox",
                "question": "What types of bugs have you encountered? (Select all that apply)",
                "options": [
                    "Performance Issues",
                    "UI/UX Problems",
                    "Feature Not Working",
                    "Crashes/Freezes",
                    "Data Loss",
                    "Login/Authentication",
                    "Integration Issues",
                    "Other"
                ],
                "required": False
            },
            {
                "id": "recent_bug_description",
                "type": "textarea",
                "question": "Describe the most recent bug you encountered:",
                "required": False
            },
            {
                "id": "bug_reporting_experience",
                "type": "rating",
                "question": "How satisfied are you with the bug reporting process?",
                "scale": 5,
                "required": True
            }
        ]

        return FeedbackSurvey(
            survey_id="bug_report_survey",
            name="Bug Report Survey",
            description="Collect information about bugs and technical issues",
            target_segments=list(UserSegment),
            questions=questions
        )

    def create_weekly_checkin_survey(self) -> FeedbackSurvey:
        """Create weekly checkin survey"""
        questions = [
            {
                "id": "weekly_satisfaction",
                "type": "rating",
                "question": "How was your experience with DMLogn8n this week?",
                "scale": 5,
                "required": True
            },
            {
                "id": "new_features_discovered",
                "type": "rating",
                "question": "Did you discover any new features this week?",
                "scale": 5,
                "required": True,
                "labels": ["No new features", "1-2 features", "3-4 features", "5+ features", "Many features"]
            },
            {
                "id": "weekly_highlights",
                "type": "text",
                "question": "What was the highlight of your DMLogn8n experience this week?",
                "required": False
            },
            {
                "id": "weekly_challenges",
                "type": "text",
                "question": "What challenges or frustrations did you encounter this week?",
                "required": False
            },
            {
                "id": "weekly_goals_achieved",
                "type": "checkbox",
                "question": "What did you accomplish this week? (Select all that apply)",
                "options": [
                    "Created new workflows",
                    "Completed a project",
                    "Collaborated with others",
                    "Explored new features",
                    "Helped other users",
                    "Provided feedback",
                    "Other"
                ],
                "required": False
            },
            {
                "id": "next_week_plans",
                "type": "text",
                "question": "What do you plan to do with DMLogn8n next week?",
                "required": False
            }
        ]

        return FeedbackSurvey(
            survey_id="weekly_checkin_survey",
            name="Weekly Check-in Survey",
            description="Quick weekly feedback to track ongoing user experience",
            target_segments=list(UserSegment),
            questions=questions
        )

    async def submit_feedback(self, feedback_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Submit new feedback"""
        try:
            # Validate required fields
            required_fields = ['user_id', 'user_segment', 'feedback_type', 'channel', 'title', 'content']
            for field in required_fields:
                if field not in feedback_data:
                    return False, f"Missing required field: {field}"

            # Create feedback submission
            feedback = FeedbackSubmission(
                feedback_id=str(uuid.uuid4()),
                user_id=feedback_data['user_id'],
                user_segment=UserSegment(feedback_data['user_segment'].lower()),
                feedback_type=FeedbackType(feedback_data['feedback_type'].lower()),
                channel=FeedbackChannel(feedback_data['channel'].lower()),
                title=feedback_data['title'],
                content=feedback_data['content'],
                rating=feedback_data.get('rating'),
                priority=FeedbackPriority(feedback_data.get('priority', 'medium').lower()),
                tags=feedback_data.get('tags', []),
                metadata=feedback_data.get('metadata', {}),
                action_items=feedback_data.get('action_items', [])
            )

            # Analyze sentiment
            feedback.sentiment_score = self.analyze_sentiment(feedback.content)

            # Auto-categorize and tag
            auto_tags = self.auto_categorize_feedback(feedback)
            feedback.tags.extend(auto_tags)

            # Save to database
            await self.save_feedback(feedback)
            self.feedback_submissions[feedback.feedback_id] = feedback

            # Auto-assign based on type and priority
            await self.auto_assign_feedback(feedback)

            # Send acknowledgment
            await self.send_feedback_acknowledgment(feedback)

            logger.info(f"New feedback submitted: {feedback.feedback_id} from {feedback.user_id}")
            return True, feedback.feedback_id

        except Exception as e:
            logger.error(f"Error submitting feedback: {e}")
            return False, f"Failed to submit feedback: {str(e)}"

    def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of feedback text"""
        try:
            blob = TextBlob(text)
            return blob.sentiment.polarity  # Returns value between -1 and 1
        except:
            return 0.0  # Neutral sentiment if analysis fails

    def auto_categorize_feedback(self, feedback: FeedbackSubmission) -> List[str]:
        """Auto-categorize feedback based on content"""
        tags = []
        content_lower = feedback.content.lower()
        title_lower = feedback.title.lower()

        # Bug indicators
        bug_keywords = ['bug', 'error', 'crash', 'issue', 'problem', 'broken', 'not working', 'failed']
        if any(keyword in content_lower or keyword in title_lower for keyword in bug_keywords):
            tags.append('bug')
            feedback.feedback_type = FeedbackType.BUG_REPORT

        # Feature request indicators
        feature_keywords = ['feature', 'add', 'implement', 'would like', 'wish', 'suggestion', 'improve']
        if any(keyword in content_lower or keyword in title_lower for keyword in feature_keywords):
            tags.append('feature_request')
            if feedback.feedback_type != FeedbackType.BUG_REPORT:
                feedback.feedback_type = FeedbackType.FEATURE_REQUEST

        # Performance indicators
        perf_keywords = ['slow', 'lag', 'performance', 'speed', 'fast', 'responsive', 'loading']
        if any(keyword in content_lower or keyword in title_lower for keyword in perf_keywords):
            tags.append('performance')
            feedback.feedback_type = FeedbackType.PERFORMANCE

        # UI/UX indicators
        ux_keywords = ['ui', 'ux', 'interface', 'design', 'layout', 'usability', 'user experience']
        if any(keyword in content_lower or keyword in title_lower for keyword in ux_keywords):
            tags.append('ui_ux')
            feedback.feedback_type = FeedbackType.USABILITY

        # Documentation indicators
        doc_keywords = ['documentation', 'docs', 'help', 'guide', 'tutorial', 'instructions']
        if any(keyword in content_lower or keyword in title_lower for keyword in doc_keywords):
            tags.append('documentation')
            feedback.feedback_type = FeedbackType.DOCUMENTATION

        return tags

    async def save_feedback(self, feedback: FeedbackSubmission):
        """Save feedback to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO feedback_submissions
            (feedback_id, user_id, user_segment, feedback_type, channel, title,
             content, rating, priority, status, tags, metadata, submission_date,
             last_updated, assigned_to, response, resolution_date, sentiment_score, action_items)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            feedback.feedback_id, feedback.user_id, feedback.user_segment.value,
            feedback.feedback_type.value, feedback.channel.value, feedback.title,
            feedback.content, feedback.rating, feedback.priority.value,
            feedback.status.value, json.dumps(feedback.tags), json.dumps(feedback.metadata),
            feedback.submission_date, feedback.last_updated, feedback.assigned_to,
            feedback.response, feedback.resolution_date, feedback.sentiment_score,
            json.dumps(feedback.action_items)
        ))

        conn.commit()
        conn.close()

        # Update tags usage
        await self.update_tag_usage(feedback.tags)

    async def update_tag_usage(self, tags: List[str]):
        """Update tag usage counts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for tag in tags:
            cursor.execute('''
                INSERT INTO feedback_tags (tag, usage_count)
                VALUES (?, 1)
                ON CONFLICT(tag) DO UPDATE SET usage_count = usage_count + 1
            ''', (tag,))

        conn.commit()
        conn.close()

    async def auto_assign_feedback(self, feedback: FeedbackSubmission):
        """Auto-assign feedback based on type and priority"""
        assignment_rules = {
            FeedbackType.BUG_REPORT: "engineering_team",
            FeedbackType.FEATURE_REQUEST: "product_team",
            FeedbackType.PERFORMANCE: "engineering_team",
            FeedbackType.USABILITY: "design_team",
            FeedbackType.DOCUMENTATION: "content_team",
            FeedbackType.TECHNICAL: "support_team",
            FeedbackType.COMMUNITY: "community_team"
        }

        if feedback.priority in [FeedbackPriority.HIGH, FeedbackPriority.CRITICAL, FeedbackPriority.URGENT]:
            feedback.assigned_to = "priority_team"
        else:
            feedback.assigned_to = assignment_rules.get(feedback.feedback_type, "general_team")

    async def send_feedback_acknowledgment(self, feedback: FeedbackSubmission):
        """Send acknowledgment to user"""
        try:
            # Update tag counts in tags table
            await self.update_tag_usage(feedback.tags)

            # Log acknowledgment
            logger.info(f"Feedback acknowledgment sent to user {feedback.user_id} for {feedback.feedback_id}")

        except Exception as e:
            logger.error(f"Error sending feedback acknowledgment: {e}")

    async def respond_to_feedback(self, feedback_id: str, response: str, responder_id: str) -> Tuple[bool, str]:
        """Respond to feedback submission"""
        try:
            if feedback_id not in self.feedback_submissions:
                return False, "Feedback not found"

            feedback = self.feedback_submissions[feedback_id]
            feedback.response = response
            feedback.assigned_to = responder_id
            feedback.last_updated = datetime.now()
            feedback.status = FeedbackStatus.ACKNOWLEDGED

            await self.save_feedback(feedback)

            # Send response to user
            await self.send_feedback_response(feedback, response)

            logger.info(f"Response sent for feedback {feedback_id}")
            return True, "Response sent successfully"

        except Exception as e:
            logger.error(f"Error responding to feedback: {e}")
            return False, f"Failed to send response: {str(e)}"

    async def send_feedback_response(self, feedback: FeedbackSubmission, response: str):
        """Send response to user"""
        try:
            response_message = f"""
            Subject: Re: {feedback.title}

            Thank you for your feedback on DMLogn8n!

            Your feedback ID: {feedback.feedback_id}
            Category: {feedback.feedback_type.value}
            Submitted: {feedback.submission_date.strftime('%Y-%m-%d %H:%M')}

            Our response:
            {response}

            We value your input and are committed to improving DMLogn8n based on user feedback.

            Best regards,
            The DMLogn8n Team
            """

            logger.info(f"Feedback response sent to user {feedback.user_id}")

        except Exception as e:
            logger.error(f"Error sending feedback response: {e}")

    async def resolve_feedback(self, feedback_id: str, resolution_notes: str, resolver_id: str) -> Tuple[bool, str]:
        """Mark feedback as resolved"""
        try:
            if feedback_id not in self.feedback_submissions:
                return False, "Feedback not found"

            feedback = self.feedback_submissions[feedback_id]
            feedback.status = FeedbackStatus.RESOLVED
            feedback.resolution_date = datetime.now()
            feedback.last_updated = datetime.now()
            feedback.assigned_to = resolver_id

            # Add resolution notes to response
            if feedback.response:
                feedback.response += f"\n\nResolution: {resolution_notes}"
            else:
                feedback.response = f"Resolution: {resolution_notes}"

            await self.save_feedback(feedback)

            # Send resolution notification
            await self.send_resolution_notification(feedback, resolution_notes)

            logger.info(f"Feedback {feedback_id} resolved by {resolver_id}")
            return True, "Feedback resolved successfully"

        except Exception as e:
            logger.error(f"Error resolving feedback: {e}")
            return False, f"Failed to resolve feedback: {str(e)}"

    async def send_resolution_notification(self, feedback: FeedbackSubmission, resolution_notes: str):
        """Send resolution notification to user"""
        try:
            notification = f"""
            Subject: Your Feedback Has Been Resolved - {feedback.title}

            Great news! We've resolved the feedback you submitted.

            Feedback ID: {feedback.feedback_id}
            Original Issue: {feedback.title}
            Resolution Date: {feedback.resolution_date.strftime('%Y-%m-%d %H:%M')}

            Resolution Details:
            {resolution_notes}

            Thank you for helping us improve DMLogn8n!

            Best regards,
            The DMLogn8n Team
            """

            logger.info(f"Resolution notification sent to user {feedback.user_id}")

        except Exception as e:
            logger.error(f"Error sending resolution notification: {e}")

    async def get_feedback_by_user(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get feedback submitted by a specific user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM feedback_submissions WHERE user_id = ?
            ORDER BY submission_date DESC
            LIMIT ?
        ''', (user_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_feedback_dict(row) for row in rows]

    def _row_to_feedback_dict(self, row) -> Dict[str, Any]:
        """Convert database row to feedback dictionary"""
        return {
            "feedback_id": row[0],
            "user_id": row[1],
            "user_segment": row[2],
            "feedback_type": row[3],
            "channel": row[4],
            "title": row[5],
            "content": row[6],
            "rating": row[7],
            "priority": row[8],
            "status": row[9],
            "tags": json.loads(row[10]) if row[10] else [],
            "metadata": json.loads(row[11]) if row[11] else {},
            "submission_date": row[12],
            "last_updated": row[13],
            "assigned_to": row[14],
            "response": row[15],
            "resolution_date": row[16],
            "sentiment_score": row[17],
            "action_items": json.loads(row[18]) if row[18] else []
        }

    async def get_feedback_analytics(self, days: int = 30) -> FeedbackAnalysis:
        """Get comprehensive feedback analytics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get date range
            start_date = datetime.now() - timedelta(days=days)

            cursor.execute('''
                SELECT * FROM feedback_submissions
                WHERE submission_date >= ?
                ORDER BY submission_date DESC
            ''', (start_date,))

            rows = cursor.fetchall()
            conn.close()

            submissions = [self._row_to_feedback_dict(row) for row in rows]

            # Calculate analytics
            total_submissions = len(submissions)

            # Submissions by type
            submissions_by_type = {}
            for submission in submissions:
                feedback_type = submission['feedback_type']
                submissions_by_type[feedback_type] = submissions_by_type.get(feedback_type, 0) + 1

            # Submissions by channel
            submissions_by_channel = {}
            for submission in submissions:
                channel = submission['channel']
                submissions_by_channel[channel] = submissions_by_channel.get(channel, 0) + 1

            # Submissions by segment
            submissions_by_segment = {}
            for submission in submissions:
                segment = submission['user_segment']
                submissions_by_segment[segment] = submissions_by_segment.get(segment, 0) + 1

            # Average rating
            ratings = [s['rating'] for s in submissions if s['rating'] is not None]
            average_rating = sum(ratings) / len(ratings) if ratings else 0

            # Sentiment distribution
            sentiments = [s['sentiment_score'] for s in submissions if s['sentiment_score'] is not None]
            sentiment_distribution = {"positive": 0, "neutral": 0, "negative": 0}
            for sentiment in sentiments:
                if sentiment > 0.1:
                    sentiment_distribution["positive"] += 1
                elif sentiment < -0.1:
                    sentiment_distribution["negative"] += 1
                else:
                    sentiment_distribution["neutral"] += 1

            # Top issues (most common tags)
            all_tags = []
            for submission in submissions:
                all_tags.extend(submission['tags'])
            tag_counter = Counter(all_tags)
            top_issues = tag_counter.most_common(10)

            # Calculate response times and resolution rates
            response_times = {}
            resolution_rates = {}

            for feedback_type in FeedbackType:
                type_submissions = [s for s in submissions if s['feedback_type'] == feedback_type.value]
                if type_submissions:
                    # Response time (mock calculation)
                    response_times[feedback_type.value] = 24.0  # hours
                    # Resolution rate
                    resolved = len([s for s in type_submissions if s['status'] == 'resolved'])
                    resolution_rates[feedback_type.value] = resolved / len(type_submissions)

            # Trends (simplified)
            trends = {
                "daily_submissions": [0] * days,
                "average_sentiment": [0.0] * days
            }

            return FeedbackAnalysis(
                total_submissions=total_submissions,
                submissions_by_type=submissions_by_type,
                submissions_by_channel=submissions_by_channel,
                submissions_by_segment=submissions_by_segment,
                average_rating=average_rating,
                sentiment_distribution=sentiment_distribution,
                top_issues=top_issues,
                top_suggestions=[],  # Would need more sophisticated analysis
                response_times=response_times,
                resolution_rates=resolution_rates,
                trends=trends
            )

        except Exception as e:
            logger.error(f"Error getting feedback analytics: {e}")
            return FeedbackAnalysis(0, {}, {}, {}, 0, {}, [], {}, {}, {}, {})

    async def get_top_feedback_by_priority(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top feedback by priority"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Priority order
        priority_order = {
            'urgent': 1,
            'critical': 2,
            'high': 3,
            'medium': 4,
            'low': 5
        }

        cursor.execute('''
            SELECT * FROM feedback_submissions
            WHERE status NOT IN ('resolved', 'closed')
            ORDER BY CASE priority
                WHEN 'urgent' THEN 1
                WHEN 'critical' THEN 2
                WHEN 'high' THEN 3
                WHEN 'medium' THEN 4
                WHEN 'low' THEN 5
            END, submission_date DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_feedback_dict(row) for row in rows]

    async def save_survey(self, survey: FeedbackSurvey):
        """Save survey to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO feedback_surveys
            (survey_id, name, description, target_segments, questions,
             is_active, created_date, expiry_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            survey.survey_id, survey.name, survey.description,
            json.dumps([seg.value for seg in survey.target_segments]),
            json.dumps(survey.questions), survey.is_active,
            survey.created_date, survey.expiry_date
        ))

        conn.commit()
        conn.close()

    async def submit_survey_response(self, survey_id: str, user_id: str, user_segment: UserSegment,
                                   responses: Dict[str, Any]) -> Tuple[bool, str]:
        """Submit survey response"""
        try:
            response_id = str(uuid.uuid4())

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO survey_responses
                (response_id, survey_id, user_id, user_segment, responses, submission_date, completed)
                VALUES (?, ?, ?, ?, ?, ?, TRUE)
            ''', (
                response_id, survey_id, user_id, user_segment.value,
                json.dumps(responses), datetime.now()
            ))

            conn.commit()
            conn.close()

            logger.info(f"Survey response submitted: {response_id} for survey {survey_id}")
            return True, response_id

        except Exception as e:
            logger.error(f"Error submitting survey response: {e}")
            return False, f"Failed to submit response: {str(e)}"

    async def generate_feedback_report(self, days: int = 30) -> str:
        """Generate comprehensive feedback report"""
        analytics = await self.get_feedback_analytics(days)
        top_feedback = await self.get_top_feedback_by_priority(10)

        report = f"""
# DMLogn8n Beta Feedback Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Period: Last {days} days

## Overview
- Total Submissions: {analytics.total_submissions}
- Average Rating: {analytics.average_rating:.2f}/5.0
- Sentiment Distribution: {analytics.sentiment_distribution}

## Feedback by Type
"""
        for feedback_type, count in analytics.submissions_by_type.items():
            report += f"- {feedback_type.replace('_', ' ').title()}: {count}\n"

        report += f"""
## Feedback by Channel
"""
        for channel, count in analytics.submissions_by_channel.items():
            report += f"- {channel.replace('_', ' ').title()}: {count}\n"

        report += f"""
## Top Issues & Tags
"""
        for issue, count in analytics.top_issues[:10]:
            report += f"- {issue}: {count} mentions\n"

        report += f"""
## Priority Feedback Items
"""
        for i, feedback in enumerate(top_feedback[:5], 1):
            report += f"""
{i}. **{feedback['title']}** ({feedback['priority'].upper()})
   - Type: {feedback['feedback_type']}
   - User Segment: {feedback['user_segment']}
   - Status: {feedback['status']}
   - Submitted: {feedback['submission_date']}
   - Content: {feedback['content'][:200]}{'...' if len(feedback['content']) > 200 else ''}
"""

        report += f"""
## Resolution Rates
"""
        for feedback_type, rate in analytics.resolution_rates.items():
            report += f"- {feedback_type.replace('_', ' ').title()}: {rate:.1%}\n"

        return report

# Main execution
async def main():
    """Main execution for feedback collector"""
    collector = FeedbackCollector()

    print("DMLogn8n Feedback Collection System Initialized")
    print("=" * 50)

    # Get analytics
    analytics = await collector.get_feedback_analytics()
    print(f"Total Feedback: {analytics.total_submissions}")
    print(f"Average Rating: {analytics.average_rating:.2f}/5.0")
    print(f"Sentiment Distribution: {analytics.sentiment_distribution}")

    # Generate report
    report = await collector.generate_feedback_report()
    print("\nFeedback Report Generated")
    print(report[:500] + "..." if len(report) > 500 else report)

if __name__ == "__main__":
    asyncio.run(main())