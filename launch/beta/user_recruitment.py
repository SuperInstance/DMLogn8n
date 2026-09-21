#!/usr/bin/env python3
"""
DMLogn8n Beta User Recruitment System
Manages beta user acquisition, screening, and recruitment workflows for 10,000 user beta program
"""

import asyncio
import json
import logging
import random
import re
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
        logging.FileHandler('/home/activeloguser/DMLogn8n/launch/beta/logs/user_recruitment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RecruitmentSource(Enum):
    """Beta user recruitment sources"""
    WEBSITE_FORM = "website_form"
    DISCORD_COMMUNITY = "discord_community"
    TWITTER_CAMPAIGN = "twitter_campaign"
    REDDIT_OUTREACH = "reddit_outreach"
    PARTNER_REFERRAL = "partner_referral"
    EMPLOYEE_REFERRAL = "employee_referral"
    WAITING_LIST = "waiting_list"
    DIRECT_INVITE = "direct_invite"
    BETA_LISTING = "beta_listing"
    CONFERENCE_EVENT = "conference_event"

class RecruitmentStatus(Enum):
    """Recruitment application status"""
    PENDING_REVIEW = "pending_review"
    SCREENING = "screening"
    APPROVED = "approved"
    REJECTED = "rejected"
    WAITLISTED = "waitlisted"
    ACCEPTED = "accepted"
    DECLINED = "declined"

class UserSegment(Enum):
    """Beta user segments"""
    GAMERS = "gamers"
    DEVELOPERS = "developers"
    EDUCATORS = "educators"
    ENTERPRISE = "enterprise"
    CONTENT_CREATORS = "content_creators"
    COMMUNITY_MANAGERS = "community_managers"

@dataclass
class RecruitmentApplication:
    """Beta user recruitment application"""
    application_id: str
    email: str
    name: str
    username: str
    age_group: str
    country: str
    segment: UserSegment
    recruitment_source: RecruitmentSource
    experience_level: str  # beginner, intermediate, advanced, expert
    time_commitment: str  # hours per week
    motivation: str
    relevant_experience: str
    technical_skills: List[str]
    availability: Dict[str, bool]  # days/times available
    referral_code: Optional[str] = None
    application_date: datetime = None
    status: RecruitmentStatus = RecruitmentStatus.PENDING_REVIEW
    screening_score: float = 0.0
    reviewer_notes: str = ""
    priority_score: float = 0.0

    def __post_init__(self):
        if self.application_date is None:
            self.application_date = datetime.now()

@dataclass
class ScreeningCriteria:
    """Screening criteria for beta applications"""
    segment_weights: Dict[UserSegment, float]
    experience_weights: Dict[str, float]
    source_weights: Dict[RecruitmentSource, float]
    commitment_weights: Dict[str, float]
    required_skills: Dict[UserSegment, List[str]]
    priority_factors: Dict[str, float]

class UserRecruitmentSystem:
    """Beta user recruitment and screening system"""

    def __init__(self):
        self.db_path = "/home/activeloguser/DMLogn8n/launch/beta/data/user_recruitment.db"
        self.config_path = "/home/activeloguser/DMLogn8n/launch/beta/config/recruitment_config.json"
        self.applications: Dict[str, RecruitmentApplication] = {}
        self.screening_criteria = self.load_screening_criteria()
        self.recruitment_targets = {
            UserSegment.GAMERS: 2000,
            UserSegment.DEVELOPERS: 2500,
            UserSegment.EDUCATORS: 1500,
            UserSegment.ENTERPRISE: 1500,
            UserSegment.CONTENT_CREATORS: 1500,
            UserSegment.COMMUNITY_MANAGERS: 1000
        }
        self.init_database()

    def load_screening_criteria(self) -> ScreeningCriteria:
        """Load screening criteria from config"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                criteria_config = config.get('screening_criteria', {})

            return ScreeningCriteria(
                segment_weights={UserSegment(k): v for k, v in criteria_config.get('segment_weights', {}).items()},
                experience_weights=criteria_config.get('experience_weights', {}),
                source_weights={RecruitmentSource(k): v for k, v in criteria_config.get('source_weights', {}).items()},
                commitment_weights=criteria_config.get('commitment_weights', {}),
                required_skills={UserSegment(k): v for k, v in criteria_config.get('required_skills', {}).items()},
                priority_factors=criteria_config.get('priority_factors', {})
            )
        except FileNotFoundError:
            return self.create_default_criteria()

    def create_default_criteria(self) -> ScreeningCriteria:
        """Create default screening criteria"""
        return ScreeningCriteria(
            segment_weights={
                UserSegment.GAMERS: 0.15,
                UserSegment.DEVELOPERS: 0.25,
                UserSegment.EDUCATORS: 0.15,
                UserSegment.ENTERPRISE: 0.20,
                UserSegment.CONTENT_CREATORS: 0.15,
                UserSegment.COMMUNITY_MANAGERS: 0.10
            },
            experience_weights={
                "beginner": 0.6,
                "intermediate": 0.8,
                "advanced": 1.0,
                "expert": 1.2
            },
            source_weights={
                RecruitmentSource.WEBSITE_FORM: 0.8,
                RecruitmentSource.DISCORD_COMMUNITY: 1.0,
                RecruitmentSource.TWITTER_CAMPAIGN: 0.7,
                RecruitmentSource.REDDIT_OUTREACH: 0.8,
                RecruitmentSource.PARTNER_REFERRAL: 1.2,
                RecruitmentSource.EMPLOYEE_REFERRAL: 1.3,
                RecruitmentSource.WAITING_LIST: 0.9,
                RecruitmentSource.DIRECT_INVITE: 1.5,
                RecruitmentSource.BETA_LISTING: 0.6,
                RecruitmentSource.CONFERENCE_EVENT: 1.1
            },
            commitment_weights={
                "1-2 hours": 0.5,
                "3-5 hours": 0.8,
                "6-10 hours": 1.0,
                "11-15 hours": 1.2,
                "16+ hours": 1.0
            },
            required_skills={
                UserSegment.DEVELOPERS: ["python", "javascript", "api_integration", "automation"],
                UserSegment.GAMERS: ["gaming", "ttrpg", "storytelling", "creativity"],
                UserSegment.EDUCATORS: ["teaching", "curriculum_design", "student_engagement"],
                UserSegment.ENTERPRISE: ["project_management", "team_leadership", "business_analysis"],
                UserSegment.CONTENT_CREATORS: ["content_creation", "social_media", "community_building"],
                UserSegment.COMMUNITY_MANAGERS: ["community_management", "moderation", "communication"]
            },
            priority_factors={
                "referral_bonus": 0.2,
                "early_application": 0.1,
                "technical_expertise": 0.15,
                "community_influence": 0.15,
                "diversity_bonus": 0.1
            }
        )

    def init_database(self):
        """Initialize SQLite database for recruitment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Applications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recruitment_applications (
                application_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                username TEXT NOT NULL,
                age_group TEXT,
                country TEXT,
                segment TEXT NOT NULL,
                recruitment_source TEXT NOT NULL,
                experience_level TEXT,
                time_commitment TEXT,
                motivation TEXT,
                relevant_experience TEXT,
                technical_skills TEXT,
                availability TEXT,
                referral_code TEXT,
                application_date TIMESTAMP,
                status TEXT DEFAULT 'pending_review',
                screening_score REAL DEFAULT 0.0,
                reviewer_notes TEXT,
                priority_score REAL DEFAULT 0.0
            )
        ''')

        # Recruitment metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recruitment_metrics (
                date DATE PRIMARY KEY,
                total_applications INTEGER,
                approved_applications INTEGER,
                rejected_applications INTEGER,
                waitlisted_applications INTEGER,
                conversion_rate REAL,
                segment_distribution TEXT
            )
        ''')

        # Outreach campaigns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS outreach_campaigns (
                campaign_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                source TEXT NOT NULL,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                target_audience TEXT,
                budget REAL,
                applications_generated INTEGER,
                conversion_rate REAL,
                status TEXT DEFAULT 'active'
            )
        ''')

        conn.commit()
        conn.close()

    async def submit_application(self, application_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Submit new beta application"""
        try:
            # Validate required fields
            required_fields = ['email', 'name', 'username', 'segment', 'recruitment_source']
            for field in required_fields:
                if field not in application_data:
                    return False, f"Missing required field: {field}"

            # Check for existing application
            existing = await self.get_application_by_email(application_data['email'])
            if existing:
                return False, "Application already exists for this email"

            # Create application
            application = RecruitmentApplication(
                application_id=str(uuid.uuid4()),
                email=application_data['email'],
                name=application_data['name'],
                username=application_data['username'],
                age_group=application_data.get('age_group', ''),
                country=application_data.get('country', ''),
                segment=UserSegment(application_data['segment'].lower()),
                recruitment_source=RecruitmentSource(application_data['recruitment_source'].lower()),
                experience_level=application_data.get('experience_level', 'intermediate'),
                time_commitment=application_data.get('time_commitment', '3-5 hours'),
                motivation=application_data.get('motivation', ''),
                relevant_experience=application_data.get('relevant_experience', ''),
                technical_skills=application_data.get('technical_skills', []),
                availability=application_data.get('availability', {}),
                referral_code=application_data.get('referral_code'),
                application_date=datetime.now()
            )

            # Save to database
            await self.save_application(application)
            self.applications[application.application_id] = application

            # Send confirmation email
            await self.send_application_confirmation(application)

            # Queue for screening
            await self.queue_for_screening(application.application_id)

            logger.info(f"New application received: {application.email} - {application.segment.value}")
            return True, "Application submitted successfully"

        except Exception as e:
            logger.error(f"Error submitting application: {e}")
            return False, f"Submission failed: {str(e)}"

    async def get_application_by_email(self, email: str) -> Optional[RecruitmentApplication]:
        """Get application by email"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM recruitment_applications WHERE email = ?
        ''', (email,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_application(row)
        return None

    def _row_to_application(self, row) -> RecruitmentApplication:
        """Convert database row to RecruitmentApplication"""
        return RecruitmentApplication(
            application_id=row[0],
            email=row[1],
            name=row[2],
            username=row[3],
            age_group=row[4],
            country=row[5],
            segment=UserSegment(row[6]),
            recruitment_source=RecruitmentSource(row[7]),
            experience_level=row[8],
            time_commitment=row[9],
            motivation=row[10],
            relevant_experience=row[11],
            technical_skills=json.loads(row[12]) if row[12] else [],
            availability=json.loads(row[13]) if row[13] else {},
            referral_code=row[14],
            application_date=datetime.fromisoformat(row[15]) if row[15] else None,
            status=RecruitmentStatus(row[16]),
            screening_score=row[17],
            reviewer_notes=row[18],
            priority_score=row[19]
        )

    async def save_application(self, application: RecruitmentApplication):
        """Save application to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO recruitment_applications
            (application_id, email, name, username, age_group, country, segment,
             recruitment_source, experience_level, time_commitment, motivation,
             relevant_experience, technical_skills, availability, referral_code,
             application_date, status, screening_score, reviewer_notes, priority_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            application.application_id, application.email, application.name,
            application.username, application.age_group, application.country,
            application.segment.value, application.recruitment_source.value,
            application.experience_level, application.time_commitment,
            application.motivation, application.relevant_experience,
            json.dumps(application.technical_skills), json.dumps(application.availability),
            application.referral_code, application.application_date,
            application.status.value, application.screening_score,
            application.reviewer_notes, application.priority_score
        ))

        conn.commit()
        conn.close()

    async def send_application_confirmation(self, application: RecruitmentApplication):
        """Send application confirmation email"""
        try:
            subject = "DMLogn8n Beta Program - Application Received"

            body = f"""
            Dear {application.name},

            Thank you for applying to the DMLogn8n Beta Program! We've received your application and will review it shortly.

            Application Details:
            - Application ID: {application.application_id}
            - Email: {application.email}
            - Username: {application.username}
            - Segment: {application.segment.value}
            - Source: {application.recruitment_source.value}

            What happens next:
            1. Your application will be screened by our team
            2. You'll hear back from us within 5-7 business days
            3. If approved, you'll receive onboarding instructions
            4. Join our Discord to connect with other applicants: [Discord Link]

            Timeline:
            - Application Review: 3-5 days
            - Beta Wave Assignment: Based on segment and availability
            - Onboarding Start: Dates announced soon

            Questions? Reply to this email or join our Discord.

            Best regards,
            The DMLogn8n Beta Team
            """

            logger.info(f"Application confirmation queued for {application.email}")

        except Exception as e:
            logger.error(f"Error sending application confirmation: {e}")

    async def queue_for_screening(self, application_id: str):
        """Queue application for screening"""
        # In a real implementation, this would add to a screening queue
        logger.info(f"Application {application_id} queued for screening")

    async def screen_application(self, application_id: str) -> Tuple[bool, float, str]:
        """Screen application and return score and recommendation"""
        try:
            if application_id not in self.applications:
                return False, 0.0, "Application not found"

            application = self.applications[application_id]
            score = await self.calculate_screening_score(application)
            recommendation = await self.generate_recommendation(score, application)

            # Update application
            application.screening_score = score
            application.status = RecruitmentStatus.SCREENING
            await self.save_application(application)

            logger.info(f"Application {application_id} screened: {score:.2f} - {recommendation}")
            return True, score, recommendation

        except Exception as e:
            logger.error(f"Error screening application {application_id}: {e}")
            return False, 0.0, f"Screening failed: {str(e)}"

    async def calculate_screening_score(self, application: RecruitmentApplication) -> float:
        """Calculate screening score for application"""
        try:
            score = 0.0

            # Segment weight
            score += self.screening_criteria.segment_weights.get(application.segment, 0.5) * 30

            # Experience level weight
            score += self.screening_criteria.experience_weights.get(application.experience_level, 0.5) * 20

            # Recruitment source weight
            score += self.screening_criteria.source_weights.get(application.recruitment_source, 0.5) * 15

            # Time commitment weight
            score += self.screening_criteria.commitment_weights.get(application.time_commitment, 0.5) * 15

            # Skills matching
            required_skills = self.screening_criteria.required_skills.get(application.segment, [])
            skill_matches = len([skill for skill in application.technical_skills
                               if any(req in skill.lower() for req in required_skills)])
            skill_score = min(skill_matches / max(len(required_skills), 1), 1.0) * 15

            # Motivation quality (simple keyword analysis)
            motivation_score = self._analyze_motivation_quality(application.motivation) * 5

            total_score = score + skill_score + motivation_score

            # Priority factors
            if application.referral_code:
                total_score += self.screening_criteria.priority_factors.get('referral_bonus', 0.2) * 10

            # Early application bonus
            days_since_start = (datetime.now() - application.application_date).days
            if days_since_start < 7:
                total_score += self.screening_criteria.priority_factors.get('early_application', 0.1) * 5

            return min(total_score, 100.0)  # Cap at 100

        except Exception as e:
            logger.error(f"Error calculating screening score: {e}")
            return 0.0

    def _analyze_motivation_quality(self, motivation: str) -> float:
        """Simple motivation quality analysis"""
        if not motivation:
            return 0.0

        quality_indicators = [
            'passionate', 'excited', 'interested', 'curious', 'enthusiastic',
            'dedicated', 'committed', 'experienced', 'skilled', 'knowledgeable',
            'contribute', 'improve', 'help', 'test', 'feedback', 'community'
        ]

        motivation_lower = motivation.lower()
        indicator_count = sum(1 for indicator in quality_indicators if indicator in motivation_lower)

        # Score based on quality indicators and length
        length_score = min(len(motivation) / 200, 1.0)  # Normalize by length
        quality_score = min(indicator_count / 5, 1.0)  # Normalize by indicator count

        return (length_score + quality_score) / 2

    async def generate_recommendation(self, score: float, application: RecruitmentApplication) -> str:
        """Generate recommendation based on screening score"""
        if score >= 80:
            return "APPROVE - High quality applicant, strong fit for beta"
        elif score >= 65:
            return "APPROVE - Good fit, meets beta requirements"
        elif score >= 50:
            return "CONSIDER - Meets minimum requirements, review manually"
        elif score >= 35:
            return "WAITLIST - Some potential but not currently ready"
        else:
            return "REJECT - Does not meet beta requirements"

    async def approve_application(self, application_id: str, reviewer_notes: str = "") -> Tuple[bool, str]:
        """Approve application and send acceptance"""
        try:
            if application_id not in self.applications:
                return False, "Application not found"

            application = self.applications[application_id]
            application.status = RecruitmentStatus.APPROVED
            application.reviewer_notes = reviewer_notes
            await self.save_application(application)

            # Send acceptance email
            await self.send_acceptance_email(application)

            # Add to beta coordinator
            await self.add_to_beta_program(application)

            logger.info(f"Application approved: {application.email}")
            return True, "Application approved successfully"

        except Exception as e:
            logger.error(f"Error approving application: {e}")
            return False, f"Approval failed: {str(e)}"

    async def send_acceptance_email(self, application: RecruitmentApplication):
        """Send acceptance email"""
        try:
            subject = "Congratulations! You're Accepted to DMLogn8n Beta"

            body = f"""
            Dear {application.name},

            Congratulations! We're thrilled to accept you into the DMLogn8n Beta Program.

            Your Acceptance Details:
            - Application ID: {application.application_id}
            - Beta Segment: {application.segment.value}
            - Screening Score: {application.screening_score:.1f}/100

            Next Steps:
            1. Complete your beta profile: [Profile Link]
            2. Join our Discord community: [Discord Link]
            3. Choose your onboarding wave: [Wave Selection Link]
            4. Sign the beta agreement: [Agreement Link]

            Important Dates:
            - Beta Program Start: [Start Date]
            - Onboarding Period: [Onboarding Dates]
            - Full Access: [Full Access Date]

            As a beta tester, you'll receive:
            - Early access to DMLogn8n features
            - Exclusive beta tester badge
            - Direct communication with the development team
            - Influence on product development
            - Special rewards for active participation

            Welcome to the DMLogn8n beta community!

            Best regards,
            The DMLogn8n Team
            """

            logger.info(f"Acceptance email queued for {application.email}")

        except Exception as e:
            logger.error(f"Error sending acceptance email: {e}")

    async def add_to_beta_program(self, application: RecruitmentApplication):
        """Add approved user to beta program"""
        # This would integrate with the beta coordinator
        logger.info(f"Adding {application.email} to beta program as {application.segment.value}")

    async def reject_application(self, application_id: str, reason: str, reviewer_notes: str = "") -> Tuple[bool, str]:
        """Reject application with reason"""
        try:
            if application_id not in self.applications:
                return False, "Application not found"

            application = self.applications[application_id]
            application.status = RecruitmentStatus.REJECTED
            application.reviewer_notes = f"Reason: {reason}\n{reviewer_notes}"
            await self.save_application(application)

            # Send rejection email
            await self.send_rejection_email(application, reason)

            logger.info(f"Application rejected: {application.email} - {reason}")
            return True, "Application rejected"

        except Exception as e:
            logger.error(f"Error rejecting application: {e}")
            return False, f"Rejection failed: {str(e)}"

    async def send_rejection_email(self, application: RecruitmentApplication, reason: str):
        """Send rejection email"""
        try:
            subject = "DMLogn8n Beta Program - Update on Your Application"

            body = f"""
            Dear {application.name},

            Thank you for your interest in the DMLogn8n Beta Program. We've carefully reviewed your application.

            While we're unable to offer you a spot in the current beta cohort, we appreciate the time and effort you put into your application.

            Your application details:
            - Application ID: {application.application_id}
            - Segment: {application.segment.value}
            - Screening Score: {application.screening_score:.1f}/100

            Why weren't you selected?
            {reason}

            Stay Connected:
            - Join our waiting list for future cohorts: [Waiting List Link]
            - Follow us on social media for updates: [Social Links]
            - Sign up for our newsletter: [Newsletter Link]

            We'll keep your information on file and may reach out for future testing opportunities.

            Thank you for your understanding and interest in DMLogn8n!

            Best regards,
            The DMLogn8n Team
            """

            logger.info(f"Rejection email queued for {application.email}")

        except Exception as e:
            logger.error(f"Error sending rejection email: {e}")

    async def get_recruitment_metrics(self) -> Dict[str, Any]:
        """Get recruitment metrics and analytics"""
        try:
            total_applications = len(self.applications)
            approved = len([a for a in self.applications.values() if a.status == RecruitmentStatus.APPROVED])
            rejected = len([a for a in self.applications.values() if a.status == RecruitmentStatus.REJECTED])
            waitlisted = len([a for a in self.applications.values() if a.status == RecruitmentStatus.WAITLISTED])
            pending = len([a for a in self.applications.values() if a.status == RecruitmentStatus.PENDING_REVIEW])

            conversion_rate = approved / total_applications if total_applications > 0 else 0

            # Segment distribution
            segment_dist = {}
            for segment in UserSegment:
                segment_count = len([a for a in self.applications.values() if a.segment == segment])
                segment_dist[segment.value] = segment_count

            # Source distribution
            source_dist = {}
            for source in RecruitmentSource:
                source_count = len([a for a in self.applications.values() if a.recruitment_source == source])
                source_dist[source.value] = source_count

            # Experience level distribution
            exp_dist = {}
            for exp in ['beginner', 'intermediate', 'advanced', 'expert']:
                exp_count = len([a for a in self.applications.values() if a.experience_level == exp])
                exp_dist[exp] = exp_count

            return {
                "total_applications": total_applications,
                "approved": approved,
                "rejected": rejected,
                "waitlisted": waitlisted,
                "pending": pending,
                "conversion_rate": f"{conversion_rate:.2%}",
                "segment_distribution": segment_dist,
                "source_distribution": source_dist,
                "experience_distribution": exp_dist,
                "targets_progress": {
                    segment.value: {
                        "target": target,
                        "approved": len([a for a in self.applications.values()
                                       if a.segment == segment and a.status == RecruitmentStatus.APPROVED]),
                        "progress": len([a for a in self.applications.values()
                                      if a.segment == segment and a.status == RecruitmentStatus.APPROVED]) / target
                    }
                    for segment, target in self.recruitment_targets.items()
                }
            }

        except Exception as e:
            logger.error(f"Error getting recruitment metrics: {e}")
            return {}

    async def generate_waiting_list(self, limit: int = 500) -> List[str]:
        """Generate ranked waiting list from pending applications"""
        try:
            pending_apps = [app for app in self.applications.values()
                          if app.status == RecruitmentStatus.PENDING_REVIEW]

            # Sort by screening score (descending)
            pending_apps.sort(key=lambda x: x.screening_score, reverse=True)

            waiting_list = []
            for app in pending_apps[:limit]:
                app.status = RecruitmentStatus.WAITLISTED
                await self.save_application(app)
                waiting_list.append(app.application_id)

                # Send waitlist email
                await self.send_waitlist_email(app)

            logger.info(f"Generated waiting list with {len(waiting_list)} applicants")
            return waiting_list

        except Exception as e:
            logger.error(f"Error generating waiting list: {e}")
            return []

    async def send_waitlist_email(self, application: RecruitmentApplication):
        """Send waitlist notification email"""
        try:
            subject = "DMLogn8n Beta Program - You're on the Waitlist!"

            body = f"""
            Dear {application.name},

            Thank you for your patience! We've placed you on the DMLogn8n Beta Program waitlist.

            Your Waitlist Details:
            - Application ID: {application.application_id}
            - Waitlist Position: Based on screening score and segment needs
            - Screening Score: {application.screening_score:.1f}/100

            What this means:
            - You're qualified for the beta program
            - We'll contact you if a spot becomes available
            - Priority given to higher-scored applicants
            - May be contacted for future beta waves

            Stay engaged:
            - Join our Discord community: [Discord Link]
            - Follow development updates: [Blog Link]
            - Participate in community discussions

            We appreciate your interest in DMLogn8n and hope to include you in the beta soon!

            Best regards,
            The DMLogn8n Team
            """

            logger.info(f"Waitlist email queued for {application.email}")

        except Exception as e:
            logger.error(f"Error sending waitlist email: {e}")

    async def bulk_screen_applications(self, limit: int = 100) -> Dict[str, Any]:
        """Bulk screen pending applications"""
        try:
            pending_apps = [app for app in self.applications.values()
                          if app.status == RecruitmentStatus.PENDING_REVIEW][:limit]

            results = {
                "processed": 0,
                "approved": 0,
                "rejected": 0,
                "waitlisted": 0,
                "errors": []
            }

            for app in pending_apps:
                try:
                    success, score, recommendation = await self.screen_application(app.application_id)
                    if success:
                        results["processed"] += 1

                        # Auto-approve high scores, auto-reject low scores
                        if score >= 75:
                            await self.approve_application(app.application_id, f"Auto-approved: Score {score:.1f}")
                            results["approved"] += 1
                        elif score < 30:
                            await self.reject_application(app.application_id, "Auto-rejected: Insufficient screening score")
                            results["rejected"] += 1
                        # Manual review needed for middle scores
                    else:
                        results["errors"].append(f"Failed to screen {app.application_id}: {recommendation}")

                except Exception as e:
                    results["errors"].append(f"Error screening {app.application_id}: {str(e)}")

            logger.info(f"Bulk screening completed: {results}")
            return results

        except Exception as e:
            logger.error(f"Error in bulk screening: {e}")
            return {"error": str(e)}

# Main execution
async def main():
    """Main execution for user recruitment system"""
    recruitment = UserRecruitmentSystem()

    print("DMLogn8n User Recruitment System Initialized")
    print("=" * 50)

    # Get recruitment metrics
    metrics = await recruitment.get_recruitment_metrics()
    print(f"Total Applications: {metrics.get('total_applications', 0)}")
    print(f"Approved: {metrics.get('approved', 0)}")
    print(f"Conversion Rate: {metrics.get('conversion_rate', '0%')}")

    # Segment distribution
    segment_dist = metrics.get('segment_distribution', {})
    print("\nSegment Distribution:")
    for segment, count in segment_dist.items():
        print(f"  {segment}: {count}")

if __name__ == "__main__":
    asyncio.run(main())