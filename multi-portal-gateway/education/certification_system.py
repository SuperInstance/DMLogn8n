#!/usr/bin/env python3
"""
DMLogn8n Certification System - Skill Assessment and Certification
Comprehensive certification system with exams, projects, peer review, and blockchain verification
"""

import asyncio
import json
import logging
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import secrets
import base64
from PIL import Image, ImageDraw, ImageFont
import qrcode

# Third-party imports
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import yaml
import aiofiles
import aiohttp
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Boolean, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import redis
import web3
from web3.auto import w3
from web3.contract import Contract
import pdfkit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('certification_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

Base = declarative_base()

class CertificationLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    MASTER = "master"

class AssessmentType(Enum):
    QUIZ = "quiz"
    CODING_CHALLENGE = "coding_challenge"
    PROJECT = "project"
    PEER_REVIEW = "peer_review"
    INTERVIEW = "interview"
    PRACTICAL_EXAM = "practical_exam"
    WRITTEN_EXAM = "written_exam"

class QuestionType(Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    CODING = "coding"
    PRACTICAL = "practical"

class CertificationStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"

class ExamStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PASSED = "passed"
    FAILED = "failed"
    EXPIRED = "expired"

@dataclass
class Certification:
    id: str
    title: str
    description: str
    level: CertificationLevel
    duration_hours: int
    prerequisites: List[str]
    learning_objectives: List[str]
    skills_assessed: List[str]
    exam_format: str
    passing_score: float
    validity_months: int
    status: CertificationStatus
    created_at: datetime
    updated_at: datetime

@dataclass
class Question:
    id: str
    certification_id: str
    question_type: QuestionType
    question_text: str
    options: List[str]  # For multiple choice
    correct_answer: str
    explanation: str
    points: float
    difficulty: int
    tags: List[str]
    metadata: Dict[str, Any]

@dataclass
class Exam:
    id: str
    certification_id: str
    user_id: str
    status: ExamStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    time_limit_minutes: int
    score: float
    max_score: float
    answers: Dict[str, Any]
    graded_at: Optional[datetime]
    grader_id: Optional[str]
    feedback: str
    attempts: int
    certificate_issued: bool

@dataclass
class Certificate:
    id: str
    certification_id: str
    user_id: str
    exam_id: str
    certificate_number: str
    issue_date: datetime
    expiry_date: datetime
    verification_code: str
    blockchain_tx_hash: Optional[str]
    pdf_url: str
    image_url: str
    status: str
    revoked: bool
    revoke_reason: Optional[str]

class CertificationDB(Base):
    __tablename__ = "certifications"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    level = Column(String, nullable=False)
    duration_hours = Column(Integer)
    prerequisites = Column(Text)  # JSON string
    learning_objectives = Column(Text)  # JSON string
    skills_assessed = Column(Text)  # JSON string
    exam_format = Column(String)
    passing_score = Column(Float, nullable=False)
    validity_months = Column(Integer)
    status = Column(String, default=CertificationStatus.DRAFT.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    questions = relationship("QuestionDB", back_populates="certification")
    exams = relationship("ExamDB", back_populates="certification")

class QuestionDB(Base):
    __tablename__ = "certification_questions"

    id = Column(String, primary_key=True)
    certification_id = Column(String, ForeignKey("certifications.id"), nullable=False)
    question_type = Column(String, nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(Text)  # JSON string
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text)
    points = Column(Float, nullable=False)
    difficulty = Column(Integer, default=1)
    tags = Column(Text)  # JSON string
    metadata = Column(Text)  # JSON string

    # Relationships
    certification = relationship("CertificationDB", back_populates="questions")

class ExamDB(Base):
    __tablename__ = "certification_exams"

    id = Column(String, primary_key=True)
    certification_id = Column(String, ForeignKey("certifications.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(String, default=ExamStatus.NOT_STARTED.value)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    time_limit_minutes = Column(Integer)
    score = Column(Float, default=0.0)
    max_score = Column(Float)
    answers = Column(Text)  # JSON string
    graded_at = Column(DateTime)
    grader_id = Column(String, ForeignKey("users.id"))
    feedback = Column(Text)
    attempts = Column(Integer, default=0)
    certificate_issued = Column(Boolean, default=False)

    # Relationships
    certification = relationship("CertificationDB", back_populates="exams")
    user = relationship("User")
    grader = relationship("User", foreign_keys=[grader_id])

class CertificateDB(Base):
    __tablename__ = "certificates"

    id = Column(String, primary_key=True)
    certification_id = Column(String, ForeignKey("certifications.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    exam_id = Column(String, ForeignKey("certification_exams.id"), nullable=False)
    certificate_number = Column(String, unique=True, nullable=False)
    issue_date = Column(DateTime, default=datetime.utcnow)
    expiry_date = Column(DateTime)
    verification_code = Column(String, unique=True, nullable=False)
    blockchain_tx_hash = Column(String)
    pdf_url = Column(String)
    image_url = Column(String)
    status = Column(String, default="active")
    revoked = Column(Boolean, default=False)
    revoke_reason = Column(Text)

    # Relationships
    certification = relationship("CertificationDB")
    user = relationship("User")
    exam = relationship("ExamDB")

class QuestionBank:
    """Advanced question bank management system"""

    def __init__(self, db_session: Session):
        self.db = db_session

    def add_question(self, question_data: Dict[str, Any]) -> str:
        """Add new question to the bank"""
        question = QuestionDB(
            id=str(uuid.uuid4()),
            certification_id=question_data["certification_id"],
            question_type=question_data["question_type"],
            question_text=question_data["question_text"],
            options=json.dumps(question_data.get("options", [])),
            correct_answer=question_data["correct_answer"],
            explanation=question_data.get("explanation", ""),
            points=question_data.get("points", 1.0),
            difficulty=question_data.get("difficulty", 1),
            tags=json.dumps(question_data.get("tags", [])),
            metadata=json.dumps(question_data.get("metadata", {}))
        )

        self.db.add(question)
        self.db.commit()

        return question.id

    def generate_exam(self, certification_id: str, question_count: int, difficulty_distribution: Dict[str, int] = None) -> List[Question]:
        """Generate exam with balanced question distribution"""
        if difficulty_distribution is None:
            difficulty_distribution = {"easy": 3, "medium": 4, "hard": 3}

        questions_db = self.db.query(QuestionDB).filter(
            QuestionDB.certification_id == certification_id
        ).all()

        # Group questions by difficulty
        questions_by_difficulty = {1: [], 2: [], 3: [], 4: [], 5: []}
        for q in questions_db:
            questions_by_difficulty[q.difficulty].append(q)

        # Select questions based on distribution
        selected_questions = []

        difficulty_map = {"easy": [1, 2], "medium": [3], "hard": [4, 5]}

        for difficulty, count in difficulty_distribution.items():
            available_levels = difficulty_map.get(difficulty, [3])
            available_questions = []

            for level in available_levels:
                available_questions.extend(questions_by_difficulty[level])

            # Randomly select questions
            import random
            selected = random.sample(
                available_questions,
                min(count, len(available_questions))
            )
            selected_questions.extend(selected)

        # Convert to Question objects
        exam_questions = []
        for q in selected_questions:
            exam_questions.append(Question(
                id=q.id,
                certification_id=q.certification_id,
                question_type=QuestionType(q.question_type),
                question_text=q.question_text,
                options=json.loads(q.options or "[]"),
                correct_answer=q.correct_answer,
                explanation=q.explanation,
                points=q.points,
                difficulty=q.difficulty,
                tags=json.loads(q.tags or "[]"),
                metadata=json.loads(q.metadata or "{}")
            ))

        return exam_questions

    def validate_answer(self, question: Question, user_answer: str) -> Dict[str, Any]:
        """Validate user answer against correct answer"""
        result = {
            "is_correct": False,
            "score": 0.0,
            "feedback": "",
            "explanation": question.explanation
        }

        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            result["is_correct"] = user_answer.strip().lower() == question.correct_answer.strip().lower()
            result["score"] = question.points if result["is_correct"] else 0

        elif question.question_type == QuestionType.TRUE_FALSE:
            result["is_correct"] = user_answer.strip().lower() == question.correct_answer.strip().lower()
            result["score"] = question.points if result["is_correct"] else 0

        elif question.question_type == QuestionType.SHORT_ANSWER:
            # Simple string matching with some flexibility
            user_clean = user_answer.strip().lower()
            correct_clean = question.correct_answer.strip().lower()
            result["is_correct"] = user_clean == correct_clean
            result["score"] = question.points if result["is_correct"] else 0

        elif question.question_type == QuestionType.ESSAY:
            # Essays require manual grading
            result["feedback"] = "Essay questions require manual grading."
            result["score"] = 0  # Will be set by grader

        elif question.question_type == QuestionType.CODING:
            # Code challenges require automated testing
            result = self._validate_code_answer(question, user_answer)

        return result

    def _validate_code_answer(self, question: Question, user_code: str) -> Dict[str, Any]:
        """Validate coding challenge answer"""
        result = {
            "is_correct": False,
            "score": 0.0,
            "feedback": "",
            "test_results": []
        }

        try:
            # Get test cases from question metadata
            metadata = json.loads(question.metadata or "{}")
            test_cases = metadata.get("test_cases", [])

            if not test_cases:
                result["feedback"] = "No test cases defined for this coding challenge."
                return result

            # Execute code against test cases
            passed_tests = 0
            total_tests = len(test_cases)

            for i, test_case in enumerate(test_cases):
                test_result = self._run_code_test(user_code, test_case)
                result["test_results"].append(test_result)

                if test_result["passed"]:
                    passed_tests += 1

            # Calculate score based on passed tests
            result["score"] = (passed_tests / total_tests) * question.points
            result["is_correct"] = passed_tests == total_tests
            result["feedback"] = f"Passed {passed_tests} out of {total_tests} test cases."

        except Exception as e:
            result["feedback"] = f"Error executing code: {str(e)}"

        return result

    def _run_code_test(self, code: str, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run single test case against user code"""
        test_result = {
            "passed": False,
            "error": "",
            "actual_output": "",
            "expected_output": test_case.get("expected", "")
        }

        try:
            # Create safe execution environment
            safe_globals = {
                '__builtins__': {},
                'print': lambda *args: None,  # Disable print
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'list': list,
                'dict': dict,
                'set': set,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'sum': sum,
                'max': max,
                'min': min
            }

            # Execute user code
            exec(code, safe_globals)

            # Get the function to test
            function_name = test_case.get("function_name")
            if not function_name or function_name not in safe_globals:
                test_result["error"] = f"Function '{function_name}' not found."
                return test_result

            func = safe_globals[function_name]

            # Run test case
            test_input = test_case.get("input", [])
            expected = test_case.get("expected")
            actual = func(*test_input) if isinstance(test_input, list) else func(test_input)

            test_result["actual_output"] = str(actual)

            # Compare results
            if actual == expected:
                test_result["passed"] = True
            else:
                test_result["error"] = f"Expected {expected}, got {actual}"

        except Exception as e:
            test_result["error"] = f"Execution error: {str(e)}"

        return test_result

class ExamGrader:
    """Automated and manual exam grading system"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.question_bank = QuestionBank(db_session)

    async def grade_exam(self, exam_id: str) -> Dict[str, Any]:
        """Grade completed exam"""
        exam = self.db.query(ExamDB).filter(ExamDB.id == exam_id).first()
        if not exam:
            raise ValueError("Exam not found")

        certification = self.db.query(CertificationDB).filter(
            CertificationDB.id == exam.certification_id
        ).first()

        answers = json.loads(exam.answers or "{}")
        total_score = 0
        max_score = 0
        question_results = []

        for question_id, user_answer in answers.items():
            question = self.db.query(QuestionDB).filter(QuestionDB.id == question_id).first()
            if not question:
                continue

            question_obj = Question(
                id=question.id,
                certification_id=question.certification_id,
                question_type=QuestionType(question.question_type),
                question_text=question.question_text,
                options=json.loads(question.options or "[]"),
                correct_answer=question.correct_answer,
                explanation=question.explanation,
                points=question.points,
                difficulty=question.difficulty,
                tags=json.loads(question.tags or "[]"),
                metadata=json.loads(question.metadata or "{}")
            )

            result = self.question_bank.validate_answer(question_obj, user_answer)
            total_score += result["score"]
            max_score += question.points

            question_results.append({
                "question_id": question_id,
                "user_answer": user_answer,
                "result": result
            })

        # Update exam record
        exam.score = total_score
        exam.max_score = max_score
        exam.status = ExamStatus.COMPLETED.value
        exam.graded_at = datetime.utcnow()

        # Determine if passed
        passing_score = certification.passing_score if certification else 70.0
        percentage_score = (total_score / max_score * 100) if max_score > 0 else 0

        if percentage_score >= passing_score:
            exam.status = ExamStatus.PASSED.value
        else:
            exam.status = ExamStatus.FAILED.value

        self.db.commit()

        return {
            "exam_id": exam_id,
            "score": total_score,
            "max_score": max_score,
            "percentage_score": percentage_score,
            "passed": exam.status == ExamStatus.PASSED.value,
            "question_results": question_results,
            "feedback": self._generate_feedback(question_results, percentage_score)
        }

    def _generate_feedback(self, question_results: List[Dict[str, Any]], percentage_score: float) -> str:
        """Generate personalized feedback based on exam performance"""
        feedback = []

        if percentage_score >= 90:
            feedback.append("Excellent work! You've demonstrated mastery of the subject matter.")
        elif percentage_score >= 80:
            feedback.append("Great job! You have a strong understanding of the material.")
        elif percentage_score >= 70:
            feedback.append("Good work! You've met the passing requirements.")
        else:
            feedback.append("You didn't pass this time. Review the material and try again.")

        # Identify weak areas
        incorrect_questions = [r for r in question_results if not r["result"]["is_correct"]]
        if incorrect_questions:
            feedback.append("Areas for improvement:")
            for result in incorrect_questions[:3]:  # Show top 3 areas
                feedback.append(f"- Review: {result['result'].get('explanation', 'Question concept')}")

        return "\n".join(feedback)

class CertificateGenerator:
    """Advanced certificate generation with blockchain verification"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.template_dir = Path(self.config.get("template_dir", "templates/certificates"))
        self.output_dir = Path(self.config.get("output_dir", "certificates"))
        self.output_dir.mkdir(exist_ok=True)

        # Blockchain setup
        self.web3 = None
        self.contract = None
        if self.config.get("blockchain_enabled"):
            self._setup_blockchain()

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load certificate configuration"""
        default_config = {
            "template_dir": "templates/certificates",
            "output_dir": "certificates",
            "blockchain_enabled": False,
            "blockchain_network": "ethereum",
            "contract_address": "",
            "private_key": "",
            "qr_code_enabled": True,
            "digital_signature": True,
            "certificate_prefix": "DMLOG",
            "font_path": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        }

        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)

        return default_config

    def _setup_blockchain(self):
        """Setup blockchain connection"""
        try:
            # Connect to Ethereum network
            self.web3 = web3.Web3(web3.HTTPProvider(self.config.get("blockchain_rpc_url")))

            if not self.web3.is_connected():
                logger.warning("Failed to connect to blockchain")
                return

            # Load contract ABI and address
            contract_address = self.config.get("contract_address")
            if contract_address:
                # Would load contract ABI from file
                # self.contract = self.web3.eth.contract(address=contract_address, abi=contract_abi)
                pass

        except Exception as e:
            logger.error(f"Blockchain setup failed: {e}")

    async def generate_certificate(self, exam: ExamDB, user_data: Dict[str, Any], certification: CertificationDB) -> Certificate:
        """Generate certificate for passed exam"""
        # Generate certificate details
        certificate_number = self._generate_certificate_number()
        verification_code = self._generate_verification_code()
        issue_date = datetime.utcnow()
        expiry_date = issue_date + timedelta(days=certification.validity_months * 30)

        # Generate certificate image
        image_path = await self._generate_certificate_image(
            certificate_number,
            user_data,
            certification,
            issue_date,
            expiry_date,
            verification_code
        )

        # Generate PDF
        pdf_path = await self._generate_certificate_pdf(
            certificate_number,
            user_data,
            certification,
            issue_date,
            expiry_date,
            verification_code
        )

        # Mint on blockchain if enabled
        blockchain_tx_hash = None
        if self.config.get("blockchain_enabled") and self.web3:
            blockchain_tx_hash = await self._mint_certificate_nft(
                certificate_number,
                user_data["id"],
                verification_code
            )

        # Create certificate record
        certificate = Certificate(
            id=str(uuid.uuid4()),
            certification_id=exam.certification_id,
            user_id=exam.user_id,
            exam_id=exam.id,
            certificate_number=certificate_number,
            issue_date=issue_date,
            expiry_date=expiry_date,
            verification_code=verification_code,
            blockchain_tx_hash=blockchain_tx_hash,
            pdf_url=f"/certificates/pdf/{certificate_number}.pdf",
            image_url=f"/certificates/images/{certificate_number}.png",
            status="active",
            revoked=False
        )

        return certificate

    def _generate_certificate_number(self) -> str:
        """Generate unique certificate number"""
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        random_suffix = secrets.token_hex(4).upper()
        return f"{self.config['certificate_prefix']}-{timestamp}-{random_suffix}"

    def _generate_verification_code(self) -> str:
        """Generate unique verification code"""
        return secrets.token_urlsafe(16).upper()

    async def _generate_certificate_image(
        self,
        certificate_number: str,
        user_data: Dict[str, Any],
        certification: CertificationDB,
        issue_date: datetime,
        expiry_date: datetime,
        verification_code: str
    ) -> str:
        """Generate certificate image"""
        # Create certificate image
        width, height = 1200, 800
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)

        try:
            # Load font
            font_path = self.config.get("font_path")
            if font_path and Path(font_path).exists():
                title_font = ImageFont.truetype(font_path, 48)
                text_font = ImageFont.truetype(font_path, 24)
                small_font = ImageFont.truetype(font_path, 18)
            else:
                title_font = ImageFont.load_default()
                text_font = ImageFont.load_default()
                small_font = ImageFont.load_default()
        except:
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Draw border
        draw.rectangle([20, 20, width-20, height-20], outline='black', width=3)

        # Draw title
        title = "Certificate of Achievement"
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(((width - title_width) // 2, 80), title, font=title_font, fill='black')

        # Draw certification name
        cert_name = certification.title
        cert_bbox = draw.textbbox((0, 0), cert_name, font=text_font)
        cert_width = cert_bbox[2] - cert_bbox[0]
        draw.text(((width - cert_width) // 2, 200), cert_name, font=text_font, fill='darkblue')

        # Draw recipient name
        recipient_text = "This is to certify that"
        recipient_bbox = draw.textbbox((0, 0), recipient_text, font=small_font)
        recipient_width = recipient_bbox[2] - recipient_bbox[0]
        draw.text(((width - recipient_width) // 2, 280), recipient_text, font=small_font, fill='black')

        name_text = user_data.get("full_name", user_data.get("username", ""))
        name_bbox = draw.textbbox((0, 0), name_text, font=title_font)
        name_width = name_bbox[2] - name_bbox[0]
        draw.text(((width - name_width) // 2, 320), name_text, font=title_font, fill='darkgreen')

        # Draw completion text
        completion_text = f"has successfully completed the {certification.title} certification"
        completion_bbox = draw.textbbox((0, 0), completion_text, font=text_font)
        completion_width = completion_bbox[2] - completion_bbox[0]
        draw.text(((width - completion_width) // 2, 400), completion_text, font=text_font, fill='black')

        # Draw dates
        issue_text = f"Issued: {issue_date.strftime('%B %d, %Y')}"
        expiry_text = f"Expires: {expiry_date.strftime('%B %d, %Y')}"
        draw.text((100, 500), issue_text, font=small_font, fill='black')
        draw.text((100, 530), expiry_text, font=small_font, fill='black')

        # Draw certificate number
        cert_num_text = f"Certificate No: {certificate_number}"
        draw.text((100, 580), cert_num_text, font=small_font, fill='black')

        # Generate QR code for verification
        if self.config.get("qr_code_enabled"):
            qr_url = f"https://verify.dmlogn8n.com/{verification_code}"
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_url)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")

            # Resize QR code and paste
            qr_img = qr_img.resize((150, 150))
            img.paste(qr_img, (width - 200, height - 200))

        # Save image
        image_path = self.output_dir / "images" / f"{certificate_number}.png"
        image_path.parent.mkdir(exist_ok=True)
        img.save(image_path)

        return str(image_path)

    async def _generate_certificate_pdf(
        self,
        certificate_number: str,
        user_data: Dict[str, Any],
        certification: CertificationDB,
        issue_date: datetime,
        expiry_date: datetime,
        verification_code: str
    ) -> str:
        """Generate certificate PDF"""
        # Generate HTML template
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Certificate - {certification.title}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: white;
                }}
                .certificate {{
                    width: 100%;
                    max-width: 1200px;
                    margin: 0 auto;
                    border: 3px solid #000;
                    padding: 40px;
                    text-align: center;
                    position: relative;
                }}
                .title {{
                    font-size: 48px;
                    font-weight: bold;
                    margin-bottom: 20px;
                    color: #000;
                }}
                .certification-name {{
                    font-size: 32px;
                    color: #0066cc;
                    margin-bottom: 40px;
                }}
                .recipient {{
                    font-size: 36px;
                    font-weight: bold;
                    color: #006600;
                    margin: 30px 0;
                }}
                .completion-text {{
                    font-size: 24px;
                    margin: 20px 0;
                }}
                .dates {{
                    font-size: 18px;
                    margin-top: 60px;
                    text-align: left;
                }}
                .certificate-number {{
                    font-size: 16px;
                    margin-top: 20px;
                    text-align: left;
                }}
                .verification {{
                    position: absolute;
                    bottom: 40px;
                    right: 40px;
                    text-align: center;
                }}
                .qr-code {{
                    margin-top: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="certificate">
                <div class="title">Certificate of Achievement</div>
                <div class="certification-name">{certification.title}</div>

                <div class="completion-text">This is to certify that</div>
                <div class="recipient">{user_data.get('full_name', user_data.get('username', ''))}</div>
                <div class="completion-text">
                    has successfully completed the {certification.title} certification
                    with a score of {certification.passing_score}% or higher.
                </div>

                <div class="dates">
                    <div><strong>Issued:</strong> {issue_date.strftime('%B %d, %Y')}</div>
                    <div><strong>Expires:</strong> {expiry_date.strftime('%B %d, %Y')}</div>
                </div>

                <div class="certificate-number">
                    <strong>Certificate No:</strong> {certificate_number}
                </div>

                <div class="verification">
                    <div>Verify Online</div>
                    <div class="qr-code">
                        <img src="/certificates/images/{certificate_number}.png" alt="QR Code" width="150">
                    </div>
                    <div style="font-size: 12px; margin-top: 5px;">
                        Code: {verification_code}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        # Save HTML file
        html_path = self.output_dir / "html" / f"{certificate_number}.html"
        html_path.parent.mkdir(exist_ok=True)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Convert to PDF
        pdf_path = self.output_dir / "pdf" / f"{certificate_number}.pdf"
        pdf_path.parent.mkdir(exist_ok=True)

        try:
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None
            }
            pdfkit.from_file(str(html_path), str(pdf_path), options=options)
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            # Fallback: return HTML path
            return str(html_path)

        return str(pdf_path)

    async def _mint_certificate_nft(self, certificate_number: str, user_id: str, verification_code: str) -> Optional[str]:
        """Mint certificate as NFT on blockchain"""
        if not self.web3 or not self.contract:
            return None

        try:
            # Create NFT metadata
            metadata = {
                "name": f"DMLogn8n Certificate - {certificate_number}",
                "description": "Official DMLogn8n Certification Certificate",
                "certificate_number": certificate_number,
                "verification_code": verification_code,
                "issue_date": datetime.utcnow().isoformat(),
                "image": f"https://certificates.dmlogn8n.com/images/{certificate_number}.png"
            }

            # Mint NFT (simplified)
            # In practice, this would interact with the smart contract
            tx_hash = "0x" + secrets.token_hex(32)  # Mock transaction hash

            return tx_hash

        except Exception as e:
            logger.error(f"NFT minting failed: {e}")
            return None

    async def verify_certificate(self, verification_code: str) -> Optional[Dict[str, Any]]:
        """Verify certificate using verification code"""
        db = sessionmaker(bind=self.engine)()
        try:
            certificate = db.query(CertificateDB).filter(
                CertificateDB.verification_code == verification_code
            ).first()

            if not certificate:
                return None

            # Check if certificate is valid
            if certificate.revoked:
                return {
                    "valid": False,
                    "reason": "Certificate has been revoked",
                    "revoke_reason": certificate.revoke_reason
                }

            # Check expiry
            if certificate.expiry_date and certificate.expiry_date < datetime.utcnow():
                return {
                    "valid": False,
                    "reason": "Certificate has expired"
                }

            # Return certificate details
            return {
                "valid": True,
                "certificate_number": certificate.certificate_number,
                "issue_date": certificate.issue_date.isoformat(),
                "expiry_date": certificate.expiry_date.isoformat() if certificate.expiry_date else None,
                "verification_code": certificate.verification_code,
                "blockchain_tx_hash": certificate.blockchain_tx_hash
            }

        finally:
            db.close()

# API Models
class CreateExamRequest(BaseModel):
    certification_id: str
    user_id: str
    time_limit_minutes: Optional[int] = 120

class SubmitExamRequest(BaseModel):
    exam_id: str
    answers: Dict[str, Any]

class VerifyCertificateRequest(BaseModel):
    verification_code: str

class CertificationSystemApp:
    """Main Certification System Application"""

    def __init__(self):
        self.app = FastAPI(title="DMLogn8n Certification System", version="1.0.0")
        self.setup_middleware()
        self.setup_routes()

        # Initialize database
        self.engine = create_engine('sqlite:///certification_system.db')
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Initialize components
        self.question_bank = None
        self.exam_grader = None
        self.certificate_generator = CertificateGenerator()

        # Templates and static files
        self.templates = Jinja2Templates(directory="templates")
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
        self.app.mount("/certificates", StaticFiles(directory="certificates"), name="certificates")

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
            return {"message": "DMLogn8n Certification System API"}

        @self.app.get("/certifications")
        async def get_certifications():
            """Get available certifications"""
            db = self.SessionLocal()
            try:
                certifications = db.query(CertificationDB).filter(
                    CertificationDB.status == CertificationStatus.ACTIVE.value
                ).all()

                return {
                    "certifications": [
                        {
                            "id": cert.id,
                            "title": cert.title,
                            "description": cert.description,
                            "level": cert.level,
                            "duration_hours": cert.duration_hours,
                            "passing_score": cert.passing_score,
                            "validity_months": cert.validity_months,
                            "prerequisites": json.loads(cert.prerequisites or "[]"),
                            "learning_objectives": json.loads(cert.learning_objectives or "[]"),
                            "skills_assessed": json.loads(cert.skills_assessed or "[]")
                        }
                        for cert in certifications
                    ]
                }
            finally:
                db.close()

        @self.app.post("/exams/create")
        async def create_exam(request: CreateExamRequest):
            """Create new exam attempt"""
            db = self.SessionLocal()
            try:
                # Check if user has active exam
                existing_exam = db.query(ExamDB).filter(
                    ExamDB.certification_id == request.certification_id,
                    ExamDB.user_id == request.user_id,
                    ExamDB.status.in_([ExamStatus.NOT_STARTED.value, ExamStatus.IN_PROGRESS.value])
                ).first()

                if existing_exam:
                    raise HTTPException(status_code=400, detail="User already has an active exam")

                # Get certification details
                certification = db.query(CertificationDB).filter(
                    CertificationDB.id == request.certification_id
                ).first()

                if not certification:
                    raise HTTPException(status_code=404, detail="Certification not found")

                # Initialize components
                if not self.question_bank:
                    self.question_bank = QuestionBank(db)

                # Generate exam questions
                questions = self.question_bank.generate_exam(request.certification_id, 10)

                # Create exam record
                exam = ExamDB(
                    id=str(uuid.uuid4()),
                    certification_id=request.certification_id,
                    user_id=request.user_id,
                    status=ExamStatus.NOT_STARTED.value,
                    time_limit_minutes=request.time_limit_minutes or 120,
                    max_score=sum(q.points for q in questions)
                )

                db.add(exam)
                db.commit()

                return {
                    "exam_id": exam.id,
                    "questions": [
                        {
                            "id": q.id,
                            "type": q.question_type.value,
                            "question": q.question_text,
                            "options": q.options if q.question_type == QuestionType.MULTIPLE_CHOICE else None,
                            "points": q.points,
                            "difficulty": q.difficulty
                        }
                        for q in questions
                    ],
                    "time_limit_minutes": exam.time_limit_minutes,
                    "max_score": exam.max_score
                }

            finally:
                db.close()

        @self.app.post("/exams/submit")
        async def submit_exam(request: SubmitExamRequest):
            """Submit completed exam for grading"""
            db = self.SessionLocal()
            try:
                exam = db.query(ExamDB).filter(ExamDB.id == request.exam_id).first()
                if not exam:
                    raise HTTPException(status_code=404, detail="Exam not found")

                # Update exam with answers
                exam.answers = json.dumps(request.answers)
                exam.completed_at = datetime.utcnow()
                exam.status = ExamStatus.IN_PROGRESS.value  # Will be updated by grader

                db.commit()

                # Grade exam
                if not self.exam_grader:
                    self.exam_grader = ExamGrader(db)

                # Schedule grading in background
                import asyncio
                asyncio.create_task(self._grade_exam_background(request.exam_id))

                return {"message": "Exam submitted successfully. Grading in progress."}

            finally:
                db.close()

        @self.app.get("/exams/{exam_id}/result")
        async def get_exam_result(exam_id: str):
            """Get exam results"""
            db = self.SessionLocal()
            try:
                exam = db.query(ExamDB).filter(ExamDB.id == exam_id).first()
                if not exam:
                    raise HTTPException(status_code=404, detail="Exam not found")

                if exam.status not in [ExamStatus.COMPLETED.value, ExamStatus.PASSED.value, ExamStatus.FAILED.value]:
                    return {"status": "pending", "message": "Exam not yet graded"}

                return {
                    "exam_id": exam.id,
                    "score": exam.score,
                    "max_score": exam.max_score,
                    "percentage_score": (exam.score / exam.max_score * 100) if exam.max_score > 0 else 0,
                    "status": exam.status,
                    "graded_at": exam.graded_at,
                    "feedback": exam.feedback,
                    "certificate_issued": exam.certificate_issued
                }

            finally:
                db.close()

        @self.app.get("/certificates/{user_id}")
        async def get_user_certificates(user_id: str):
            """Get user's certificates"""
            db = self.SessionLocal()
            try:
                certificates = db.query(CertificateDB).filter(
                    CertificateDB.user_id == user_id,
                    CertificateDB.revoked == False
                ).all()

                return {
                    "certificates": [
                        {
                            "id": cert.id,
                            "certificate_number": cert.certificate_number,
                            "certification_id": cert.certification_id,
                            "issue_date": cert.issue_date,
                            "expiry_date": cert.expiry_date,
                            "verification_code": cert.verification_code,
                            "pdf_url": cert.pdf_url,
                            "image_url": cert.image_url,
                            "status": cert.status
                        }
                        for cert in certificates
                    ]
                }
            finally:
                db.close()

        @self.app.post("/certificates/verify")
        async def verify_certificate(request: VerifyCertificateRequest):
            """Verify certificate using verification code"""
            result = await self.certificate_generator.verify_certificate(request.verification_code)

            if not result:
                raise HTTPException(status_code=404, detail="Certificate not found")

            return result

        @self.app.get("/certificates/pdf/{certificate_number}")
        async def get_certificate_pdf(certificate_number: str):
            """Download certificate PDF"""
            pdf_path = self.certificate_generator.output_dir / "pdf" / f"{certificate_number}.pdf"
            if pdf_path.exists():
                return FileResponse(pdf_path, media_type="application/pdf")
            else:
                raise HTTPException(status_code=404, detail="Certificate PDF not found")

        @self.app.get("/certificates/images/{certificate_number}")
        async def get_certificate_image(certificate_number: str):
            """Download certificate image"""
            image_path = self.certificate_generator.output_dir / "images" / f"{certificate_number}.png"
            if image_path.exists():
                return FileResponse(image_path, media_type="image/png")
            else:
                raise HTTPException(status_code=404, detail="Certificate image not found")

    async def _grade_exam_background(self, exam_id: str):
        """Grade exam in background"""
        db = self.SessionLocal()
        try:
            if not self.exam_grader:
                self.exam_grader = ExamGrader(db)

            result = await self.exam_grader.grade_exam(exam_id)

            # Issue certificate if passed
            if result["passed"]:
                exam = db.query(ExamDB).filter(ExamDB.id == exam_id).first()
                if exam and not exam.certificate_issued:
                    await self._issue_certificate(exam)

        except Exception as e:
            logger.error(f"Background grading failed for exam {exam_id}: {e}")
        finally:
            db.close()

    async def _issue_certificate(self, exam: ExamDB):
        """Issue certificate for passed exam"""
        db = self.SessionLocal()
        try:
            # Get user data
            user = db.query(User).filter(User.id == exam.user_id).first()
            if not user:
                return

            # Get certification
            certification = db.query(CertificationDB).filter(
                CertificationDB.id == exam.certification_id
            ).first()

            if not certification:
                return

            # Generate certificate
            certificate = await self.certificate_generator.generate_certificate(
                exam,
                {
                    "id": user.id,
                    "full_name": user.full_name,
                    "username": user.username
                },
                Certification(
                    id=certification.id,
                    title=certification.title,
                    description=certification.description,
                    level=CertificationLevel(certification.level),
                    duration_hours=certification.duration_hours,
                    prerequisites=json.loads(certification.prerequisites or "[]"),
                    learning_objectives=json.loads(certification.learning_objectives or "[]"),
                    skills_assessed=json.loads(certification.skills_assessed or "[]"),
                    exam_format=certification.exam_format,
                    passing_score=certification.passing_score,
                    validity_months=certification.validity_months,
                    status=CertificationStatus(certification.status),
                    created_at=certification.created_at,
                    updated_at=certification.updated_at
                )
            )

            # Save certificate to database
            cert_db = CertificateDB(
                id=certificate.id,
                certification_id=certificate.certification_id,
                user_id=certificate.user_id,
                exam_id=certificate.exam_id,
                certificate_number=certificate.certificate_number,
                issue_date=certificate.issue_date,
                expiry_date=certificate.expiry_date,
                verification_code=certificate.verification_code,
                blockchain_tx_hash=certificate.blockchain_tx_hash,
                pdf_url=certificate.pdf_url,
                image_url=certificate.image_url,
                status=certificate.status,
                revoked=certificate.revoked
            )

            db.add(cert_db)

            # Update exam record
            exam.certificate_issued = True

            db.commit()

        except Exception as e:
            logger.error(f"Certificate issuance failed: {e}")
        finally:
            db.close()

    def run(self, host: str = "0.0.0.0", port: int = 8004):
        """Run the certification system server"""
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)

# Main execution
if __name__ == "__main__":
    app = CertificationSystemApp()
    app.run()