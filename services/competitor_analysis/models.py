"""
Pydantic models for Competitor Analysis service.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CompetitorAnalysisRequest(BaseModel):
    competitor_name: str
    include_llm_analysis: bool = True


class CompetitorAnalysisResult(BaseModel):
    competitor_name: str
    domain: str
    gap_keywords: list[str]
    shared_keywords: list[str]
    serp_overlap_percentage: float
    their_keywords: list[str]
    article_ideas: list[str]
    their_strengths: list[str]
    their_weaknesses: list[str]
    recommended_strategy: str
    opportunities: list[str]
    traffic_estimate: int
    domain_authority: int
    analyzed_at: str


class KeywordGapRequest(BaseModel):
    our_keywords: list[str]
    their_keywords: list[str]


class ContentCalendarItem(BaseModel):
    week: int
    title: str
    competitor: Optional[str] = None
    target_keyword: Optional[str] = None
    type: str
    priority: int
