"""
SEO Analytics Engine
Tracks rankings via SerpAPI (real) + simulated fallback.
Pulls real impressions/clicks from Google Search Console.
Generates weekly AI-powered recommendations.
"""
import json
import logging
import random
from datetime import datetime, date
from shared.gemini_client import generate
from shared.models import SEOReport
from shared import storage
from shared.serp_client import get_top_keywords_rankings, is_available as serp_available
from shared.gsc_client import get_search_performance, get_page_performance, is_available as gsc_available

logger = logging.getLogger(__name__)

# CTR curve by position (industry averages)
TRAFFIC_BY_POSITION = {
    1: 0.284, 2: 0.152, 3: 0.108, 4: 0.079, 5: 0.061,
    6: 0.049, 7: 0.039, 8: 0.032, 9: 0.026, 10: 0.022,
}

VOLUME_MAP = {"high": 5000, "medium": 1000, "low": 200}

SIMULATED_RANGES = {
    "high":    (5,  25),
    "medium":  (15, 50),
    "low":     (35, 80),
    "unknown": (50, 100),
}


def estimate_monthly_traffic(position: int, search_volume: str) -> int:
    vol = VOLUME_MAP.get(search_volume, 500)
    ctr = TRAFFIC_BY_POSITION.get(position, max(0.008, 0.25 / position))
    return int(vol * ctr)


def _simulate_position(kw) -> int:
    """Fallback simulated ranking when no real data available."""
    if kw.opportunity_score > 0.8:
        r = SIMULATED_RANGES["medium"]
    elif kw.opportunity_score > 0.6:
        r = SIMULATED_RANGES["low"]
    else:
        r = SIMULATED_RANGES["unknown"]
    return random.randint(*r)


def track_rankings(keywords: list) -> dict:
    """
    Build ranking dict for all keywords.
    Real data from SerpAPI for top 10 (if key set).
    Real data from GSC for any matching queries (if credentials set).
    Falls back to simulation for the rest.
    """
    rankings = {}

    # 1. Fetch real SerpAPI data (top 10 keywords only to preserve quota)
    real_serp = {}
    if serp_available():
        logger.info("Fetching real rankings from SerpAPI...")
        real_serp = get_top_keywords_rankings(keywords, max_queries=10)

    # 2. Fetch real GSC data
    real_gsc = {}
    if gsc_available():
        logger.info("Fetching real search performance from Google Search Console...")
        real_gsc = get_search_performance(days=28)

    # 3. Build unified rankings
    for kw in keywords:
        if kw.term in real_serp:
            data = real_serp[kw.term]
            position = data["position"]
            source = "serpapi"
        elif kw.term in real_gsc:
            data = real_gsc[kw.term]
            position = int(data["position"])
            source = "gsc"
        else:
            position = _simulate_position(kw)
            source = "simulated"

        gsc_row = real_gsc.get(kw.term, {})

        rankings[kw.term] = {
            "position": position,
            "search_volume": kw.search_volume_estimate,
            "estimated_monthly_clicks": estimate_monthly_traffic(position, kw.search_volume_estimate),
            "real_clicks_28d": gsc_row.get("clicks", 0),
            "real_impressions_28d": gsc_row.get("impressions", 0),
            "real_ctr": gsc_row.get("ctr", 0),
            "trend": kw.trend,
            "category": kw.category,
            "data_source": source,
        }

    return rankings


def get_page_traffic(articles: list) -> dict:
    """Fetch per-page traffic from GSC if available."""
    if not gsc_available():
        return {}
    page_data = get_page_performance(days=28)
    result = {}
    for article in articles:
        url = f"https://kubegraf.github.io/seo-automation/blog/{article.slug}"
        if url in page_data:
            result[article.slug] = page_data[url]
    return result


def generate_recommendations(articles, keywords, competitors, rankings: dict) -> list:
    """Use Gemini to generate specific, actionable SEO recommendations."""
    published_count = len([a for a in articles if a.status == "published"])
    avg_score = sum(a.seo_score for a in articles) / max(len(articles), 1)
    low_score = [a for a in articles if a.seo_score < 60]
    gap_keywords = []
    for c in competitors:
        gap_keywords.extend(c.gap_keywords[:3])

    # Find keywords we rank poorly for (position > 30)
    poor_rankings = [
        kw for kw, data in rankings.items()
        if data["position"] > 30 and data["data_source"] != "simulated"
    ]

    # Real traffic context
    has_real_data = any(d["data_source"] in ("serpapi", "gsc") for d in rankings.values())
    real_clicks = sum(d.get("real_clicks_28d", 0) for d in rankings.values())
    real_impressions = sum(d.get("real_impressions_28d", 0) for d in rankings.values())

    prompt = f"""You are a senior SEO strategist for Kubegraf, an AI Kubernetes SRE platform.

Current SEO state:
- Published articles: {published_count}
- Average SEO score: {avg_score:.1f}/100
- Articles scoring below 60: {len(low_score)}
- Competitor keyword gaps not yet covered: {', '.join(gap_keywords[:10])}
- Keywords with poor real rankings (position >30): {', '.join(poor_rankings[:5]) if poor_rankings else 'N/A (no real data yet)'}
- Real data available: {'Yes' if has_real_data else 'No (using estimates)'}
- Real clicks (last 28d): {real_clicks}
- Real impressions (last 28d): {real_impressions}

Generate 7 specific, actionable SEO recommendations for the next 2 weeks.
Focus on: quick wins, content gaps, internal linking, technical SEO, and competitor opportunities.
Each recommendation should be 1-2 sentences and very specific (include keyword names, article topics, actions).
Return a JSON array of 7 recommendation strings."""

    try:
        raw = generate(prompt)
        if "[" in raw and "]" in raw:
            start = raw.index("[")
            end = raw.rindex("]") + 1
            return json.loads(raw[start:end])
    except Exception as e:
        logger.warning(f"Failed to generate AI recommendations: {e}")

    return [
        f"Target '{gap_keywords[0] if gap_keywords else 'kubernetes ai debugging'}' — no top results yet, high opportunity",
        "Add FAQ schema markup to tutorial articles to capture featured snippets",
        "Create a pillar page on 'kubernetes incident management' linking all incident articles",
        "Improve internal linking: every comparison article should link to 2+ incident examples",
        "Update article titles to include the current year (2025) for freshness signals",
        "Add 'Related Articles' sections to boost time-on-page and crawl depth",
        "Submit sitemap.xml to Google Search Console to speed up indexing",
    ]


def generate_sitemap(articles: list) -> str:
    """Generate sitemap.xml for all published articles."""
    base = "https://kubegraf.github.io/seo-automation"
    urls = [
        f"""  <url>
    <loc>{base}/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>""",
        f"""  <url>
    <loc>{base}/blog/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>""",
        f"""  <url>
    <loc>{base}/dashboard/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>""",
    ]
    for a in articles:
        if a.status == "published":
            date_str = (a.published_at or a.created_at)[:10]
            urls.append(f"""  <url>
    <loc>{base}/blog/{a.slug}/</loc>
    <lastmod>{date_str}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>"""


def run():
    """Main entrypoint for SEO analytics pipeline step."""
    from pathlib import Path
    from rich.console import Console
    console = Console()

    console.print("[bold blue]📊 SEO Analytics Engine[/bold blue]")
    console.print(f"  SerpAPI: {'✅ enabled' if serp_available() else '⚠️  not configured (simulated rankings)'}")
    console.print(f"  Google Search Console: {'✅ enabled' if gsc_available() else '⚠️  not configured (no real traffic)'}")

    articles = storage.load_articles()
    keywords = storage.load_keywords()
    competitors = storage.load_competitors()
    reports = storage.load_reports()

    # Track rankings (real + simulated)
    rankings = track_rankings(keywords[:40])

    # Per-page traffic from GSC
    page_traffic = get_page_traffic([a for a in articles if a.status == "published"])

    # Stats
    published_articles = [a for a in articles if a.status == "published"]
    total_estimated_traffic = sum(v["estimated_monthly_clicks"] for v in rankings.values())
    total_real_clicks = sum(v.get("real_clicks_28d", 0) for v in rankings.values())
    total_real_impressions = sum(v.get("real_impressions_28d", 0) for v in rankings.values())
    top_keywords = sorted(rankings.items(), key=lambda x: x[1]["position"])[:10]
    real_data_count = sum(1 for d in rankings.values() if d["data_source"] != "simulated")

    today = date.today()
    week_str = f"{today.year}-W{today.isocalendar()[1]:02d}"

    # Generate AI recommendations
    recommendations = generate_recommendations(articles, keywords, competitors, rankings)

    # Build report
    report = SEOReport(
        week=week_str,
        articles_generated=len(articles),
        articles_published=len(published_articles),
        keywords_discovered=len(keywords),
        competitors_analyzed=len([c for c in competitors if c.last_analyzed]),
        top_keywords=[kw for kw, _ in top_keywords[:5]],
        top_articles=[
            a.title for a in sorted(published_articles, key=lambda x: x.seo_score, reverse=True)[:5]
        ],
        recommendations=recommendations,
    )
    reports.append(report)
    storage.save_reports(reports)

    # Save full rankings to data/rankings.json for dashboard use
    rankings_path = Path(__file__).parent.parent / "data" / "rankings.json"
    rankings_path.parent.mkdir(exist_ok=True)
    rankings_path.write_text(
        json.dumps({"week": week_str, "rankings": rankings, "page_traffic": page_traffic}, indent=2),
        encoding="utf-8",
    )

    # Generate and save sitemap.xml
    sitemap_path = Path(__file__).parent.parent / "docs" / "sitemap.xml"
    sitemap_path.write_text(generate_sitemap(articles), encoding="utf-8")
    console.print("  📍 sitemap.xml updated")

    # Display summary
    console.print(f"\n[bold]📈 Week {week_str} SEO Report[/bold]")
    console.print(f"  Published articles  : {len(published_articles)}")
    console.print(f"  Keywords tracked    : {len(keywords)}")
    console.print(f"  Real ranking data   : {real_data_count} keywords")
    console.print(f"  Est. monthly traffic: {total_estimated_traffic:,} clicks")
    if total_real_clicks:
        console.print(f"  Real clicks (28d)   : {total_real_clicks:,}")
        console.print(f"  Real impressions    : {total_real_impressions:,}")
    console.print(f"\n[bold]Top Keyword Positions:[/bold]")
    for kw, data in top_keywords[:5]:
        src = "📡" if data["data_source"] != "simulated" else "~"
        console.print(f"  {src} #{data['position']:3d} | {kw[:50]}")
    console.print(f"\n[bold]Recommendations:[/bold]")
    for rec in recommendations[:4]:
        console.print(f"  • {rec[:110]}")

    return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
