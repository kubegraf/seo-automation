"""
Backlink Automation Engine
Identifies backlink opportunities and tracks link building.
"""
import json
import logging
from shared.gemini_client import generate_json
from shared import storage

logger = logging.getLogger(__name__)

BACKLINK_TARGETS = [
    {"site": "dev.to", "type": "developer_community", "approach": "cross_post"},
    {"site": "medium.com", "type": "technical_blog", "approach": "cross_post"},
    {"site": "dzone.com", "type": "developer_news", "approach": "syndication"},
    {"site": "reddit.com/r/kubernetes", "type": "community", "approach": "engagement"},
    {"site": "reddit.com/r/devops", "type": "community", "approach": "engagement"},
    {"site": "hashnode.com", "type": "developer_blog", "approach": "cross_post"},
    {"site": "kubernetes.io/blog", "type": "official_docs", "approach": "contribute"},
    {"site": "cncf.io", "type": "foundation", "approach": "contribute"},
]


def identify_opportunities() -> list:
    """Identify backlink opportunities based on published articles."""
    articles = storage.load_articles()
    published = [a for a in articles if a.status == "published"]

    if not published:
        return []

    opportunities = []
    for article in published[:5]:
        for target in BACKLINK_TARGETS:
            opportunities.append({
                "article_title": article.title,
                "article_slug": article.slug,
                "target_site": target["site"],
                "approach": target["approach"],
                "priority": "high" if article.seo_score > 70 else "medium",
            })

    return opportunities


def run():
    """Main entrypoint for backlink automation pipeline step."""
    from rich.console import Console
    console = Console()

    console.print("[bold blue]🔗 Backlink Automation Engine[/bold blue]")

    opportunities = identify_opportunities()

    if not opportunities:
        console.print("[yellow]No published articles yet. Backlink opportunities will appear after publishing.[/yellow]")
        return []

    console.print(f"\n[bold]Top Backlink Opportunities:[/bold]")
    shown = set()
    for opp in opportunities[:10]:
        key = opp["target_site"]
        if key not in shown:
            console.print(f"  {opp['target_site']} [{opp['approach']}] -> {opp['article_title'][:50]}")
            shown.add(key)

    console.print(f"\n[green]✅ Identified {len(opportunities)} backlink opportunities[/green]")
    return opportunities


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
