"""
SEO Analytics Service - FastAPI application.
"""
import logging
import uuid
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import sys

sys.path.insert(0, "/app")

from shared.database import get_db, init_db, check_db_connection, get_db_context
from shared.redis_client import redis_client, CHANNEL_ANALYTICS_UPDATED
from shared.models.article import Article, ArticleStatus
from shared.models.keyword import Keyword
from .engine import SEOAnalyticsEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SEO Analytics Service starting...")
    await init_db()
    await redis_client.connect()
    logger.info("SEO Analytics Service ready")
    yield
    await redis_client.disconnect()


app = FastAPI(
    title="SEO Analytics Service",
    description="Tracks SEO performance and generates reports",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = SEOAnalyticsEngine()


@app.get("/health")
async def health_check():
    db_ok = await check_db_connection()
    redis_ok = await redis_client.health_check()
    return {
        "status": "healthy" if db_ok and redis_ok else "degraded",
        "service": "seo-analytics",
        "database": "connected" if db_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/status")
async def get_status(db: AsyncSession = Depends(get_db)):
    articles_result = await db.execute(
        select(Article).where(Article.status == ArticleStatus.PUBLISHED)
    )
    published = len(articles_result.scalars().all())
    keywords_result = await db.execute(select(Keyword).where(Keyword.is_active == True))
    tracked_keywords = len(keywords_result.scalars().all())
    return {
        "service": "seo-analytics",
        "published_articles": published,
        "tracked_keywords": tracked_keywords,
    }


@app.post("/run")
async def run_analytics(background_tasks: BackgroundTasks):
    """Trigger analytics update."""
    run_id = str(uuid.uuid4())
    background_tasks.add_task(run_analytics_task, run_id)
    return {
        "run_id": run_id,
        "status": "started",
        "message": "Analytics update started in background",
    }


async def run_analytics_task(run_id: str):
    """Background task for analytics update."""
    try:
        logger.info(f"Starting analytics run {run_id}")
        await redis_client.emit_pipeline_event("seo-analytics", "started", {"run_id": run_id})

        async with get_db_context() as db:
            # Get keywords to track
            kw_result = await db.execute(
                select(Keyword).where(Keyword.is_active == True).limit(100)
            )
            keywords = kw_result.scalars().all()
            keyword_terms = [kw.term for kw in keywords]

            # Track rankings
            rankings = await engine.track_rankings(keyword_terms)

            # Update keyword positions
            for ranking in rankings:
                existing = await db.execute(
                    select(Keyword).where(Keyword.term == ranking["keyword"])
                )
                kw = existing.scalar_one_or_none()
                if kw:
                    await db.execute(
                        update(Keyword)
                        .where(Keyword.term == ranking["keyword"])
                        .values(
                            previous_position=kw.current_position,
                            current_position=ranking["current_position"],
                            last_checked=datetime.utcnow(),
                        )
                    )

            # Get published articles for traffic calculation
            art_result = await db.execute(
                select(Article).where(Article.status == ArticleStatus.PUBLISHED)
            )
            articles = art_result.scalars().all()
            article_dicts = [a.to_dict() for a in articles]

            # Calculate traffic
            traffic_data = await engine.calculate_organic_traffic(article_dicts)

            # Update article traffic metrics
            for article_traffic in traffic_data.get("articles", []):
                if article_traffic.get("article_id"):
                    await db.execute(
                        update(Article)
                        .where(Article.id == article_traffic["article_id"])
                        .values(
                            organic_clicks=article_traffic["clicks"],
                            impressions=article_traffic["impressions"],
                            ctr=article_traffic["ctr"],
                            average_position=article_traffic["avg_position"],
                        )
                    )

        await redis_client.publish(CHANNEL_ANALYTICS_UPDATED, {
            "run_id": run_id,
            "keywords_tracked": len(keyword_terms),
            "articles_tracked": len(article_dicts),
        })
        await redis_client.emit_pipeline_event("seo-analytics", "completed", {
            "run_id": run_id,
        })

        logger.info(f"Analytics run {run_id} completed")

    except Exception as e:
        logger.error(f"Analytics run {run_id} failed: {e}", exc_info=True)
        await redis_client.emit_pipeline_event("seo-analytics", "failed", {
            "run_id": run_id,
            "error": str(e),
        })


@app.get("/rankings")
async def get_rankings(db: AsyncSession = Depends(get_db), limit: int = 50):
    """Get current keyword rankings."""
    result = await db.execute(
        select(Keyword)
        .where(Keyword.is_active == True)
        .where(Keyword.current_position != None)
        .order_by(Keyword.current_position)
        .limit(limit)
    )
    keywords = result.scalars().all()
    return {"rankings": [kw.to_dict() for kw in keywords]}


@app.get("/rankings/{keyword}")
async def get_keyword_ranking_history(keyword: str, days: int = 30):
    """Get ranking history for a specific keyword."""
    history = await engine.get_ranking_history(keyword, days=days)
    return {"keyword": keyword, "history": history}


@app.get("/report")
async def get_report():
    """Generate and return weekly SEO report."""
    report = await engine.generate_report()
    return report


@app.get("/opportunities")
async def get_opportunities():
    """Get SEO optimization opportunities."""
    opportunities = await engine.identify_opportunities()
    return {"opportunities": opportunities, "total": len(opportunities)}


@app.get("/traffic")
async def get_traffic(db: AsyncSession = Depends(get_db)):
    """Get organic traffic estimates."""
    result = await db.execute(
        select(Article).where(Article.status == ArticleStatus.PUBLISHED)
    )
    articles = [a.to_dict() for a in result.scalars().all()]
    traffic = await engine.calculate_organic_traffic(articles)
    return traffic
