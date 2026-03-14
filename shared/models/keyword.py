"""
Keyword SQLAlchemy model for SEO Automation Platform.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String,
    Integer,
    Float,
    DateTime,
    JSON,
    func,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column

from shared.database import Base


class Keyword(Base):
    """
    Represents a target keyword with metrics and tracking data.
    """
    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    term: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)

    # Search metrics
    search_volume: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    difficulty: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-100
    cpc: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Cost per click

    # Opportunity scoring
    opportunity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-100

    # Competitor context
    competitor: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    competitor_domain: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Trend data
    trend: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # rising/stable/declining
    trend_data: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # Monthly trend values

    # Search intent
    intent: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )  # informational/navigational/commercial/transactional

    # Current rankings
    current_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    previous_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    best_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # SERP features
    has_featured_snippet: Mapped[bool] = mapped_column(Boolean, default=False)
    has_local_pack: Mapped[bool] = mapped_column(Boolean, default=False)
    has_knowledge_panel: Mapped[bool] = mapped_column(Boolean, default=False)
    has_video_results: Mapped[bool] = mapped_column(Boolean, default=False)

    # Categorization
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Status flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    has_article: Mapped[bool] = mapped_column(Boolean, default=False)
    is_seed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_updated: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
        nullable=True,
    )
    last_checked: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<Keyword id={self.id} term='{self.term}' volume={self.search_volume}>"

    @property
    def position_change(self) -> Optional[int]:
        """Calculate position change (positive = improvement)."""
        if self.current_position and self.previous_position:
            return self.previous_position - self.current_position
        return None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "term": self.term,
            "search_volume": self.search_volume,
            "difficulty": self.difficulty,
            "cpc": self.cpc,
            "opportunity_score": self.opportunity_score,
            "competitor": self.competitor,
            "trend": self.trend,
            "intent": self.intent,
            "current_position": self.current_position,
            "previous_position": self.previous_position,
            "position_change": self.position_change,
            "category": self.category,
            "is_active": self.is_active,
            "has_article": self.has_article,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
        }
