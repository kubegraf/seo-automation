"""
Pydantic models for Keyword Discovery service.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class KeywordOpportunity(BaseModel):
    term: str
    search_volume: int = 0
    difficulty: float = Field(ge=0, le=100, default=50.0)
    opportunity_score: float = Field(ge=0, le=100, default=0.0)
    trend: str = "stable"
    intent: str = "informational"
    competitor: Optional[str] = None
    category: str = "general"
    is_seed: bool = False


class KeywordDiscoveryRequest(BaseModel):
    topic: Optional[str] = None
    seed_keywords: Optional[list[str]] = None
    count: int = Field(default=20, ge=1, le=100)
    min_search_volume: int = Field(default=100, ge=0)
    max_difficulty: float = Field(default=80.0, ge=0, le=100)


class KeywordDiscoveryResponse(BaseModel):
    keywords: list[KeywordOpportunity]
    total_found: int
    run_id: str
    timestamp: datetime


class KeywordAnalysisResult(BaseModel):
    term: str
    opportunity_score: float
    recommended_article_type: str
    estimated_traffic_potential: int
    competitor_gap: bool = False
    reasoning: str
