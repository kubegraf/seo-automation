#!/usr/bin/env python3
"""
Article HTML Renderer
Converts published markdown articles into full white-theme HTML pages.
Each article gets docs/blog/{slug}/index.html for clean URLs.
"""
import sys
import re
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

import markdown as md_lib
from shared import storage

logger = logging.getLogger(__name__)

DOCS_BLOG = Path(__file__).parent.parent / "docs" / "blog"

ARTICLE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | Kubegraf Blog</title>
  <meta name="description" content="{meta_description}">
  <meta name="keywords" content="{keywords}">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{meta_description}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="https://kubegraf.github.io/seo-automation/blog/{slug}/">
  <link rel="canonical" href="https://kubegraf.github.io/seo-automation/blog/{slug}/">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  {schema_markup}
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Inter', sans-serif; background: #f8fafc; color: #1e293b; line-height: 1.7; }}
    .navbar {{ background: #fff; border-bottom: 1px solid #e2e8f0; padding: 0 24px; display: flex; align-items: center; justify-content: space-between; min-height: 64px; position: sticky; top: 0; z-index: 50; flex-wrap: wrap; }}
    .navbar-links {{ display: flex; align-items: center; gap: 8px; }}
    .navbar-links a {{ font-size: 14px; font-weight: 500; color: #64748b; text-decoration: none; padding: 8px 14px; border-radius: 8px; }}
    .navbar-links a:hover {{ color: #2563eb; background: #eff6ff; }}
    .btn-primary {{ background: #2563eb; color: #fff !important; border-radius: 8px; font-weight: 600 !important; }}
    .hamburger {{ display: none; background: none; border: none; cursor: pointer; padding: 8px; flex-direction: column; gap: 5px; }}
    .hamburger span {{ display: block; width: 22px; height: 2px; background: #0f172a; border-radius: 2px; }}
    .mobile-menu {{ display: none; width: 100%; background: #fff; border-top: 1px solid #e2e8f0; padding: 12px 16px 20px; flex-direction: column; gap: 4px; }}
    .mobile-menu a {{ font-size: 15px; font-weight: 500; color: #374151; text-decoration: none; padding: 10px 12px; border-radius: 8px; display: block; }}
    .mobile-menu .btn-primary {{ text-align: center; margin-top: 8px; padding: 12px !important; }}
    @media (max-width: 768px) {{
      .navbar-links {{ display: none; }}
      .hamburger {{ display: flex; }}
      .mobile-menu.open {{ display: flex; }}
      .article-header {{ padding: 32px 20px 28px; }}
      .article-header h1 {{ font-size: 24px; }}
      .layout {{ grid-template-columns: 1fr; padding: 24px 16px; gap: 24px; }}
      .sidebar {{ position: static; }}
      .article-body {{ padding: 24px 16px; }}
      .article-body pre {{ margin: 16px -16px; border-radius: 0; }}
      .article-body table {{ font-size: 13px; }}
    }}
    .article-header {{ background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%); border-bottom: 1px solid #e2e8f0; padding: 56px 32px 48px; }}
    .article-header-inner {{ max-width: 800px; margin: 0 auto; }}
    .article-meta {{ display: flex; align-items: center; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }}
    .tag {{ background: #eff6ff; color: #2563eb; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }}
    .article-date {{ font-size: 13px; color: #94a3b8; }}
    .article-header h1 {{ font-size: clamp(24px, 4vw, 38px); font-weight: 800; color: #0f172a; line-height: 1.2; letter-spacing: -0.02em; margin-bottom: 16px; }}
    .article-header .lead {{ font-size: 17px; color: #64748b; line-height: 1.7; max-width: 680px; }}
    .article-stats {{ display: flex; gap: 20px; margin-top: 20px; flex-wrap: wrap; }}
    .article-stat {{ font-size: 12px; color: #94a3b8; display: flex; align-items: center; gap: 4px; }}
    .layout {{ max-width: 1100px; margin: 0 auto; padding: 48px 32px; display: grid; grid-template-columns: 1fr 280px; gap: 48px; align-items: start; }}
    .article-body {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 48px; }}
    .article-body h1 {{ font-size: 28px; font-weight: 800; color: #0f172a; margin: 40px 0 16px; letter-spacing: -0.02em; }}
    .article-body h2 {{ font-size: 22px; font-weight: 700; color: #0f172a; margin: 36px 0 14px; padding-bottom: 8px; border-bottom: 2px solid #e2e8f0; letter-spacing: -0.01em; }}
    .article-body h3 {{ font-size: 18px; font-weight: 600; color: #1e293b; margin: 28px 0 12px; }}
    .article-body h4 {{ font-size: 15px; font-weight: 600; color: #374151; margin: 20px 0 8px; }}
    .article-body p {{ font-size: 16px; color: #374151; line-height: 1.8; margin-bottom: 16px; }}
    .article-body ul, .article-body ol {{ padding-left: 24px; margin-bottom: 16px; }}
    .article-body li {{ font-size: 16px; color: #374151; line-height: 1.7; margin-bottom: 6px; }}
    .article-body a {{ color: #2563eb; text-decoration: none; border-bottom: 1px solid #bfdbfe; }}
    .article-body a:hover {{ border-bottom-color: #2563eb; }}
    .article-body pre {{ background: #0f172a; border-radius: 10px; padding: 20px 24px; margin: 24px 0; overflow-x: auto; }}
    .article-body pre code {{ font-family: 'JetBrains Mono', monospace; font-size: 13px; color: #e2e8f0; background: none; padding: 0; border-radius: 0; }}
    .article-body code {{ font-family: 'JetBrains Mono', monospace; font-size: 13px; background: #f1f5f9; color: #0f172a; padding: 2px 6px; border-radius: 4px; }}
    .article-body blockquote {{ border-left: 4px solid #2563eb; background: #eff6ff; padding: 16px 20px; border-radius: 0 8px 8px 0; margin: 24px 0; }}
    .article-body blockquote p {{ color: #1e40af; margin: 0; }}
    .article-body table {{ width: 100%; border-collapse: collapse; margin: 24px 0; font-size: 14px; }}
    .article-body th {{ background: #f8fafc; padding: 10px 14px; text-align: left; font-weight: 600; border: 1px solid #e2e8f0; color: #374151; }}
    .article-body td {{ padding: 10px 14px; border: 1px solid #e2e8f0; color: #374151; }}
    .article-body tr:hover td {{ background: #f8fafc; }}
    .article-body img {{ max-width: 100%; border-radius: 8px; margin: 16px 0; }}
    .article-body hr {{ border: none; border-top: 1px solid #e2e8f0; margin: 32px 0; }}
    /* Sidebar */
    .sidebar {{ position: sticky; top: 80px; }}
    .sidebar-card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; margin-bottom: 20px; }}
    .sidebar-card h3 {{ font-size: 13px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 14px; }}
    .sidebar-card a {{ display: block; font-size: 13px; color: #374151; text-decoration: none; padding: 6px 0; border-bottom: 1px solid #f1f5f9; }}
    .sidebar-card a:last-child {{ border-bottom: none; }}
    .sidebar-card a:hover {{ color: #2563eb; }}
    .keyword-tags {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .keyword-tag {{ background: #f1f5f9; color: #475569; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 500; }}
    .cta-card {{ background: linear-gradient(135deg, #2563eb, #1d4ed8); border-radius: 12px; padding: 24px; color: #fff; }}
    .cta-card h3 {{ font-size: 15px; font-weight: 700; margin-bottom: 8px; color: #fff; }}
    .cta-card p {{ font-size: 13px; color: #bfdbfe; line-height: 1.5; margin-bottom: 16px; }}
    .cta-card a {{ display: inline-block; background: #fff; color: #2563eb; padding: 9px 18px; border-radius: 8px; font-size: 13px; font-weight: 700; text-decoration: none; }}
    .breadcrumb {{ font-size: 13px; color: #94a3b8; margin-bottom: 12px; }}
    .breadcrumb a {{ color: #64748b; text-decoration: none; }}
    .breadcrumb a:hover {{ color: #2563eb; }}
    footer {{ text-align: center; padding: 32px; color: #94a3b8; font-size: 13px; border-top: 1px solid #e2e8f0; background: #fff; margin-top: 32px; }}
    footer a {{ color: #2563eb; text-decoration: none; }}
    @media (max-width: 900px) {{
      .layout {{ grid-template-columns: 1fr; }}
      .sidebar {{ position: static; }}
      .article-body {{ padding: 28px 20px; }}
    }}
  </style>
</head>
<body>

  <nav class="navbar">
    <a href="/seo-automation/" style="font-size:18px;font-weight:700;color:#2563eb;text-decoration:none;white-space:nowrap;">Kubegraf</a>
    <div class="navbar-links">
      <a href="/seo-automation/">Home</a>
      <a href="/seo-automation/blog/">Blog</a>
      <a href="/seo-automation/dashboard/">Dashboard</a>
      <a href="https://github.com/kubegraf/seo-automation" class="btn-primary">GitHub</a>
    </div>
    <button class="hamburger" onclick="this.closest('nav').querySelector('.mobile-menu').classList.toggle('open')" aria-label="Menu">
      <span></span><span></span><span></span>
    </button>
    <div class="mobile-menu">
      <a href="/seo-automation/">Home</a>
      <a href="/seo-automation/blog/" class="active">Blog</a>
      <a href="/seo-automation/dashboard/">Dashboard</a>
      <a href="https://github.com/kubegraf/seo-automation" class="btn-primary">GitHub</a>
    </div>
  </nav>

  <div class="article-header">
    <div class="article-header-inner">
      <div class="breadcrumb">
        <a href="/seo-automation/">Home</a> &rsaquo; <a href="/seo-automation/blog/">Blog</a> &rsaquo; {category}
      </div>
      <div class="article-meta">
        <span class="tag">{article_type}</span>
        <span class="tag" style="background:#f0fdf4;color:#16a34a;">{category_label}</span>
        <span class="article-date">{date}</span>
      </div>
      <h1>{title}</h1>
      <p class="lead">{meta_description}</p>
      <div class="article-stats">
        <span class="article-stat">📖 {word_count:,} words</span>
        <span class="article-stat">⏱ {read_time} min read</span>
        <span class="article-stat">✍️ Kubegraf Team</span>
      </div>
    </div>
  </div>

  <div class="layout">
    <article class="article-body">
      {content_html}
    </article>

    <aside class="sidebar">
      <div class="cta-card">
        <h3>Try Kubegraf</h3>
        <p>AI-powered Kubernetes SRE. Automatic root cause analysis and remediation.</p>
        <a href="/seo-automation/">Learn More →</a>
      </div>

      <div class="sidebar-card">
        <h3>Keywords</h3>
        <div class="keyword-tags">
          {keyword_tags}
        </div>
      </div>

      {related_articles_html}
    </aside>
  </div>

  <footer>
    <a href="/seo-automation/">Home</a> &middot;
    <a href="/seo-automation/blog/">Blog</a> &middot;
    <a href="/seo-automation/dashboard/">Dashboard</a> &middot;
    <a href="https://github.com/kubegraf/seo-automation">GitHub</a>
    <br><br>&copy; 2024 Kubegraf &middot; AI-powered Kubernetes SRE Platform
  </footer>

</body>
</html>"""


def strip_frontmatter(content: str) -> str:
    """Remove YAML frontmatter block from markdown."""
    if content.strip().startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return content.strip()


def markdown_to_html(content: str) -> str:
    """Convert markdown to HTML with extensions."""
    return md_lib.markdown(
        content,
        extensions=["fenced_code", "tables", "toc", "nl2br", "codehilite"],
        extension_configs={
            "codehilite": {"css_class": "highlight", "use_pygments": False},
        },
    )


def render_article(article, all_articles: list) -> str:
    """Render a single article to full HTML."""
    # Strip frontmatter from content
    clean_content = strip_frontmatter(article.content)
    content_html = markdown_to_html(clean_content)

    # Related articles (same category, different article)
    related = [
        a for a in all_articles
        if a.slug != article.slug and a.status == "published" and a.category == article.category
    ][:4]
    if not related:
        related = [a for a in all_articles if a.slug != article.slug and a.status == "published"][:4]

    related_html = ""
    if related:
        links = "\n".join(
            f'<a href="/seo-automation/blog/{a.slug}/">{a.title[:55]}{"…" if len(a.title) > 55 else ""}</a>'
            for a in related
        )
        related_html = f'<div class="sidebar-card"><h3>Related Articles</h3>{links}</div>'

    # Keyword tags
    keyword_tags = " ".join(
        f'<span class="keyword-tag">{kw}</span>' for kw in article.keywords
    )

    # Read time
    read_time = max(1, article.word_count // 200)

    # Date
    date_str = (article.published_at or article.created_at)[:10]
    try:
        date_fmt = datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %d, %Y")
    except ValueError:
        date_fmt = date_str

    category_label = article.category.replace("_", " ").title()
    article_type_label = article.article_type.replace("_", " ").title()

    return ARTICLE_HTML.format(
        title=article.title.replace('"', "&quot;"),
        meta_description=article.meta_description.replace('"', "&quot;"),
        keywords=", ".join(article.keywords),
        slug=article.slug,
        schema_markup=article.schema_markup or "",
        content_html=content_html,
        category=article.category,
        category_label=category_label,
        article_type=article_type_label,
        date=date_fmt,
        word_count=article.word_count,
        read_time=read_time,
        keyword_tags=keyword_tags,
        related_articles_html=related_html,
    )


def run():
    from rich.console import Console
    console = Console()

    console.print("[bold blue]🖥️  Article HTML Renderer[/bold blue]")

    articles = storage.load_articles()
    published = [a for a in articles if a.status == "published"]

    if not published:
        console.print("[yellow]No published articles to render.[/yellow]")
        return 0

    rendered = 0
    for article in published:
        try:
            html = render_article(article, published)

            # Write to docs/blog/{slug}/index.html (clean URL)
            article_dir = DOCS_BLOG / article.slug
            article_dir.mkdir(parents=True, exist_ok=True)
            out_path = article_dir / "index.html"
            out_path.write_text(html, encoding="utf-8")
            rendered += 1
            console.print(f"  [green]✓[/green] {article.slug}/index.html")
        except Exception as e:
            console.print(f"  [red]✗[/red] Failed to render {article.slug}: {e}")
            logger.error(f"Render failed for {article.slug}: {e}", exc_info=True)

    console.print(f"\n[green]✅ Rendered {rendered}/{len(published)} articles to docs/blog/*/index.html[/green]")
    return rendered


# Alias
generate = run

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
