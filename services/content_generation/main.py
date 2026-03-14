"""
Content Generation Service - FastAPI application.
Generates SEO-optimized articles using LLM.
"""
import logging
import uuid
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import sys

sys.path.insert(0, "/app")

from shared.database import get_db, init_db, check_db_connection, get_db_context
from shared.redis_client import redis_client, CHANNEL_CONTENT_GENERATED
from shared.llm_client import llm_client
from shared.models.article import Article, ArticleStatus, ArticleType
from shared.models.keyword import Keyword
from .engine import ContentGenerationEngine, SAMPLE_TOPICS
from .models import (
    ArticleGenerationRequest,
    TutorialGenerationRequest,
    ComparisonArticleRequest,
    BatchGenerationRequest,
    GeneratedArticle,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Content Generation Service starting...")
    await init_db()
    await redis_client.connect()
    logger.info("Content Generation Service ready")
    yield
    await redis_client.disconnect()


app = FastAPI(
    title="Content Generation Service",
    description="AI-powered SEO article generation for Kubegraf blog",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = ContentGenerationEngine(llm_client=llm_client)


@app.get("/health")
async def health_check():
    db_ok = await check_db_connection()
    redis_ok = await redis_client.health_check()
    llm_ok = await llm_client.health_check() if llm_client else False
    return {
        "status": "healthy" if db_ok and redis_ok else "degraded",
        "service": "content-generation",
        "database": "connected" if db_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
        "llm": "connected" if llm_ok else "unavailable",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/status")
async def get_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Article))
    articles = result.scalars().all()
    status_counts = {}
    for article in articles:
        status_counts[article.status] = status_counts.get(article.status, 0) + 1
    return {
        "service": "content-generation",
        "total_articles": len(articles),
        "status_breakdown": status_counts,
        "sample_topics_available": len(SAMPLE_TOPICS),
    }


@app.post("/run")
async def run_generation(
    background_tasks: BackgroundTasks,
    request: Optional[BatchGenerationRequest] = None,
):
    """Trigger batch content generation pipeline."""
    run_id = str(uuid.uuid4())
    req = request or BatchGenerationRequest()
    background_tasks.add_task(run_generation_task, run_id, req)
    return {
        "run_id": run_id,
        "status": "started",
        "message": f"Content generation started for up to {req.max_articles} articles",
    }


async def run_generation_task(run_id: str, request: BatchGenerationRequest):
    """Background task for batch article generation."""
    try:
        logger.info(f"Starting content generation run {run_id}")
        await redis_client.emit_pipeline_event("content-generation", "started", {"run_id": run_id})

        articles = await engine.batch_generate(
            topics=request.topics,
            max_articles=request.max_articles,
        )

        async with get_db_context() as db:
            saved_count = 0
            for article_data in articles:
                slug = article_data["slug"]
                existing = await db.execute(select(Article).where(Article.slug == slug))
                if existing.scalar_one_or_none():
                    logger.info(f"Article with slug '{slug}' already exists, skipping")
                    continue

                article = Article(
                    title=article_data["title"],
                    slug=slug,
                    content=article_data["content"],
                    meta_description=article_data["meta_description"],
                    primary_keyword=article_data["primary_keyword"],
                    keywords=article_data["keywords"],
                    word_count=article_data["word_count"],
                    article_type=article_data.get("article_type", ArticleType.STANDARD),
                    status=ArticleStatus.GENERATED,
                    generation_model="claude-3-5-sonnet",
                )
                db.add(article)
                saved_count += 1

        await redis_client.publish(CHANNEL_CONTENT_GENERATED, {
            "run_id": run_id,
            "articles_generated": len(articles),
            "articles_saved": saved_count,
        })
        await redis_client.emit_pipeline_event("content-generation", "completed", {
            "run_id": run_id,
            "articles_generated": len(articles),
        })

        logger.info(f"Content generation run {run_id} completed: {len(articles)} articles")

    except Exception as e:
        logger.error(f"Content generation run {run_id} failed: {e}", exc_info=True)
        await redis_client.emit_pipeline_event("content-generation", "failed", {
            "run_id": run_id,
            "error": str(e),
        })


@app.post("/generate", response_model=GeneratedArticle)
async def generate_article(
    request: ArticleGenerationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate a single article."""
    try:
        result = await engine.generate_article(
            topic=request.topic,
            keywords=request.keywords,
            article_type=request.article_type,
            word_count=request.word_count,
            custom_prompt=request.custom_prompt,
        )
        return GeneratedArticle(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate/comparison", response_model=GeneratedArticle)
async def generate_comparison_article(request: ComparisonArticleRequest):
    """Generate a competitor comparison article."""
    try:
        result = await engine.generate_comparison_article(
            our_product="Kubegraf",
            competitor=request.competitor_name,
            competitor_domain=request.competitor_domain,
            competitor_description=request.competitor_description,
            competitor_features=request.competitor_features,
        )
        return GeneratedArticle(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate/tutorial", response_model=GeneratedArticle)
async def generate_tutorial(request: TutorialGenerationRequest):
    """Generate a technical tutorial."""
    try:
        result = await engine.generate_tutorial(
            topic=request.topic,
            steps=request.steps,
            primary_keyword=request.primary_keyword,
            skill_level=request.skill_level,
            time_estimate=request.time_estimate,
        )
        return GeneratedArticle(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/articles")
async def list_articles(
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None,
):
    """List generated articles."""
    query = select(Article).order_by(Article.created_at.desc()).limit(limit).offset(offset)
    if status:
        query = query.where(Article.status == status)
    result = await db.execute(query)
    articles = result.scalars().all()
    return {"articles": [a.to_dict() for a in articles], "total": len(articles)}


@app.get("/articles/{article_id}")
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific article."""
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article.to_dict()


@app.get("/topics")
async def get_sample_topics():
    """Get the list of predefined article topics."""
    return {"topics": SAMPLE_TOPICS, "total": len(SAMPLE_TOPICS)}
