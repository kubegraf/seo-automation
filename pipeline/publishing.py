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
    """Generate a white-theme HTML blog index page."""
    published = [a for a in articles if a.status == "published"]
    published.sort(key=lambda x: x.published_at or x.created_at, reverse=True)

    if published:
        cards_html = ""
        for article in published[:20]:
            date = article.published_at[:10] if article.published_at else article.created_at[:10]
            cat = article.category.replace("_", " ").title()
            desc = article.meta_description[:140] if article.meta_description else ""
            cards_html += f'''<a href="/seo-automation/blog/{article.slug}" class="article-card">
      <h2>{article.title}</h2>
      <p>{desc}</p>
      <div class="meta"><span class="tag">{cat}</span><span>{date}</span><span>{article.word_count:,} words</span></div>
    </a>\n'''
        content_html = f'<div class="articles">{cards_html}</div>'
    else:
        content_html = '''<div class="empty-state">
      <div class="icon">&#9203;</div>
      <h2>Articles Coming Soon</h2>
      <p>The AI content pipeline is generating articles. Check back after the next scheduled pipeline run (every Monday), or trigger it manually on GitHub.</p>
      <a href="https://github.com/kubegraf/seo-automation/actions">View Pipeline Status &#8594;</a>
    </div>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Kubegraf Engineering Blog</title>
  <meta name="description" content="Technical articles on Kubernetes operations, AI-driven SRE, incident automation, and observability.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: #f8fafc; color: #1e293b; }}
    .navbar {{ background: #fff; border-bottom: 1px solid #e2e8f0; padding: 0 32px; display: flex; align-items: center; justify-content: space-between; height: 64px; position: sticky; top: 0; z-index: 50; }}
    .navbar-links {{ display: flex; align-items: center; gap: 8px; }}
    .navbar-links a {{ font-size: 14px; font-weight: 500; color: #64748b; text-decoration: none; padding: 8px 14px; border-radius: 8px; }}
    .navbar-links a:hover {{ color: #2563eb; background: #eff6ff; }}
    .btn-primary {{ background: #2563eb; color: #fff !important; border-radius: 8px; font-weight: 600 !important; }}
    .hero {{ background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%); border-bottom: 1px solid #e2e8f0; padding: 56px 32px 48px; text-align: center; }}
    .hero h1 {{ font-size: 36px; font-weight: 700; color: #0f172a; margin-bottom: 14px; }}
    .hero h1 span {{ color: #2563eb; }}
    .hero p {{ font-size: 17px; color: #64748b; max-width: 560px; margin: 0 auto; line-height: 1.7; }}
    .container {{ max-width: 900px; margin: 0 auto; padding: 48px 32px; }}
    .empty-state {{ text-align: center; padding: 80px 32px; background: #fff; border: 1px solid #e2e8f0; border-radius: 16px; }}
    .empty-state .icon {{ font-size: 56px; margin-bottom: 20px; }}
    .empty-state h2 {{ font-size: 22px; font-weight: 600; color: #0f172a; margin-bottom: 10px; }}
    .empty-state p {{ color: #64748b; max-width: 480px; margin: 0 auto 24px; line-height: 1.6; font-size: 15px; }}
    .empty-state a {{ display: inline-block; background: #2563eb; color: #fff; padding: 11px 26px; border-radius: 8px; text-decoration: none; font-size: 14px; font-weight: 600; }}
    .articles {{ display: flex; flex-direction: column; gap: 16px; }}
    .article-card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; text-decoration: none; color: inherit; display: block; transition: all 0.2s; }}
    .article-card:hover {{ border-color: #2563eb; box-shadow: 0 4px 16px rgba(37,99,235,0.08); }}
    .article-card h2 {{ font-size: 17px; font-weight: 600; color: #0f172a; margin-bottom: 8px; }}
    .article-card p {{ color: #64748b; font-size: 14px; line-height: 1.6; margin-bottom: 12px; }}
    .meta {{ display: flex; gap: 12px; align-items: center; font-size: 12px; color: #94a3b8; }}
    .tag {{ background: #eff6ff; color: #2563eb; padding: 2px 10px; border-radius: 20px; font-weight: 500; font-size: 11px; }}
    footer {{ text-align: center; padding: 32px; color: #94a3b8; font-size: 13px; border-top: 1px solid #e2e8f0; background: #fff; margin-top: 48px; }}
    footer a {{ color: #2563eb; text-decoration: none; }}
  </style>
</head>
<body>
  <nav class="navbar">
    <a href="/seo-automation/" style="font-size:18px;font-weight:700;color:#2563eb;text-decoration:none;white-space:nowrap;">Kubegraf</a>
    <div class="navbar-links">
      <a href="/seo-automation/">Home</a>
      <a href="/seo-automation/blog/" style="color:#2563eb;background:#eff6ff;">Blog</a>
      <a href="/seo-automation/dashboard/">Dashboard</a>
      <a href="https://github.com/kubegraf/seo-automation" class="btn-primary">GitHub</a>
    </div>
  </nav>
  <div class="hero">
    <h1>Kubegraf <span>Engineering Blog</span></h1>
    <p>Technical articles on Kubernetes operations, AI-driven SRE, incident automation, and observability — generated automatically by the Kubegraf SEO pipeline.</p>
  </div>
  <div class="container">
    {content_html}
  </div>
  <footer>
    <a href="/seo-automation/">Home</a> &middot; <a href="/seo-automation/dashboard/">Dashboard</a> &middot; <a href="https://github.com/kubegraf/seo-automation">GitHub</a>
    <br><br>&copy; 2024 Kubegraf &middot; AI-powered Kubernetes SRE Platform
  </footer>
</body>
</html>'''


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
    index_path = DOCS_DIR / "index.html"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)

    console.print(f"\n[green]✅ Published {published_count} articles to docs/blog/[/green]")
    return published_count


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
