#!/usr/bin/env python3
"""
DMLogn8n Learning Platform - Interactive Learning Management System
World-class educational platform for multi-agent development and deployment
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid
import hashlib
import re
from enum import Enum

# Third-party imports
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import aiofiles
import aiohttp
import jwt
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Boolean, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import redis
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('learning_platform.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

Base = declarative_base()

class SkillLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class ContentType(Enum):
    VIDEO = "video"
    ARTICLE = "article"
    TUTORIAL = "tutorial"
    EXERCISE = "exercise"
    QUIZ = "quiz"
    PROJECT = "project"
    WORKSHOP = "workshop"
    LAB = "lab"

class LearningStyle(Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING = "reading"
    MIXED = "mixed"

@dataclass
class LearningPath:
    id: str
    title: str
    description: str
    skill_level: SkillLevel
    estimated_hours: float
    modules: List[str]
    prerequisites: List[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime

@dataclass
class Course:
    id: str
    title: str
    description: str
    instructor: str
    skill_level: SkillLevel
    duration_hours: float
    content_type: ContentType
    learning_objectives: List[str]
    modules: List[Dict]
    assessments: List[Dict]
    resources: List[Dict]
    tags: List[str]
    rating: float
    enrollment_count: int
    created_at: datetime
    updated_at: datetime

@dataclass
class UserProgress:
    user_id: str
    course_id: str
    progress_percentage: float
    completed_modules: List[str]
    current_module: str
    time_spent_minutes: int
    last_accessed: datetime
    achievements: List[str]
    notes: Dict[str, str]
    bookmarks: List[str]

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String)
    bio = Column(Text)
    skill_level = Column(String, default=SkillLevel.BEGINNER.value)
    learning_style = Column(String, default=LearningStyle.MIXED.value)
    interests = Column(Text)  # JSON string
    timezone = Column(String, default="UTC")
    language = Column(String, default="en")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)

    # Relationships
    enrollments = relationship("Enrollment", back_populates="user")
    achievements = relationship("UserAchievement", back_populates="user")
    progress = relationship("UserProgress", back_populates="user")

class CourseDB(Base):
    __tablename__ = "courses"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    instructor_id = Column(String, ForeignKey("users.id"))
    skill_level = Column(String, nullable=False)
    duration_hours = Column(Float)
    content_type = Column(String, nullable=False)
    learning_objectives = Column(Text)  # JSON string
    modules = Column(Text)  # JSON string
    assessments = Column(Text)  # JSON string
    resources = Column(Text)  # JSON string
    tags = Column(Text)  # JSON string
    rating = Column(Float, default=0.0)
    enrollment_count = Column(Integer, default=0)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    enrollments = relationship("Enrollment", back_populates="course")

class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    progress_percentage = Column(Float, default=0.0)
    time_spent_minutes = Column(Integer, default=0)
    current_module = Column(String)
    completed_modules = Column(Text)  # JSON string
    certificate_earned = Column(Boolean, default=False)
    certificate_url = Column(String)

    # Relationships
    user = relationship("User", back_populates="enrollments")
    course = relationship("CourseDB", back_populates="enrollments")

class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    achievement_type = Column(String, nullable=False)
    achievement_data = Column(Text)  # JSON string
    earned_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="achievements")

class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    module_id = Column(String)
    progress_data = Column(Text)  # JSON string
    time_spent_minutes = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
    bookmarks = Column(Text)  # JSON string

    # Relationships
    user = relationship("User", back_populates="progress")

class InteractiveCodeEnvironment:
    """Interactive coding environment for hands-on learning"""

    def __init__(self):
        self.active_sessions = {}
        self.docker_client = None  # Would initialize Docker client
        self.code_templates = self._load_code_templates()

    def _load_code_templates(self) -> Dict[str, str]:
        """Load code templates for different exercises"""
        return {
            "basic_agent": '''# Basic Agent Template
from dmlogn8n import Agent, Workflow

class MyAgent(Agent):
    def __init__(self):
        super().__init__()
        self.name = "My First Agent"

    async def process(self, input_data):
        # Your code here
        return {"result": "Hello from my agent!"}

# Create and test your agent
agent = MyAgent()
result = await agent.process({"message": "test"})
print(result)
''',
            "workflow_builder": '''# Workflow Builder Template
from dmlogn8n import Workflow, Node, Connection

# Create a simple workflow
workflow = Workflow("My Workflow")

# Add nodes
node1 = workflow.add_node("input", "Input Node")
node2 = workflow.add_node("process", "Process Node")
node3 = workflow.add_node("output", "Output Node")

# Create connections
workflow.add_connection(node1, node2)
workflow.add_connection(node2, node3)

# Execute workflow
result = await workflow.execute({"data": "test input"})
print(result)
''',
            "api_integration": '''# API Integration Template
from dmlogn8n import HTTPNode, Authentication

# Configure API authentication
auth = Authentication(
    type="bearer",
    token="your_api_token_here"
)

# Create HTTP node
api_node = HTTPNode(
    name="api_call",
    url="https://api.example.com/data",
    method="GET",
    auth=auth
)

# Test the API call
result = await api_node.execute()
print(result)
'''
        }

    async def create_session(self, user_id: str, exercise_id: str) -> Dict[str, Any]:
        """Create an interactive coding session"""
        session_id = str(uuid.uuid4())
        template = self.code_templates.get(exercise_id, "# Start coding here\n")

        session = {
            "session_id": session_id,
            "user_id": user_id,
            "exercise_id": exercise_id,
            "code": template,
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow(),
            "executions": [],
            "test_results": []
        }

        self.active_sessions[session_id] = session
        return session

    async def execute_code(self, session_id: str, code: str) -> Dict[str, Any]:
        """Execute code in a safe environment"""
        if session_id not in self.active_sessions:
            raise ValueError("Session not found")

        session = self.active_sessions[session_id]

        # Log execution
        execution = {
            "timestamp": datetime.utcnow(),
            "code": code,
            "status": "pending",
            "output": "",
            "error": ""
        }

        try:
            # In production, this would execute in a sandboxed Docker container
            # For now, we'll simulate execution

            # Basic safety checks
            dangerous_patterns = [
                r'import\s+os\s*',
                r'subprocess\.',
                r'eval\s*\(',
                r'exec\s*\(',
                r'__import__',
                r'open\s*\(',
                r'file\s*\('
            ]

            for pattern in dangerous_patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    execution["status"] = "error"
                    execution["error"] = "Code contains potentially dangerous operations"
                    break
            else:
                # Simulate execution
                execution["status"] = "success"
                execution["output"] = "Code executed successfully!\n"
                execution["output"] += "In production, this would show actual output."

        except Exception as e:
            execution["status"] = "error"
            execution["error"] = str(e)

        session["executions"].append(execution)
        session["last_updated"] = datetime.utcnow()

        return execution

    async def run_tests(self, session_id: str, code: str) -> Dict[str, Any]:
        """Run automated tests against submitted code"""
        if session_id not in self.active_sessions:
            raise ValueError("Session not found")

        session = self.active_sessions[session_id]
        exercise_id = session["exercise_id"]

        # Define tests for different exercises
        test_suites = {
            "basic_agent": [
                {
                    "name": "Agent class exists",
                    "test": "class MyAgent",
                    "expected": True
                },
                {
                    "name": "Agent inherits from Agent",
                    "test": "Agent)" in code,
                    "expected": True
                },
                {
                    "name": "Process method defined",
                    "test": "def process",
                    "expected": True
                }
            ],
            "workflow_builder": [
                {
                    "name": "Workflow created",
                    "test": "Workflow(" in code,
                    "expected": True
                },
                {
                    "name": "Nodes added",
                    "test": "add_node" in code,
                    "expected": True
                },
                {
                    "name": "Connections made",
                    "test": "add_connection" in code,
                    "expected": True
                }
            ]
        }

        test_results = []
        tests = test_suites.get(exercise_id, [])

        for test in tests:
            result = {
                "name": test["name"],
                "passed": eval(test["test"]) if test["test"] else False,
                "expected": test["expected"],
                "actual": eval(test["test"]) if test["test"] else False
            }
            test_results.append(result)

        session["test_results"] = test_results
        return {"tests": test_results, "passed": sum(1 for t in test_results if t["passed"])}

class LearningAnalytics:
    """Analytics for tracking learning effectiveness and engagement"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.redis_client = redis.Redis(host='localhost', port=6379, db=1)

    async def track_engagement(self, user_id: str, action: str, metadata: Dict[str, Any] = None):
        """Track user engagement events"""
        event = {
            "user_id": user_id,
            "action": action,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }

        # Store in Redis for real-time analytics
        event_key = f"engagement:{user_id}:{datetime.utcnow().strftime('%Y%m%d')}"
        self.redis_client.lpush(event_key, json.dumps(event))
        self.redis_client.expire(event_key, 86400 * 30)  # Keep for 30 days

        # Store aggregate metrics
        daily_key = f"daily_stats:{datetime.utcnow().strftime('%Y%m%d')}"
        self.redis_client.hincrby(daily_key, f"action:{action}", 1)
        self.redis_client.expire(daily_key, 86400 * 365)

    async def get_learning_progress(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive learning progress for a user"""
        enrollments = self.db.query(Enrollment).filter(
            Enrollment.user_id == user_id
        ).all()

        total_courses = len(enrollments)
        completed_courses = len([e for e in enrollments if e.completed_at])
        total_time = sum(e.time_spent_minutes for e in enrollments)
        avg_progress = sum(e.progress_percentage for e in enrollments) / total_courses if total_courses > 0 else 0

        # Get achievements
        achievements = self.db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id
        ).all()

        # Calculate skill level progression
        skill_progression = await self._calculate_skill_progression(user_id)

        return {
            "user_id": user_id,
            "courses_enrolled": total_courses,
            "courses_completed": completed_courses,
            "completion_rate": completed_courses / total_courses if total_courses > 0 else 0,
            "total_learning_time_minutes": total_time,
            "average_progress": avg_progress,
            "achievements_count": len(achievements),
            "skill_progression": skill_progression,
            "streak_days": await self._calculate_learning_streak(user_id)
        }

    async def _calculate_skill_progression(self, user_id: str) -> Dict[str, Any]:
        """Calculate progression across different skill areas"""
        enrollments = self.db.query(Enrollment).join(CourseDB).filter(
            Enrollment.user_id == user_id
        ).all()

        skill_areas = {}
        for enrollment in enrollments:
            course = enrollment.course
            skill_level = course.skill_level

            if skill_level not in skill_areas:
                skill_areas[skill_level] = {
                    "courses_attempted": 0,
                    "courses_completed": 0,
                    "total_time": 0,
                    "average_progress": 0
                }

            skill_areas[skill_level]["courses_attempted"] += 1
            skill_areas[skill_level]["total_time"] += enrollment.time_spent_minutes

            if enrollment.completed_at:
                skill_areas[skill_level]["courses_completed"] += 1

        # Calculate averages
        for skill_level, data in skill_areas.items():
            if data["courses_attempted"] > 0:
                data["completion_rate"] = data["courses_completed"] / data["courses_attempted"]
            else:
                data["completion_rate"] = 0

        return skill_areas

    async def _calculate_learning_streak(self, user_id: str) -> int:
        """Calculate current learning streak in days"""
        today = datetime.utcnow().date()
        streak = 0

        for i in range(365):  # Check up to a year
            check_date = today - timedelta(days=i)
            daily_key = f"engagement:{user_id}:{check_date.strftime('%Y%m%d')}"

            if self.redis_client.exists(daily_key):
                events = self.redis_client.llen(daily_key)
                if events > 0:
                    streak += 1
                else:
                    break
            else:
                break

        return streak

    async def get_course_analytics(self, course_id: str) -> Dict[str, Any]:
        """Get analytics for a specific course"""
        enrollments = self.db.query(Enrollment).filter(
            Enrollment.course_id == course_id
        ).all()

        total_enrollments = len(enrollments)
        completed_enrollments = len([e for e in enrollments if e.completed_at])
        total_time = sum(e.time_spent_minutes for e in enrollments)
        avg_progress = sum(e.progress_percentage for e in enrollments) / total_enrollments if total_enrollments > 0 else 0

        # Calculate dropout points
        dropout_modules = {}
        for enrollment in enrollments:
            if not enrollment.completed_at and enrollment.current_module:
                module = enrollment.current_module
                dropout_modules[module] = dropout_modules.get(module, 0) + 1

        return {
            "course_id": course_id,
            "total_enrollments": total_enrollments,
            "completion_rate": completed_enrollments / total_enrollments if total_enrollments > 0 else 0,
            "average_time_to_completion": total_time / completed_enrollments if completed_enrollments > 0 else 0,
            "average_progress": avg_progress,
            "dropout_points": dropout_modules,
            "engagement_metrics": await self._get_course_engagement(course_id)
        }

    async def _get_course_engagement(self, course_id: str) -> Dict[str, Any]:
        """Get engagement metrics for a course"""
        # This would typically query engagement events from Redis
        # For now, return placeholder data
        return {
            "video_watch_time": 0,
            "exercise_attempts": 0,
            "forum_posts": 0,
            "resource_downloads": 0
        }

class PersonalizedLearningEngine:
    """AI-powered personalized learning recommendations"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.analytics = LearningAnalytics(db_session)

    async def recommend_courses(self, user_id: str, count: int = 5) -> List[Dict[str, Any]]:
        """Get personalized course recommendations"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []

        # Get user's current skill level and interests
        current_level = user.skill_level
        interests = json.loads(user.interests or "[]")

        # Get user's progress and completed courses
        enrollments = self.db.query(Enrollment).filter(
            Enrollment.user_id == user_id
        ).all()
        completed_course_ids = [e.course_id for e in enrollments if e.completed_at]

        # Get available courses
        available_courses = self.db.query(CourseDB).filter(
            CourseDB.is_published == True,
            CourseDB.id.notin_(completed_course_ids)
        ).all()

        # Score courses based on relevance
        scored_courses = []
        for course in available_courses:
            score = 0

            # Skill level match
            if self._skill_level_match(current_level, course.skill_level):
                score += 30

            # Interest match
            course_tags = json.loads(course.tags or "[]")
            interest_match = len(set(interests) & set(course_tags))
            score += interest_match * 15

            # Rating boost
            score += course.rating * 10

            # Popularity boost
            score += min(course.enrollment_count / 100, 20)

            scored_courses.append({
                "course": course,
                "score": score,
                "reasons": self._generate_recommendation_reasons(score, current_level, interests, course)
            })

        # Sort by score and return top recommendations
        scored_courses.sort(key=lambda x: x["score"], reverse=True)

        recommendations = []
        for item in scored_courses[:count]:
            course = item["course"]
            recommendations.append({
                "id": course.id,
                "title": course.title,
                "description": course.description,
                "skill_level": course.skill_level,
                "duration_hours": course.duration_hours,
                "rating": course.rating,
                "enrollment_count": course.enrollment_count,
                "score": item["score"],
                "reasons": item["reasons"]
            })

        return recommendations

    def _skill_level_match(self, user_level: str, course_level: str) -> bool:
        """Check if course level is appropriate for user"""
        level_hierarchy = {
            SkillLevel.BEGINNER.value: 0,
            SkillLevel.INTERMEDIATE.value: 1,
            SkillLevel.ADVANCED.value: 2,
            SkillLevel.EXPERT.value: 3
        }

        user_rank = level_hierarchy.get(user_level, 0)
        course_rank = level_hierarchy.get(course_level, 0)

        # Recommend courses at or slightly above current level
        return course_rank <= user_rank + 1

    def _generate_recommendation_reasons(self, score: int, user_level: str, interests: List[str], course) -> List[str]:
        """Generate explanations for why a course is recommended"""
        reasons = []

        if self._skill_level_match(user_level, course.skill_level):
            reasons.append("Matches your current skill level")

        course_tags = json.loads(course.tags or "[]")
        if interests:
            matching_tags = set(interests) & set(course_tags)
            if matching_tags:
                reasons.append(f"Matches your interests: {', '.join(matching_tags)}")

        if course.rating >= 4.5:
            reasons.append("Highly rated by other learners")

        if course.enrollment_count > 100:
            reasons.append("Popular among learners")

        return reasons[:3]  # Return top 3 reasons

    async def create_learning_path(self, user_id: str, goal: str) -> LearningPath:
        """Create a personalized learning path based on user goals"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        # Analyze goal and recommend appropriate courses
        goal_keywords = goal.lower().split()

        # Find relevant courses
        all_courses = self.db.query(CourseDB).filter(
            CourseDB.is_published == True
        ).all()

        relevant_courses = []
        for course in all_courses:
            course_text = f"{course.title} {course.description} {course.tags}".lower()
            relevance_score = sum(1 for keyword in goal_keywords if keyword in course_text)

            if relevance_score > 0:
                relevant_courses.append((course, relevance_score))

        # Sort by relevance
        relevant_courses.sort(key=lambda x: x[1], reverse=True)

        # Create learning path
        path_id = str(uuid.uuid4())
        selected_courses = [course for course, _ in relevant_courses[:10]]  # Top 10 courses

        learning_path = LearningPath(
            id=path_id,
            title=f"Learning Path: {goal}",
            description=f"Personalized learning path to achieve: {goal}",
            skill_level=user.skill_level,
            estimated_hours=sum(c.duration_hours for c in selected_courses),
            modules=[course.id for course in selected_courses],
            prerequisites=self._identify_prerequisites(selected_courses),
            tags=self._extract_path_tags(selected_courses),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        return learning_path

    def _identify_prerequisites(self, courses: List[CourseDB]) -> List[str]:
        """Identify prerequisite courses for a learning path"""
        # This would typically analyze course dependencies
        # For now, return basic skill-based prerequisites
        beginner_courses = [c.id for c in courses if c.skill_level == SkillLevel.BEGINNER.value]
        return beginner_courses[:2]  # Return first 2 beginner courses as prerequisites

    def _extract_path_tags(self, courses: List[CourseDB]) -> List[str]:
        """Extract common tags from courses in the path"""
        all_tags = []
        for course in courses:
            course_tags = json.loads(course.tags or "[]")
            all_tags.extend(course_tags)

        # Return most common tags
        from collections import Counter
        tag_counts = Counter(all_tags)
        return [tag for tag, _ in tag_counts.most_common(10)]

# API Models
class CourseEnrollment(BaseModel):
    course_id: str
    user_id: str

class ProgressUpdate(BaseModel):
    course_id: str
    module_id: Optional[str] = None
    progress_percentage: float
    time_spent_minutes: int = 0
    notes: Optional[str] = None

class UserPreferences(BaseModel):
    skill_level: Optional[str] = None
    learning_style: Optional[str] = None
    interests: Optional[List[str]] = None
    timezone: Optional[str] = None
    language: Optional[str] = None

class CodeSubmission(BaseModel):
    session_id: str
    code: str

class LearningPlatformApp:
    """Main Learning Platform Application"""

    def __init__(self):
        self.app = FastAPI(title="DMLogn8n Learning Platform", version="1.0.0")
        self.setup_middleware()
        self.setup_routes()

        # Initialize database
        self.engine = create_engine('sqlite:///learning_platform.db')
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Initialize components
        self.code_env = InteractiveCodeEnvironment()

        # Templates and static files
        self.templates = Jinja2Templates(directory="templates")
        self.app.mount("/static", StaticFiles(directory="static"), name="static")

    def setup_middleware(self):
        """Setup FastAPI middleware"""
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
            return {"message": "DMLogn8n Learning Platform API"}

        @self.app.get("/courses")
        async def get_courses(
            skill_level: Optional[str] = None,
            content_type: Optional[str] = None,
            tags: Optional[str] = None,
            limit: int = 50,
            offset: int = 0
        ):
            """Get available courses with filtering"""
            db = self.SessionLocal()
            try:
                query = db.query(CourseDB).filter(CourseDB.is_published == True)

                if skill_level:
                    query = query.filter(CourseDB.skill_level == skill_level)
                if content_type:
                    query = query.filter(CourseDB.content_type == content_type)
                if tags:
                    tag_list = tags.split(',')
                    # Would need to implement proper JSON filtering

                courses = query.offset(offset).limit(limit).all()

                return {
                    "courses": [
                        {
                            "id": course.id,
                            "title": course.title,
                            "description": course.description,
                            "skill_level": course.skill_level,
                            "duration_hours": course.duration_hours,
                            "content_type": course.content_type,
                            "rating": course.rating,
                            "enrollment_count": course.enrollment_count,
                            "tags": json.loads(course.tags or "[]")
                        }
                        for course in courses
                    ],
                    "total": len(courses)
                }
            finally:
                db.close()

        @self.app.post("/enroll")
        async def enroll_course(enrollment: CourseEnrollment):
            """Enroll user in a course"""
            db = self.SessionLocal()
            try:
                # Check if already enrolled
                existing = db.query(Enrollment).filter(
                    Enrollment.user_id == enrollment.user_id,
                    Enrollment.course_id == enrollment.course_id
                ).first()

                if existing:
                    raise HTTPException(status_code=400, detail="Already enrolled")

                # Create enrollment
                new_enrollment = Enrollment(
                    id=str(uuid.uuid4()),
                    user_id=enrollment.user_id,
                    course_id=enrollment.course_id
                )

                db.add(new_enrollment)

                # Update course enrollment count
                course = db.query(CourseDB).filter(CourseDB.id == enrollment.course_id).first()
                if course:
                    course.enrollment_count += 1

                db.commit()

                return {"message": "Successfully enrolled", "enrollment_id": new_enrollment.id}
            finally:
                db.close()

        @self.app.get("/enrollments/{user_id}")
        async def get_user_enrollments(user_id: str):
            """Get user's course enrollments"""
            db = self.SessionLocal()
            try:
                enrollments = db.query(Enrollment).filter(
                    Enrollment.user_id == user_id
                ).all()

                result = []
                for enrollment in enrollments:
                    course = db.query(CourseDB).filter(CourseDB.id == enrollment.course_id).first()
                    if course:
                        result.append({
                            "enrollment_id": enrollment.id,
                            "course": {
                                "id": course.id,
                                "title": course.title,
                                "description": course.description,
                                "skill_level": course.skill_level,
                                "duration_hours": course.duration_hours
                            },
                            "progress": enrollment.progress_percentage,
                            "time_spent": enrollment.time_spent_minutes,
                            "current_module": enrollment.current_module,
                            "enrolled_at": enrollment.enrolled_at,
                            "completed_at": enrollment.completed_at,
                            "certificate_earned": enrollment.certificate_earned
                        })

                return {"enrollments": result}
            finally:
                db.close()

        @self.app.put("/progress")
        async def update_progress(progress: ProgressUpdate):
            """Update learning progress"""
            db = self.SessionLocal()
            try:
                enrollment = db.query(Enrollment).filter(
                    Enrollment.user_id == progress.user_id,
                    Enrollment.course_id == progress.course_id
                ).first()

                if not enrollment:
                    raise HTTPException(status_code=404, detail="Enrollment not found")

                # Update enrollment
                enrollment.progress_percentage = progress.progress_percentage
                enrollment.time_spent_minutes += progress.time_spent_minutes

                if progress.module_id:
                    enrollment.current_module = progress.module_id

                    # Update completed modules
                    completed = json.loads(enrollment.completed_modules or "[]")
                    if progress.module_id not in completed:
                        completed.append(progress.module_id)
                    enrollment.completed_modules = json.dumps(completed)

                # Check if course is completed
                if progress.progress_percentage >= 100:
                    enrollment.completed_at = datetime.utcnow()

                db.commit()

                # Track engagement
                analytics = LearningAnalytics(db)
                await analytics.track_engagement(
                    progress.user_id,
                    "progress_update",
                    {
                        "course_id": progress.course_id,
                        "module_id": progress.module_id,
                        "progress": progress.progress_percentage
                    }
                )

                return {"message": "Progress updated successfully"}
            finally:
                db.close()

        @self.app.post("/code/session")
        async def create_code_session(user_id: str, exercise_id: str):
            """Create interactive coding session"""
            session = await self.code_env.create_session(user_id, exercise_id)
            return session

        @self.app.post("/code/execute")
        async def execute_code(submission: CodeSubmission):
            """Execute code in interactive environment"""
            result = await self.code_env.execute_code(submission.session_id, submission.code)
            return result

        @self.app.post("/code/test")
        async def test_code(submission: CodeSubmission):
            """Run tests against submitted code"""
            results = await self.code_env.run_tests(submission.session_id, submission.code)
            return results

        @self.app.get("/recommendations/{user_id}")
        async def get_recommendations(user_id: str, count: int = 5):
            """Get personalized course recommendations"""
            db = self.SessionLocal()
            try:
                engine = PersonalizedLearningEngine(db)
                recommendations = await engine.recommend_courses(user_id, count)
                return {"recommendations": recommendations}
            finally:
                db.close()

        @self.app.post("/learning-path")
        async def create_learning_path(user_id: str, goal: str):
            """Create personalized learning path"""
            db = self.SessionLocal()
            try:
                engine = PersonalizedLearningEngine(db)
                learning_path = await engine.create_learning_path(user_id, goal)
                return asdict(learning_path)
            finally:
                db.close()

        @self.app.get("/analytics/user/{user_id}")
        async def get_user_analytics(user_id: str):
            """Get user learning analytics"""
            db = self.SessionLocal()
            try:
                analytics = LearningAnalytics(db)
                progress = await analytics.get_learning_progress(user_id)
                return progress
            finally:
                db.close()

        @self.app.get("/analytics/course/{course_id}")
        async def get_course_analytics(course_id: str):
            """Get course analytics"""
            db = self.SessionLocal()
            try:
                analytics = LearningAnalytics(db)
                analytics_data = await analytics.get_course_analytics(course_id)
                return analytics_data
            finally:
                db.close()

        @self.app.websocket("/ws/code/{session_id}")
        async def websocket_code_endpoint(websocket: WebSocket, session_id: str):
            """WebSocket for real-time code collaboration"""
            await websocket.accept()

            try:
                while True:
                    # Receive message from client
                    data = await websocket.receive_json()

                    if data["type"] == "code_change":
                        # Broadcast code changes to other participants
                        await websocket.send_json({
                            "type": "code_update",
                            "code": data["code"],
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    elif data["type"] == "execution_request":
                        # Execute code and send results
                        result = await self.code_env.execute_code(session_id, data["code"])
                        await websocket.send_json({
                            "type": "execution_result",
                            "result": result
                        })

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for session {session_id}")

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the learning platform server"""
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)

# Main execution
if __name__ == "__main__":
    platform = LearningPlatformApp()
    platform.run()