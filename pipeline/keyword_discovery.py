"""
Keyword Discovery Engine
Discovers and scores keywords for DevOps/K8s/SRE/AI-ops domains.
Uses Gemini to expand seed keywords and evaluate opportunities.
"""
import json
import logging
import os
from datetime import datetime
from shared.gemini_client import generate_json
from shared.models import Keyword
from shared import storage

logger = logging.getLogger(__name__)

SEED_KEYWORDS = [
    # Kubernetes Operations
    "kubernetes root cause analysis",
    "kubernetes incident remediation",
    "kubernetes troubleshooting automation",
    "kubernetes alert management",
    "kubernetes crashloopbackoff fix",
    "kubernetes oomkilled remediation",
    "kubernetes pod restart loop",
    "kubernetes deployment rollback automation",
    # SRE & Reliability
    "sre automation platform",
    "ai sre platform",
    "site reliability engineering ai",
    "incident response automation",
    "automated incident remediation",
    "on-call automation",
    "runbook automation",
    # AI Operations
    "ai root cause analysis",
    "ai incident investigation",
    "machine learning ops troubleshooting",
    "llm ops kubernetes",
    "ai devops platform",
    # Monitoring & Observability
    "prometheus alert automation",
    "grafana incident response",
    "kubernetes observability ai",
    "opentelemetry kubernetes",
    "distributed tracing kubernetes",
    # Platform Engineering
    "platform engineering kubernetes",
    "kubernetes gitops automation",
    "devsecops kubernetes",
    "kubernetes cost optimization",
    "kubernetes security automation",
]

CATEGORIES = {
    "kubernetes_ops": ["kubernetes", "k8s", "pod", "deployment", "cluster"],
    "sre": ["sre", "site reliability", "on-call", "incident", "runbook"],
    "ai_operations": ["ai", "llm", "machine learning", "artificial intelligence", "automated"],
    "monitoring": ["prometheus", "grafana", "observability", "tracing", "metrics"],
    "platform_engineering": ["platform", "gitops", "devsecops", "security"],
}


def categorize_keyword(keyword: str) -> str:
    kw_lower = keyword.lower()
    for cat, signals in CATEGORIES.items():
        if any(s in kw_lower for s in signals):
            return cat
    return "general"


def discover_keywords(num_keywords: int = 20) -> list:
    """Discover and score keywords using Gemini."""
    logger.info("Starting keyword discovery...")

    # Ask Gemini to expand our seed keywords and find trending ones
    prompt = f"""You are an SEO expert for a Kubernetes AI SRE platform called Kubegraf.
Kubegraf automatically investigates Kubernetes incidents, performs root cause analysis, and applies fixes.

Given these seed keywords: {json.dumps(SEED_KEYWORDS[:15])}

Discover and return exactly {num_keywords} high-value SEO keywords for Kubegraf.
Focus on: DevOps, Kubernetes, SRE, AI-operations, incident management, observability.

For each keyword return a JSON object with:
- "term": the keyword phrase (2-5 words, highly specific)
- "search_volume_estimate": "high" | "medium" | "low"
- "difficulty": "high" | "medium" | "low"
- "category": one of "kubernetes_ops" | "sre" | "ai_operations" | "monitoring" | "platform_engineering"
- "trend": "rising" | "stable" | "declining"
- "opportunity_score": float 0.0-1.0 (higher = better opportunity for Kubegraf)
- "reasoning": brief reason why this keyword is valuable for Kubegraf

Return a JSON array of {num_keywords} keyword objects.
Prioritize keywords where:
1. Search volume is medium-high
2. Difficulty is medium (not too competitive)
3. Topic closely matches Kubegraf's capabilities
4. Trend is rising or stable
"""

    try:
        raw = generate_json(prompt)
        discovered = json.loads(raw)
        if not isinstance(discovered, list):
            discovered = discovered.get("keywords", [])
    except Exception as e:
        logger.error(f"Failed to parse Gemini keyword response: {e}")
        # Fall back to seed keywords with default scoring
        discovered = [
            {"term": kw, "search_volume_estimate": "medium", "difficulty": "medium",
             "category": categorize_keyword(kw), "trend": "rising", "opportunity_score": 0.7}
            for kw in SEED_KEYWORDS[:num_keywords]
        ]

    keywords = []
    for item in discovered[:num_keywords]:
        try:
            kw = Keyword(
                term=item.get("term", ""),
                search_volume_estimate=item.get("search_volume_estimate", "medium"),
                difficulty=item.get("difficulty", "medium"),
                opportunity_score=float(item.get("opportunity_score", 0.5)),
                category=item.get("category", categorize_keyword(item.get("term", ""))),
                trend=item.get("trend", "stable"),
            )
            if kw.term:
                keywords.append(kw)
        except Exception as e:
            logger.warning(f"Skipping malformed keyword: {e}")

    logger.info(f"Discovered {len(keywords)} keywords")
    return keywords


def run():
    """Main entrypoint for the keyword discovery pipeline step."""
    from rich.console import Console
    console = Console()

    console.print("[bold blue]🔍 Keyword Discovery Engine[/bold blue]")

    # Load existing keywords
    existing = storage.load_keywords()
    existing_terms = {k.term.lower() for k in existing}

    console.print(f"Existing keywords in DB: {len(existing)}")

    # Discover new keywords
    num_to_discover = int(os.environ.get("KEYWORDS_PER_RUN", "20"))
    new_keywords = discover_keywords(num_to_discover)

    # Deduplicate
    added = 0
    for kw in new_keywords:
        if kw.term.lower() not in existing_terms:
            existing.append(kw)
            existing_terms.add(kw.term.lower())
            added += 1

    # Sort by opportunity score
    existing.sort(key=lambda x: x.opportunity_score, reverse=True)

    # Save
    storage.save_keywords(existing)
    console.print(f"[green]✅ Added {added} new keywords. Total: {len(existing)}[/green]")

    # Print top 10
    console.print("\n[bold]Top 10 Keyword Opportunities:[/bold]")
    for kw in existing[:10]:
        console.print(f"  [{kw.trend}] {kw.term} | score: {kw.opportunity_score:.2f} | vol: {kw.search_volume_estimate}")

    return existing


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
