"""
Pydantic models for SEO Optimization service.
"""
from typing import Optional
from pydantic import BaseModel, Field


class SEOOptimizationRequest(BaseModel):
    article_id: Optional[int] = None
    article: Optional[dict] = None
    optimize_title: bool = True
    optimize_meta: bool = True
    optimize_keywords: bool = True
    add_schema: bool = True
    optimize_headings: bool = True


class SEOScoreResponse(BaseModel):
    article_id: Optional[int] = None
    title: str
    seo_score: float = Field(ge=0, le=100)
    score_breakdown: dict
    recommendations: list[str]


class BatchOptimizationRequest(BaseModel):
    status_filter: str = "generated"
    max_articles: int = Field(default=10, ge=1, le=50)
