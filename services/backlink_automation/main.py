"""
Backlink Automation Service - FastAPI application.
"""
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import sys

sys.path.insert(0, "/app")

from shared.database import get_db, init_db, check_db_connection
from shared.redis_client import redis_client
from shared.models.article import Article, ArticleStatus
from .engine import BacklinkAutomationEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await redis_client.connect()
    yield
    await redis_client.disconnect()


app = FastAPI(title="Backlink Automation Service", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

engine = BacklinkAutomationEngine()


@app.get("/health")
async def health_check():
    db_ok = await check_db_connection()
    redis_ok = await redis_client.health_check()
    return {
        "status": "healthy" if db_ok and redis_ok else "degraded",
        "service": "backlink-automation",
        "database": "connected" if db_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/status")
async def get_status():
    return {"service": "backlink-automation", "status": "operational"}


@app.post("/run")
async def run_backlink_analysis(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Trigger backlink opportunity analysis."""
    result = await db.execute(
        select(Article).where(Article.status == ArticleStatus.PUBLISHED)
    )
    articles = [a.to_dict() for a in result.scalars().all()]
    background_tasks.add_task(analyze_backlinks, articles)
    return {"status": "started", "articles_to_analyze": len(articles)}


async def analyze_backlinks(articles: list[dict]):
    opportunities = await engine.find_opportunities(articles)
    await redis_client.set_json("seo:backlink:opportunities", opportunities[:100], ttl=86400)
    logger.info(f"Found {len(opportunities)} backlink opportunities")


@app.get("/opportunities")
async def get_opportunities(db: AsyncSession = Depends(get_db)):
    """Get backlink opportunities."""
    cached = await redis_client.get_json("seo:backlink:opportunities")
    if cached:
        return {"opportunities": cached, "source": "cache"}
    result = await db.execute(
        select(Article).where(Article.status == ArticleStatus.PUBLISHED).limit(10)
    )
    articles = [a.to_dict() for a in result.scalars().all()]
    opportunities = await engine.find_opportunities(articles)
    return {"opportunities": opportunities[:20], "source": "fresh"}


@app.get("/guest-post-targets")
async def get_guest_post_targets():
    """Get guest post target websites."""
    targets = await engine.identify_guest_post_targets([])
    return {"targets": targets}


@app.get("/competitor-backlinks/{domain}")
async def analyze_competitor_backlinks(domain: str):
    """Analyze competitor backlinks."""
    analysis = await engine.analyze_competitor_backlinks(domain)
    return analysis
