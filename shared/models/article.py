"""
Article SQLAlchemy model for SEO Automation Platform.
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String,
    Text,
    Integer,
    Float,
    DateTime,
    Enum,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class ArticleStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    GENERATED = "generated"
    OPTIMIZING = "optimizing"
    OPTIMIZED = "optimized"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    ARCHIVED = "archived"


class ArticleType(str, enum.Enum):
    STANDARD = "standard"
    COMPARISON = "comparison"
    TUTORIAL = "tutorial"
    LISTICLE = "listicle"
    CASE_STUDY = "case_study"
    NEWS = "news"


class Article(Base):
    """
    Represents an SEO article in the automation pipeline.
    """
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Keyword targeting
    keywords: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # List of target keywords
    primary_keyword: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(
        Enum(ArticleStatus),
        default=ArticleStatus.PENDING,
        nullable=False,
        index=True,
    )
    article_type: Mapped[str] = mapped_column(
        Enum(ArticleType),
        default=ArticleType.STANDARD,
        nullable=False,
    )

    # SEO metrics
    seo_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    readability_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    keyword_density: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Competitor targeting
    competitor_target: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Publishing info
    published_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    github_sha: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Schema markup
    schema_markup: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Internal links
    internal_links: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Headings structure
    headings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Performance tracking
    organic_clicks: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    impressions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    average_position: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ctr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Generation metadata
    generation_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    generation_prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    generation_completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<Article id={self.id} title='{self.title[:50]}' status={self.status}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "meta_description": self.meta_description,
            "keywords": self.keywords,
            "primary_keyword": self.primary_keyword,
            "status": self.status,
            "article_type": self.article_type,
            "seo_score": self.seo_score,
            "word_count": self.word_count,
            "readability_score": self.readability_score,
            "competitor_target": self.competitor_target,
            "published_url": self.published_url,
            "organic_clicks": self.organic_clicks,
            "impressions": self.impressions,
            "average_position": self.average_position,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
        }
