"""
Competitor Analysis Service - FastAPI application.
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

from shared.database import get_db, init_db, check_db_connection
from shared.redis_client import redis_client, CHANNEL_COMPETITORS_ANALYZED
from shared.llm_client import llm_client
from shared.models.competitor import Competitor
from .engine import CompetitorAnalysisEngine
from .competitors import COMPETITORS, get_all_competitors
from .models import CompetitorAnalysisRequest, ContentCalendarItem

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Competitor Analysis Service starting...")
    await init_db()
    await redis_client.connect()
    logger.info("Competitor Analysis Service ready")
    yield
    await redis_client.disconnect()


app = FastAPI(
    title="Competitor Analysis Service",
    description="Analyzes competitors and identifies content opportunities for Kubegraf",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = CompetitorAnalysisEngine(llm_client=llm_client)


@app.get("/health")
async def health_check():
    db_ok = await check_db_connection()
    redis_ok = await redis_client.health_check()
    return {
        "status": "healthy" if db_ok and redis_ok else "degraded",
        "service": "competitor-analysis",
        "database": "connected" if db_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/status")
async def get_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Competitor))
    total = len(result.scalars().all())
    return {
        "service": "competitor-analysis",
        "total_competitors_tracked": total,
        "configured_competitors": len(COMPETITORS),
        "status": "operational",
    }


@app.post("/run")
async def run_analysis(background_tasks: BackgroundTasks):
    """Trigger full competitor analysis pipeline."""
    run_id = str(uuid.uuid4())
    background_tasks.add_task(run_analysis_task, run_id)
    return {
        "run_id": run_id,
        "status": "started",
        "message": "Competitor analysis started in background",
    }


async def run_analysis_task(run_id: str):
    """Background task for competitor analysis."""
    try:
        logger.info(f"Starting competitor analysis run {run_id}")
        await redis_client.emit_pipeline_event("competitor-analysis", "started", {"run_id": run_id})

        results = await engine.analyze_all_competitors()

        # Persist to database
        from shared.database import get_db_context
        async with get_db_context() as db:
            for result in results:
                existing = await db.execute(
                    select(Competitor).where(Competitor.domain == result["domain"])
                )
                existing_comp = existing.scalar_one_or_none()

                if existing_comp:
                    await db.execute(
                        update(Competitor)
                        .where(Competitor.domain == result["domain"])
                        .values(
                            gap_keywords=result["gap_keywords"],
                            keywords=result["their_keywords"],
                            article_ideas=result["article_ideas"],
                            their_strengths=result["their_strengths"],
                            their_weaknesses=result["their_weaknesses"],
                            recommended_strategy=result["recommended_strategy"],
                            serp_overlap_percentage=result["serp_overlap_percentage"],
                            shared_keywords=result["shared_keywords"],
                            last_analyzed=datetime.utcnow(),
                        )
                    )
                else:
                    comp = Competitor(
                        name=result["competitor_name"],
                        domain=result["domain"],
                        keywords=result["their_keywords"],
                        gap_keywords=result["gap_keywords"],
                        article_ideas=result["article_ideas"],
                        their_strengths=result["their_strengths"],
                        their_weaknesses=result["their_weaknesses"],
                        recommended_strategy=result["recommended_strategy"],
                        serp_overlap_percentage=result["serp_overlap_percentage"],
                        shared_keywords=result["shared_keywords"],
                        traffic_estimate=result.get("traffic_estimate", 0),
                        domain_authority=result.get("domain_authority", 0),
                        last_analyzed=datetime.utcnow(),
                    )
                    db.add(comp)

        all_gaps = []
        for r in results:
            all_gaps.extend(r.get("gap_keywords", []))

        await redis_client.publish(CHANNEL_COMPETITORS_ANALYZED, {
            "run_id": run_id,
            "competitors_analyzed": len(results),
            "total_gap_keywords": len(set(all_gaps)),
        })
        await redis_client.emit_pipeline_event("competitor-analysis", "completed", {
            "run_id": run_id,
            "competitors_analyzed": len(results),
        })

        logger.info(f"Competitor analysis run {run_id} completed")

    except Exception as e:
        logger.error(f"Competitor analysis run {run_id} failed: {e}", exc_info=True)
        await redis_client.emit_pipeline_event("competitor-analysis", "failed", {
            "run_id": run_id,
            "error": str(e),
        })


@app.post("/analyze")
async def analyze_competitor(request: CompetitorAnalysisRequest):
    """Analyze a specific competitor."""
    try:
        result = await engine.analyze_competitor(request.competitor_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/competitors")
async def list_competitors(db: AsyncSession = Depends(get_db)):
    """List all tracked competitors."""
    result = await db.execute(select(Competitor).order_by(Competitor.name))
    competitors = result.scalars().all()
    return {
        "competitors": [c.to_dict() for c in competitors],
        "configured": [
            {
                "name": c.name,
                "domain": c.domain,
                "category": c.category,
                "priority": c.priority,
            }
            for c in get_all_competitors()
        ],
    }


@app.get("/gaps")
async def get_keyword_gaps():
    """Get all keyword gaps across all competitors."""
    gaps = await engine.find_all_keyword_gaps()
    return {"gap_keywords": gaps, "total": len(gaps)}


@app.get("/calendar")
async def get_content_calendar(weeks: int = 4):
    """Get recommended content calendar."""
    calendar = await engine.generate_content_calendar(weeks=weeks)
    return {"calendar": calendar, "weeks": weeks, "total_items": len(calendar)}


@app.get("/article-ideas/{competitor_name}")
async def get_article_ideas(competitor_name: str):
    """Get article ideas for competing with a specific competitor."""
    from .competitors import get_competitor_by_name
    competitor = get_competitor_by_name(competitor_name)
    if not competitor:
        raise HTTPException(status_code=404, detail=f"Competitor '{competitor_name}' not found")

    ideas = engine.generate_comparison_article_ideas(competitor)
    return {"competitor": competitor_name, "article_ideas": ideas}
