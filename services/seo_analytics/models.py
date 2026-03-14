"""
Pydantic models for SEO Analytics service.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class RankingData(BaseModel):
    keyword: str
    current_position: int
    previous_position: int
    position_change: int
    url: str
    search_volume: int
    impressions: int
    clicks: int
    ctr: float
    checked_at: str


class TrafficReport(BaseModel):
    total_impressions: int
    total_clicks: int
    total_estimated_value: float
    average_ctr: float
    articles: list[dict]
    calculated_at: str


class SEOOpportunity(BaseModel):
    type: str
    title: str
    priority: str
    recommendation: str
    identified_at: str
