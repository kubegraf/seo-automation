"""
Keyword Discovery Engine for SEO Automation Platform.
Discovers trending DevOps/K8s/SRE/AI-ops keywords and scores opportunities.
"""
import os
import logging
import random
import uuid
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")

# Seed keywords for Kubegraf's target market
SEED_KEYWORDS = [
    "kubernetes alerting",
    "sre automation",
    "ai incident response",
    "kubernetes root cause analysis",
    "prometheus alert management",
    "grafana automation",
    "kubernetes ops",
    "incident remediation ai",
    "k8s troubleshooting",
    "devops ai",
    "kubernetes monitoring",
    "sre platform",
    "ai sre",
    "kubernetes incident management",
    "automated remediation",
    "kubernetes observability",
    "site reliability engineering",
    "on-call automation",
    "kubernetes debugging",
    "platform engineering",
]

# Extended keyword categories
KEYWORD_CATEGORIES = {
    "kubernetes_operations": [
        "kubernetes pod crashloopbackoff fix",
        "kubernetes oomkilled debug",
        "kubernetes node not ready",
        "kubernetes deployment failed",
        "kubernetes resource limits",
        "kubectl troubleshooting commands",
        "kubernetes liveness probe failing",
        "kubernetes persistent volume issues",
        "kubernetes network policies",
        "kubernetes rbac configuration",
    ],
    "sre_and_reliability": [
        "sre best practices",
        "service level objectives slo",
        "error budget management",
        "reliability engineering tools",
        "chaos engineering kubernetes",
        "sre runbooks automation",
        "incident postmortem template",
        "mttr reduction strategies",
        "on-call management software",
        "pagerduty alternative",
    ],
    "ai_operations": [
        "aiops platform",
        "ai for devops",
        "machine learning operations monitoring",
        "predictive incident management",
        "anomaly detection kubernetes",
        "intelligent alerting",
        "root cause analysis automation",
        "ai observability platform",
        "natural language devops",
        "gpt kubernetes operations",
    ],
    "monitoring_observability": [
        "kubernetes monitoring tools",
        "prometheus grafana setup",
        "opentelemetry kubernetes",
        "distributed tracing kubernetes",
        "log aggregation kubernetes",
        "datadog kubernetes alternative",
        "new relic kubernetes",
        "cloud native monitoring",
        "ebpf kubernetes observability",
        "continuous profiling kubernetes",
    ],
    "incident_management": [
        "incident management platform",
        "incident response automation",
        "war room management",
        "incident communication tools",
        "statuspage alternative",
        "incident timeline tracking",
        "post-incident review automation",
        "alert fatigue reduction",
        "smart alerting platform",
        "incident management integration",
    ],
}

# Realistic search volume ranges by keyword type
VOLUME_RANGES = {
    "high": (5000, 50000),
    "medium": (1000, 5000),
    "low": (100, 1000),
    "micro": (10, 100),
}

# Difficulty ranges
DIFFICULTY_RANGES = {
    "easy": (10, 30),
    "medium": (30, 60),
    "hard": (60, 80),
    "very_hard": (80, 95),
}


class KeywordDiscoveryEngine:
    """
    Discovers and analyzes SEO keyword opportunities for Kubegraf.
    In production, integrates with SerpAPI, Google Trends, DataForSEO.
    """

    def __init__(self):
        self.serpapi_key = SERPAPI_KEY
        self.http_client = httpx.AsyncClient(timeout=30.0)
        logger.info("KeywordDiscoveryEngine initialized")

    async def get_seed_keywords(self) -> list[dict]:
        """
        Returns the hardcoded seed keyword list for DevOps/K8s/SRE.

        Returns:
            List of seed keyword dicts
        """
        seed_data = []
        for keyword in SEED_KEYWORDS:
            seed_data.append({
                "term": keyword,
                "search_volume": random.randint(*VOLUME_RANGES["medium"]),
                "difficulty": random.uniform(*DIFFICULTY_RANGES["medium"]),
                "trend": random.choice(["rising", "rising", "stable"]),  # Bias toward rising
                "intent": "informational",
                "is_seed": True,
                "category": "core",
            })
        logger.info(f"Retrieved {len(seed_data)} seed keywords")
        return seed_data

    async def discover_trending_keywords(self, topic: Optional[str] = None) -> list[dict]:
        """
        Discovers trending keywords via SerpAPI or simulation.
        In production, calls SerpAPI Google Trends endpoint.

        Args:
            topic: Optional topic to focus discovery on

        Returns:
            List of trending keyword opportunities
        """
        all_keywords = []

        # Try SerpAPI if key available
        if self.serpapi_key:
            try:
                trending = await self._fetch_from_serpapi(topic or "kubernetes")
                all_keywords.extend(trending)
                logger.info(f"Fetched {len(trending)} keywords from SerpAPI")
            except Exception as e:
                logger.warning(f"SerpAPI fetch failed, using simulated data: {e}")

        # Augment with category keywords
        for category, keywords in KEYWORD_CATEGORIES.items():
            for kw in keywords:
                # Simulate realistic metrics
                volume_tier = self._estimate_volume_tier(kw)
                difficulty_tier = self._estimate_difficulty_tier(kw)

                all_keywords.append({
                    "term": kw,
                    "search_volume": random.randint(*VOLUME_RANGES[volume_tier]),
                    "difficulty": round(random.uniform(*DIFFICULTY_RANGES[difficulty_tier]), 1),
                    "trend": self._estimate_trend(kw),
                    "intent": self._classify_intent(kw),
                    "category": category,
                    "is_seed": False,
                })

        # Add seed keywords
        seed_keywords = await self.get_seed_keywords()
        all_keywords.extend(seed_keywords)

        # Deduplicate by term
        seen = set()
        unique_keywords = []
        for kw in all_keywords:
            if kw["term"] not in seen:
                seen.add(kw["term"])
                unique_keywords.append(kw)

        logger.info(f"Discovered {len(unique_keywords)} unique keywords")
        return unique_keywords

    async def _fetch_from_serpapi(self, query: str) -> list[dict]:
        """Fetch related keywords from SerpAPI."""
        url = "https://serpapi.com/search"
        params = {
            "engine": "google_trends",
            "q": query,
            "api_key": self.serpapi_key,
            "data_type": "RELATED_QUERIES",
        }

        response = await self.http_client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        keywords = []
        related_queries = data.get("related_queries", {})

        for item in related_queries.get("rising", []):
            keywords.append({
                "term": item.get("query", ""),
                "search_volume": random.randint(500, 10000),
                "difficulty": random.uniform(20, 60),
                "trend": "rising",
                "intent": "informational",
                "category": "trending",
                "is_seed": False,
            })

        for item in related_queries.get("top", []):
            keywords.append({
                "term": item.get("query", ""),
                "search_volume": random.randint(1000, 50000),
                "difficulty": random.uniform(30, 70),
                "trend": "stable",
                "intent": "informational",
                "category": "established",
                "is_seed": False,
            })

        return keywords

    async def analyze_keyword_opportunity(self, keyword: str) -> dict:
        """
        Scores a keyword by volume, difficulty, and relevance to Kubegraf.

        Args:
            keyword: Keyword term to analyze

        Returns:
            Dict with opportunity score and analysis
        """
        # Simulate analysis (in production: call DataForSEO or Ahrefs API)
        search_volume = random.randint(100, 10000)
        difficulty = random.uniform(10, 80)

        # Calculate opportunity score
        # Formula: (volume_score * 0.4) + (ease_score * 0.35) + (relevance_score * 0.25)
        volume_score = min(100, (search_volume / 10000) * 100)
        ease_score = 100 - difficulty
        relevance_score = self._calculate_relevance(keyword)

        opportunity_score = (
            (volume_score * 0.4) +
            (ease_score * 0.35) +
            (relevance_score * 0.25)
        )

        # Determine recommended article type
        article_type = self._recommend_article_type(keyword)

        # Estimate traffic potential (CTR ~10% for position 1, volume * CTR)
        traffic_potential = int(search_volume * 0.10 * (ease_score / 100))

        result = {
            "term": keyword,
            "search_volume": search_volume,
            "difficulty": round(difficulty, 1),
            "opportunity_score": round(opportunity_score, 1),
            "volume_score": round(volume_score, 1),
            "ease_score": round(ease_score, 1),
            "relevance_score": round(relevance_score, 1),
            "recommended_article_type": article_type,
            "estimated_traffic_potential": traffic_potential,
            "trend": self._estimate_trend(keyword),
            "intent": self._classify_intent(keyword),
        }

        logger.debug(f"Analyzed keyword '{keyword}': score={opportunity_score:.1f}")
        return result

    async def discover_and_score_all(
        self,
        min_score: float = 30.0,
        max_difficulty: float = 75.0,
        min_volume: int = 100,
    ) -> list[dict]:
        """
        Full discovery and scoring pipeline.

        Args:
            min_score: Minimum opportunity score to include
            max_difficulty: Maximum keyword difficulty
            min_volume: Minimum monthly search volume

        Returns:
            Sorted list of keyword opportunities
        """
        logger.info("Starting full keyword discovery and scoring")

        # Discover all keywords
        all_keywords = await self.discover_trending_keywords()

        # Score and filter
        scored = []
        for kw in all_keywords:
            term = kw["term"]
            volume = kw.get("search_volume", 0)
            difficulty = kw.get("difficulty", 100)

            # Apply filters
            if volume < min_volume:
                continue
            if difficulty > max_difficulty:
                continue

            # Calculate opportunity score if not already done
            if "opportunity_score" not in kw:
                analysis = await self.analyze_keyword_opportunity(term)
                kw.update(analysis)
            else:
                # Calculate from existing data
                volume_score = min(100, (volume / 10000) * 100)
                ease_score = 100 - difficulty
                relevance_score = self._calculate_relevance(term)
                kw["opportunity_score"] = round(
                    (volume_score * 0.4) + (ease_score * 0.35) + (relevance_score * 0.25),
                    1
                )

            if kw.get("opportunity_score", 0) >= min_score:
                scored.append(kw)

        # Sort by opportunity score descending
        scored.sort(key=lambda x: x.get("opportunity_score", 0), reverse=True)

        logger.info(f"Discovered and scored {len(scored)} keyword opportunities")
        return scored

    def _estimate_volume_tier(self, keyword: str) -> str:
        """Estimate search volume tier based on keyword characteristics."""
        keyword_lower = keyword.lower()
        # Generic high-volume terms
        if any(term in keyword_lower for term in ["kubernetes", "devops", "monitoring"]):
            return "medium"
        # Long-tail keywords
        if len(keyword.split()) >= 4:
            return "low"
        # Specific technical terms
        if any(term in keyword_lower for term in ["oomkilled", "crashloopbackoff", "ebpf"]):
            return "micro"
        return "low"

    def _estimate_difficulty_tier(self, keyword: str) -> str:
        """Estimate keyword difficulty based on competition signals."""
        keyword_lower = keyword.lower()
        # Very competitive generic terms
        if any(term in keyword_lower for term in ["monitoring", "devops", "incident management"]):
            return "hard"
        # Medium competition
        if any(term in keyword_lower for term in ["kubernetes", "sre", "aiops"]):
            return "medium"
        # Lower competition long-tail
        if len(keyword.split()) >= 4:
            return "easy"
        return "medium"

    def _estimate_trend(self, keyword: str) -> str:
        """Estimate trend direction for a keyword."""
        keyword_lower = keyword.lower()
        # AI/ML related keywords are trending up
        if any(term in keyword_lower for term in ["ai", "llm", "gpt", "ml", "machine learning"]):
            return "rising"
        # Platform engineering is trending
        if "platform engineering" in keyword_lower:
            return "rising"
        # eBPF is trending
        if "ebpf" in keyword_lower:
            return "rising"
        # OpenTelemetry is trending
        if "opentelemetry" in keyword_lower or "otel" in keyword_lower:
            return "rising"
        # Established terms
        if any(term in keyword_lower for term in ["prometheus", "grafana"]):
            return "stable"
        return random.choice(["rising", "stable", "stable"])

    def _classify_intent(self, keyword: str) -> str:
        """Classify search intent for a keyword."""
        keyword_lower = keyword.lower()
        # Commercial intent
        if any(term in keyword_lower for term in ["best", "top", "platform", "tool", "software", "vs"]):
            return "commercial"
        # Transactional intent
        if any(term in keyword_lower for term in ["buy", "pricing", "cost", "free", "demo"]):
            return "transactional"
        # Navigational
        if any(term in keyword_lower for term in ["login", "dashboard", "download"]):
            return "navigational"
        # Default: informational
        return "informational"

    def _calculate_relevance(self, keyword: str) -> float:
        """Calculate relevance score for Kubegraf's target market."""
        keyword_lower = keyword.lower()
        score = 50.0  # Base score

        # High relevance terms for Kubegraf
        high_relevance = [
            "kubernetes", "k8s", "incident", "sre", "remediation",
            "root cause", "alerting", "monitoring", "ai", "automation",
            "devops", "platform", "reliability", "observability",
        ]
        for term in high_relevance:
            if term in keyword_lower:
                score += 10.0

        # Medium relevance
        medium_relevance = [
            "grafana", "prometheus", "helm", "operator", "cluster",
            "pod", "deployment", "service", "ingress", "node",
        ]
        for term in medium_relevance:
            if term in keyword_lower:
                score += 5.0

        return min(100.0, score)

    def _recommend_article_type(self, keyword: str) -> str:
        """Recommend the best article type for a keyword."""
        keyword_lower = keyword.lower()

        if " vs " in keyword_lower or "alternative" in keyword_lower or "comparison" in keyword_lower:
            return "comparison"
        if any(term in keyword_lower for term in ["how to", "guide", "tutorial", "setup", "install"]):
            return "tutorial"
        if any(term in keyword_lower for term in ["best", "top", "list"]):
            return "listicle"
        if any(term in keyword_lower for term in ["what is", "overview", "introduction"]):
            return "standard"
        return "standard"

    async def close(self) -> None:
        """Close HTTP client."""
        await self.http_client.aclose()
