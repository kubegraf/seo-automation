"""
Pydantic models for Backlink Automation service.
"""
from pydantic import BaseModel
from typing import Optional


class BacklinkOpportunity(BaseModel):
    article_title: str
    article_url: str
    target_platform: str
    target_type: str
    domain_authority: int
    strategy: str
    relevance: str
    estimated_value: float
    status: str
    identified_at: str
