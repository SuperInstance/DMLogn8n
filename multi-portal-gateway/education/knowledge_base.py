#!/usr/bin/env python3
"""
DMLogn8n Knowledge Base - Comprehensive Knowledge Base and Wiki System
Advanced wiki-style knowledge management with collaborative editing, version control, and intelligent search
"""

import asyncio
import json
import logging
import hashlib
import difflib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Set
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import uuid
import yaml
import markdown
from bs4 import BeautifulSoup
import aiofiles
import aiohttp
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Boolean, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
import redis
from whoosh import fields, index
from whoosh.analysis import StandardAnalyzer
from whoosh.query import Query, Term, And, Or
from whoosh.qparser import QueryParser
import git

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('knowledge_base.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

Base = declarative_base()

class ArticleType(Enum):
    ARTICLE = "article"
    TUTORIAL = "tutorial"
    REFERENCE = "reference"
    GUIDE = "guide"
    FAQ = "faq"
    NEWS = "news"
    ANNOUNCEMENT = "announcement"
    API_DOC = "api_doc"
    EXAMPLE = "example"

class ArticleStatus(Enum):
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"

class ChangeType(Enum):
    CREATE = "create"
    EDIT = "edit"
    DELETE = "delete"
    RESTORE = "restore"
    MOVE = "move"

@dataclass
class KnowledgeArticle:
    id: str
    title: str
    slug: str
    content: str
    excerpt: str
    article_type: ArticleType
    status: ArticleStatus
    author_id: str
    category_id: Optional[str]
    tags: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    view_count: int
    edit_count: int
    last_editor_id: str
    parent_id: Optional[str] = None
    children_ids: List[str] = None

@dataclass
class ArticleVersion:
    id: str
    article_id: str
    version_number: int
    title: str
    content: str
    change_summary: str
    author_id: str
    created_at: datetime
    content_diff: str
    word_count: int
    character_count: int

@dataclass
class Category:
    id: str
    name: str
    slug: str
    description: str
    parent_id: Optional[str]
    icon: str
    color: str
    sort_order: int
    article_count: int
    created_at: datetime

class ArticleDB(Base):
    __tablename__ = "knowledge_articles"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    content = Column(Text, nullable=False)
    excerpt = Column(Text)
    article_type = Column(String, nullable=False)
    status = Column(String, default=ArticleStatus.DRAFT.value)
    author_id = Column(String, ForeignKey("users.id"), nullable=False)
    category_id = Column(String, ForeignKey("knowledge_categories.id"))
    tags = Column(Text)  # JSON string
    metadata = Column(Text)  # JSON string
    view_count = Column(Integer, default=0)
    edit_count = Column(Integer, default=0)
    last_editor_id = Column(String, ForeignKey("users.id"))
    parent_id = Column(String, ForeignKey("knowledge_articles.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    author = relationship("User", foreign_keys=[author_id])
    last_editor = relationship("User", foreign_keys=[last_editor_id])
    category = relationship("CategoryDB", foreign_keys=[category_id])
    versions = relationship("ArticleVersionDB", back_populates="article")
    children = relationship("ArticleDB", backref="parent", remote_side=[id])

class ArticleVersionDB(Base):
    __tablename__ = "article_versions"

    id = Column(String, primary_key=True)
    article_id = Column(String, ForeignKey("knowledge_articles.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    change_summary = Column(Text)
    author_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    content_diff = Column(Text)
    word_count = Column(Integer, default=0)
    character_count = Column(Integer, default=0)

    # Relationships
    article = relationship("ArticleDB", back_populates="versions")
    author = relationship("User")

class CategoryDB(Base):
    __tablename__ = "knowledge_categories"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    description = Column(Text)
    parent_id = Column(String, ForeignKey("knowledge_categories.id"))
    icon = Column(String)
    color = Column(String)
    sort_order = Column(Integer, default=0)
    article_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    parent = relationship("CategoryDB", remote_side=[id])
    children = relationship("CategoryDB")

class SearchIndex:
    """Full-text search indexing using Whoosh"""

    def __init__(self, index_dir: str = "search_index"):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(exist_ok=True)
        self.analyzer = StandardAnalyzer()
        self.index = self._create_or_open_index()

    def _create_or_open_index(self):
        """Create or open the search index"""
        schema = fields.Schema(
            id=fields.ID(stored=True),
            title=fields.TEXT(analyzer=self.analyzer, stored=True),
            content=fields.TEXT(analyzer=self.analyzer, stored=True),
            article_type=fields.ID(stored=True),
            tags=fields.KEYWORD(stored=True, commas=True),
            category=fields.ID(stored=True),
            author=fields.ID(stored=True),
            created_at=fields.DATETIME(stored=True),
            updated_at=fields.DATETIME(stored=True),
            view_count=fields.NUMERIC(stored=True),
            excerpt=fields.TEXT(stored=True)
        )

        if index.exists_in(str(self.index_dir)):
            return index.open_dir(str(self.index_dir))
        else:
            return index.create_in(str(self.index_dir), schema)

    def add_article(self, article: KnowledgeArticle):
        """Add article to search index"""
        writer = self.index.writer()

        writer.add_document(
            id=article.id,
            title=article.title,
            content=article.content,
            article_type=article.article_type.value,
            tags=",".join(article.tags),
            category=article.category_id or "",
            author=article.author_id,
            created_at=article.created_at,
            updated_at=article.updated_at,
            view_count=article.view_count,
            excerpt=article.excerpt
        )

        writer.commit()

    def update_article(self, article: KnowledgeArticle):
        """Update article in search index"""
        writer = self.index.writer()

        # Delete existing document
        writer.delete_by_term('id', article.id)

        # Add updated document
        writer.add_document(
            id=article.id,
            title=article.title,
            content=article.content,
            article_type=article.article_type.value,
            tags=",".join(article.tags),
            category=article.category_id or "",
            author=article.author_id,
            created_at=article.created_at,
            updated_at=article.updated_at,
            view_count=article.view_count,
            excerpt=article.excerpt
        )

        writer.commit()

    def delete_article(self, article_id: str):
        """Remove article from search index"""
        writer = self.index.writer()
        writer.delete_by_term('id', article_id)
        writer.commit()

    def search(self, query_str: str, limit: int = 20, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search articles"""
        with self.index.searcher() as searcher:
            # Parse query
            parser = QueryParser("content", self.index.schema)
            query = parser.parse(query_str)

            # Apply filters
            if filters:
                filter_terms = []
                if filters.get("article_type"):
                    filter_terms.append(Term("article_type", filters["article_type"]))
                if filters.get("category"):
                    filter_terms.append(Term("category", filters["category"]))
                if filters.get("tags"):
                    tag_terms = [Term("tags", tag) for tag in filters["tags"]]
                    filter_terms.extend(tag_terms)

                if filter_terms:
                    if len(filter_terms) == 1:
                        query = And([query, filter_terms[0]])
                    else:
                        query = And([query] + filter_terms)

            # Execute search
            results = searcher.search(query, limit=limit)

            search_results = []
            for hit in results:
                search_results.append({
                    "id": hit["id"],
                    "title": hit["title"],
                    "excerpt": hit.get("excerpt", ""),
                    "article_type": hit["article_type"],
                    "tags": hit["tags"].split(",") if hit["tags"] else [],
                    "category": hit["category"],
                    "author": hit["author"],
                    "created_at": hit["created_at"],
                    "updated_at": hit["updated_at"],
                    "view_count": hit["view_count"],
                    "score": hit.score
                })

            return search_results

class WikiParser:
    """Enhanced wiki markup parser with extensions"""

    def __init__(self):
        self.markdown_extensions = [
            'markdown.extensions.extra',
            'markdown.extensions.codehilite',
            'markdown.extensions.toc',
            'markdown.extensions.tables',
            'markdown.extensions.fenced_code',
            'markdown.extensions.footnotes',
            'markdown.extensions.attr_list',
            'markdown.extensions.def_list',
            'markdown.extensions.abbr',
            'markdown.extensions.md_in_html'
        ]

    def parse_content(self, content: str, article_type: str = "article") -> Dict[str, Any]:
        """Parse wiki content and extract metadata"""
        # Parse YAML frontmatter
        frontmatter, content_body = self._extract_frontmatter(content)

        # Parse markdown content
        html_content = markdown.markdown(
            content_body,
            extensions=self.markdown_extensions,
            extension_configs={
                'codehilite': {
                    'css_class': 'highlight',
                    'use_pygments': True
                }
            }
        )

        # Extract table of contents
        toc = self._extract_toc(html_content)

        # Extract links
        internal_links, external_links = self._extract_links(content_body)

        # Extract headings
        headings = self._extract_headings(html_content)

        # Generate excerpt
        excerpt = self._generate_excerpt(content_body)

        # Process wiki-specific syntax
        html_content = self._process_wiki_syntax(html_content)

        return {
            "frontmatter": frontmatter,
            "content": content_body,
            "html_content": html_content,
            "toc": toc,
            "internal_links": internal_links,
            "external_links": external_links,
            "headings": headings,
            "excerpt": excerpt,
            "word_count": len(content_body.split()),
            "character_count": len(content_body),
            "reading_time_minutes": max(1, len(content_body.split()) // 200)  # Assuming 200 words per minute
        }

    def _extract_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """Extract YAML frontmatter from content"""
        if content.startswith('---\n'):
            try:
                end_index = content.find('\n---\n', 4)
                if end_index != -1:
                    frontmatter_str = content[4:end_index]
                    frontmatter = yaml.safe_load(frontmatter_str)
                    content_body = content[end_index + 5:]
                    return frontmatter, content_body
            except yaml.YAMLError:
                pass

        return {}, content

    def _extract_toc(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract table of contents from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        toc = []

        for i, heading in enumerate(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])):
            level = int(heading.name[1])
            text = heading.get_text().strip()
            anchor = self._generate_anchor(text)

            toc.append({
                "level": level,
                "text": text,
                "anchor": anchor,
                "id": f"heading-{i}"
            })

        return toc

    def _extract_links(self, content: str) -> Tuple[List[str], List[str]]:
        """Extract internal and external links from content"""
        internal_links = []
        external_links = []

        # Markdown links
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        matches = re.findall(link_pattern, content)

        for text, url in matches:
            if url.startswith(('http://', 'https://')):
                external_links.append(url)
            elif url.startswith(('/', './')):
                internal_links.append(url)

        # Wiki links [[Page Name]]
        wiki_link_pattern = r'\[\[([^\]]+)\]\]'
        wiki_matches = re.findall(wiki_link_pattern, content)
        internal_links.extend(wiki_matches)

        return list(set(internal_links)), list(set(external_links))

    def _extract_headings(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract headings from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        headings = []

        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            level = int(heading.name[1])
            text = heading.get_text().strip()
            anchor = self._generate_anchor(text)

            headings.append({
                "level": level,
                "text": text,
                "anchor": anchor
            })

        return headings

    def _generate_excerpt(self, content: str, max_length: int = 200) -> str:
        """Generate excerpt from content"""
        # Remove markdown formatting
        plain_text = re.sub(r'[#*`\[\]]', '', content)
        plain_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', plain_text)

        # Get first paragraph
        paragraphs = plain_text.split('\n\n')
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if len(paragraph) > 50:  # Skip very short paragraphs
                if len(paragraph) <= max_length:
                    return paragraph
                else:
                    return paragraph[:max_length].rsplit(' ', 1)[0] + '...'

        return plain_text[:max_length].rsplit(' ', 1)[0] + '...' if len(plain_text) > max_length else plain_text

    def _process_wiki_syntax(self, html_content: str) -> str:
        """Process wiki-specific syntax"""
        # Process wiki links [[Page Name]]
        html_content = re.sub(
            r'\[\[([^\]]+)\]\]',
            r'<a href="/wiki/\1" class="wiki-link">\1</a>',
            html_content
        )

        # Process category links [[Category:Name]]
        html_content = re.sub(
            r'\[\[Category:([^\]]+)\]\]',
            r'<span class="category-link">\1</span>',
            html_content
        )

        # Process template syntax {{TemplateName}}
        html_content = re.sub(
            r'\{\{([^}]+)\}\}',
            r'<span class="template">\1</span>',
            html_content
        )

        return html_content

    def _generate_anchor(self, text: str) -> str:
        """Generate URL anchor from heading text"""
        # Convert to lowercase, remove special characters, replace spaces with hyphens
        anchor = re.sub(r'[^\w\s-]', '', text.lower())
        anchor = re.sub(r'[-\s]+', '-', anchor)
        return anchor.strip('-')

class VersionControl:
    """Version control system for articles"""

    def __init__(self, db_session: Session, repo_path: str = "wiki_repo"):
        self.db = db_session
        self.repo_path = Path(repo_path)
        self.repo_path.mkdir(exist_ok=True)
        self._init_repository()

    def _init_repository(self):
        """Initialize Git repository"""
        try:
            self.repo = git.Repo(self.repo_path)
        except git.exc.InvalidGitRepositoryError:
            self.repo = git.Repo.init(self.repo_path)
            # Configure git user
            with self.repo.config_writer() as config:
                config.set_value('user', 'name', 'DMLogn8n Wiki')
                config.set_value('user', 'email', 'wiki@dmlogn8n.com')

    def create_version(self, article: KnowledgeArticle, change_summary: str = "") -> ArticleVersion:
        """Create a new version of an article"""
        # Get current version number
        latest_version = self.db.query(ArticleVersionDB).filter(
            ArticleVersionDB.article_id == article.id
        ).order_by(ArticleVersionDB.version_number.desc()).first()

        version_number = (latest_version.version_number + 1) if latest_version else 1

        # Calculate diff with previous version
        content_diff = ""
        if latest_version:
            content_diff = self._calculate_diff(latest_version.content, article.content)

        # Create version record
        version_db = ArticleVersionDB(
            id=str(uuid.uuid4()),
            article_id=article.id,
            version_number=version_number,
            title=article.title,
            content=article.content,
            change_summary=change_summary,
            author_id=article.last_editor_id,
            content_diff=content_diff,
            word_count=len(article.content.split()),
            character_count=len(article.content)
        )

        self.db.add(version_db)

        # Commit to Git
        self._commit_to_git(article, version_number, change_summary)

        return ArticleVersion(
            id=version_db.id,
            article_id=version_db.article_id,
            version_number=version_db.version_number,
            title=version_db.title,
            content=version_db.content,
            change_summary=version_db.change_summary,
            author_id=version_db.author_id,
            created_at=version_db.created_at,
            content_diff=version_db.content_diff,
            word_count=version_db.word_count,
            character_count=version_db.character_count
        )

    def _calculate_diff(self, old_content: str, new_content: str) -> str:
        """Calculate unified diff between content versions"""
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile='old',
            tofile='new',
            lineterm=''
        )

        return ''.join(diff)

    def _commit_to_git(self, article: KnowledgeArticle, version_number: int, change_summary: str):
        """Commit article version to Git repository"""
        try:
            # Write article to file
            article_file = self.repo_path / f"{article.slug}.md"
            with open(article_file, 'w', encoding='utf-8') as f:
                f.write(article.content)

            # Add to git
            self.repo.index.add([str(article_file)])

            # Commit changes
            commit_message = f"Update {article.title} - v{version_number}"
            if change_summary:
                commit_message += f"\n\n{change_summary}"

            self.repo.index.commit(commit_message)

        except Exception as e:
            logger.error(f"Git commit failed for article {article.id}: {e}")

    def get_version_history(self, article_id: str, limit: int = 50) -> List[ArticleVersion]:
        """Get version history for an article"""
        versions_db = self.db.query(ArticleVersionDB).filter(
            ArticleVersionDB.article_id == article_id
        ).order_by(ArticleVersionDB.version_number.desc()).limit(limit).all()

        return [
            ArticleVersion(
                id=v.id,
                article_id=v.article_id,
                version_number=v.version_number,
                title=v.title,
                content=v.content,
                change_summary=v.change_summary,
                author_id=v.author_id,
                created_at=v.created_at,
                content_diff=v.content_diff,
                word_count=v.word_count,
                character_count=v.character_count
            )
            for v in versions_db
        ]

    def restore_version(self, article_id: str, version_number: int) -> KnowledgeArticle:
        """Restore article to a specific version"""
        version = self.db.query(ArticleVersionDB).filter(
            ArticleVersionDB.article_id == article_id,
            ArticleVersionDB.version_number == version_number
        ).first()

        if not version:
            raise ValueError(f"Version {version_number} not found for article {article_id}")

        # Update article with version content
        article = self.db.query(ArticleDB).filter(ArticleDB.id == article_id).first()
        if not article:
            raise ValueError(f"Article {article_id} not found")

        article.title = version.title
        article.content = version.content
        article.updated_at = datetime.utcnow()
        article.edit_count += 1

        # Create new version for the restore
        self.create_version(
            KnowledgeArticle(
                id=article.id,
                title=article.title,
                slug=article.slug,
                content=article.content,
                excerpt=article.excerpt,
                article_type=ArticleType(article.article_type),
                status=ArticleStatus(article.status),
                author_id=article.author_id,
                category_id=article.category_id,
                tags=json.loads(article.tags or "[]"),
                metadata=json.loads(article.metadata or "{}"),
                created_at=article.created_at,
                updated_at=article.updated_at,
                view_count=article.view_count,
                edit_count=article.edit_count,
                last_editor_id=article.last_editor_id
            ),
            f"Restored to version {version_number}"
        )

        self.db.commit()

        return self._db_to_model(article)

    def _db_to_model(self, article_db: ArticleDB) -> KnowledgeArticle:
        """Convert database model to dataclass"""
        return KnowledgeArticle(
            id=article_db.id,
            title=article_db.title,
            slug=article_db.slug,
            content=article_db.content,
            excerpt=article_db.excerpt or "",
            article_type=ArticleType(article_db.article_type),
            status=ArticleStatus(article_db.status),
            author_id=article_db.author_id,
            category_id=article_db.category_id,
            tags=json.loads(article_db.tags or "[]"),
            metadata=json.loads(article_db.metadata or "{}"),
            created_at=article_db.created_at,
            updated_at=article_db.updated_at,
            view_count=article_db.view_count,
            edit_count=article_db.edit_count,
            last_editor_id=article_db.last_editor_id or article_db.author_id
        )

class ContentRenderer:
    """Enhanced content rendering with multiple output formats"""

    def __init__(self):
        self.parser = WikiParser()
        self.template_env = self._setup_templates()

    def _setup_templates(self):
        """Setup Jinja2 templates"""
        template_dir = Path("templates/knowledge_base")
        if template_dir.exists():
            from jinja2 import Environment, FileSystemLoader
            return Environment(loader=FileSystemLoader(str(template_dir)))
        return None

    def render_article(self, article: KnowledgeArticle, format: str = "html") -> Dict[str, Any]:
        """Render article in specified format"""
        parsed = self.parser.parse_content(article.content, article.article_type.value)

        if format == "html":
            return self._render_html(article, parsed)
        elif format == "json":
            return self._render_json(article, parsed)
        elif format == "markdown":
            return self._render_markdown(article, parsed)
        elif format == "pdf":
            return self._render_pdf(article, parsed)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _render_html(self, article: KnowledgeArticle, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Render article as HTML"""
        html_content = parsed["html_content"]

        # Add table of contents
        if parsed["toc"]:
            toc_html = self._generate_toc_html(parsed["toc"])
            html_content = toc_html + html_content

        # Process internal links
        html_content = self._process_internal_links(html_content)

        # Add syntax highlighting
        html_content = self._add_syntax_highlighting(html_content)

        return {
            "content": html_content,
            "toc": parsed["toc"],
            "metadata": {
                "word_count": parsed["word_count"],
                "character_count": parsed["character_count"],
                "reading_time_minutes": parsed["reading_time_minutes"],
                "internal_links": parsed["internal_links"],
                "external_links": parsed["external_links"],
                "headings": parsed["headings"]
            }
        }

    def _render_json(self, article: KnowledgeArticle, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Render article as JSON"""
        return {
            "id": article.id,
            "title": article.title,
            "slug": article.slug,
            "content": parsed["content"],
            "excerpt": article.excerpt,
            "article_type": article.article_type.value,
            "status": article.status.value,
            "author_id": article.author_id,
            "category_id": article.category_id,
            "tags": article.tags,
            "metadata": article.metadata,
            "created_at": article.created_at.isoformat(),
            "updated_at": article.updated_at.isoformat(),
            "view_count": article.view_count,
            "edit_count": article.edit_count,
            "parsed_content": parsed
        }

    def _render_markdown(self, article: KnowledgeArticle, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Render article as Markdown"""
        return {
            "content": parsed["content"],
            "frontmatter": parsed["frontmatter"],
            "metadata": {
                "word_count": parsed["word_count"],
                "character_count": parsed["character_count"],
                "reading_time_minutes": parsed["reading_time_minutes"]
            }
        }

    def _render_pdf(self, article: KnowledgeArticle, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Render article as PDF (placeholder)"""
        # In production, this would use a proper PDF generation library
        return {
            "content": "PDF generation not implemented",
            "metadata": {
                "title": article.title,
                "author": article.author_id
            }
        }

    def _generate_toc_html(self, toc: List[Dict[str, Any]]) -> str:
        """Generate HTML table of contents"""
        if not toc:
            return ""

        toc_html = '<div class="table-of-contents">\n<h3>Table of Contents</h3>\n<ul>\n'

        for item in toc:
            indent = '  ' * (item["level"] - 1)
            toc_html += f'{indent}<li><a href="#{item["anchor"]}">{item["text"]}</a></li>\n'

        toc_html += '</ul>\n</div>\n'

        return toc_html

    def _process_internal_links(self, html_content: str) -> str:
        """Process internal wiki links"""
        # Convert [[Page Name]] to proper links
        html_content = re.sub(
            r'\[\[([^\]]+)\]\]',
            r'<a href="/wiki/\1" class="internal-link">\1</a>',
            html_content
        )

        return html_content

    def _add_syntax_highlighting(self, html_content: str) -> str:
        """Add syntax highlighting to code blocks"""
        # This would integrate with a syntax highlighting library
        # For now, return content as-is
        return html_content

class KnowledgeManager:
    """Main knowledge base management system"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)

        # Initialize database
        self.engine = create_engine('sqlite:///knowledge_base.db')
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Initialize components
        self.search_index = SearchIndex(self.config.get("search_index_dir", "search_index"))
        self.parser = WikiParser()
        self.version_control = VersionControl(self.SessionLocal())
        self.renderer = ContentRenderer()

        # Initialize Redis for caching
        self.redis_client = redis.Redis(
            host=self.config.get("redis_host", "localhost"),
            port=self.config.get("redis_port", 6379),
            db=self.config.get("redis_db", 2)
        )

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            "search_index_dir": "search_index",
            "wiki_repo": "wiki_repo",
            "redis_host": "localhost",
            "redis_port": 6379,
            "redis_db": 2,
            "cache_ttl": 3600,
            "max_article_revisions": 100
        }

        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)

        return default_config

    async def create_article(self, article_data: Dict[str, Any], author_id: str) -> str:
        """Create a new knowledge article"""
        db = self.SessionLocal()

        try:
            # Generate slug
            slug = self._generate_slug(article_data["title"])

            # Parse content
            parsed = self.parser.parse_content(article_data["content"])

            # Create article
            article_db = ArticleDB(
                id=str(uuid.uuid4()),
                title=article_data["title"],
                slug=slug,
                content=article_data["content"],
                excerpt=parsed["excerpt"],
                article_type=article_data["article_type"],
                status=article_data.get("status", "draft"),
                author_id=author_id,
                category_id=article_data.get("category_id"),
                tags=json.dumps(article_data.get("tags", [])),
                metadata=json.dumps(article_data.get("metadata", {})),
                last_editor_id=author_id,
                parent_id=article_data.get("parent_id")
            )

            db.add(article_db)
            db.commit()

            # Create initial version
            article = self._db_to_model(article_db)
            self.version_control.create_version(article, "Initial version")

            # Add to search index
            self.search_index.add_article(article)

            # Update category article count
            if article.category_id:
                self._update_category_count(db, article.category_id)

            return article.id

        finally:
            db.close()

    async def update_article(self, article_id: str, update_data: Dict[str, Any], editor_id: str, change_summary: str = "") -> bool:
        """Update an existing article"""
        db = self.SessionLocal()

        try:
            article_db = db.query(ArticleDB).filter(ArticleDB.id == article_id).first()
            if not article_db:
                return False

            # Update fields
            if "title" in update_data:
                article_db.title = update_data["title"]
                article_db.slug = self._generate_slug(update_data["title"])

            if "content" in update_data:
                article_db.content = update_data["content"]
                parsed = self.parser.parse_content(update_data["content"])
                article_db.excerpt = parsed["excerpt"]

            if "article_type" in update_data:
                article_db.article_type = update_data["article_type"]

            if "status" in update_data:
                article_db.status = update_data["status"]

            if "category_id" in update_data:
                old_category = article_db.category_id
                article_db.category_id = update_data["category_id"]
                # Update category counts
                if old_category:
                    self._update_category_count(db, old_category)
                if update_data["category_id"]:
                    self._update_category_count(db, update_data["category_id"])

            if "tags" in update_data:
                article_db.tags = json.dumps(update_data["tags"])

            if "metadata" in update_data:
                article_db.metadata = json.dumps(update_data["metadata"])

            article_db.last_editor_id = editor_id
            article_db.updated_at = datetime.utcnow()
            article_db.edit_count += 1

            db.commit()

            # Create new version
            article = self._db_to_model(article_db)
            self.version_control.create_version(article, change_summary)

            # Update search index
            self.search_index.update_article(article)

            return True

        finally:
            db.close()

    async def get_article(self, article_id: str, increment_view: bool = True) -> Optional[Dict[str, Any]]:
        """Get article by ID"""
        # Check cache first
        cache_key = f"article:{article_id}"
        cached = self.redis_client.get(cache_key)
        if cached:
            article_data = json.loads(cached)
            if increment_view:
                await self._increment_view_count(article_id)
            return article_data

        db = self.SessionLocal()
        try:
            article_db = db.query(ArticleDB).filter(ArticleDB.id == article_id).first()
            if not article_db:
                return None

            article = self._db_to_model(article_db)

            # Render content
            rendered = self.renderer.render_article(article)

            article_data = {
                **asdict(article),
                "rendered_content": rendered
            }

            # Cache the result
            self.redis_client.setex(
                cache_key,
                self.config["cache_ttl"],
                json.dumps(article_data, default=str)
            )

            if increment_view:
                await self._increment_view_count(article_id)

            return article_data

        finally:
            db.close()

    async def search_articles(self, query: str, filters: Dict[str, Any] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Search articles"""
        search_results = self.search_index.search(query, limit, filters)

        # Enrich with additional data
        db = self.SessionLocal()
        try:
            enriched_results = []
            for result in search_results:
                article_db = db.query(ArticleDB).filter(ArticleDB.id == result["id"]).first()
                if article_db:
                    enriched_results.append({
                        **result,
                        "slug": article_db.slug,
                        "excerpt": article_db.excerpt,
                        "tags": json.loads(article_db.tags or "[]"),
                        "author_id": article_db.author_id
                    })

            return enriched_results

        finally:
            db.close()

    async def get_article_history(self, article_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get article version history"""
        versions = self.version_control.get_version_history(article_id, limit)

        return [
            {
                "id": v.id,
                "version_number": v.version_number,
                "title": v.title,
                "change_summary": v.change_summary,
                "author_id": v.author_id,
                "created_at": v.created_at,
                "word_count": v.word_count,
                "character_count": v.character_count
            }
            for v in versions
        ]

    async def restore_article_version(self, article_id: str, version_number: int, restorer_id: str) -> bool:
        """Restore article to specific version"""
        try:
            article = self.version_control.restore_version(article_id, version_number)

            # Update search index
            self.search_index.update_article(article)

            # Clear cache
            cache_key = f"article:{article_id}"
            self.redis_client.delete(cache_key)

            return True

        except Exception as e:
            logger.error(f"Failed to restore article {article_id} to version {version_number}: {e}")
            return False

    def _generate_slug(self, title: str) -> str:
        """Generate URL slug from title"""
        # Convert to lowercase and replace spaces with hyphens
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)

        # Ensure uniqueness
        base_slug = slug.strip('-')
        counter = 1
        final_slug = base_slug

        db = self.SessionLocal()
        try:
            while db.query(ArticleDB).filter(ArticleDB.slug == final_slug).first():
                final_slug = f"{base_slug}-{counter}"
                counter += 1
        finally:
            db.close()

        return final_slug

    def _db_to_model(self, article_db: ArticleDB) -> KnowledgeArticle:
        """Convert database model to dataclass"""
        return KnowledgeArticle(
            id=article_db.id,
            title=article_db.title,
            slug=article_db.slug,
            content=article_db.content,
            excerpt=article_db.excerpt or "",
            article_type=ArticleType(article_db.article_type),
            status=ArticleStatus(article_db.status),
            author_id=article_db.author_id,
            category_id=article_db.category_id,
            tags=json.loads(article_db.tags or "[]"),
            metadata=json.loads(article_db.metadata or "{}"),
            created_at=article_db.created_at,
            updated_at=article_db.updated_at,
            view_count=article_db.view_count,
            edit_count=article_db.edit_count,
            last_editor_id=article_db.last_editor_id or article_db.author_id
        )

    async def _increment_view_count(self, article_id: str):
        """Increment article view count"""
        db = self.SessionLocal()
        try:
            article = db.query(ArticleDB).filter(ArticleDB.id == article_id).first()
            if article:
                article.view_count += 1
                db.commit()
        finally:
            db.close()

    def _update_category_count(self, db: Session, category_id: str):
        """Update category article count"""
        count = db.query(ArticleDB).filter(
            ArticleDB.category_id == category_id,
            ArticleDB.status == ArticleStatus.PUBLISHED.value
        ).count()

        category = db.query(CategoryDB).filter(CategoryDB.id == category_id).first()
        if category:
            category.article_count = count
            db.commit()

# API Models
class CreateArticleRequest(BaseModel):
    title: str
    content: str
    article_type: str
    category_id: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    parent_id: Optional[str] = None

class UpdateArticleRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    article_type: Optional[str] = None
    status: Optional[str] = None
    category_id: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class SearchRequest(BaseModel):
    query: str
    filters: Dict[str, Any] = {}
    limit: int = 20

class KnowledgeBaseApp:
    """Main Knowledge Base Application"""

    def __init__(self):
        self.app = FastAPI(title="DMLogn8n Knowledge Base", version="1.0.0")
        self.setup_middleware()
        self.setup_routes()

        # Initialize knowledge manager
        self.knowledge_manager = KnowledgeManager()

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
            return {"message": "DMLogn8n Knowledge Base API"}

        @self.app.post("/articles")
        async def create_article(request: CreateArticleRequest, author_id: str):
            """Create new article"""
            article_id = await self.knowledge_manager.create_article(
                request.dict(),
                author_id
            )
            return {"article_id": article_id, "message": "Article created successfully"}

        @self.app.put("/articles/{article_id}")
        async def update_article(
            article_id: str,
            request: UpdateArticleRequest,
            editor_id: str,
            change_summary: str = ""
        ):
            """Update article"""
            success = await self.knowledge_manager.update_article(
                article_id,
                request.dict(exclude_unset=True),
                editor_id,
                change_summary
            )

            if not success:
                raise HTTPException(status_code=404, detail="Article not found")

            return {"message": "Article updated successfully"}

        @self.app.get("/articles/{article_id}")
        async def get_article(article_id: str, view: bool = True):
            """Get article by ID"""
            article = await self.knowledge_manager.get_article(article_id, view)
            if not article:
                raise HTTPException(status_code=404, detail="Article not found")
            return article

        @self.app.post("/search")
        async def search_articles(request: SearchRequest):
            """Search articles"""
            results = await self.knowledge_manager.search_articles(
                request.query,
                request.filters,
                request.limit
            )
            return {"results": results, "total": len(results)}

        @self.app.get("/articles/{article_id}/history")
        async def get_article_history(article_id: str, limit: int = 50):
            """Get article version history"""
            history = await self.knowledge_manager.get_article_history(article_id, limit)
            return {"history": history}

        @self.app.post("/articles/{article_id}/restore/{version_number}")
        async def restore_article_version(article_id: str, version_number: int, restorer_id: str):
            """Restore article to specific version"""
            success = await self.knowledge_manager.restore_article_version(
                article_id,
                version_number,
                restorer_id
            )

            if not success:
                raise HTTPException(status_code=400, detail="Failed to restore version")

            return {"message": "Article restored successfully"}

    def run(self, host: str = "0.0.0.0", port: int = 8002):
        """Run the knowledge base server"""
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)

# Main execution
if __name__ == "__main__":
    app = KnowledgeBaseApp()
    app.run()