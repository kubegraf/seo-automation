"""
SEO Analytics Engine
Tracks rankings, calculates traffic estimates, generates weekly reports.
"""
import json
import logging
import random
from datetime import datetime, timedelta
from shared.gemini_client import generate
from shared.models import SEOReport
from shared import storage

logger = logging.getLogger(__name__)

RANKING_POSITIONS = {
    "high": (1, 15),
    "medium": (5, 40),
    "low": (20, 80),
    "unknown": (30, 100),
}

TRAFFIC_BY_POSITION = {
    1: 0.28, 2: 0.15, 3: 0.11, 4: 0.08, 5: 0.07,
    6: 0.06, 7: 0.05, 8: 0.04, 9: 0.03, 10: 0.025,
}


def estimate_monthly_traffic(position: int, search_volume: str) -> int:
    """Estimate monthly organic traffic clicks."""
    volume_map = {"high": 5000, "medium": 1000, "low": 200}
    vol = volume_map.get(search_volume, 500)
    ctr = TRAFFIC_BY_POSITION.get(position, max(0.01, 0.3 / position))
    return int(vol * ctr)


def track_rankings(keywords) -> dict:
    """Simulate rank tracking (in production: use SerpAPI or Google Search Console)."""
    rankings = {}
    for kw in keywords:
        # Simulate ranking based on opportunity score
        if kw.opportunity_score > 0.8:
            pos_range = RANKING_POSITIONS["medium"]
        elif kw.opportunity_score > 0.6:
            pos_range = RANKING_POSITIONS["low"]
        else:
            pos_range = RANKING_POSITIONS["unknown"]

        position = random.randint(*pos_range)
        rankings[kw.term] = {
            "position": position,
            "search_volume": kw.search_volume_estimate,
            "estimated_monthly_clicks": estimate_monthly_traffic(position, kw.search_volume_estimate),
            "trend": kw.trend,
            "category": kw.category,
        }
    return rankings


def generate_recommendations(articles, keywords, competitors) -> list:
    """Use Gemini to generate SEO recommendations."""
    published_count = len([a for a in articles if a.status == "published"])
    low_score_articles = [a for a in articles if a.seo_score < 60]
    gap_keywords = []
    for c in competitors:
        gap_keywords.extend(c.gap_keywords[:3])

    prompt = f"""You are an SEO strategist for Kubegraf, an AI Kubernetes SRE platform.

Current state:
- Published articles: {published_count}
- Average SEO score: {sum(a.seo_score for a in articles) / max(len(articles), 1):.1f}/100
- Articles needing improvement (score < 60): {len(low_score_articles)}
- Keyword opportunities not yet covered: {gap_keywords[:10]}

Generate 5 specific, actionable SEO recommendations for the next week.
Return a JSON array of 5 recommendation strings.
Each recommendation should be specific and actionable (e.g., "Write a tutorial on 'specific topic' targeting 'specific keyword' -- currently no top results for this query").
"""
    try:
        raw = generate(prompt)
        # Parse the list from response
        if "[" in raw and "]" in raw:
            start = raw.index("[")
            end = raw.rindex("]") + 1
            return json.loads(raw[start:end])
    except Exception as e:
        logger.warning(f"Failed to generate AI recommendations: {e}")

    return [
        "Improve internal linking between comparison articles",
        f"Create articles targeting competitor gap keywords: {', '.join(gap_keywords[:3])}",
        "Add FAQ schema markup to tutorial articles for featured snippets",
        "Increase article word count for low-SEO-score articles to 2000+ words",
        "Create a pillar page targeting 'kubernetes incident management' with cluster content",
    ]


def run():
    """Main entrypoint for SEO analytics pipeline step."""
    from datetime import date
    from rich.console import Console
    console = Console()

    console.print("[bold blue]📊 SEO Analytics Engine[/bold blue]")

    articles = storage.load_articles()
    keywords = storage.load_keywords()
    competitors = storage.load_competitors()
    reports = storage.load_reports()

    # Track rankings
    rankings = track_rankings(keywords[:30])

    # Calculate stats
    published_articles = [a for a in articles if a.status == "published"]
    total_estimated_traffic = sum(v["estimated_monthly_clicks"] for v in rankings.values())
    top_keywords = sorted(rankings.items(), key=lambda x: x[1]["position"])[:10]

    # Get current week
    today = date.today()
    week_str = f"{today.year}-W{today.isocalendar()[1]:02d}"

    # Generate recommendations
    recommendations = generate_recommendations(articles, keywords, competitors)

    # Build report
    report = SEOReport(
        week=week_str,
        articles_generated=len(articles),
        articles_published=len(published_articles),
        keywords_discovered=len(keywords),
        competitors_analyzed=len([c for c in competitors if c.last_analyzed]),
        top_keywords=[kw for kw, _ in top_keywords[:5]],
        top_articles=[a.title for a in sorted(published_articles, key=lambda x: x.seo_score, reverse=True)[:5]],
        recommendations=recommendations,
    )

    # Save report
    reports.append(report)
    storage.save_reports(reports)

    # Display summary
    console.print(f"\n[bold]📈 Week {week_str} SEO Report[/bold]")
    console.print(f"  Published articles: {len(published_articles)}")
    console.print(f"  Keywords tracked: {len(keywords)}")
    console.print(f"  Estimated monthly traffic: {total_estimated_traffic:,} clicks")
    console.print(f"\n[bold]Top Keyword Positions:[/bold]")
    for kw, data in top_keywords[:5]:
        console.print(f"  #{data['position']:3d} | {kw[:50]}")
    console.print(f"\n[bold]Recommendations:[/bold]")
    for rec in recommendations[:3]:
        console.print(f"  • {rec[:100]}")

    return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
