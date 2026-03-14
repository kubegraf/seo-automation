"""
SEO Optimization Engine
Scores and optimizes articles for search engines.
Adds schema markup, optimizes headings, calculates SEO score.
"""
import json
import re
import logging
from shared.gemini_client import generate_json
from shared.models import Article
from shared import storage

logger = logging.getLogger(__name__)


def calculate_seo_score(article: Article) -> float:
    """Calculate SEO score 0-100 based on multiple factors."""
    score = 0.0
    content = article.content.lower()
    primary_kw = article.keywords[0].lower() if article.keywords else ""

    # Title optimization (20 points)
    if primary_kw in article.title.lower():
        score += 15
    if 30 <= len(article.title) <= 65:
        score += 5

    # Meta description (15 points)
    if article.meta_description:
        if primary_kw in article.meta_description.lower():
            score += 8
        if 100 <= len(article.meta_description) <= 160:
            score += 7

    # Content length (20 points)
    word_count = len(article.content.split())
    if word_count >= 2000:
        score += 20
    elif word_count >= 1500:
        score += 15
    elif word_count >= 1000:
        score += 10
    elif word_count >= 500:
        score += 5

    # Keyword density (15 points) - target 1-2%
    if primary_kw:
        kw_count = content.count(primary_kw)
        density = kw_count / max(len(content.split()), 1)
        if 0.005 <= density <= 0.025:
            score += 15
        elif density > 0:
            score += 8

    # Heading structure (15 points)
    h1_count = len(re.findall(r'^# .+', article.content, re.MULTILINE))
    h2_count = len(re.findall(r'^## .+', article.content, re.MULTILINE))
    h3_count = len(re.findall(r'^### .+', article.content, re.MULTILINE))
    if h1_count == 1:
        score += 5
    if h2_count >= 3:
        score += 5
    if h3_count >= 2:
        score += 5

    # Code blocks (10 points)
    code_blocks = article.content.count("```")
    if code_blocks >= 4:
        score += 10
    elif code_blocks >= 2:
        score += 7
    elif code_blocks >= 1:
        score += 3

    # Diagram (5 points)
    if article.diagram_included:
        score += 5

    return min(score, 100.0)


def generate_schema_markup(article: Article) -> str:
    """Generate JSON-LD schema markup for the article."""
    schema = {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": article.title,
        "description": article.meta_description,
        "keywords": ", ".join(article.keywords),
        "author": {
            "@type": "Organization",
            "name": "Kubegraf",
            "url": "https://kubegraf.io"
        },
        "publisher": {
            "@type": "Organization",
            "name": "Kubegraf",
            "logo": {
                "@type": "ImageObject",
                "url": "https://kubegraf.io/logo.png"
            }
        },
        "datePublished": article.created_at[:10],
        "dateModified": article.created_at[:10],
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": f"https://kubegraf.io/blog/{article.slug}"
        },
        "about": {
            "@type": "SoftwareApplication",
            "name": "Kubegraf",
            "applicationCategory": "DevOps",
        }
    }
    return json.dumps(schema, indent=2)


def optimize_article(article: Article) -> Article:
    """Optimize article for SEO."""
    # Calculate score
    article.seo_score = calculate_seo_score(article)

    # Generate schema markup
    article.schema_markup = generate_schema_markup(article)

    # Add schema to content
    if '<script type="application/ld+json">' not in article.content:
        schema_block = f'\n<script type="application/ld+json">\n{article.schema_markup}\n</script>\n'
        article.content = article.content + schema_block

    article.status = "optimized"
    return article


def run():
    """Main entrypoint for SEO optimization pipeline step."""
    from rich.console import Console
    console = Console()

    console.print("[bold blue]⚡ SEO Optimization Engine[/bold blue]")

    articles = storage.load_articles()
    optimized_count = 0

    for i, article in enumerate(articles):
        if article.status == "draft":
            articles[i] = optimize_article(article)
            optimized_count += 1
            score_color = "green" if article.seo_score >= 70 else "yellow" if article.seo_score >= 50 else "red"
            console.print(f"  [{score_color}]{article.seo_score:.0f}/100[/{score_color}] {article.title[:60]}")

    storage.save_articles(articles)
    console.print(f"\n[green]✅ Optimized {optimized_count} articles[/green]")

    if articles:
        avg_score = sum(a.seo_score for a in articles) / len(articles)
        console.print(f"Average SEO score: {avg_score:.1f}/100")

    return articles


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
