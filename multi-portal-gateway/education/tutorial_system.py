#!/usr/bin/env python3
"""
DMLogn8n Tutorial System - Interactive Tutorials and Guided Learning
Comprehensive interactive tutorial system with hands-on exercises and real-time guidance
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
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tutorial_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

Base = declarative_base()

class TutorialType(Enum):
    INTERACTIVE = "interactive"
    VIDEO = "video"
    READING = "reading"
    HANDS_ON = "hands_on"
    WORKSHOP = "workshop"
    QUIZ = "quiz"
    PROJECT = "project"

class DifficultyLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class TutorialStatus(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    FEATURED = "featured"

@dataclass
class TutorialStep:
    id: str
    title: str
    content: str
    step_type: str  # text, code, interactive, quiz
    order: int
    instructions: str
    hints: List[str]
    expected_output: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None
    resources: List[Dict[str, str]] = None
    time_estimate_minutes: int = 5

@dataclass
class Tutorial:
    id: str
    title: str
    description: str
    tutorial_type: TutorialType
    difficulty_level: DifficultyLevel
    estimated_duration_minutes: int
    steps: List[TutorialStep]
    prerequisites: List[str]
    learning_objectives: List[str]
    tags: List[str]
    author: str
    status: TutorialStatus
    created_at: datetime
    updated_at: datetime

@dataclass
class UserProgress:
    user_id: str
    tutorial_id: str
    current_step: int
    completed_steps: List[str]
    progress_percentage: float
    time_spent_minutes: int
    started_at: datetime
    last_accessed: datetime
    completed_at: Optional[datetime] = None
    notes: Dict[str, str] = None
    bookmarks: List[str] = None
    attempts: Dict[str, int] = None

class TutorialDB(Base):
    __tablename__ = "tutorials"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    tutorial_type = Column(String, nullable=False)
    difficulty_level = Column(String, nullable=False)
    estimated_duration_minutes = Column(Integer)
    steps = Column(Text)  # JSON string
    prerequisites = Column(Text)  # JSON string
    learning_objectives = Column(Text)  # JSON string
    tags = Column(Text)  # JSON string
    author_id = Column(String, ForeignKey("users.id"))
    status = Column(String, default=TutorialStatus.DRAFT.value)
    view_count = Column(Integer, default=0)
    completion_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class UserTutorialProgress(Base):
    __tablename__ = "user_tutorial_progress"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    tutorial_id = Column(String, ForeignKey("tutorials.id"), nullable=False)
    current_step = Column(Integer, default=0)
    completed_steps = Column(Text)  # JSON string
    progress_percentage = Column(Float, default=0.0)
    time_spent_minutes = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    notes = Column(Text)  # JSON string
    bookmarks = Column(Text)  # JSON string
    attempts = Column(Text)  # JSON string

class CodeExecutionEnvironment:
    """Secure code execution environment for hands-on tutorials"""

    def __init__(self):
        self.active_sessions = {}
        self.execution_timeout = 30  # seconds
        self.max_memory_mb = 256
        self.allowed_modules = [
            'json', 'datetime', 'math', 'random', 'string', 're',
            'collections', 'itertools', 'functools', 'operator'
        ]

    async def create_session(self, tutorial_id: str, step_id: str, user_id: str) -> Dict[str, Any]:
        """Create a new code execution session"""
        session_id = str(uuid.uuid4())

        session = {
            "session_id": session_id,
            "tutorial_id": tutorial_id,
            "step_id": step_id,
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "code": "",
            "executions": [],
            "files": {},
            "environment_variables": {}
        }

        self.active_sessions[session_id] = session
        return session

    async def execute_code(self, session_id: str, code: str) -> Dict[str, Any]:
        """Execute code in a secure sandboxed environment"""
        if session_id not in self.active_sessions:
            raise ValueError("Session not found")

        session = self.active_sessions[session_id]
        session["last_activity"] = datetime.utcnow()
        session["code"] = code

        execution_result = {
            "session_id": session_id,
            "timestamp": datetime.utcnow(),
            "status": "pending",
            "output": "",
            "error": "",
            "execution_time_ms": 0,
            "memory_usage_mb": 0
        }

        try:
            # Security checks
            security_result = await self._security_check(code)
            if not security_result["safe"]:
                execution_result["status"] = "error"
                execution_result["error"] = f"Security violation: {security_result['reason']}"
                session["executions"].append(execution_result)
                return execution_result

            # In production, this would execute in a Docker container or similar sandbox
            # For demonstration, we'll simulate execution with basic Python eval

            start_time = datetime.utcnow()

            # Create a safe execution context
            safe_globals = {
                '__builtins__': {},
                'print': self._safe_print,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'list': list,
                'dict': dict,
                'set': set,
                'tuple': tuple,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'sum': sum,
                'max': max,
                'min': min,
                'abs': abs,
                'round': round,
                # Add allowed modules
                **{module: __import__(module) for module in self.allowed_modules if module in globals()}
            }

            # Capture output
            output_buffer = []

            def _safe_print(*args, **kwargs):
                output_buffer.append(' '.join(str(arg) for arg in args))

            safe_globals['print'] = _safe_print

            # Execute the code
            try:
                exec(code, safe_globals)
                execution_result["status"] = "success"
                execution_result["output"] = '\n'.join(output_buffer)
            except Exception as e:
                execution_result["status"] = "error"
                execution_result["error"] = str(e)

            execution_result["execution_time_ms"] = (datetime.utcnow() - start_time).total_seconds() * 1000
            execution_result["memory_usage_mb"] = 50  # Simulated

        except Exception as e:
            execution_result["status"] = "error"
            execution_result["error"] = f"Execution failed: {str(e)}"

        session["executions"].append(execution_result)
        return execution_result

    async def _security_check(self, code: str) -> Dict[str, Any]:
        """Perform security checks on code"""
        dangerous_patterns = [
            (r'import\s+os', "os module access"),
            (r'import\s+sys', "sys module access"),
            (r'import\s+subprocess', "subprocess module access"),
            (r'import\s+socket', "network access"),
            (r'import\s+urllib', "network access"),
            (r'import\s+requests', "network access"),
            (r'import\s+shutil', "file system access"),
            (r'import\s+tempfile', "file system access"),
            (r'open\s*\(', "file access"),
            (r'file\s*\(', "file access"),
            (r'exec\s*\(', "code execution"),
            (r'eval\s*\(', "code execution"),
            (r'__import__\s*\(', "module import"),
            (r'globals\s*\(\)', "globals access"),
            (r'locals\s*\(\)', "locals access"),
            (r'vars\s*\(\)', "variable access"),
            (r'dir\s*\(\)', "introspection"),
            (r'hasattr\s*\(', "introspection"),
            (r'getattr\s*\(', "attribute access"),
            (r'setattr\s*\(', "attribute modification"),
            (r'delattr\s*\(', "attribute deletion"),
            (r'__.*__', "magic method access"),
            (r'input\s*\(', "user input"),
            (r'raw_input\s*\(', "user input"),
            (r'exit\s*\(', "system exit"),
            (r'quit\s*\(\)', "system exit"),
        ]

        for pattern, reason in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return {"safe": False, "reason": reason}

        # Check for suspicious operations
        if re.search(r'while\s+True\s*:', code):
            return {"safe": False, "reason": "potential infinite loop"}

        # Check code length
        if len(code) > 5000:  # 5KB limit
            return {"safe": False, "reason": "code too long"}

        return {"safe": True, "reason": None}

    def _safe_print(self, *args, **kwargs):
        """Safe print function that captures output"""
        return None

    async def cleanup_sessions(self, max_age_minutes: int = 60):
        """Clean up old inactive sessions"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)

        expired_sessions = [
            session_id for session_id, session in self.active_sessions.items()
            if session["last_activity"] < cutoff_time
        ]

        for session_id in expired_sessions:
            del self.active_sessions[session_id]

        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

class InteractiveValidator:
    """Interactive validation system for tutorial steps"""

    def __init__(self):
        self.validation_rules = self._load_validation_rules()

    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules for different types of exercises"""
        return {
            "code_output": {
                "exact_match": self._validate_exact_output,
                "contains": self._validate_contains_output,
                "regex": self._validate_regex_output,
                "json_structure": self._validate_json_structure
            },
            "code_structure": {
                "function_exists": self._validate_function_exists,
                "class_exists": self._validate_class_exists,
                "variable_defined": self._validate_variable_defined,
                "import_present": self._validate_import_present
            },
            "interactive": {
                "button_clicked": self._validate_button_clicked,
                "form_completed": self._validate_form_completed,
                "drag_drop_completed": self._validate_drag_drop_completed
            }
        }

    async def validate_step(self, step: TutorialStep, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user input against step requirements"""
        validation_result = {
            "step_id": step.id,
            "is_valid": False,
            "feedback": "",
            "hints": [],
            "score": 0,
            "max_score": 100,
            "validation_details": {}
        }

        try:
            if step.step_type == "code":
                result = await self._validate_code_step(step, user_input)
            elif step.step_type == "quiz":
                result = await self._validate_quiz_step(step, user_input)
            elif step.step_type == "interactive":
                result = await self._validate_interactive_step(step, user_input)
            else:
                result = {"is_valid": True, "feedback": "Step completed!"}

            validation_result.update(result)

        except Exception as e:
            logger.error(f"Validation error for step {step.id}: {e}")
            validation_result["feedback"] = "Validation failed due to system error"
            validation_result["hints"] = ["Please try again or contact support"]

        return validation_result

    async def _validate_code_step(self, step: TutorialStep, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate code-based step"""
        code = user_input.get("code", "")
        execution_output = user_input.get("output", "")

        result = {"is_valid": False, "feedback": "", "hints": [], "score": 0}

        if not step.validation_rules:
            return {"is_valid": True, "feedback": "Code submitted successfully!", "score": 100}

        # Check expected output
        if step.expected_output:
            if execution_output.strip() == step.expected_output.strip():
                result["is_valid"] = True
                result["feedback"] = "Perfect! Your code produces the expected output."
                result["score"] = 100
            else:
                result["feedback"] = "Output doesn't match expected result."
                result["hints"] = [f"Expected: {step.expected_output}"]
                result["score"] = 50

        # Check validation rules
        if "validation_rules" in step.validation_rules:
            rules = step.validation_rules["validation_rules"]
            for rule in rules:
                if rule["type"] == "function_exists":
                    if self._validate_function_exists(code, rule["function_name"]):
                        result["score"] += 25
                    else:
                        result["hints"].append(f"Make sure you define a function named '{rule['function_name']}'")

                elif rule["type"] == "variable_defined":
                    if self._validate_variable_defined(code, rule["variable_name"]):
                        result["score"] += 25
                    else:
                        result["hints"].append(f"Make sure you define a variable named '{rule['variable_name']}'")

        if result["score"] >= 100:
            result["is_valid"] = True

        return result

    async def _validate_quiz_step(self, step: TutorialStep, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate quiz-based step"""
        user_answers = user_input.get("answers", {})
        correct_answers = step.validation_rules.get("correct_answers", {})

        result = {"is_valid": False, "feedback": "", "score": 0, "max_score": len(correct_answers) * 20}

        correct_count = 0
        for question_id, correct_answer in correct_answers.items():
            if user_answers.get(question_id) == correct_answer:
                correct_count += 1

        result["score"] = (correct_count / len(correct_answers)) * 100

        if result["score"] >= 80:
            result["is_valid"] = True
            result["feedback"] = f"Excellent! You got {correct_count} out of {len(correct_answers)} questions correct."
        elif result["score"] >= 60:
            result["feedback"] = f"Good job! You got {correct_count} out of {len(correct_answers)} questions correct. Review the material and try again."
        else:
            result["feedback"] = f"You got {correct_count} out of {len(correct_answers)} questions correct. Please review the tutorial content."

        return result

    async def _validate_interactive_step(self, step: TutorialStep, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate interactive step"""
        interaction_data = user_input.get("interaction_data", {})
        required_interactions = step.validation_rules.get("required_interactions", [])

        result = {"is_valid": False, "feedback": "", "score": 0}

        completed_interactions = 0
        for interaction in required_interactions:
            if interaction["type"] == "button_click":
                if interaction_data.get("button_clicked") == interaction["button_id"]:
                    completed_interactions += 1
            elif interaction["type"] == "drag_drop":
                if interaction_data.get("drag_drop_completed"):
                    completed_interactions += 1

        result["score"] = (completed_interactions / len(required_interactions)) * 100

        if result["score"] >= 100:
            result["is_valid"] = True
            result["feedback"] = "Great job! You completed all the required interactions."

        return result

    def _validate_exact_output(self, code: str, expected: str) -> bool:
        """Validate exact output match"""
        return False  # Would execute code and compare output

    def _validate_contains_output(self, code: str, expected: str) -> bool:
        """Validate output contains expected text"""
        return False  # Would execute code and check output

    def _validate_regex_output(self, code: str, pattern: str) -> bool:
        """Validate output matches regex pattern"""
        return False  # Would execute code and test against regex

    def _validate_json_structure(self, code: str, expected_structure: Dict) -> bool:
        """Validate JSON output structure"""
        return False  # Would execute code and validate JSON structure

    def _validate_function_exists(self, code: str, function_name: str) -> bool:
        """Check if function exists in code"""
        pattern = rf'def\s+{re.escape(function_name)}\s*\('
        return bool(re.search(pattern, code))

    def _validate_class_exists(self, code: str, class_name: str) -> bool:
        """Check if class exists in code"""
        pattern = rf'class\s+{re.escape(class_name)}\s*:'
        return bool(re.search(pattern, code))

    def _validate_variable_defined(self, code: str, variable_name: str) -> bool:
        """Check if variable is defined in code"""
        pattern = rf'{re.escape(variable_name)}\s*='
        return bool(re.search(pattern, code))

    def _validate_import_present(self, code: str, module_name: str) -> bool:
        """Check if import statement is present"""
        pattern = rf'import\s+{re.escape(module_name)}'
        return bool(re.search(pattern, code))

    def _validate_button_clicked(self, user_input: Dict[str, Any], button_id: str) -> bool:
        """Validate button click interaction"""
        return user_input.get("button_clicked") == button_id

    def _validate_form_completed(self, user_input: Dict[str, Any], required_fields: List[str]) -> bool:
        """Validate form completion"""
        form_data = user_input.get("form_data", {})
        return all(field in form_data and form_data[field] for field in required_fields)

    def _validate_drag_drop_completed(self, user_input: Dict[str, Any], required_items: List[str]) -> bool:
        """Validate drag and drop completion"""
        dropped_items = user_input.get("dropped_items", [])
        return all(item in dropped_items for item in required_items)

class TutorialRecommender:
    """AI-powered tutorial recommendation system"""

    def __init__(self, db_session: Session):
        self.db = db_session

    async def recommend_tutorials(self, user_id: str, count: int = 5) -> List[Dict[str, Any]]:
        """Get personalized tutorial recommendations"""
        # Get user's completed tutorials
        completed_tutorials = self.db.query(UserTutorialProgress).filter(
            UserTutorialProgress.user_id == user_id,
            UserTutorialProgress.completed_at.isnot(None)
        ).all()

        completed_ids = [t.tutorial_id for t in completed_tutorials]

        # Get user's skill level and interests
        user = self.db.query(User).filter(User.id == user_id).first()
        skill_level = user.skill_level if user else "beginner"

        # Get available tutorials
        available_tutorials = self.db.query(TutorialDB).filter(
            TutorialDB.status == TutorialStatus.PUBLISHED.value,
            TutorialDB.id.notin_(completed_ids)
        ).all()

        # Score tutorials based on relevance
        scored_tutorials = []
        for tutorial in available_tutorials:
            score = 0

            # Skill level match
            if self._skill_level_match(skill_level, tutorial.difficulty_level):
                score += 30

            # Prerequisite satisfaction
            if self._prerequisites_satisfied(completed_ids, tutorial.prerequisites):
                score += 40

            # Popularity boost
            score += min(tutorial.view_count / 100, 20)

            # Rating boost
            score += tutorial.rating * 5

            # Recency boost
            days_since_created = (datetime.utcnow() - tutorial.created_at).days
            if days_since_created < 30:
                score += 10

            scored_tutorials.append({
                "tutorial": tutorial,
                "score": score,
                "reasons": self._generate_recommendation_reasons(tutorial, skill_level, completed_ids)
            })

        # Sort by score and return top recommendations
        scored_tutorials.sort(key=lambda x: x["score"], reverse=True)

        recommendations = []
        for item in scored_tutorials[:count]:
            tutorial = item["tutorial"]
            recommendations.append({
                "id": tutorial.id,
                "title": tutorial.title,
                "description": tutorial.description,
                "tutorial_type": tutorial.tutorial_type,
                "difficulty_level": tutorial.difficulty_level,
                "estimated_duration_minutes": tutorial.estimated_duration_minutes,
                "rating": tutorial.rating,
                "view_count": tutorial.view_count,
                "tags": json.loads(tutorial.tags or "[]"),
                "score": item["score"],
                "reasons": item["reasons"]
            })

        return recommendations

    def _skill_level_match(self, user_level: str, tutorial_level: str) -> bool:
        """Check if tutorial difficulty matches user skill level"""
        level_hierarchy = {
            "beginner": 0,
            "intermediate": 1,
            "advanced": 2,
            "expert": 3
        }

        user_rank = level_hierarchy.get(user_level, 0)
        tutorial_rank = level_hierarchy.get(tutorial_level, 0)

        # Recommend tutorials at or slightly above current level
        return tutorial_rank <= user_rank + 1

    def _prerequisites_satisfied(self, completed_ids: List[str], prerequisites: str) -> bool:
        """Check if user has completed prerequisite tutorials"""
        if not prerequisites:
            return True

        prerequisite_ids = json.loads(prerequisites or "[]")
        return all(prereq_id in completed_ids for prereq_id in prerequisite_ids)

    def _generate_recommendation_reasons(self, tutorial: TutorialDB, user_level: str, completed_ids: List[str]) -> List[str]:
        """Generate reasons for tutorial recommendation"""
        reasons = []

        if self._skill_level_match(user_level, tutorial.difficulty_level):
            reasons.append(f"Matches your {user_level} skill level")

        if self._prerequisites_satisfied(completed_ids, tutorial.prerequisites):
            reasons.append("You have the required prerequisites")

        if tutorial.rating >= 4.5:
            reasons.append("Highly rated by other learners")

        if tutorial.view_count > 100:
            reasons.append("Popular among learners")

        return reasons[:3]  # Return top 3 reasons

# API Models
class TutorialStepSubmission(BaseModel):
    step_id: str
    user_input: Dict[str, Any]
    code: Optional[str] = None
    output: Optional[str] = None

class TutorialProgress(BaseModel):
    tutorial_id: str
    step_id: str
    time_spent_minutes: int
    notes: Optional[str] = None

class TutorialSession(BaseModel):
    tutorial_id: str
    user_id: str

class TutorialSystemApp:
    """Main Tutorial System Application"""

    def __init__(self):
        self.app = FastAPI(title="DMLogn8n Tutorial System", version="1.0.0")
        self.setup_middleware()
        self.setup_routes()

        # Initialize database
        self.engine = create_engine('sqlite:///tutorial_system.db')
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Initialize components
        self.code_env = CodeExecutionEnvironment()
        self.validator = InteractiveValidator()
        self.active_sessions = {}

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
            return {"message": "DMLogn8n Tutorial System API"}

        @self.app.get("/tutorials")
        async def get_tutorials(
            tutorial_type: Optional[str] = None,
            difficulty_level: Optional[str] = None,
            tags: Optional[str] = None,
            limit: int = 20,
            offset: int = 0
        ):
            """Get available tutorials with filtering"""
            db = self.SessionLocal()
            try:
                query = db.query(TutorialDB).filter(
                    TutorialDB.status == TutorialStatus.PUBLISHED.value
                )

                if tutorial_type:
                    query = query.filter(TutorialDB.tutorial_type == tutorial_type)
                if difficulty_level:
                    query = query.filter(TutorialDB.difficulty_level == difficulty_level)

                tutorials = query.offset(offset).limit(limit).all()

                return {
                    "tutorials": [
                        {
                            "id": tutorial.id,
                            "title": tutorial.title,
                            "description": tutorial.description,
                            "tutorial_type": tutorial.tutorial_type,
                            "difficulty_level": tutorial.difficulty_level,
                            "estimated_duration_minutes": tutorial.estimated_duration_minutes,
                            "rating": tutorial.rating,
                            "view_count": tutorial.view_count,
                            "completion_count": tutorial.completion_count,
                            "tags": json.loads(tutorial.tags or "[]")
                        }
                        for tutorial in tutorials
                    ],
                    "total": len(tutorials)
                }
            finally:
                db.close()

        @self.app.get("/tutorials/{tutorial_id}")
        async def get_tutorial(tutorial_id: str):
            """Get tutorial details"""
            db = self.SessionLocal()
            try:
                tutorial = db.query(TutorialDB).filter(
                    TutorialDB.id == tutorial_id
                ).first()

                if not tutorial:
                    raise HTTPException(status_code=404, detail="Tutorial not found")

                # Increment view count
                tutorial.view_count += 1
                db.commit()

                steps = json.loads(tutorial.steps or "[]")

                return {
                    "id": tutorial.id,
                    "title": tutorial.title,
                    "description": tutorial.description,
                    "tutorial_type": tutorial.tutorial_type,
                    "difficulty_level": tutorial.difficulty_level,
                    "estimated_duration_minutes": tutorial.estimated_duration_minutes,
                    "steps": steps,
                    "prerequisites": json.loads(tutorial.prerequisites or "[]"),
                    "learning_objectives": json.loads(tutorial.learning_objectives or "[]"),
                    "tags": json.loads(tutorial.tags or "[]"),
                    "rating": tutorial.rating,
                    "view_count": tutorial.view_count,
                    "completion_count": tutorial.completion_count
                }
            finally:
                db.close()

        @self.app.post("/tutorials/{tutorial_id}/start")
        async def start_tutorial(session: TutorialSession):
            """Start a tutorial session"""
            db = self.SessionLocal()
            try:
                # Check if progress already exists
                existing_progress = db.query(UserTutorialProgress).filter(
                    UserTutorialProgress.user_id == session.user_id,
                    UserTutorialProgress.tutorial_id == session.tutorial_id
                ).first()

                if existing_progress:
                    # Update last accessed
                    existing_progress.last_accessed = datetime.utcnow()
                    db.commit()
                    progress_id = existing_progress.id
                else:
                    # Create new progress record
                    new_progress = UserTutorialProgress(
                        id=str(uuid.uuid4()),
                        user_id=session.user_id,
                        tutorial_id=session.tutorial_id
                    )
                    db.add(new_progress)
                    db.commit()
                    progress_id = new_progress.id

                return {"progress_id": progress_id, "message": "Tutorial started"}
            finally:
                db.close()

        @self.app.post("/tutorials/submit")
        async def submit_step(submission: TutorialStepSubmission):
            """Submit tutorial step for validation"""
            validation_result = await self.validator.validate_step(
                TutorialStep(
                    id=submission.step_id,
                    title="",
                    content="",
                    step_type="code",
                    order=0,
                    instructions="",
                    hints=[]
                ),
                submission.dict()
            )

            return validation_result

        @self.app.post("/code/session")
        async def create_code_session(tutorial_id: str, step_id: str, user_id: str):
            """Create code execution session"""
            session = await self.code_env.create_session(tutorial_id, step_id, user_id)
            return session

        @self.app.post("/code/execute")
        async def execute_code(session_id: str, code: str):
            """Execute code in tutorial environment"""
            result = await self.code_env.execute_code(session_id, code)
            return result

        @self.app.put("/progress")
        async def update_progress(progress: TutorialProgress):
            """Update tutorial progress"""
            db = self.SessionLocal()
            try:
                user_progress = db.query(UserTutorialProgress).filter(
                    UserTutorialProgress.user_id == progress.user_id,
                    UserTutorialProgress.tutorial_id == progress.tutorial_id
                ).first()

                if not user_progress:
                    raise HTTPException(status_code=404, detail="Progress not found")

                # Update progress
                user_progress.time_spent_minutes += progress.time_spent_minutes
                user_progress.last_accessed = datetime.utcnow()

                if progress.notes:
                    notes = json.loads(user_progress.notes or "{}")
                    notes[progress.step_id] = progress.notes
                    user_progress.notes = json.dumps(notes)

                db.commit()

                return {"message": "Progress updated successfully"}
            finally:
                db.close()

        @self.app.get("/recommendations/{user_id}")
        async def get_recommendations(user_id: str, count: int = 5):
            """Get personalized tutorial recommendations"""
            db = self.SessionLocal()
            try:
                recommender = TutorialRecommender(db)
                recommendations = await recommender.recommend_tutorials(user_id, count)
                return {"recommendations": recommendations}
            finally:
                db.close()

        @self.app.get("/progress/{user_id}")
        async def get_user_progress(user_id: str):
            """Get user's tutorial progress"""
            db = self.SessionLocal()
            try:
                progress_records = db.query(UserTutorialProgress).filter(
                    UserTutorialProgress.user_id == user_id
                ).all()

                result = []
                for record in progress_records:
                    tutorial = db.query(TutorialDB).filter(
                        TutorialDB.id == record.tutorial_id
                    ).first()

                    if tutorial:
                        result.append({
                            "tutorial_id": record.tutorial_id,
                            "tutorial_title": tutorial.title,
                            "progress_percentage": record.progress_percentage,
                            "current_step": record.current_step,
                            "time_spent_minutes": record.time_spent_minutes,
                            "started_at": record.started_at,
                            "completed_at": record.completed_at,
                            "status": "completed" if record.completed_at else "in_progress"
                        })

                return {"progress": result}
            finally:
                db.close()

        @self.app.websocket("/ws/tutorial/{tutorial_id}/{user_id}")
        async def websocket_tutorial_endpoint(websocket: WebSocket, tutorial_id: str, user_id: str):
            """WebSocket for real-time tutorial interaction"""
            await websocket.accept()

            try:
                while True:
                    # Receive message from client
                    data = await websocket.receive_json()

                    if data["type"] == "step_submit":
                        # Validate step and send results
                        validation_result = await self.validator.validate_step(
                            TutorialStep(
                                id=data["step_id"],
                                title="",
                                content="",
                                step_type=data.get("step_type", "code"),
                                order=0,
                                instructions="",
                                hints=[]
                            ),
                            data["user_input"]
                        )

                        await websocket.send_json({
                            "type": "validation_result",
                            "step_id": data["step_id"],
                            "result": validation_result
                        })

                    elif data["type"] == "code_execute":
                        # Execute code and send results
                        result = await self.code_env.execute_code(
                            data["session_id"],
                            data["code"]
                        )

                        await websocket.send_json({
                            "type": "execution_result",
                            "session_id": data["session_id"],
                            "result": result
                        })

                    elif data["type"] == "heartbeat":
                        # Keep connection alive
                        await websocket.send_json({"type": "heartbeat_response"})

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for tutorial {tutorial_id}, user {user_id}")

    async def cleanup_old_sessions(self):
        """Periodically clean up old sessions"""
        while True:
            try:
                await self.code_env.cleanup_sessions()
                await asyncio.sleep(3600)  # Clean up every hour
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")
                await asyncio.sleep(300)  # Retry after 5 minutes

    def run(self, host: str = "0.0.0.0", port: int = 8001):
        """Run the tutorial system server"""
        import uvicorn

        # Start background cleanup task
        asyncio.create_task(self.cleanup_old_sessions())

        uvicorn.run(self.app, host=host, port=port)

# Main execution
if __name__ == "__main__":
    app = TutorialSystemApp()
    app.run()