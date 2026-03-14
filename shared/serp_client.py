"""
SerpAPI client for real keyword ranking data.
Falls back to simulation if SERP_API_KEY is not set.
Free tier: 100 searches/month — used only for top keywords.
"""
import os
import logging
import requests

logger = logging.getLogger(__name__)

SERP_API_URL = "https://serpapi.com/search"


def is_available() -> bool:
    return bool(os.environ.get("SERP_API_KEY"))


def get_ranking(keyword: str, domain: str = "kubegraf.io") -> dict | None:
    """
    Fetch real Google ranking for a keyword.
    Returns dict with position, url, title or None on failure.
    """
    api_key = os.environ.get("SERP_API_KEY")
    if not api_key:
        return None

    try:
        resp = requests.get(
            SERP_API_URL,
            params={
                "q": keyword,
                "api_key": api_key,
                "engine": "google",
                "num": "20",
                "gl": "us",
                "hl": "en",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        organic = data.get("organic_results", [])
        for i, result in enumerate(organic, start=1):
            link = result.get("link", "")
            if domain in link or "kubegraf" in link.lower():
                return {
                    "position": i,
                    "url": link,
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "source": "serpapi",
                }

        # Not ranking yet
        return {"position": 100, "url": "", "title": "", "snippet": "", "source": "serpapi"}

    except Exception as e:
        logger.warning(f"SerpAPI error for '{keyword}': {e}")
        return None


def get_top_keywords_rankings(keywords: list, max_queries: int = 10) -> dict:
    """
    Fetch real rankings for the top N keywords (conserves free-tier quota).
    Returns {keyword: ranking_dict}.
    """
    if not is_available():
        logger.info("SERP_API_KEY not set — skipping real ranking fetch")
        return {}

    results = {}
    # Only query top keywords by opportunity score to save API calls
    top = sorted(keywords, key=lambda k: k.opportunity_score, reverse=True)[:max_queries]

    for kw in top:
        ranking = get_ranking(kw.term)
        if ranking:
            results[kw.term] = ranking
            logger.info(f"Real ranking for '{kw.term}': #{ranking['position']}")

    return results
