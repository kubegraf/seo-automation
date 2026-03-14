"""
Publishing Service - FastAPI application.
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
from shared.redis_client import redis_client, CHANNEL_CONTENT_PUBLISHED
from shared.models.article import Article, ArticleStatus
from .engine import PublishingEngine
from .models import PublishRequest, BatchPublishRequest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Publishing Service starting...")
    await init_db()
    await redis_client.connect()
    logger.info("Publishing Service ready")
    yield
    await redis_client.disconnect()
    await engine.close()


app = FastAPI(
    title="Publishing Service",
    description="Publishes optimized articles to GitHub Pages / Hugo",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = PublishingEngine()


@app.get("/health")
async def health_check():
    db_ok = await check_db_connection()
    redis_ok = await redis_client.health_check()
    return {
        "status": "healthy" if db_ok and redis_ok else "degraded",
        "service": "publishing",
        "database": "connected" if db_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
        "github_configured": bool(engine.github_token),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/status")
async def get_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Article).where(Article.status == ArticleStatus.PUBLISHED)
    )
    published = len(result.scalars().all())
    return {
        "service": "publishing",
        "published_articles": published,
        "github_repo": f"{engine.repo_owner}/{engine.repo_name}",
        "github_branch": engine.branch,
    }


@app.post("/run")
async def run_publishing(
    background_tasks: BackgroundTasks,
    request: Optional[BatchPublishRequest] = None,
):
    """Trigger batch publishing pipeline."""
    run_id = str(uuid.uuid4())
    req = request or BatchPublishRequest()
    background_tasks.add_task(run_publishing_task, run_id, req)
    return {
        "run_id": run_id,
        "status": "started",
        "message": "Publishing started in background",
    }


async def run_publishing_task(run_id: str, request: BatchPublishRequest):
    """Background task for batch publishing."""
    try:
        logger.info(f"Starting publishing run {run_id}")
        await redis_client.emit_pipeline_event("publishing", "started", {"run_id": run_id})

        async with get_db_context() as db:
            result = await db.execute(
                select(Article)
                .where(Article.status == request.status_filter)
                .limit(request.max_articles)
            )
            articles = result.scalars().all()

            # Get all published articles for internal link building
            all_result = await db.execute(
                select(Article).where(Article.status == ArticleStatus.PUBLISHED)
            )
            all_published = [
                {"title": a.title, "slug": a.slug, "keywords": a.keywords or []}
                for a in all_result.scalars().all()
            ]

            published_count = 0
            for article in articles:
                try:
                    article_dict = {
                        "title": article.title,
                        "slug": article.slug,
                        "content": article.content or "",
                        "meta_description": article.meta_description or "",
                        "primary_keyword": article.primary_keyword or "",
                        "keywords": article.keywords or [],
                        "article_type": article.article_type,
                        "seo_score": article.seo_score or 0,
                        "word_count": article.word_count or 0,
                        "competitor_target": article.competitor_target or "",
                        "schema_markup": article.schema_markup or {},
                    }

                    # Build internal links
                    article_dict = engine.build_internal_links(article_dict, all_published)

                    # Publish to GitHub
                    result_data = await engine.publish_to_github(article_dict)

                    await db.execute(
                        update(Article)
                        .where(Article.id == article.id)
                        .values(
                            status=ArticleStatus.PUBLISHED,
                            published_url=result_data["published_url"],
                            github_sha=result_data["github_sha"],
                            published_at=datetime.utcnow(),
                            content=article_dict["content"],
                            internal_links=article_dict.get("internal_links", []),
                        )
                    )
                    published_count += 1
                    all_published.append({
                        "title": article.title,
                        "slug": article.slug,
                        "keywords": article.keywords or [],
                    })

                except Exception as e:
                    logger.error(f"Failed to publish article {article.id}: {e}")

        await redis_client.publish(CHANNEL_CONTENT_PUBLISHED, {
            "run_id": run_id,
            "published_count": published_count,
        })
        await redis_client.emit_pipeline_event("publishing", "completed", {
            "run_id": run_id,
            "published_count": published_count,
        })

        logger.info(f"Publishing run {run_id} completed: {published_count} articles")

    except Exception as e:
        logger.error(f"Publishing run {run_id} failed: {e}", exc_info=True)
        await redis_client.emit_pipeline_event("publishing", "failed", {
            "run_id": run_id,
            "error": str(e),
        })


@app.post("/publish/{article_id}")
async def publish_article(article_id: int, db: AsyncSession = Depends(get_db)):
    """Publish a specific article."""
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    article_dict = {
        "title": article.title,
        "slug": article.slug,
        "content": article.content or "",
        "meta_description": article.meta_description or "",
        "primary_keyword": article.primary_keyword or "",
        "keywords": article.keywords or [],
        "article_type": article.article_type,
        "seo_score": article.seo_score or 0,
        "word_count": article.word_count or 0,
        "schema_markup": article.schema_markup or {},
    }

    try:
        result_data = await engine.publish_to_github(article_dict)
        await db.execute(
            update(Article)
            .where(Article.id == article_id)
            .values(
                status=ArticleStatus.PUBLISHED,
                published_url=result_data["published_url"],
                github_sha=result_data["github_sha"],
                published_at=datetime.utcnow(),
            )
        )
        return result_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/frontmatter")
async def generate_frontmatter(article: dict):
    """Generate frontmatter for an article."""
    return {"frontmatter": engine.generate_frontmatter(article)}
