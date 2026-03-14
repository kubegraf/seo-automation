"""
Competitor SQLAlchemy model for SEO Automation Platform.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String,
    Integer,
    Float,
    DateTime,
    JSON,
    Boolean,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Competitor(Base):
    """
    Represents a competitor with their SEO data and keyword gaps.
    """
    __tablename__ = "competitors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)

    # Keyword data
    keywords: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # Their known keywords
    gap_keywords: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # Keywords we're missing

    # Traffic estimates
    traffic_estimate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    domain_authority: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0-100
    backlinks_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Content analysis
    content_gaps: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    article_ideas: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    their_strengths: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    their_weaknesses: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    recommended_strategy: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)

    # SERP overlap
    serp_overlap_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    shared_keywords: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Comparison articles
    has_comparison_article: Mapped[bool] = mapped_column(Boolean, default=False)
    comparison_article_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Analysis status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    analysis_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_analyzed: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<Competitor id={self.id} name='{self.name}' domain='{self.domain}'>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "domain": self.domain,
            "keywords": self.keywords,
            "gap_keywords": self.gap_keywords,
            "traffic_estimate": self.traffic_estimate,
            "domain_authority": self.domain_authority,
            "content_gaps": self.content_gaps,
            "article_ideas": self.article_ideas,
            "their_strengths": self.their_strengths,
            "their_weaknesses": self.their_weaknesses,
            "recommended_strategy": self.recommended_strategy,
            "serp_overlap_percentage": self.serp_overlap_percentage,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_analyzed": self.last_analyzed.isoformat() if self.last_analyzed else None,
        }
