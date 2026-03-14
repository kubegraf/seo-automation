"""
Google Search Console client for real impressions/clicks data.
Requires GSC_CREDENTIALS env var (JSON service account key, base64 encoded).
Falls back gracefully if not configured.

Setup:
1. Create a Google Cloud project
2. Enable Search Console API
3. Create a Service Account, download JSON key
4. Add service account email to Search Console property as Owner
5. base64-encode the JSON: base64 -i service-account.json
6. Add as GitHub secret GSC_CREDENTIALS
"""
import os
import json
import base64
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

SITE_URL = "https://kubegraf.github.io/seo-automation/"


def is_available() -> bool:
    return bool(os.environ.get("GSC_CREDENTIALS"))


def _get_service():
    """Build authenticated GSC service."""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds_b64 = os.environ.get("GSC_CREDENTIALS", "")
        creds_json = json.loads(base64.b64decode(creds_b64).decode("utf-8"))

        credentials = service_account.Credentials.from_service_account_info(
            creds_json,
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
        )
        return build("searchconsole", "v1", credentials=credentials)
    except Exception as e:
        logger.warning(f"Failed to build GSC service: {e}")
        return None


def get_search_performance(days: int = 28) -> dict:
    """
    Fetch real search performance: clicks, impressions, CTR, position.
    Returns summary dict or empty dict if unavailable.
    """
    if not is_available():
        logger.info("GSC_CREDENTIALS not set — skipping real search performance fetch")
        return {}

    service = _get_service()
    if not service:
        return {}

    try:
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)

        response = service.searchanalytics().query(
            siteUrl=SITE_URL,
            body={
                "startDate": str(start_date),
                "endDate": str(end_date),
                "dimensions": ["query"],
                "rowLimit": 50,
            },
        ).execute()

        rows = response.get("rows", [])
        results = {}
        for row in rows:
            query = row["keys"][0]
            results[query] = {
                "clicks": row.get("clicks", 0),
                "impressions": row.get("impressions", 0),
                "ctr": round(row.get("ctr", 0) * 100, 2),
                "position": round(row.get("position", 0), 1),
                "source": "gsc",
            }

        logger.info(f"GSC: fetched {len(results)} queries with real data")
        return results

    except Exception as e:
        logger.warning(f"GSC query failed: {e}")
        return {}


def get_page_performance(days: int = 28) -> dict:
    """Fetch per-page performance from GSC."""
    if not is_available():
        return {}

    service = _get_service()
    if not service:
        return {}

    try:
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)

        response = service.searchanalytics().query(
            siteUrl=SITE_URL,
            body={
                "startDate": str(start_date),
                "endDate": str(end_date),
                "dimensions": ["page"],
                "rowLimit": 50,
            },
        ).execute()

        rows = response.get("rows", [])
        results = {}
        for row in rows:
            page = row["keys"][0]
            results[page] = {
                "clicks": row.get("clicks", 0),
                "impressions": row.get("impressions", 0),
                "ctr": round(row.get("ctr", 0) * 100, 2),
                "position": round(row.get("position", 0), 1),
            }

        return results

    except Exception as e:
        logger.warning(f"GSC page query failed: {e}")
        return {}
