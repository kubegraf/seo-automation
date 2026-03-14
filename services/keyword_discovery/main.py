"""
Keyword Discovery Service - FastAPI application.
Discovers and scores SEO keyword opportunities.
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
import os

sys.path.insert(0, "/app")

from shared.database import get_db, init_db, check_db_connection
from shared.redis_client import redis_client, CHANNEL_KEYWORDS_DISCOVERED
from shared.models.keyword import Keyword
from .engine import KeywordDiscoveryEngine
from .models import KeywordDiscoveryRequest, KeywordDiscoveryResponse, KeywordOpportunity

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Keyword Discovery Service starting...")
    await init_db()
    await redis_client.connect()
    logger.info("Keyword Discovery Service ready")
    yield
    await redis_client.disconnect()
    logger.info("Keyword Discovery Service stopped")


app = FastAPI(
    title="Keyword Discovery Service",
    description="Discovers and scores SEO keyword opportunities for Kubegraf",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = KeywordDiscoveryEngine()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    db_ok = await check_db_connection()
    redis_ok = await redis_client.health_check()
    return {
        "status": "healthy" if db_ok and redis_ok else "degraded",
        "service": "keyword-discovery",
        "database": "connected" if db_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/status")
async def get_status(db: AsyncSession = Depends(get_db)):
    """Get service status and stats."""
    result = await db.execute(select(Keyword))
    total = len(result.scalars().all())
    return {
        "service": "keyword-discovery",
        "total_keywords": total,
        "status": "operational",
    }


@app.post("/run")
async def run_discovery(
    background_tasks: BackgroundTasks,
    request: Optional[KeywordDiscoveryRequest] = None,
):
    """Trigger keyword discovery pipeline."""
    run_id = str(uuid.uuid4())
    req = request or KeywordDiscoveryRequest()

    background_tasks.add_task(run_discovery_task, run_id, req)

    return {
        "run_id": run_id,
        "status": "started",
        "message": "Keyword discovery started in background",
    }


async def run_discovery_task(run_id: str, request: KeywordDiscoveryRequest):
    """Background task for keyword discovery."""
    try:
        logger.info(f"Starting keyword discovery run {run_id}")
        await redis_client.emit_pipeline_event("keyword-discovery", "started", {"run_id": run_id})

        keywords = await engine.discover_and_score_all(
            min_volume=request.min_search_volume,
            max_difficulty=request.max_difficulty,
        )

        # Persist to database
        from shared.database import get_db_context
        async with get_db_context() as db:
            saved_count = 0
            for kw_data in keywords:
                # Check if keyword already exists
                existing = await db.execute(
                    select(Keyword).where(Keyword.term == kw_data["term"])
                )
                existing_kw = existing.scalar_one_or_none()

                if existing_kw:
                    # Update existing keyword
                    await db.execute(
                        update(Keyword)
                        .where(Keyword.term == kw_data["term"])
                        .values(
                            search_volume=kw_data.get("search_volume"),
                            difficulty=kw_data.get("difficulty"),
                            opportunity_score=kw_data.get("opportunity_score"),
                            trend=kw_data.get("trend"),
                            intent=kw_data.get("intent"),
                            category=kw_data.get("category"),
                        )
                    )
                else:
                    # Create new keyword
                    new_kw = Keyword(
                        term=kw_data["term"],
                        search_volume=kw_data.get("search_volume"),
                        difficulty=kw_data.get("difficulty"),
                        opportunity_score=kw_data.get("opportunity_score"),
                        trend=kw_data.get("trend"),
                        intent=kw_data.get("intent"),
                        category=kw_data.get("category"),
                        is_seed=kw_data.get("is_seed", False),
                    )
                    db.add(new_kw)
                    saved_count += 1

            await db.commit()
            logger.info(f"Saved {saved_count} new keywords to database")

        # Publish event
        await redis_client.publish(CHANNEL_KEYWORDS_DISCOVERED, {
            "run_id": run_id,
            "keyword_count": len(keywords),
            "top_opportunities": [k["term"] for k in keywords[:10]],
        })
        await redis_client.emit_pipeline_event("keyword-discovery", "completed", {
            "run_id": run_id,
            "keywords_found": len(keywords),
        })

        logger.info(f"Keyword discovery run {run_id} completed: {len(keywords)} keywords")

    except Exception as e:
        logger.error(f"Keyword discovery run {run_id} failed: {e}", exc_info=True)
        await redis_client.emit_pipeline_event("keyword-discovery", "failed", {
            "run_id": run_id,
            "error": str(e),
        })


@app.post("/discover", response_model=KeywordDiscoveryResponse)
async def discover_keywords(
    request: KeywordDiscoveryRequest,
    db: AsyncSession = Depends(get_db),
):
    """Synchronously discover keywords and return results."""
    run_id = str(uuid.uuid4())

    keywords = await engine.discover_and_score_all(
        min_volume=request.min_search_volume,
        max_difficulty=request.max_difficulty,
    )

    if request.count:
        keywords = keywords[:request.count]

    keyword_objects = [
        KeywordOpportunity(
            term=kw["term"],
            search_volume=kw.get("search_volume", 0),
            difficulty=kw.get("difficulty", 50.0),
            opportunity_score=kw.get("opportunity_score", 0.0),
            trend=kw.get("trend", "stable"),
            intent=kw.get("intent", "informational"),
            category=kw.get("category", "general"),
            is_seed=kw.get("is_seed", False),
        )
        for kw in keywords
    ]

    return KeywordDiscoveryResponse(
        keywords=keyword_objects,
        total_found=len(keyword_objects),
        run_id=run_id,
        timestamp=datetime.utcnow(),
    )


@app.get("/keywords")
async def list_keywords(
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
    min_score: float = 0.0,
):
    """List keywords from database."""
    result = await db.execute(
        select(Keyword)
        .where(Keyword.opportunity_score >= min_score)
        .order_by(Keyword.opportunity_score.desc())
        .limit(limit)
        .offset(offset)
    )
    keywords = result.scalars().all()
    return {"keywords": [kw.to_dict() for kw in keywords], "total": len(keywords)}


@app.post("/analyze/{keyword}")
async def analyze_keyword(keyword: str):
    """Analyze a specific keyword."""
    result = await engine.analyze_keyword_opportunity(keyword)
    return result


@app.get("/seeds")
async def get_seed_keywords():
    """Get the list of seed keywords."""
    seeds = await engine.get_seed_keywords()
    return {"seeds": seeds, "count": len(seeds)}
