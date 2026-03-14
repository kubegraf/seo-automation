from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid


class Keyword(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    term: str
    search_volume_estimate: str  # "high", "medium", "low"
    difficulty: str  # "high", "medium", "low"
    opportunity_score: float  # 0.0 - 1.0
    competitor_ranking: Optional[str] = None
    category: str  # "kubernetes_ops", "sre", "ai_operations", etc.
    trend: str = "stable"  # "rising", "stable", "declining"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Competitor(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    domain: str
    focus_areas: List[str]
    target_keywords: List[str]
    gap_keywords: List[str] = []
    comparison_article_ideas: List[str] = []
    last_analyzed: Optional[str] = None
    traffic_tier: str = "medium"  # "high", "medium", "low"


class Article(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    slug: str
    meta_description: str
    content: str  # full markdown content
    keywords: List[str]
    category: str
    article_type: str  # "tutorial", "comparison", "deep_dive", "incident_example"
    seo_score: float = 0.0
    word_count: int = 0
    status: str = "draft"  # "draft", "optimized", "published"
    competitor_target: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    published_at: Optional[str] = None
    schema_markup: Optional[str] = None
    internal_links: List[str] = []
    diagram_included: bool = False


class SEOReport(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    week: str  # ISO week e.g. "2024-W42"
    articles_generated: int
    articles_published: int
    keywords_discovered: int
    competitors_analyzed: int
    top_keywords: List[str]
    top_articles: List[str]
    recommendations: List[str]
    total_real_clicks: int = 0
    total_real_impressions: int = 0
    real_data_sources: List[str] = []
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class BacklinkOpportunity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    article_title: str
    article_slug: str
    article_url: str
    target_site: str
    approach: str  # "cross_post", "syndication", "engagement", "contribute"
    priority: str  # "high", "medium", "low"
    outreach_draft: str = ""
    cross_post_intro: str = ""
    status: str = "draft"  # "draft", "submitted", "acquired", "rejected"
    issue_url: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
