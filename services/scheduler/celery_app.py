"""
Celery application for SEO Automation Platform.
Defines scheduled tasks and pipeline orchestration.
"""
import logging
import os
import asyncio
from datetime import datetime

from celery import Celery
from celery.schedules import crontab
import httpx

logger = logging.getLogger(__name__)

# Celery configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2")

# Service URLs
KEYWORD_DISCOVERY_URL = os.getenv("KEYWORD_DISCOVERY_URL", "http://keyword-discovery:8000")
COMPETITOR_ANALYSIS_URL = os.getenv("COMPETITOR_ANALYSIS_URL", "http://competitor-analysis:8000")
CONTENT_GENERATION_URL = os.getenv("CONTENT_GENERATION_URL", "http://content-generation:8000")
SEO_OPTIMIZATION_URL = os.getenv("SEO_OPTIMIZATION_URL", "http://seo-optimization:8000")
PUBLISHING_URL = os.getenv("PUBLISHING_URL", "http://publishing:8000")
SEO_ANALYTICS_URL = os.getenv("SEO_ANALYTICS_URL", "http://seo-analytics:8000")

# Create Celery app
app = Celery(
    "seo-automation",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

# Celery configuration
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=3600,  # 1 hour soft limit
    task_time_limit=7200,       # 2 hour hard limit
    result_expires=86400,       # Results expire after 24 hours
)

# Beat schedule - automated pipeline runs
app.conf.beat_schedule = {
    # Full pipeline every Monday at 2 AM UTC
    "full-seo-pipeline-weekly": {
        "task": "celery_app.full_seo_pipeline",
        "schedule": crontab(hour=2, minute=0, day_of_week=1),  # Monday 2 AM
        "options": {"queue": "pipeline"},
    },
    # Daily rankings check at 6 AM UTC
    "check-rankings-daily": {
        "task": "celery_app.check_rankings",
        "schedule": crontab(hour=6, minute=0),  # Daily 6 AM
        "options": {"queue": "analytics"},
    },
    # Weekly competitor analysis on Sunday at midnight
    "competitor-analysis-weekly": {
        "task": "celery_app.run_competitor_analysis",
        "schedule": crontab(hour=0, minute=0, day_of_week=0),  # Sunday midnight
        "options": {"queue": "analysis"},
    },
    # Daily keyword discovery at 4 AM
    "keyword-discovery-daily": {
        "task": "celery_app.run_keyword_discovery",
        "schedule": crontab(hour=4, minute=0),
        "options": {"queue": "discovery"},
    },
}

# Queue configuration
app.conf.task_routes = {
    "celery_app.full_seo_pipeline": {"queue": "pipeline"},
    "celery_app.check_rankings": {"queue": "analytics"},
    "celery_app.run_competitor_analysis": {"queue": "analysis"},
    "celery_app.run_keyword_discovery": {"queue": "discovery"},
    "celery_app.run_content_generation": {"queue": "generation"},
    "celery_app.run_seo_optimization": {"queue": "optimization"},
    "celery_app.run_publishing": {"queue": "publishing"},
}


def trigger_service(url: str, endpoint: str = "/run", payload: dict = None) -> dict:
    """Synchronously trigger a service endpoint."""
    try:
        with httpx.Client(timeout=300.0) as client:
            response = client.post(f"{url}{endpoint}", json=payload or {})
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Service {url}{endpoint} returned error: {e.response.status_code}")
        raise
    except Exception as e:
        logger.error(f"Failed to trigger {url}{endpoint}: {e}")
        raise


def wait_for_service_health(url: str, max_retries: int = 5) -> bool:
    """Wait for a service to be healthy."""
    import time
    for i in range(max_retries):
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{url}/health")
                if response.status_code == 200:
                    return True
        except Exception:
            pass
        time.sleep(5)
    return False


@app.task(bind=True, name="celery_app.full_seo_pipeline", max_retries=2)
def full_seo_pipeline(self):
    """
    Full SEO pipeline task.
    Orchestrates: keyword discovery -> competitor analysis -> content generation
    -> SEO optimization -> publishing -> analytics
    """
    pipeline_id = f"pipeline-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    logger.info(f"Starting full SEO pipeline: {pipeline_id}")

    steps = [
        ("Keyword Discovery", KEYWORD_DISCOVERY_URL),
        ("Competitor Analysis", COMPETITOR_ANALYSIS_URL),
        ("Content Generation", CONTENT_GENERATION_URL),
        ("SEO Optimization", SEO_OPTIMIZATION_URL),
        ("Publishing", PUBLISHING_URL),
        ("Analytics Update", SEO_ANALYTICS_URL),
    ]

    results = {"pipeline_id": pipeline_id, "steps": {}, "started_at": datetime.utcnow().isoformat()}

    for step_name, service_url in steps:
        try:
            logger.info(f"Pipeline step: {step_name}")
            result = trigger_service(service_url, "/run")
            results["steps"][step_name] = {
                "status": "success",
                "run_id": result.get("run_id"),
                "timestamp": datetime.utcnow().isoformat(),
            }
            logger.info(f"Pipeline step '{step_name}' triggered successfully")
        except Exception as e:
            logger.error(f"Pipeline step '{step_name}' failed: {e}")
            results["steps"][step_name] = {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
            # Continue pipeline even if one step fails

    results["completed_at"] = datetime.utcnow().isoformat()
    results["status"] = "completed"

    successful_steps = sum(1 for s in results["steps"].values() if s["status"] == "success")
    logger.info(
        f"Full SEO pipeline {pipeline_id} completed: "
        f"{successful_steps}/{len(steps)} steps successful"
    )

    return results


@app.task(bind=True, name="celery_app.check_rankings", max_retries=3)
def check_rankings(self):
    """Daily rankings check task."""
    logger.info("Starting daily rankings check")
    try:
        result = trigger_service(SEO_ANALYTICS_URL, "/run")
        logger.info(f"Rankings check triggered: {result.get('run_id')}")
        return {"status": "success", "run_id": result.get("run_id")}
    except Exception as e:
        logger.error(f"Rankings check failed: {e}")
        raise self.retry(exc=e, countdown=300)


@app.task(bind=True, name="celery_app.run_competitor_analysis", max_retries=2)
def run_competitor_analysis(self):
    """Weekly competitor analysis task."""
    logger.info("Starting competitor analysis")
    try:
        result = trigger_service(COMPETITOR_ANALYSIS_URL, "/run")
        logger.info(f"Competitor analysis triggered: {result.get('run_id')}")
        return {"status": "success", "run_id": result.get("run_id")}
    except Exception as e:
        logger.error(f"Competitor analysis failed: {e}")
        raise self.retry(exc=e, countdown=600)


@app.task(bind=True, name="celery_app.run_keyword_discovery", max_retries=3)
def run_keyword_discovery(self):
    """Daily keyword discovery task."""
    logger.info("Starting keyword discovery")
    try:
        result = trigger_service(KEYWORD_DISCOVERY_URL, "/run")
        logger.info(f"Keyword discovery triggered: {result.get('run_id')}")
        return {"status": "success", "run_id": result.get("run_id")}
    except Exception as e:
        logger.error(f"Keyword discovery failed: {e}")
        raise self.retry(exc=e, countdown=300)


@app.task(bind=True, name="celery_app.run_content_generation", max_retries=2)
def run_content_generation(self, max_articles: int = 5):
    """Content generation task."""
    logger.info(f"Starting content generation (max: {max_articles} articles)")
    try:
        result = trigger_service(
            CONTENT_GENERATION_URL,
            "/run",
            {"max_articles": max_articles},
        )
        return {"status": "success", "run_id": result.get("run_id")}
    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        raise self.retry(exc=e, countdown=600)


@app.task(bind=True, name="celery_app.run_seo_optimization", max_retries=3)
def run_seo_optimization(self):
    """SEO optimization task."""
    logger.info("Starting SEO optimization")
    try:
        result = trigger_service(SEO_OPTIMIZATION_URL, "/run")
        return {"status": "success", "run_id": result.get("run_id")}
    except Exception as e:
        logger.error(f"SEO optimization failed: {e}")
        raise self.retry(exc=e, countdown=300)


@app.task(bind=True, name="celery_app.run_publishing", max_retries=2)
def run_publishing(self):
    """Publishing task."""
    logger.info("Starting publishing")
    try:
        result = trigger_service(PUBLISHING_URL, "/run")
        return {"status": "success", "run_id": result.get("run_id")}
    except Exception as e:
        logger.error(f"Publishing failed: {e}")
        raise self.retry(exc=e, countdown=300)
