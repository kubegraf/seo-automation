"""
Publishing Engine
Publishes optimized articles to docs/blog/ directory.
Files are committed to the repo and served via GitHub Pages.
"""
import os
import re
import logging
from pathlib import Path
from datetime import datetime
from slugify import slugify
from shared.models import Article
from shared import storage

logger = logging.getLogger(__name__)

DOCS_DIR = Path(__file__).parent.parent / "docs" / "blog"
REPO_ROOT = Path(__file__).parent.parent


def generate_frontmatter(article: Article) -> str:
    """Generate Jekyll/Hugo compatible frontmatter."""
    date = article.created_at[:10] if article.created_at else datetime.utcnow().strftime("%Y-%m-%d")
    keywords_str = ", ".join(f'"{k}"' for k in article.keywords)

    return f"""---
title: "{article.title.replace('"', "'")}"
description: "{article.meta_description.replace('"', "'")}"
date: {date}
slug: {article.slug}
keywords: [{keywords_str}]
category: {article.category}
article_type: {article.article_type}
seo_score: {article.seo_score:.1f}
word_count: {article.word_count}
layout: blog
author: Kubegraf Team
---
"""


def clean_content_for_publish(content: str) -> str:
    """Remove JSON-LD schema from markdown (it goes in HTML template instead)."""
    # Remove script tags from markdown content
    content = re.sub(r'\n<script[^>]*>.*?</script>\n', '', content, flags=re.DOTALL)
    return content.strip()


def ensure_internal_links(content: str, all_articles: list) -> str:
    """Add a 'Related Articles' section if not present."""
    if "## Related Articles" in content or "## Related" in content:
        return content
    if not all_articles:
        return content
    # Add up to 3 related article links at the end
    related = all_articles[:3]
    lines = ["\n## Related Articles\n"]
    for a in related:
        lines.append(f"- [{a.title}](/blog/{a.slug})")
    return content + "\n".join(lines)


def publish_article(article: Article, all_articles: list) -> str:
    """Write article to docs/blog/ directory. Returns file path."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Build file content
    frontmatter = generate_frontmatter(article)
    clean_content = clean_content_for_publish(article.content)

    # Remove any existing frontmatter from generated content
    if clean_content.startswith("---"):
        parts = clean_content.split("---", 2)
        if len(parts) >= 3:
            clean_content = parts[2].strip()

    full_content = frontmatter + "\n" + clean_content

    # Write file
    filename = f"{article.slug}.md"
    filepath = DOCS_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_content)

    logger.info(f"Published: {filepath}")
    return str(filepath)


def generate_blog_index(articles: list) -> str:
    """Generate a blog index page."""
    published = [a for a in articles if a.status == "published"]
    published.sort(key=lambda x: x.published_at or x.created_at, reverse=True)

    lines = [
        "---",
        "title: Kubegraf Blog",
        "description: Technical articles on Kubernetes, SRE automation, AI operations, and incident management.",
        "layout: blog-index",
        "---",
        "",
        "# Kubegraf Engineering Blog",
        "",
        "Deep technical content on Kubernetes operations, AI-driven SRE, and incident automation.",
        "",
    ]

    # Group by category
    categories = {}
    for article in published:
        cat = article.category.replace("_", " ").title()
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(article)

    for cat, cat_articles in sorted(categories.items()):
        lines.append(f"## {cat}")
        lines.append("")
        for article in cat_articles[:10]:
            date = article.published_at[:10] if article.published_at else article.created_at[:10]
            lines.append(f"- [{article.title}](/blog/{article.slug}) — *{date}*")
        lines.append("")

    return "\n".join(lines)


def run():
    """Main entrypoint for publishing pipeline step."""
    from rich.console import Console
    console = Console()

    console.print("[bold blue]🚀 Publishing Engine[/bold blue]")

    articles = storage.load_articles()
    published_count = 0

    for i, article in enumerate(articles):
        if article.status == "optimized":
            try:
                filepath = publish_article(article, articles)
                articles[i].status = "published"
                articles[i].published_at = datetime.utcnow().isoformat()
                published_count += 1
                console.print(f"  [green]✓[/green] Published: {article.slug}.md")
            except Exception as e:
                console.print(f"  [red]✗[/red] Failed to publish {article.slug}: {e}")
                logger.error(f"Publishing failed for {article.slug}: {e}")

    # Update storage
    storage.save_articles(articles)

    # Generate blog index
    index_content = generate_blog_index(articles)
    index_path = DOCS_DIR / "index.md"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)

    console.print(f"\n[green]✅ Published {published_count} articles to docs/blog/[/green]")
    return published_count


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
