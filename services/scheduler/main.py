"""
Scheduler Service - FastAPI application wrapping Celery.
Provides HTTP API for triggering pipeline tasks.
"""
import logging
import os
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys

sys.path.insert(0, "/app")

from .celery_app import (
    app as celery_app,
    full_seo_pipeline,
    check_rankings,
    run_competitor_analysis,
    run_keyword_discovery,
    run_content_generation,
    run_seo_optimization,
    run_publishing,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class TriggerRequest(BaseModel):
    max_articles: Optional[int] = 5


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Scheduler Service starting...")
    yield
    logger.info("Scheduler Service stopped")


app = FastAPI(
    title="Scheduler Service",
    description="Orchestrates the SEO automation pipeline via Celery",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Check Celery broker connectivity
    try:
        celery_app.control.ping(timeout=2)
        broker_status = "connected"
    except Exception:
        broker_status = "disconnected"

    return {
        "status": "healthy" if broker_status == "connected" else "degraded",
        "service": "scheduler",
        "broker": broker_status,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/status")
async def get_status():
    """Get scheduler status."""
    try:
        stats = celery_app.control.inspect().stats()
        active = celery_app.control.inspect().active()
        return {
            "service": "scheduler",
            "celery_workers": list(stats.keys()) if stats else [],
            "active_tasks": sum(len(tasks) for tasks in (active or {}).values()),
            "status": "operational",
        }
    except Exception as e:
        return {
            "service": "scheduler",
            "status": "degraded",
            "error": str(e),
        }


@app.post("/trigger/full-pipeline")
async def trigger_full_pipeline():
    """Trigger the full SEO pipeline."""
    try:
        task = full_seo_pipeline.delay()
        logger.info(f"Full SEO pipeline triggered: task_id={task.id}")
        return {
            "task_id": task.id,
            "status": "queued",
            "message": "Full SEO pipeline queued for execution",
            "triggered_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to trigger full pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trigger/keyword-discovery")
async def trigger_keyword_discovery():
    """Trigger keyword discovery task."""
    try:
        task = run_keyword_discovery.delay()
        return {
            "task_id": task.id,
            "status": "queued",
            "message": "Keyword discovery queued",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trigger/competitor-analysis")
async def trigger_competitor_analysis():
    """Trigger competitor analysis task."""
    try:
        task = run_competitor_analysis.delay()
        return {
            "task_id": task.id,
            "status": "queued",
            "message": "Competitor analysis queued",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trigger/content-generation")
async def trigger_content_generation(request: Optional[TriggerRequest] = None):
    """Trigger content generation task."""
    try:
        max_articles = request.max_articles if request else 5
        task = run_content_generation.delay(max_articles=max_articles)
        return {
            "task_id": task.id,
            "status": "queued",
            "message": f"Content generation queued for {max_articles} articles",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trigger/seo-optimization")
async def trigger_seo_optimization():
    """Trigger SEO optimization task."""
    try:
        task = run_seo_optimization.delay()
        return {
            "task_id": task.id,
            "status": "queued",
            "message": "SEO optimization queued",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trigger/publishing")
async def trigger_publishing():
    """Trigger publishing task."""
    try:
        task = run_publishing.delay()
        return {
            "task_id": task.id,
            "status": "queued",
            "message": "Publishing queued",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trigger/rankings")
async def trigger_rankings_check():
    """Trigger rankings check task."""
    try:
        task = check_rankings.delay()
        return {
            "task_id": task.id,
            "status": "queued",
            "message": "Rankings check queued",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a Celery task."""
    try:
        task = celery_app.AsyncResult(task_id)
        response = {
            "task_id": task_id,
            "status": task.status,
            "ready": task.ready(),
        }

        if task.ready():
            if task.successful():
                response["result"] = task.result
            elif task.failed():
                response["error"] = str(task.result)
        elif task.status == "STARTED":
            response["info"] = task.info

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scheduled-tasks")
async def get_scheduled_tasks():
    """List all scheduled (beat) tasks."""
    schedule = celery_app.conf.beat_schedule
    tasks = []
    for name, config in schedule.items():
        tasks.append({
            "name": name,
            "task": config["task"],
            "schedule": str(config["schedule"]),
        })
    return {"scheduled_tasks": tasks}
