"""
Pydantic models for Content Generation service.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ArticleGenerationRequest(BaseModel):
    topic: str
    keywords: list[str]
    article_type: str = Field(default="standard", pattern="^(standard|comparison|tutorial|listicle|case_study)$")
    word_count: int = Field(default=2000, ge=500, le=5000)
    competitor: Optional[str] = None
    custom_prompt: Optional[str] = None


class TutorialGenerationRequest(BaseModel):
    topic: str
    steps: list[str]
    primary_keyword: str
    skill_level: str = Field(default="intermediate", pattern="^(beginner|intermediate|advanced)$")
    time_estimate: int = Field(default=30, ge=5, le=480)


class ComparisonArticleRequest(BaseModel):
    competitor_name: str
    competitor_domain: str
    competitor_description: str = ""
    competitor_features: list[str] = []


class GeneratedArticle(BaseModel):
    title: str
    slug: str
    content: str
    meta_description: str
    primary_keyword: str
    keywords: list[str]
    word_count: int
    article_type: str
    generated_at: str
    is_sample: bool = False


class BatchGenerationRequest(BaseModel):
    max_articles: int = Field(default=5, ge=1, le=20)
    topics: Optional[list[dict]] = None
