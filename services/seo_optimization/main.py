"""
SEO Optimization Service - FastAPI application.
"""
import logging
import uuid
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import sys

sys.path.insert(0, "/app")

from shared.database import get_db, init_db, check_db_connection, get_db_context
from shared.redis_client import redis_client, CHANNEL_SEO_OPTIMIZED
from shared.llm_client import llm_client
from shared.models.article import Article, ArticleStatus
from .engine import SEOOptimizationEngine
from .models import SEOOptimizationRequest, BatchOptimizationRequest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SEO Optimization Service starting...")
    await init_db()
    await redis_client.connect()
    logger.info("SEO Optimization Service ready")
    yield
    await redis_client.disconnect()


app = FastAPI(
    title="SEO Optimization Service",
    description="Optimizes articles for search engine ranking",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = SEOOptimizationEngine(llm_client=llm_client)


@app.get("/health")
async def health_check():
    db_ok = await check_db_connection()
    redis_ok = await redis_client.health_check()
    return {
        "status": "healthy" if db_ok and redis_ok else "degraded",
        "service": "seo-optimization",
        "database": "connected" if db_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/status")
async def get_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Article).where(Article.status == ArticleStatus.OPTIMIZED)
    )
    optimized = len(result.scalars().all())
    pending_result = await db.execute(
        select(Article).where(Article.status == ArticleStatus.GENERATED)
    )
    pending = len(pending_result.scalars().all())
    return {
        "service": "seo-optimization",
        "optimized_articles": optimized,
        "pending_optimization": pending,
    }


@app.post("/run")
async def run_optimization(
    background_tasks: BackgroundTasks,
    request: Optional[BatchOptimizationRequest] = None,
):
    """Trigger batch SEO optimization."""
    run_id = str(uuid.uuid4())
    req = request or BatchOptimizationRequest()
    background_tasks.add_task(run_optimization_task, run_id, req)
    return {
        "run_id": run_id,
        "status": "started",
        "message": "SEO optimization started in background",
    }


async def run_optimization_task(run_id: str, request: BatchOptimizationRequest):
    """Background task for batch SEO optimization."""
    try:
        logger.info(f"Starting SEO optimization run {run_id}")
        await redis_client.emit_pipeline_event("seo-optimization", "started", {"run_id": run_id})

        async with get_db_context() as db:
            result = await db.execute(
                select(Article)
                .where(Article.status == request.status_filter)
                .limit(request.max_articles)
            )
            articles = result.scalars().all()

            optimized_count = 0
            for article in articles:
                try:
                    article_dict = {
                        "title": article.title,
                        "content": article.content or "",
                        "meta_description": article.meta_description or "",
                        "primary_keyword": article.primary_keyword or "",
                        "keywords": article.keywords or [],
                        "slug": article.slug,
                        "word_count": article.word_count or 0,
                    }

                    optimized = await engine.optimize_article(article_dict)

                    await db.execute(
                        update(Article)
                        .where(Article.id == article.id)
                        .values(
                            title=optimized["title"],
                            content=optimized["content"],
                            meta_description=optimized["meta_description"],
                            seo_score=optimized["seo_score"],
                            schema_markup=optimized.get("schema_markup"),
                            status=ArticleStatus.OPTIMIZED,
                        )
                    )
                    optimized_count += 1

                except Exception as e:
                    logger.error(f"Failed to optimize article {article.id}: {e}")

        await redis_client.publish(CHANNEL_SEO_OPTIMIZED, {
            "run_id": run_id,
            "optimized_count": optimized_count,
        })
        await redis_client.emit_pipeline_event("seo-optimization", "completed", {
            "run_id": run_id,
            "optimized_count": optimized_count,
        })

        logger.info(f"SEO optimization run {run_id} completed: {optimized_count} articles")

    except Exception as e:
        logger.error(f"SEO optimization run {run_id} failed: {e}", exc_info=True)
        await redis_client.emit_pipeline_event("seo-optimization", "failed", {
            "run_id": run_id,
            "error": str(e),
        })


@app.post("/optimize/{article_id}")
async def optimize_article(article_id: int, db: AsyncSession = Depends(get_db)):
    """Optimize a specific article by ID."""
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    article_dict = {
        "title": article.title,
        "content": article.content or "",
        "meta_description": article.meta_description or "",
        "primary_keyword": article.primary_keyword or "",
        "keywords": article.keywords or [],
        "slug": article.slug,
        "word_count": article.word_count or 0,
    }

    try:
        optimized = await engine.optimize_article(article_dict)
        await db.execute(
            update(Article)
            .where(Article.id == article_id)
            .values(
                title=optimized["title"],
                content=optimized["content"],
                meta_description=optimized["meta_description"],
                seo_score=optimized["seo_score"],
                schema_markup=optimized.get("schema_markup"),
                status=ArticleStatus.OPTIMIZED,
            )
        )
        return {"article_id": article_id, "seo_score": optimized["seo_score"], "status": "optimized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/score")
async def score_article(request: dict):
    """Calculate SEO score for article content."""
    score = engine.calculate_seo_score(request)
    return {"seo_score": score}
