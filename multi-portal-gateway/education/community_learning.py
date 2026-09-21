#!/usr/bin/env python3
"""
DMLogn8n Community Learning - Peer Learning and Knowledge Sharing
Comprehensive community platform with forums, study groups, mentorship, and collaborative learning
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import re

# Third-party imports
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import yaml
import aiofiles
import aiohttp
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Boolean, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import redis
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('community_learning.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

Base = declarative_base()

class PostType(Enum):
    QUESTION = "question"
    DISCUSSION = "discussion"
    TUTORIAL = "tutorial"
    RESOURCE = "resource"
    ANNOUNCEMENT = "announcement"
    SHOWCASE = "showcase"
    HELP_REQUEST = "help_request"

class GroupType(Enum):
    STUDY_GROUP = "study_group"
    PROJECT_TEAM = "project_team"
    BOOK_CLUB = "book_club"
    WORKSHOP = "workshop"
    MENTORSHIP = "mentorship"
    INTEREST_GROUP = "interest_group"

class MentorshipStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

class ContentType(Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    CODE = "code"
    LINK = "link"

class ReactionType(Enum):
    LIKE = "like"
    LOVE = "love"
    LAUGH = "laugh"
    WOW = "wow"
    SAD = "sad"
    ANGRY = "angry"

@dataclass
class CommunityPost:
    id: str
    title: str
    content: str
    post_type: PostType
    author_id: str
    category_id: Optional[str]
    tags: List[str]
    attachments: List[Dict[str, Any]]
    view_count: int
    like_count: int
    reply_count: int
    is_pinned: bool
    is_locked: bool
    created_at: datetime
    updated_at: datetime
    last_activity: datetime

@dataclass
class CommunityReply:
    id: str
    post_id: str
    author_id: str
    content: str
    parent_reply_id: Optional[str]
    attachments: List[Dict[str, Any]]
    like_count: int
    is_best_answer: bool
    created_at: datetime
    updated_at: datetime

@dataclass
class StudyGroup:
    id: str
    name: str
    description: str
    group_type: GroupType
    creator_id: str
    members: List[str]
    moderators: List[str]
    is_private: bool
    max_members: int
    tags: List[str]
    schedule: Dict[str, Any]
    resources: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

@dataclass
class MentorshipRelationship:
    id: str
    mentor_id: str
    mentee_id: str
    status: MentorshipStatus
    goals: List[str]
    focus_areas: List[str]
    meeting_schedule: Dict[str, Any]
    progress_notes: List[Dict[str, Any]]
    start_date: datetime
    end_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class CommunityPostDB(Base):
    __tablename__ = "community_posts"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    post_type = Column(String, nullable=False)
    author_id = Column(String, ForeignKey("users.id"), nullable=False)
    category_id = Column(String, ForeignKey("community_categories.id"))
    tags = Column(Text)  # JSON string
    attachments = Column(Text)  # JSON string
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    is_pinned = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)

    # Relationships
    author = relationship("User")
    category = relationship("CommunityCategory")
    replies = relationship("CommunityReplyDB", back_populates="post")
    reactions = relationship("PostReaction", back_populates="post")

class CommunityReplyDB(Base):
    __tablename__ = "community_replies"

    id = Column(String, primary_key=True)
    post_id = Column(String, ForeignKey("community_posts.id"), nullable=False)
    author_id = Column(String, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    parent_reply_id = Column(String, ForeignKey("community_replies.id"))
    attachments = Column(Text)  # JSON string
    like_count = Column(Integer, default=0)
    is_best_answer = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    post = relationship("CommunityPostDB", back_populates="replies")
    author = relationship("User")
    parent_reply = relationship("CommunityReplyDB", remote_side=[id])
    child_replies = relationship("CommunityReplyDB")
    reactions = relationship("ReplyReaction", back_populates="reply")

class CommunityCategory(Base):
    __tablename__ = "community_categories"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    description = Column(Text)
    icon = Column(String)
    color = Column(String)
    parent_id = Column(String, ForeignKey("community_categories.id"))
    sort_order = Column(Integer, default=0)
    post_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    parent = relationship("CommunityCategory", remote_side=[id])
    children = relationship("CommunityCategory")

class StudyGroupDB(Base):
    __tablename__ = "study_groups"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    group_type = Column(String, nullable=False)
    creator_id = Column(String, ForeignKey("users.id"), nullable=False)
    members = Column(Text)  # JSON string
    moderators = Column(Text)  # JSON string
    is_private = Column(Boolean, default=False)
    max_members = Column(Integer, default=50)
    tags = Column(Text)  # JSON string
    schedule = Column(Text)  # JSON string
    resources = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    creator = relationship("User")
    meetings = relationship("GroupMeeting", back_populates="group")

class MentorshipDB(Base):
    __tablename__ = "mentorship_relationships"

    id = Column(String, primary_key=True)
    mentor_id = Column(String, ForeignKey("users.id"), nullable=False)
    mentee_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(String, default=MentorshipStatus.PENDING.value)
    goals = Column(Text)  # JSON string
    focus_areas = Column(Text)  # JSON string
    meeting_schedule = Column(Text)  # JSON string
    progress_notes = Column(Text)  # JSON string
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    mentor = relationship("User", foreign_keys=[mentor_id])
    mentee = relationship("User", foreign_keys=[mentee_id])
    meetings = relationship("MentorshipMeeting", back_populates="relationship")

class PostReaction(Base):
    __tablename__ = "post_reactions"

    id = Column(String, primary_key=True)
    post_id = Column(String, ForeignKey("community_posts.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    reaction_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    post = relationship("CommunityPostDB", back_populates="reactions")
    user = relationship("User")

class ReplyReaction(Base):
    __tablename__ = "reply_reactions"

    id = Column(String, primary_key=True)
    reply_id = Column(String, ForeignKey("community_replies.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    reaction_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    reply = relationship("CommunityReplyDB", back_populates="reactions")
    user = relationship("User")

class GroupMeeting(Base):
    __tablename__ = "group_meetings"

    id = Column(String, primary_key=True)
    group_id = Column(String, ForeignKey("study_groups.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    actual_start = Column(DateTime)
    actual_end = Column(DateTime)
    meeting_url = Column(String)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(Text)  # JSON string
    attendee_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    group = relationship("StudyGroupDB", back_populates="meetings")

class MentorshipMeeting(Base):
    __tablename__ = "mentorship_meetings"

    id = Column(String, primary_key=True)
    relationship_id = Column(String, ForeignKey("mentorship_relationships.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    actual_start = Column(DateTime)
    actual_end = Column(DateTime)
    meeting_url = Column(String)
    notes = Column(Text)
    action_items = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    relationship = relationship("MentorshipDB", back_populates="meetings")

class ContentModerator:
    """AI-powered content moderation system"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.toxic_keywords = self._load_toxic_keywords()
        self.spam_patterns = self._load_spam_patterns()

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load moderation configuration"""
        default_config = {
            "auto_moderation_enabled": True,
            "toxicity_threshold": 0.7,
            "spam_threshold": 0.8,
            "min_content_length": 10,
            "max_content_length": 10000,
            "allowed_links_per_post": 3,
            "flag_for_review": True,
            "auto_remove_spam": True
        }

        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)

        return default_config

    def _load_toxic_keywords(self) -> List[str]:
        """Load list of toxic keywords"""
        # In production, this would be loaded from a comprehensive database
        return [
            "spam", "scam", "hate", "abuse", "harassment",
            # Add more comprehensive list
        ]

    def _load_spam_patterns(self) -> List[str]:
        """Load spam detection patterns"""
        return [
            r'buy\s+now',
            r'click\s+here',
            r'free\s+money',
            r'limited\s+time',
            r'act\s+now',
            # Add more patterns
        ]

    async def moderate_content(self, content: str, user_id: str = None) -> Dict[str, Any]:
        """Moderate content for toxicity, spam, and quality"""
        moderation_result = {
            "is_approved": True,
            "flagged_reasons": [],
            "confidence_scores": {},
            "recommendations": []
        }

        if not self.config.get("auto_moderation_enabled"):
            return moderation_result

        # Check content length
        if len(content) < self.config["min_content_length"]:
            moderation_result["is_approved"] = False
            moderation_result["flagged_reasons"].append("Content too short")

        if len(content) > self.config["max_content_length"]:
            moderation_result["is_approved"] = False
            moderation_result["flagged_reasons"].append("Content too long")

        # Check for toxic keywords
        toxic_count = sum(1 for keyword in self.toxic_keywords if keyword.lower() in content.lower())
        toxicity_score = toxic_count / len(self.toxic_keywords)
        moderation_result["confidence_scores"]["toxicity"] = toxicity_score

        if toxicity_score > self.config["toxicity_threshold"]:
            moderation_result["is_approved"] = False
            moderation_result["flagged_reasons"].append("Toxic content detected")

        # Check for spam patterns
        spam_matches = 0
        for pattern in self.spam_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                spam_matches += 1

        spam_score = spam_matches / len(self.spam_patterns)
        moderation_result["confidence_scores"]["spam"] = spam_score

        if spam_score > self.config["spam_threshold"]:
            moderation_result["is_approved"] = False
            moderation_result["flagged_reasons"].append("Spam content detected")

        # Check for excessive links
        link_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        links = re.findall(link_pattern, content)
        if len(links) > self.config["allowed_links_per_post"]:
            moderation_result["recommendations"].append("Consider reducing the number of links")

        # Generate recommendations
        if not moderation_result["flagged_reasons"]:
            moderation_result["recommendations"].append("Content looks good!")

        return moderation_result

class MatchingEngine:
    """AI-powered matching engine for mentorship and study groups"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.skill_weight = 0.4
        self.interest_weight = 0.3
        self.experience_weight = 0.2
        self.availability_weight = 0.1

    async def find_mentor_matches(self, mentee_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find potential mentors for a mentee"""
        # Get mentee profile
        mentee = self.db.query(User).filter(User.id == mentee_id).first()
        if not mentee:
            return []

        # Get potential mentors
        mentors = self.db.query(User).filter(
            User.id != mentee_id,
            User.is_mentor == True
        ).all()

        # Calculate compatibility scores
        matches = []
        for mentor in mentors:
            score = await self._calculate_mentorship_compatibility(mentee, mentor)
            matches.append({
                "mentor_id": mentor.id,
                "name": mentor.full_name or mentor.username,
                "score": score,
                "shared_skills": await self._get_shared_skills(mentee, mentor),
                "mentor_bio": mentor.bio,
                "experience_years": mentor.experience_years
            })

        # Sort by score and return top matches
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:limit]

    async def find_study_group_matches(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find suitable study groups for a user"""
        # Get user profile
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []

        # Get available groups
        groups = self.db.query(StudyGroupDB).filter(
            StudyGroupDB.is_private == False
        ).all()

        # Calculate compatibility scores
        matches = []
        for group in groups:
            score = await self._calculate_group_compatibility(user, group)
            matches.append({
                "group_id": group.id,
                "name": group.name,
                "description": group.description,
                "score": score,
                "member_count": len(json.loads(group.members or "[]")),
                "group_type": group.group_type,
                "shared_interests": await self._get_shared_interests(user, group)
            })

        # Sort by score and return top matches
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:limit]

    async def find_study_partners(self, user_id: str, skill_focus: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Find compatible study partners"""
        # Get user profile
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []

        # Get other users
        other_users = self.db.query(User).filter(User.id != user_id).all()

        # Calculate compatibility scores
        matches = []
        for other_user in other_users:
            score = await self._calculate_study_partner_compatibility(user, other_user, skill_focus)
            matches.append({
                "user_id": other_user.id,
                "name": other_user.full_name or other_user.username,
                "score": score,
                "shared_skills": await self._get_shared_skills(user, other_user),
                "skill_level": other_user.skill_level,
                "availability": other_user.availability
            })

        # Sort by score and return top matches
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:limit]

    async def _calculate_mentorship_compatibility(self, mentee, mentor) -> float:
        """Calculate mentorship compatibility score"""
        score = 0.0

        # Skill matching
        mentor_skills = set(json.loads(mentor.skills or "[]"))
        mentee_goals = set(json.loads(mentee.learning_goals or "[]"))
        skill_overlap = len(mentor_skills & mentee_goals) / max(len(mentee_goals), 1)
        score += skill_overlap * self.skill_weight

        # Interest alignment
        mentor_interests = set(json.loads(mentor.interests or "[]"))
        mentee_interests = set(json.loads(mentee.interests or "[]"))
        interest_overlap = len(mentor_interests & mentee_interests) / max(len(mentee_interests), 1)
        score += interest_overlap * self.interest_weight

        # Experience match
        if mentor.experience_years:
            # Mentors should have more experience
            experience_score = min(mentor.experience_years / 10, 1.0)
            score += experience_score * self.experience_weight

        # Availability compatibility
        if mentor.availability and mentee.availability:
            # Simple availability matching
            availability_score = 0.5  # Placeholder
            score += availability_score * self.availability_weight

        return min(score, 1.0)

    async def _calculate_group_compatibility(self, user, group) -> float:
        """Calculate user-group compatibility score"""
        score = 0.0

        # Interest matching
        user_interests = set(json.loads(user.interests or "[]"))
        group_tags = set(json.loads(group.tags or "[]"))
        interest_overlap = len(user_interests & group_tags) / max(len(group_tags), 1)
        score += interest_overlap * 0.5

        # Skill level matching
        if group.group_type == GroupType.STUDY_GROUP.value:
            # For study groups, similar skill levels are better
            # This would require analyzing current members' skill levels
            score += 0.3  # Placeholder

        # Group size preference
        current_members = len(json.loads(group.members or "[]"))
        if current_members < group.max_members * 0.8:
            score += 0.2  # Group has space

        return min(score, 1.0)

    async def _calculate_study_partner_compatibility(self, user1, user2, skill_focus: str = None) -> float:
        """Calculate study partner compatibility score"""
        score = 0.0

        # Shared interests
        interests1 = set(json.loads(user1.interests or "[]"))
        interests2 = set(json.loads(user2.interests or "[]"))
        interest_overlap = len(interests1 & interests2) / max(len(interests1 | interests2), 1)
        score += interest_overlap * 0.4

        # Complementary skills
        skills1 = set(json.loads(user1.skills or "[]"))
        skills2 = set(json.loads(user2.skills or "[]"))
        if skill_focus:
            # If focusing on specific skill, check if either has it
            if skill_focus in skills1 or skill_focus in skills2:
                score += 0.3
        else:
            # General skill complementarity
            skill_union = skills1 | skills2
            skill_intersection = skills1 & skills2
            complementarity = len(skill_union) / max(len(skill_intersection), 1) - 1
            score += min(complementarity * 0.3, 0.3)

        # Learning style compatibility
        if user1.learning_style == user2.learning_style:
            score += 0.2

        # Availability matching
        if user1.availability and user2.availability:
            # Simple availability matching
            score += 0.1

        return min(score, 1.0)

    async def _get_shared_skills(self, user1, user2) -> List[str]:
        """Get shared skills between two users"""
        skills1 = set(json.loads(user1.skills or "[]"))
        skills2 = set(json.loads(user2.skills or "[]"))
        return list(skills1 & skills2)

    async def _get_shared_interests(self, user, group) -> List[str]:
        """Get shared interests between user and group"""
        user_interests = set(json.loads(user.interests or "[]"))
        group_tags = set(json.loads(group.tags or "[]"))
        return list(user_interests & group_tags)

class RecommendationEngine:
    """AI-powered recommendation engine for content and connections"""

    def __init__(self, db_session: Session, redis_client):
        self.db = db_session
        self.redis = redis_client
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')

    async def recommend_posts(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Recommend posts to user based on interests and activity"""
        # Get user profile
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []

        # Get user's interests
        user_interests = json.loads(user.interests or "[]")

        # Get recent posts
        recent_posts = self.db.query(CommunityPostDB).filter(
            CommunityPostDB.created_at >= datetime.utcnow() - timedelta(days=30)
        ).order_by(CommunityPostDB.last_activity.desc()).limit(100).all()

        # Score posts based on relevance
        scored_posts = []
        for post in recent_posts:
            score = 0.0

            # Interest matching
            post_tags = json.loads(post.tags or "[]")
            interest_matches = len(set(user_interests) & set(post_tags))
            score += interest_matches * 0.4

            # Popularity boost
            score += (post.like_count + post.reply_count) * 0.2

            # Recency boost
            days_old = (datetime.utcnow() - post.created_at).days
            recency_score = max(0, 1 - days_old / 30)
            score += recency_score * 0.2

            # View count boost (indicates interest)
            score += min(post.view_count / 100, 1) * 0.2

            scored_posts.append({
                "post_id": post.id,
                "title": post.title,
                "score": score,
                "post_type": post.post_type,
                "like_count": post.like_count,
                "reply_count": post.reply_count,
                "created_at": post.created_at
            })

        # Sort by score and return top recommendations
        scored_posts.sort(key=lambda x: x["score"], reverse=True)
        return scored_posts[:limit]

    async def recommend_study_groups(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Recommend study groups to user"""
        matching_engine = MatchingEngine(self.db)
        return await matching_engine.find_study_group_matches(user_id, limit)

    async def recommend_mentors(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Recommend mentors to user"""
        matching_engine = MatchingEngine(self.db)
        return await matching_engine.find_mentor_matches(user_id, limit)

    async def recommend_connections(self, user_id: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Recommend potential connections (study partners, collaborators)"""
        matching_engine = MatchingEngine(self.db)
        return await matching_engine.find_study_partners(user_id, limit=limit)

class CommunityAnalytics:
    """Analytics for community engagement and activity"""

    def __init__(self, db_session: Session, redis_client):
        self.db = db_session
        self.redis = redis_client

    async def get_community_stats(self) -> Dict[str, Any]:
        """Get overall community statistics"""
        # Get counts
        total_posts = self.db.query(CommunityPostDB).count()
        total_users = self.db.query(User).count()
        total_groups = self.db.query(StudyGroupDB).count()
        active_mentorships = self.db.query(MentorshipDB).filter(
            MentorshipDB.status == MentorshipStatus.ACTIVE.value
        ).count()

        # Get activity trends (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_posts = self.db.query(CommunityPostDB).filter(
            CommunityPostDB.created_at >= thirty_days_ago
        ).count()

        recent_replies = self.db.query(CommunityReplyDB).filter(
            CommunityReplyDB.created_at >= thirty_days_ago
        ).count()

        # Get top contributors
        top_posters = self.db.query(
            CommunityPostDB.author_id,
            self.db.func.count(CommunityPostDB.id).label('post_count')
        ).group_by(CommunityPostDB.author_id).order_by(
            self.db.func.count(CommunityPostDB.id).desc()
        ).limit(10).all()

        # Get most active categories
        active_categories = self.db.query(
            CommunityCategory.name,
            self.db.func.count(CommunityPostDB.id).label('post_count')
        ).join(CommunityPostDB).group_by(
            CommunityCategory.id
        ).order_by(
            self.db.func.count(CommunityPostDB.id).desc()
        ).limit(10).all()

        return {
            "total_posts": total_posts,
            "total_users": total_users,
            "total_study_groups": total_groups,
            "active_mentorships": active_mentorships,
            "recent_posts_30_days": recent_posts,
            "recent_replies_30_days": recent_replies,
            "top_contributors": [
                {"user_id": user_id, "post_count": count}
                for user_id, count in top_posters
            ],
            "active_categories": [
                {"category": name, "post_count": count}
                for name, count in active_categories
            ]
        }

    async def get_user_activity(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user's activity summary"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get user's posts
        user_posts = self.db.query(CommunityPostDB).filter(
            CommunityPostDB.author_id == user_id,
            CommunityPostDB.created_at >= cutoff_date
        ).all()

        # Get user's replies
        user_replies = self.db.query(CommunityReplyDB).filter(
            CommunityReplyDB.author_id == user_id,
            CommunityReplyDB.created_at >= cutoff_date
        ).all()

        # Get reactions given/received
        reactions_given = self.db.query(PostReaction).filter(
            PostReaction.user_id == user_id,
            PostReaction.created_at >= cutoff_date
        ).count()

        # Calculate engagement metrics
        total_likes = sum(post.like_count for post in user_posts)
        total_reply_likes = sum(reply.like_count for reply in user_replies)

        return {
            "posts_count": len(user_posts),
            "replies_count": len(user_replies),
            "reactions_given": reactions_given,
            "total_likes_received": total_likes + total_reply_likes,
            "engagement_score": (len(user_posts) * 2 + len(user_replies) + total_likes + total_reply_likes) / days
        }

    async def get_group_analytics(self, group_id: str) -> Dict[str, Any]:
        """Get analytics for a specific study group"""
        group = self.db.query(StudyGroupDB).filter(StudyGroupDB.id == group_id).first()
        if not group:
            return {}

        members = json.loads(group.members or "[]")
        meetings = self.db.query(GroupMeeting).filter(
            GroupMeeting.group_id == group_id
        ).all()

        # Member activity
        member_posts = self.db.query(CommunityPostDB).filter(
            CommunityPostDB.author_id.in_(members)
        ).count()

        # Meeting statistics
        completed_meetings = [m for m in meetings if m.actual_start]
        attendance_rate = sum(m.attendee_count for m in completed_meetings) / (len(completed_meetings) * len(members)) if completed_meetings else 0

        return {
            "group_id": group_id,
            "name": group.name,
            "member_count": len(members),
            "total_meetings": len(meetings),
            "completed_meetings": len(completed_meetings),
            "attendance_rate": attendance_rate,
            "member_posts": member_posts,
            "group_type": group.group_type
        }

# API Models
class CreatePostRequest(BaseModel):
    title: str
    content: str
    post_type: str
    category_id: Optional[str] = None
    tags: List[str] = []

class CreateReplyRequest(BaseModel):
    post_id: str
    content: str
    parent_reply_id: Optional[str] = None

class CreateGroupRequest(BaseModel):
    name: str
    description: str
    group_type: str
    is_private: bool = False
    max_members: int = 50
    tags: List[str] = []

class MentorshipRequest(BaseModel):
    mentor_id: str
    goals: List[str]
    focus_areas: List[str]
    message: str

class CommunityLearningApp:
    """Main Community Learning Application"""

    def __init__(self):
        self.app = FastAPI(title="DMLogn8n Community Learning", version="1.0.0")
        self.setup_middleware()
        self.setup_routes()

        # Initialize database
        self.engine = create_engine('sqlite:///community_learning.db')
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Initialize components
        self.content_moderator = ContentModerator()
        self.matching_engine = None
        self.recommendation_engine = None
        self.analytics = None

        # Initialize Redis
        self.redis_client = redis.Redis(host='localhost', port=6379, db=4)

        # Active WebSocket connections
        self.active_connections = {}

        # Templates and static files
        self.templates = Jinja2Templates(directory="templates")
        self.app.mount("/static", StaticFiles(directory="static"), name="static")

    def setup_middleware(self):
        """Setup FastAPI middleware"""
        from fastapi.middleware.cors import CORSMiddleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def setup_routes(self):
        """Setup API routes"""

        @self.app.get("/")
        async def root():
            return {"message": "DMLogn8n Community Learning API"}

        @self.app.get("/community/stats")
        async def get_community_stats():
            """Get community statistics"""
            if not self.analytics:
                self.analytics = CommunityAnalytics(self.SessionLocal(), self.redis_client)

            stats = await self.analytics.get_community_stats()
            return stats

        @self.app.post("/posts")
        async def create_post(request: CreatePostRequest, author_id: str):
            """Create new community post"""
            # Moderate content
            moderation_result = await self.content_moderator.moderate_content(
                request.content, author_id
            )

            if not moderation_result["is_approved"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Content not approved: {', '.join(moderation_result['flagged_reasons'])}"
                )

            db = self.SessionLocal()
            try:
                post = CommunityPostDB(
                    id=str(uuid.uuid4()),
                    title=request.title,
                    content=request.content,
                    post_type=request.post_type,
                    author_id=author_id,
                    category_id=request.category_id,
                    tags=json.dumps(request.tags),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    last_activity=datetime.utcnow()
                )

                db.add(post)
                db.commit()

                return {"post_id": post.id, "message": "Post created successfully"}

            finally:
                db.close()

        @self.app.get("/posts")
        async def get_posts(
            category_id: Optional[str] = None,
            post_type: Optional[str] = None,
            tags: Optional[str] = None,
            limit: int = 20,
            offset: int = 0,
            sort_by: str = "recent"
        ):
            """Get community posts with filtering"""
            db = self.SessionLocal()
            try:
                query = db.query(CommunityPostDB)

                if category_id:
                    query = query.filter(CommunityPostDB.category_id == category_id)
                if post_type:
                    query = query.filter(CommunityPostDB.post_type == post_type)

                # Apply sorting
                if sort_by == "recent":
                    query = query.order_by(CommunityPostDB.last_activity.desc())
                elif sort_by == "popular":
                    query = query.order_by(CommunityPostDB.like_count.desc())
                elif sort_by == "trending":
                    # Trending would consider time decay
                    query = query.order_by(CommunityPostDB.last_activity.desc())

                posts = query.offset(offset).limit(limit).all()

                return {
                    "posts": [
                        {
                            "id": post.id,
                            "title": post.title,
                            "content": post.content[:200] + "..." if len(post.content) > 200 else post.content,
                            "post_type": post.post_type,
                            "author_id": post.author_id,
                            "category_id": post.category_id,
                            "tags": json.loads(post.tags or "[]"),
                            "view_count": post.view_count,
                            "like_count": post.like_count,
                            "reply_count": post.reply_count,
                            "is_pinned": post.is_pinned,
                            "is_locked": post.is_locked,
                            "created_at": post.created_at,
                            "last_activity": post.last_activity
                        }
                        for post in posts
                    ],
                    "total": len(posts)
                }
            finally:
                db.close()

        @self.app.get("/posts/{post_id}")
        async def get_post(post_id: str):
            """Get detailed post with replies"""
            db = self.SessionLocal()
            try:
                post = db.query(CommunityPostDB).filter(CommunityPostDB.id == post_id).first()
                if not post:
                    raise HTTPException(status_code=404, detail="Post not found")

                # Increment view count
                post.view_count += 1
                db.commit()

                # Get replies
                replies = db.query(CommunityReplyDB).filter(
                    CommunityReplyDB.post_id == post_id
                ).order_by(CommunityReplyDB.created_at).all()

                return {
                    "post": {
                        "id": post.id,
                        "title": post.title,
                        "content": post.content,
                        "post_type": post.post_type,
                        "author_id": post.author_id,
                        "category_id": post.category_id,
                        "tags": json.loads(post.tags or "[]"),
                        "attachments": json.loads(post.attachments or "[]"),
                        "view_count": post.view_count,
                        "like_count": post.like_count,
                        "reply_count": post.reply_count,
                        "is_pinned": post.is_pinned,
                        "is_locked": post.is_locked,
                        "created_at": post.created_at,
                        "updated_at": post.updated_at
                    },
                    "replies": [
                        {
                            "id": reply.id,
                            "author_id": reply.author_id,
                            "content": reply.content,
                            "parent_reply_id": reply.parent_reply_id,
                            "attachments": json.loads(reply.attachments or "[]"),
                            "like_count": reply.like_count,
                            "is_best_answer": reply.is_best_answer,
                            "created_at": reply.created_at
                        }
                        for reply in replies
                    ]
                }
            finally:
                db.close()

        @self.app.post("/replies")
        async def create_reply(request: CreateReplyRequest, author_id: str):
            """Create reply to post"""
            # Moderate content
            moderation_result = await self.content_moderator.moderate_content(
                request.content, author_id
            )

            if not moderation_result["is_approved"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Content not approved: {', '.join(moderation_result['flagged_reasons'])}"
                )

            db = self.SessionLocal()
            try:
                # Check if post exists and is not locked
                post = db.query(CommunityPostDB).filter(CommunityPostDB.id == request.post_id).first()
                if not post:
                    raise HTTPException(status_code=404, detail="Post not found")
                if post.is_locked:
                    raise HTTPException(status_code=400, detail="Post is locked")

                reply = CommunityReplyDB(
                    id=str(uuid.uuid4()),
                    post_id=request.post_id,
                    author_id=author_id,
                    content=request.content,
                    parent_reply_id=request.parent_reply_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )

                db.add(reply)

                # Update post stats
                post.reply_count += 1
                post.last_activity = datetime.utcnow()

                db.commit()

                return {"reply_id": reply.id, "message": "Reply created successfully"}

            finally:
                db.close()

        @self.app.post("/groups")
        async def create_group(request: CreateGroupRequest, creator_id: str):
            """Create new study group"""
            db = self.SessionLocal()
            try:
                group = StudyGroupDB(
                    id=str(uuid.uuid4()),
                    name=request.name,
                    description=request.description,
                    group_type=request.group_type,
                    creator_id=creator_id,
                    members=json.dumps([creator_id]),
                    moderators=json.dumps([creator_id]),
                    is_private=request.is_private,
                    max_members=request.max_members,
                    tags=json.dumps(request.tags),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )

                db.add(group)
                db.commit()

                return {"group_id": group.id, "message": "Study group created successfully"}

            finally:
                db.close()

        @self.app.get("/groups")
        async def get_groups(
            group_type: Optional[str] = None,
            tags: Optional[str] = None,
            limit: int = 20,
            offset: int = 0
        ):
            """Get study groups"""
            db = self.SessionLocal()
            try:
                query = db.query(StudyGroupDB).filter(StudyGroupDB.is_private == False)

                if group_type:
                    query = query.filter(StudyGroupDB.group_type == group_type)

                groups = query.offset(offset).limit(limit).all()

                return {
                    "groups": [
                        {
                            "id": group.id,
                            "name": group.name,
                            "description": group.description,
                            "group_type": group.group_type,
                            "creator_id": group.creator_id,
                            "member_count": len(json.loads(group.members or "[]")),
                            "max_members": group.max_members,
                            "tags": json.loads(group.tags or "[]"),
                            "created_at": group.created_at
                        }
                        for group in groups
                    ],
                    "total": len(groups)
                }
            finally:
                db.close()

        @self.app.post("/mentorship/request")
        async def request_mentorship(request: MentorshipRequest, mentee_id: str):
            """Request mentorship"""
            db = self.SessionLocal()
            try:
                # Check if relationship already exists
                existing = db.query(MentorshipDB).filter(
                    MentorshipDB.mentor_id == request.mentor_id,
                    MentorshipDB.mentee_id == mentee_id,
                    MentorshipDB.status.in_([MentorshipStatus.PENDING.value, MentorshipStatus.ACTIVE.value])
                ).first()

                if existing:
                    raise HTTPException(status_code=400, detail="Mentorship relationship already exists")

                mentorship = MentorshipDB(
                    id=str(uuid.uuid4()),
                    mentor_id=request.mentor_id,
                    mentee_id=mentee_id,
                    status=MentorshipStatus.PENDING.value,
                    goals=json.dumps(request.goals),
                    focus_areas=json.dumps(request.focus_areas),
                    start_date=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )

                db.add(mentorship)
                db.commit()

                return {"mentorship_id": mentorship.id, "message": "Mentorship request sent"}

            finally:
                db.close()

        @self.app.get("/recommendations/{user_id}")
        async def get_recommendations(user_id: str, limit: int = 10):
            """Get personalized recommendations"""
            if not self.recommendation_engine:
                self.recommendation_engine = RecommendationEngine(self.SessionLocal(), self.redis_client)

            recommendations = await asyncio.gather(
                self.recommendation_engine.recommend_posts(user_id, limit),
                self.recommendation_engine.recommend_study_groups(user_id, limit),
                self.recommendation_engine.recommend_mentors(user_id, limit),
                self.recommendation_engine.recommend_connections(user_id, limit)
            )

            return {
                "posts": recommendations[0],
                "study_groups": recommendations[1],
                "mentors": recommendations[2],
                "connections": recommendations[3]
            }

        @self.app.get("/analytics/user/{user_id}")
        async def get_user_analytics(user_id: str, days: int = 30):
            """Get user activity analytics"""
            if not self.analytics:
                self.analytics = CommunityAnalytics(self.SessionLocal(), self.redis_client)

            analytics = await self.analytics.get_user_activity(user_id, days)
            return analytics

        @self.app.websocket("/ws/chat/{room_id}")
        async def websocket_chat_endpoint(websocket: WebSocket, room_id: str):
            """WebSocket for real-time chat"""
            await websocket.accept()

            if room_id not in self.active_connections:
                self.active_connections[room_id] = []

            self.active_connections[room_id].append(websocket)

            try:
                while True:
                    data = await websocket.receive_json()

                    # Broadcast message to all connections in room
                    for connection in self.active_connections[room_id]:
                        await connection.send_json({
                            "type": "message",
                            "data": data,
                            "timestamp": datetime.utcnow().isoformat()
                        })

            except WebSocketDisconnect:
                self.active_connections[room_id].remove(websocket)
                if not self.active_connections[room_id]:
                    del self.active_connections[room_id]

    def run(self, host: str = "0.0.0.0", port: int = 8005):
        """Run the community learning server"""
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)

# Main execution
if __name__ == "__main__":
    app = CommunityLearningApp()
    app.run()