#!/usr/bin/env python3
"""
DMLogn8n Research Library - Academic Research and Paper Repository
Comprehensive research library with paper management, citations, collaboration, and academic networking
"""

import asyncio
import json
import logging
import hashlib
import uuid
import re
import fitz  # PyMuPDF
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import arxiv
import bibtexparser
from scholarly import scholarly

# Third-party imports
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
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
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('research_library.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

Base = declarative_base()

class PaperType(Enum):
    JOURNAL_ARTICLE = "journal_article"
    CONFERENCE_PAPER = "conference_paper"
    PREPRINT = "preprint"
    THESIS = "thesis"
    DISSERTATION = "dissertation"
    BOOK = "book"
    BOOK_CHAPTER = "book_chapter"
    TECHNICAL_REPORT = "technical_report"
    WORKING_PAPER = "working_paper"

class ResearchStatus(Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    PUBLISHED = "published"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    REVISION_REQUIRED = "revision_required"

class CollaborationRole(Enum):
    AUTHOR = "author"
    REVIEWER = "reviewer"
    ADVISOR = "advisor"
    COLLABORATOR = "collaborator"
    CONTRIBUTOR = "contributor"

@dataclass
class ResearchPaper:
    id: str
    title: str
    abstract: str
    authors: List[Dict[str, str]]
    publication_venue: str
    publication_date: datetime
    paper_type: PaperType
    research_status: ResearchStatus
    doi: Optional[str]
    arxiv_id: Optional[str]
    isbn: Optional[str]
    pages: str
    volume: Optional[str]
    issue: Optional[str]
    keywords: List[str]
    research_areas: List[str]
    methodology: str
    findings: str
    implications: str
    limitations: str
    future_work: str
    references: List[Dict[str, Any]]
    supplementary_materials: List[Dict[str, Any]]
    file_path: str
    file_size_mb: float
    page_count: int
    download_count: int
    view_count: int
    citation_count: int
    created_at: datetime
    updated_at: datetime

@dataclass
class ResearchProject:
    id: str
    title: str
    description: str
    research_questions: List[str]
    hypotheses: List[str]
    methodology: str
    timeline: Dict[str, Any]
    budget: Optional[float]
    funding_source: Optional[str]
    principal_investigator_id: str
    team_members: List[Dict[str, Any]]
    status: str
    progress_percentage: float
    milestones: List[Dict[str, Any]]
    deliverables: List[Dict[str, Any]]
    publications: List[str]
    datasets: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

class ResearchPaperDB(Base):
    __tablename__ = "research_papers"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    abstract = Column(Text)
    authors = Column(Text)  # JSON string
    publication_venue = Column(String)
    publication_date = Column(DateTime)
    paper_type = Column(String, nullable=False)
    research_status = Column(String, default=ResearchStatus.DRAFT.value)
    doi = Column(String)
    arxiv_id = Column(String)
    isbn = Column(String)
    pages = Column(String)
    volume = Column(String)
    issue = Column(String)
    keywords = Column(Text)  # JSON string
    research_areas = Column(Text)  # JSON string
    methodology = Column(Text)
    findings = Column(Text)
    implications = Column(Text)
    limitations = Column(Text)
    future_work = Column(Text)
    references = Column(Text)  # JSON string
    supplementary_materials = Column(Text)  # JSON string
    file_path = Column(String)
    file_size_mb = Column(Float)
    page_count = Column(Integer)
    download_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    citation_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    authors_rel = relationship("PaperAuthor", back_populates="paper")
    citations_made = relationship("PaperCitation", foreign_keys="PaperCitation.citing_paper_id", back_populates="citing_paper")
    citations_received = relationship("PaperCitation", foreign_keys="PaperCitation.cited_paper_id", back_populates="cited_paper")
    reviews = relationship("PaperReview", back_populates="paper")
    notes = relationship("PaperNote", back_populates="paper")

class ResearchProjectDB(Base):
    __tablename__ = "research_projects"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    research_questions = Column(Text)  # JSON string
    hypotheses = Column(Text)  # JSON string
    methodology = Column(Text)
    timeline = Column(Text)  # JSON string
    budget = Column(Float)
    funding_source = Column(String)
    principal_investigator_id = Column(String, ForeignKey("users.id"), nullable=False)
    team_members = Column(Text)  # JSON string
    status = Column(String, default="planning")
    progress_percentage = Column(Float, default=0.0)
    milestones = Column(Text)  # JSON string
    deliverables = Column(Text)  # JSON string
    publications = Column(Text)  # JSON string
    datasets = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    principal_investigator = relationship("User")

class PaperAuthor(Base):
    __tablename__ = "paper_authors"

    id = Column(String, primary_key=True)
    paper_id = Column(String, ForeignKey("research_papers.id"), nullable=False)
    author_id = Column(String, ForeignKey("users.id"), nullable=False)
    author_order = Column(Integer, nullable=False)
    affiliation = Column(String)
    corresponding_author = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    paper = relationship("ResearchPaperDB", back_populates="authors_rel")
    author = relationship("User")

class PaperCitation(Base):
    __tablename__ = "paper_citations"

    id = Column(String, primary_key=True)
    citing_paper_id = Column(String, ForeignKey("research_papers.id"), nullable=False)
    cited_paper_id = Column(String, ForeignKey("research_papers.id"), nullable=False)
    citation_context = Column(Text)
    citation_type = Column(String, default="reference")
    page_number = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    citing_paper = relationship("ResearchPaperDB", foreign_keys=[citing_paper_id], back_populates="citations_made")
    cited_paper = relationship("ResearchPaperDB", foreign_keys=[cited_paper_id], back_populates="citations_received")

class PaperReview(Base):
    __tablename__ = "paper_reviews"

    id = Column(String, primary_key=True)
    paper_id = Column(String, ForeignKey("research_papers.id"), nullable=False)
    reviewer_id = Column(String, ForeignKey("users.id"), nullable=False)
    review_type = Column(String, default="peer")  # peer, editorial, self
    overall_rating = Column(Integer)  # 1-5
    confidence_rating = Column(Integer)  # 1-5
    summary = Column(Text)
    strengths = Column(Text)
    weaknesses = Column(Text)
    recommendations = Column(Text)
    is_anonymous = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    paper = relationship("ResearchPaperDB", back_populates="reviews")
    reviewer = relationship("User")

class PaperNote(Base):
    __tablename__ = "paper_notes"

    id = Column(String, primary_key=True)
    paper_id = Column(String, ForeignKey("research_papers.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    note_type = Column(String, default="general")  # general, quote, question, idea
    content = Column(Text, nullable=False)
    page_number = Column(Integer)
    highlight_text = Column(Text)
    tags = Column(Text)  # JSON string
    is_private = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    paper = relationship("ResearchPaperDB", back_populates="notes")
    user = relationship("User")

class PaperProcessor:
    """Advanced paper processing and metadata extraction"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.storage_dir = Path(self.config.get("storage_dir", "research_papers"))
        self.storage_dir.mkdir(exist_ok=True)
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration"""
        default_config = {
            "storage_dir": "research_papers",
            "max_file_size_mb": 50,
            "supported_formats": [".pdf", ".doc", ".docx", ".txt"],
            "auto_extract_metadata": True,
            "generate_summaries": True,
            "extract_references": True,
            "similarity_threshold": 0.7
        }

        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)

        return default_config

    async def process_paper(self, file_path: str, paper_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process uploaded research paper"""
        try:
            # Extract metadata from file
            if self.config.get("auto_extract_metadata"):
                extracted_metadata = await self._extract_metadata_from_file(file_path)
                if paper_data:
                    paper_data.update(extracted_metadata)
                else:
                    paper_data = extracted_metadata

            # Extract text content
            text_content = await self._extract_text_from_file(file_path)

            # Generate summary if enabled
            summary = None
            if self.config.get("generate_summaries"):
                summary = await self._generate_summary(text_content)

            # Extract references if enabled
            references = []
            if self.config.get("extract_references"):
                references = await self._extract_references(text_content)

            # Generate embedding for similarity search
            embedding = self._generate_embedding(paper_data.get("abstract", "") + " " + summary)

            # Store file
            stored_path = await self._store_file(file_path, paper_data.get("title", "untitled"))

            return {
                "metadata": paper_data,
                "text_content": text_content,
                "summary": summary,
                "references": references,
                "embedding": embedding.tolist(),
                "file_path": stored_path,
                "processing_status": "completed"
            }

        except Exception as e:
            logger.error(f"Paper processing failed: {e}")
            return {
                "processing_status": "error",
                "error": str(e)
            }

    async def _extract_metadata_from_file(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF file"""
        metadata = {}

        try:
            # Open PDF
            doc = fitz.open(file_path)

            # Extract basic metadata
            pdf_metadata = doc.metadata
            metadata.update({
                "title": pdf_metadata.get("title", ""),
                "authors": self._parse_authors(pdf_metadata.get("author", "")),
                "subject": pdf_metadata.get("subject", ""),
                "creator": pdf_metadata.get("creator", ""),
                "producer": pdf_metadata.get("producer", ""),
                "creation_date": pdf_metadata.get("creationDate", ""),
                "modification_date": pdf_metadata.get("modDate", "")
            })

            # Extract page count
            metadata["page_count"] = len(doc)

            # Try to extract abstract from first pages
            abstract_text = await self._extract_abstract_from_text(doc)
            if abstract_text:
                metadata["abstract"] = abstract_text

            # Extract keywords
            keywords = await self._extract_keywords_from_text(doc)
            if keywords:
                metadata["keywords"] = keywords

            doc.close()

        except Exception as e:
            logger.warning(f"Metadata extraction failed: {e}")

        return metadata

    def _parse_authors(self, author_string: str) -> List[Dict[str, str]]:
        """Parse author string into structured format"""
        if not author_string:
            return []

        authors = []
        # Split by common separators
        author_names = re.split(r'[,;]', author_string)

        for i, name in enumerate(author_names):
            name = name.strip()
            if name:
                authors.append({
                    "name": name,
                    "order": i + 1,
                    "affiliation": ""
                })

        return authors

    async def _extract_abstract_from_text(self, doc) -> Optional[str]:
        """Extract abstract from PDF document"""
        # Look for abstract in first few pages
        for page_num in range(min(3, len(doc))):
            page = doc[page_num]
            text = page.get_text()

            # Look for "Abstract" keyword
            abstract_match = re.search(
                r'(?:Abstract|ABSTRACT)\s*[:\-]?\s*(.*?)(?:\n\s*(?:Keywords|KEYWORDS|Introduction|1\.|\n\n[A-Z])|$)',
                text,
                re.DOTALL | re.IGNORECASE
            )

            if abstract_match:
                abstract = abstract_match.group(1).strip()
                # Clean up abstract
                abstract = re.sub(r'\s+', ' ', abstract)
                return abstract

        return None

    async def _extract_keywords_from_text(self, doc) -> List[str]:
        """Extract keywords from PDF document"""
        keywords = []

        for page_num in range(min(3, len(doc))):
            page = doc[page_num]
            text = page.get_text()

            # Look for keywords section
            keywords_match = re.search(
                r'(?:Keywords|KEYWORDS)\s*[:\-]?\s*(.*?)(?:\n\s*(?:Introduction|1\.|Abstract)|\n\n|$)',
                text,
                re.DOTALL | re.IGNORECASE
            )

            if keywords_match:
                keywords_text = keywords_match.group(1).strip()
                # Split by common separators
                keyword_list = re.split(r'[,;]', keywords_text)
                keywords = [kw.strip() for kw in keyword_list if kw.strip()]
                break

        return keywords

    async def _extract_text_from_file(self, file_path: str) -> str:
        """Extract text content from file"""
        if file_path.lower().endswith('.pdf'):
            return await self._extract_text_from_pdf(file_path)
        elif file_path.lower().endswith(('.doc', '.docx')):
            return await self._extract_text_from_docx(file_path)
        elif file_path.lower().endswith('.txt'):
            return await self._extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path}")

    async def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")

        return text

    async def _extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            import docx
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"DOCX text extraction failed: {e}")
            return ""

    async def _extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except Exception as e:
            logger.error(f"TXT text extraction failed: {e}")
            return ""

    async def _generate_summary(self, text: str) -> str:
        """Generate summary of paper content"""
        # Simple extractive summarization
        # In production, this would use more sophisticated NLP models

        # Split text into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        if len(sentences) <= 3:
            return " ".join(sentences)

        # Score sentences based on position and length
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = 0

            # Position score (sentences in first third get higher score)
            if i < len(sentences) // 3:
                score += 2
            elif i < 2 * len(sentences) // 3:
                score += 1

            # Length score (moderate length sentences preferred)
            length_score = min(len(sentence) / 100, 1)
            score += length_score

            # Keyword score (sentences with research keywords)
            research_keywords = ['method', 'result', 'conclusion', 'findings', 'analysis', 'study', 'research']
            keyword_count = sum(1 for keyword in research_keywords if keyword.lower() in sentence.lower())
            score += keyword_count

            scored_sentences.append((sentence, score))

        # Sort by score and take top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        summary_sentences = [s[0] for s in scored_sentences[:3]]

        return ". ".join(summary_sentences) + "."

    async def _extract_references(self, text: str) -> List[Dict[str, Any]]:
        """Extract references from paper text"""
        references = []

        # Look for references section
        references_match = re.search(
            r'(?:References|REFERENCES|Bibliography|BIBLIOGRAPHY)\s*(.*?)(?=\n\s*$|\n\s*[A-Z][A-Z\s]+$)',
            text,
            re.DOTALL | re.IGNORECASE
        )

        if references_match:
            references_text = references_match.group(1).strip()

            # Split references by common patterns
            ref_patterns = [
                r'\[\d+\]',  # [1], [2], etc.
                r'\(\d{4}\)',  # (2023), (2022), etc.
                r'^\d+\.',  # Numbered references
                r'^[A-Z][a-z]+, [A-Z]\.'  # Author, Initial.
            ]

            # Try to extract individual references
            reference_lines = references_text.split('\n')
            current_ref = ""

            for line in reference_lines:
                line = line.strip()
                if not line:
                    continue

                # Check if line starts a new reference
                is_new_ref = any(re.match(pattern, line) for pattern in ref_patterns)

                if is_new_ref and current_ref:
                    # Save previous reference
                    ref_data = self._parse_reference(current_ref)
                    if ref_data:
                        references.append(ref_data)
                    current_ref = line
                else:
                    current_ref += " " + line

            # Add last reference
            if current_ref:
                ref_data = self._parse_reference(current_ref)
                if ref_data:
                    references.append(ref_data)

        return references

    def _parse_reference(self, reference_text: str) -> Optional[Dict[str, Any]]:
        """Parse individual reference text"""
        # Simple reference parsing
        # In production, this would use more sophisticated parsing

        ref_data = {
            "text": reference_text.strip(),
            "authors": [],
            "title": "",
            "venue": "",
            "year": "",
            "doi": "",
            "url": ""
        }

        # Extract year
        year_match = re.search(r'\b(19|20)\d{2}\b', reference_text)
        if year_match:
            ref_data["year"] = year_match.group(0)

        # Extract DOI
        doi_match = re.search(r'doi:\s*(10\.\S+)', reference_text, re.IGNORECASE)
        if doi_match:
            ref_data["doi"] = doi_match.group(1)

        # Extract URL
        url_match = re.search(r'https?://\S+', reference_text)
        if url_match:
            ref_data["url"] = url_match.group(0)

        return ref_data

    def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate text embedding for similarity search"""
        try:
            # Truncate text if too long
            max_length = 512
            if len(text) > max_length:
                text = text[:max_length]

            embedding = self.sentence_model.encode(text)
            return embedding
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return np.zeros(384)  # Return zero embedding on error

    async def _store_file(self, source_path: str, title: str) -> str:
        """Store file in research library"""
        # Generate safe filename
        safe_title = re.sub(r'[^\w\s-]', '', title).strip()
        safe_title = re.sub(r'[-\s]+', '-', safe_title)
        filename = f"{safe_title}_{uuid.uuid4().hex[:8]}{Path(source_path).suffix}"

        # Store in organized directory structure
        year = datetime.utcnow().year
        storage_path = self.storage_dir / str(year) / filename
        storage_path.parent.mkdir(exist_ok=True)

        # Copy file
        import shutil
        shutil.copy2(source_path, storage_path)

        return str(storage_path)

class CitationManager:
    """Advanced citation management and bibliographic tools"""

    def __init__(self, db_session: Session):
        self.db = db_session

    def import_bibtex(self, bibtex_content: str, user_id: str) -> List[str]:
        """Import papers from BibTeX content"""
        parser = bibtexparser.bibdatabase.BibDatabase()
        parser.loads = bibtexparser.loads
        bib_database = parser.loads(bibtex_content)

        imported_paper_ids = []

        for key, entry in bib_database.entries.items():
            try:
                # Parse BibTeX entry
                paper_data = self._parse_bibtex_entry(entry)

                # Create paper record
                paper = ResearchPaperDB(
                    id=str(uuid.uuid4()),
                    title=paper_data.get("title", ""),
                    abstract=paper_data.get("abstract", ""),
                    authors=json.dumps(paper_data.get("authors", [])),
                    publication_venue=paper_data.get("journal", entry.get("booktitle", "")),
                    paper_type=self._determine_paper_type(entry),
                    doi=entry.get("doi"),
                    isbn=entry.get("isbn"),
                    pages=entry.get("pages"),
                    volume=entry.get("volume"),
                    issue=entry.get("number"),
                    keywords=json.dumps(paper_data.get("keywords", [])),
                    references=json.dumps([]),  # Would need to extract from BibTeX
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )

                self.db.add(paper)
                imported_paper_ids.append(paper.id)

            except Exception as e:
                logger.error(f"Failed to import BibTeX entry {key}: {e}")

        self.db.commit()
        return imported_paper_ids

    def _parse_bibtex_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Parse BibTeX entry into structured data"""
        paper_data = {
            "title": entry.get("title", "").strip("{}"),
            "abstract": entry.get("abstract", "").strip("{}"),
            "authors": self._parse_bibtex_authors(entry.get("author", "")),
            "keywords": self._parse_bibtex_keywords(entry.get("keywords", "")),
            "year": entry.get("year"),
            "month": entry.get("month")
        }

        return paper_data

    def _parse_bibtex_authors(self, author_string: str) -> List[Dict[str, str]]:
        """Parse BibTeX author string"""
        if not author_string:
            return []

        authors = []
        author_list = author_string.split(" and ")

        for i, author in enumerate(author_list):
            author = author.strip().strip("{}")
            if author:
                authors.append({
                    "name": author,
                    "order": i + 1,
                    "affiliation": ""
                })

        return authors

    def _parse_bibtex_keywords(self, keyword_string: str) -> List[str]:
        """Parse BibTeX keywords"""
        if not keyword_string:
            return []

        keywords = keyword_string.strip("{}").split(",")
        return [kw.strip() for kw in keywords if kw.strip()]

    def _determine_paper_type(self, entry: Dict[str, Any]) -> str:
        """Determine paper type from BibTeX entry"""
        entry_type = entry.get("ENTRYTYPE", "").lower()

        type_mapping = {
            "article": PaperType.JOURNAL_ARTICLE.value,
            "inproceedings": PaperType.CONFERENCE_PAPER.value,
            "incollection": PaperType.BOOK_CHAPTER.value,
            "book": PaperType.BOOK.value,
            "phdthesis": PaperType.THESIS.value,
            "mastersthesis": PaperType.THESIS.value,
            "techreport": PaperType.TECHNICAL_REPORT.value
        }

        return type_mapping.get(entry_type, PaperType.JOURNAL_ARTICLE.value)

    def export_bibtex(self, paper_ids: List[str]) -> str:
        """Export papers to BibTeX format"""
        papers = self.db.query(ResearchPaperDB).filter(
            ResearchPaperDB.id.in_(paper_ids)
        ).all()

        bib_database = bibtexparser.bibdatabase.BibDatabase()

        for paper in papers:
            entry = {
                "ENTRYTYPE": self._get_bibtex_type(paper.paper_type),
                "ID": f"paper_{paper.id[:8]}",
                "title": paper.title,
                "author": self._format_bibtex_authors(json.loads(paper.authors or "[]")),
                "abstract": paper.abstract,
                "year": paper.publication_date.year if paper.publication_date else "",
                "journal": paper.publication_venue,
                "doi": paper.doi,
                "keywords": ", ".join(json.loads(paper.keywords or "[]"))
            }

            bib_database.entries.append(entry)

        return bibtexparser.dumps(bib_database)

    def _get_bibtex_type(self, paper_type: str) -> str:
        """Convert paper type to BibTeX type"""
        type_mapping = {
            PaperType.JOURNAL_ARTICLE.value: "article",
            PaperType.CONFERENCE_PAPER.value: "inproceedings",
            PaperType.BOOK_CHAPTER.value: "incollection",
            PaperType.BOOK.value: "book",
            PaperType.THESIS.value: "phdthesis",
            PaperType.TECHNICAL_REPORT.value: "techreport"
        }

        return type_mapping.get(paper_type, "article")

    def _format_bibtex_authors(self, authors: List[Dict[str, str]]) -> str:
        """Format authors for BibTeX"""
        if not authors:
            return ""

        author_names = [author["name"] for author in authors]
        return " and ".join(author_names)

    def add_citation(self, citing_paper_id: str, cited_paper_id: str, context: str = "", page_number: int = None) -> str:
        """Add citation between papers"""
        citation = PaperCitation(
            id=str(uuid.uuid4()),
            citing_paper_id=citing_paper_id,
            cited_paper_id=cited_paper_id,
            citation_context=context,
            page_number=page_number,
            created_at=datetime.utcnow()
        )

        self.db.add(citation)
        self.db.commit()

        # Update citation count
        cited_paper = self.db.query(ResearchPaperDB).filter(
            ResearchPaperDB.id == cited_paper_id
        ).first()
        if cited_paper:
            cited_paper.citation_count += 1
            self.db.commit()

        return citation.id

    def get_citation_network(self, paper_id: str, depth: int = 2) -> Dict[str, Any]:
        """Get citation network for a paper"""
        network = {
            "nodes": {},
            "edges": [],
            "center_paper": paper_id
        }

        # Get center paper
        center_paper = self.db.query(ResearchPaperDB).filter(
            ResearchPaperDB.id == paper_id
        ).first()

        if not center_paper:
            return network

        network["nodes"][paper_id] = {
            "title": center_paper.title,
            "authors": json.loads(center_paper.authors or "[]"),
            "year": center_paper.publication_date.year if center_paper.publication_date else None,
            "citation_count": center_paper.citation_count
        }

        # Get papers that cite this paper
        citing_papers = self.db.query(PaperCitation).filter(
            PaperCitation.cited_paper_id == paper_id
        ).all()

        for citation in citing_papers:
            citing_paper = self.db.query(ResearchPaperDB).filter(
                ResearchPaperDB.id == citation.citing_paper_id
            ).first()

            if citing_paper:
                network["nodes"][citation.citing_paper_id] = {
                    "title": citing_paper.title,
                    "authors": json.loads(citing_paper.authors or "[]"),
                    "year": citing_paper.publication_date.year if citing_paper.publication_date else None,
                    "citation_count": citing_paper.citation_count
                }

                network["edges"].append({
                    "from": citation.citing_paper_id,
                    "to": paper_id,
                    "type": "cites"
                })

        # Get papers cited by this paper
        cited_papers = self.db.query(PaperCitation).filter(
            PaperCitation.citing_paper_id == paper_id
        ).all()

        for citation in cited_papers:
            cited_paper = self.db.query(ResearchPaperDB).filter(
                ResearchPaperDB.id == citation.cited_paper_id
            ).first()

            if cited_paper:
                network["nodes"][citation.cited_paper_id] = {
                    "title": cited_paper.title,
                    "authors": json.loads(cited_paper.authors or "[]"),
                    "year": cited_paper.publication_date.year if cited_paper.publication_date else None,
                    "citation_count": cited_paper.citation_count
                }

                network["edges"].append({
                    "from": paper_id,
                    "to": citation.cited_paper_id,
                    "type": "cites"
                })

        return network

class AcademicSearch:
    """Integration with academic search engines"""

    def __init__(self):
        self.arxiv_client = arxiv.Client()

    async def search_arxiv(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search arXiv for papers"""
        try:
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )

            results = []
            for result in self.arxiv_client.results(search):
                paper_data = {
                    "id": result.get_short_id(),
                    "title": result.title,
                    "abstract": result.summary,
                    "authors": [{"name": author.name, "affiliation": ""} for author in result.authors],
                    "publication_date": result.published.date(),
                    "arxiv_id": result.get_short_id(),
                    "doi": result.doi,
                    "pdf_url": result.pdf_url,
                    "categories": result.categories,
                    "primary_category": result.primary_category
                }
                results.append(paper_data)

            return results

        except Exception as e:
            logger.error(f"arXiv search failed: {e}")
            return []

    async def search_google_scholar(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search Google Scholar for papers"""
        try:
            search_query = scholarly.search_pubs(query, limit=max_results)
            results = []

            for i, pub in enumerate(search_query):
                if i >= max_results:
                    break

                # Extract bibliographic information
                bib = pub.bib

                paper_data = {
                    "title": bib.get("title", ""),
                    "abstract": pub.get("summary", ""),
                    "authors": [{"name": author, "affiliation": ""} for author in pub.get("authors", [])],
                    "publication_venue": bib.get("journal", bib.get("booktitle", "")),
                    "year": bib.get("year", ""),
                    "doi": bib.get("doi", ""),
                    "url": pub.get("pub_url", ""),
                    "cited_by": pub.get("citedby", 0)
                }
                results.append(paper_data)

            return results

        except Exception as e:
            logger.error(f"Google Scholar search failed: {e}")
            return []

    async def import_from_arxiv(self, arxiv_id: str, user_id: str) -> Optional[str]:
        """Import specific paper from arXiv"""
        try:
            search = arxiv.Search(id_list=[arxiv_id])
            result = next(self.arxiv_client.results(search))

            # Create paper record
            paper = ResearchPaperDB(
                id=str(uuid.uuid4()),
                title=result.title,
                abstract=result.summary,
                authors=json.dumps([{"name": author.name, "affiliation": ""} for author in result.authors]),
                publication_venue="arXiv",
                publication_date=result.published.date(),
                paper_type=PaperType.PREPRINT.value,
                arxiv_id=arxiv_id,
                keywords=json.dumps(result.categories),
                file_path=result.pdf_url,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            db = sessionmaker(bind=create_engine('sqlite:///research_library.db'))()
            db.add(paper)
            db.commit()

            return paper.id

        except Exception as e:
            logger.error(f"arXiv import failed: {e}")
            return None

# API Models
class UploadPaperRequest(BaseModel):
    title: str
    abstract: str
    authors: List[Dict[str, str]]
    paper_type: str
    research_areas: List[str]
    keywords: List[str]

class SearchPapersRequest(BaseModel):
    query: str
    paper_type: Optional[str] = None
    research_areas: Optional[List[str]] = None
    authors: Optional[List[str]] = None
    limit: int = 20

class CreateProjectRequest(BaseModel):
    title: str
    description: str
    research_questions: List[str]
    methodology: str
    team_members: List[str]

class ResearchLibraryApp:
    """Main Research Library Application"""

    def __init__(self):
        self.app = FastAPI(title="DMLogn8n Research Library", version="1.0.0")
        self.setup_middleware()
        self.setup_routes()

        # Initialize database
        self.engine = create_engine('sqlite:///research_library.db')
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Initialize components
        self.paper_processor = PaperProcessor()
        self.citation_manager = None
        self.academic_search = AcademicSearch()

        # Initialize Redis
        self.redis_client = redis.Redis(host='localhost', port=6379, db=5)

        # Templates and static files
        self.templates = Jinja2Templates(directory="templates")
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
        self.app.mount("/papers", StaticFiles(directory="research_papers"), name="papers")

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
            return {"message": "DMLogn8n Research Library API"}

        @self.app.post("/papers/upload")
        async def upload_paper(
            background_tasks: BackgroundTasks,
            file: UploadFile = File(...),
            title: str = Form(...),
            abstract: str = Form(...),
            authors: str = Form(...),
            paper_type: str = Form(...),
            research_areas: str = Form("[]"),
            keywords: str = Form("[]"),
            uploaded_by: str = Form(...)
        ):
            """Upload research paper"""
            # Validate file
            if not self._validate_paper_file(file):
                raise HTTPException(status_code=400, detail="Invalid paper file")

            # Save uploaded file temporarily
            temp_path = Path(f"temp_{uuid.uuid4().hex}_{file.filename}")
            async with aiofiles.open(temp_path, 'wb') as f:
                content = await file.read()
                await f.write(content)

            # Process paper in background
            background_tasks.add_task(self._process_uploaded_paper, str(temp_path), {
                "title": title,
                "abstract": abstract,
                "authors": json.loads(authors),
                "paper_type": paper_type,
                "research_areas": json.loads(research_areas),
                "keywords": json.loads(keywords)
            }, uploaded_by)

            return {"message": "Paper uploaded successfully. Processing in progress."}

        @self.app.get("/papers")
        async def get_papers(
            paper_type: Optional[str] = None,
            research_areas: Optional[str] = None,
            keywords: Optional[str] = None,
            limit: int = 20,
            offset: int = 0,
            sort_by: str = "recent"
        ):
            """Get research papers with filtering"""
            db = self.SessionLocal()
            try:
                query = db.query(ResearchPaperDB)

                if paper_type:
                    query = query.filter(ResearchPaperDB.paper_type == paper_type)

                papers = query.offset(offset).limit(limit).all()

                return {
                    "papers": [
                        {
                            "id": paper.id,
                            "title": paper.title,
                            "abstract": paper.abstract[:300] + "..." if len(paper.abstract) > 300 else paper.abstract,
                            "authors": json.loads(paper.authors or "[]"),
                            "publication_venue": paper.publication_venue,
                            "publication_date": paper.publication_date,
                            "paper_type": paper.paper_type,
                            "research_areas": json.loads(paper.research_areas or "[]"),
                            "keywords": json.loads(paper.keywords or "[]"),
                            "citation_count": paper.citation_count,
                            "download_count": paper.download_count,
                            "view_count": paper.view_count,
                            "created_at": paper.created_at
                        }
                        for paper in papers
                    ],
                    "total": len(papers)
                }
            finally:
                db.close()

        @self.app.get("/papers/{paper_id}")
        async def get_paper(paper_id: str):
            """Get detailed paper information"""
            db = self.SessionLocal()
            try:
                paper = db.query(ResearchPaperDB).filter(ResearchPaperDB.id == paper_id).first()
                if not paper:
                    raise HTTPException(status_code=404, detail="Paper not found")

                # Increment view count
                paper.view_count += 1
                db.commit()

                return {
                    "id": paper.id,
                    "title": paper.title,
                    "abstract": paper.abstract,
                    "authors": json.loads(paper.authors or "[]"),
                    "publication_venue": paper.publication_venue,
                    "publication_date": paper.publication_date,
                    "paper_type": paper.paper_type,
                    "research_status": paper.research_status,
                    "doi": paper.doi,
                    "arxiv_id": paper.arxiv_id,
                    "pages": paper.pages,
                    "volume": paper.volume,
                    "issue": paper.issue,
                    "keywords": json.loads(paper.keywords or "[]"),
                    "research_areas": json.loads(paper.research_areas or "[]"),
                    "methodology": paper.methodology,
                    "findings": paper.findings,
                    "implications": paper.implications,
                    "limitations": paper.limitations,
                    "future_work": paper.future_work,
                    "references": json.loads(paper.references or "[]"),
                    "citation_count": paper.citation_count,
                    "download_count": paper.download_count,
                    "view_count": paper.view_count,
                    "file_path": paper.file_path,
                    "page_count": paper.page_count,
                    "created_at": paper.created_at
                }
            finally:
                db.close()

        @self.app.post("/papers/search")
        async def search_papers(request: SearchPapersRequest):
            """Search papers with advanced filters"""
            db = self.SessionLocal()
            try:
                # Simple text search (would use full-text search in production)
                query = db.query(ResearchPaperDB)

                # Apply text search
                if request.query:
                    search_terms = request.query.lower().split()
                    for term in search_terms:
                        query = query.filter(
                            ResearchPaperDB.title.ilike(f"%{term}%") |
                            ResearchPaperDB.abstract.ilike(f"%{term}%")
                        )

                # Apply filters
                if request.paper_type:
                    query = query.filter(ResearchPaperDB.paper_type == request.paper_type)

                if request.research_areas:
                    for area in request.research_areas:
                        query = query.filter(ResearchPaperDB.research_areas.ilike(f"%{area}%"))

                papers = query.limit(request.limit).all()

                return {
                    "papers": [
                        {
                            "id": paper.id,
                            "title": paper.title,
                            "abstract": paper.abstract[:200] + "..." if len(paper.abstract) > 200 else paper.abstract,
                            "authors": json.loads(paper.authors or "[]"),
                            "publication_venue": paper.publication_venue,
                            "publication_date": paper.publication_date,
                            "paper_type": paper.paper_type,
                            "citation_count": paper.citation_count,
                            "relevance_score": 0.8  # Placeholder
                        }
                        for paper in papers
                    ],
                    "total": len(papers)
                }
            finally:
                db.close()

        @self.app.post("/papers/citations")
        async def add_citation(
            citing_paper_id: str,
            cited_paper_id: str,
            context: str = "",
            page_number: int = None
        ):
            """Add citation between papers"""
            if not self.citation_manager:
                self.citation_manager = CitationManager(self.SessionLocal())

            citation_id = self.citation_manager.add_citation(
                citing_paper_id,
                cited_paper_id,
                context,
                page_number
            )

            return {"citation_id": citation_id, "message": "Citation added successfully"}

        @self.app.get("/papers/{paper_id}/citations/network")
        async def get_citation_network(paper_id: str, depth: int = 2):
            """Get citation network for paper"""
            if not self.citation_manager:
                self.citation_manager = CitationManager(self.SessionLocal())

            network = self.citation_manager.get_citation_network(paper_id, depth)
            return network

        @self.app.post("/projects")
        async def create_research_project(request: CreateProjectRequest, principal_investigator_id: str):
            """Create new research project"""
            db = self.SessionLocal()
            try:
                project = ResearchProjectDB(
                    id=str(uuid.uuid4()),
                    title=request.title,
                    description=request.description,
                    research_questions=json.dumps(request.research_questions),
                    methodology=request.methodology,
                    principal_investigator_id=principal_investigator_id,
                    team_members=json.dumps(request.team_members),
                    status="planning",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )

                db.add(project)
                db.commit()

                return {"project_id": project.id, "message": "Research project created successfully"}

            finally:
                db.close()

        @self.app.get("/search/academic")
        async def search_academic(query: str, source: str = "arxiv", max_results: int = 10):
            """Search academic databases"""
            if source == "arxiv":
                results = await self.academic_search.search_arxiv(query, max_results)
            elif source == "scholar":
                results = await self.academic_search.search_google_scholar(query, max_results)
            else:
                raise HTTPException(status_code=400, detail="Invalid search source")

            return {"source": source, "results": results}

        @self.app.post("/import/arxiv/{arxiv_id}")
        async def import_from_arxiv(arxiv_id: str, user_id: str):
            """Import paper from arXiv"""
            paper_id = await self.academic_search.import_from_arxiv(arxiv_id, user_id)

            if paper_id:
                return {"paper_id": paper_id, "message": "Paper imported successfully"}
            else:
                raise HTTPException(status_code=400, detail="Failed to import paper")

        @self.app.post("/import/bibtex")
        async def import_bibtex(bibtex_content: str, user_id: str):
            """Import papers from BibTeX"""
            if not self.citation_manager:
                self.citation_manager = CitationManager(self.SessionLocal())

            paper_ids = self.citation_manager.import_bibtex(bibtex_content, user_id)

            return {
                "imported_count": len(paper_ids),
                "paper_ids": paper_ids,
                "message": f"Successfully imported {len(paper_ids)} papers"
            }

        @self.app.get("/export/bibtex")
        async def export_bibtex(paper_ids: str):
            """Export papers to BibTeX format"""
            if not self.citation_manager:
                self.citation_manager = CitationManager(self.SessionLocal())

            ids = paper_ids.split(",")
            bibtex_content = self.citation_manager.export_bibtex(ids)

            return {"bibtex": bibtex_content}

    async def _process_uploaded_paper(self, file_path: str, paper_data: Dict[str, Any], uploaded_by: str):
        """Process uploaded paper in background"""
        try:
            # Process paper
            processing_result = await self.paper_processor.process_paper(file_path, paper_data)

            if processing_result["processing_status"] == "completed":
                # Save to database
                db = self.SessionLocal()
                try:
                    paper = ResearchPaperDB(
                        id=str(uuid.uuid4()),
                        title=paper_data["title"],
                        abstract=paper_data["abstract"],
                        authors=json.dumps(paper_data["authors"]),
                        paper_type=paper_data["paper_type"],
                        research_areas=json.dumps(paper_data["research_areas"]),
                        keywords=json.dumps(paper_data["keywords"]),
                        file_path=processing_result["file_path"],
                        page_count=processing_result["metadata"].get("page_count", 0),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )

                    # Add additional metadata from processing
                    if processing_result.get("summary"):
                        paper.summary = processing_result["summary"]
                    if processing_result.get("references"):
                        paper.references = json.dumps(processing_result["references"])

                    db.add(paper)
                    db.commit()

                    logger.info(f"Successfully processed and saved paper: {paper.id}")

                finally:
                    db.close()

            # Cleanup temporary file
            Path(file_path).unlink(missing_ok=True)

        except Exception as e:
            logger.error(f"Paper processing failed: {e}")
            # Cleanup temporary file
            Path(file_path).unlink(missing_ok=True)

    def _validate_paper_file(self, file: UploadFile) -> bool:
        """Validate uploaded paper file"""
        allowed_extensions = self.paper_processor.config["supported_formats"]
        max_size_mb = self.paper_processor.config["max_file_size_mb"]

        if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
            return False

        if file.size and file.size > max_size_mb * 1024 * 1024:
            return False

        return True

    def run(self, host: str = "0.0.0.0", port: int = 8006):
        """Run the research library server"""
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)

# Main execution
if __name__ == "__main__":
    app = ResearchLibraryApp()
    app.run()