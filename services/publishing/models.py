"""
Pydantic models for Publishing service.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PublishRequest(BaseModel):
    article_id: int


class PublishResult(BaseModel):
    article_id: int
    published_url: str
    github_sha: str
    file_path: str
    repo: str
    branch: str
    published_at: str
    simulated: bool = False


class BatchPublishRequest(BaseModel):
    status_filter: str = "optimized"
    max_articles: int = 10
