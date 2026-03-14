#!/usr/bin/env python3
"""
Generates a static HTML SEO dashboard page.
This is committed to docs/dashboard/index.html and served via GitHub Pages.
"""
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared import storage

DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kubegraf SEO Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: #f8fafc; color: #1e293b; }}

        /* Navbar */
        .navbar {{ background: #fff; border-bottom: 1px solid #e2e8f0; padding: 0 32px; display: flex; align-items: center; justify-content: space-between; height: 64px; position: sticky; top: 0; z-index: 50; }}
        .navbar-brand {{ font-size: 18px; font-weight: 700; color: #2563eb; text-decoration: none; letter-spacing: -0.01em; white-space: nowrap; }}
        .navbar-links {{ display: flex; align-items: center; gap: 8px; }}
        .navbar-links a {{ font-size: 14px; font-weight: 500; color: #64748b; text-decoration: none; padding: 8px 14px; border-radius: 8px; transition: all 0.15s; }}
        .navbar-links a:hover {{ color: #2563eb; background: #eff6ff; }}
        .navbar-links a.active {{ color: #2563eb; background: #eff6ff; }}
        .btn-primary {{ background: #2563eb; color: #fff !important; padding: 8px 18px !important; border-radius: 8px; font-weight: 600 !important; }}
        .btn-primary:hover {{ background: #1d4ed8 !important; color: #fff !important; }}

        /* Page header */
        .page-header {{ background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%); border-bottom: 1px solid #e2e8f0; padding: 36px 32px 28px; }}
        .page-header h1 {{ font-size: 26px; font-weight: 700; color: #0f172a; }}
        .page-header p {{ color: #64748b; margin-top: 4px; font-size: 14px; }}

        /* Stats */
        .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; padding: 24px 32px; }}
        .stat-card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; transition: box-shadow 0.15s; }}
        .stat-card:hover {{ box-shadow: 0 4px 16px rgba(37,99,235,0.07); }}
        .stat-card .label {{ font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 500; }}
        .stat-card .value {{ font-size: 34px; font-weight: 700; color: #2563eb; margin-top: 8px; }}
        .stat-card .sub {{ font-size: 12px; color: #94a3b8; margin-top: 4px; }}

        /* Section */
        .section {{ padding: 0 32px 40px; }}
        .section h2 {{ font-size: 16px; font-weight: 600; color: #0f172a; margin-bottom: 16px; padding-bottom: 10px; border-bottom: 1px solid #e2e8f0; }}

        /* Table */
        .table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; }}
        .table th {{ text-align: left; padding: 10px 16px; font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.04em; background: #f8fafc; border-bottom: 1px solid #e2e8f0; font-weight: 600; }}
        .table td {{ padding: 13px 16px; font-size: 14px; border-bottom: 1px solid #f1f5f9; color: #374151; }}
        .table tr:last-child td {{ border-bottom: none; }}
        .table tr:hover td {{ background: #f8fafc; }}

        /* Badges */
        .badge {{ display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }}
        .badge-green {{ background: #dcfce7; color: #16a34a; }}
        .badge-blue {{ background: #dbeafe; color: #2563eb; }}
        .badge-yellow {{ background: #fef9c3; color: #ca8a04; }}
        .badge-red {{ background: #fee2e2; color: #dc2626; }}

        /* Score bar */
        .score-bar {{ display: inline-flex; align-items: center; gap: 8px; }}
        .score-fill {{ height: 6px; border-radius: 3px; background: #2563eb; }}

        /* Tabs */
        .tabs {{ display: flex; gap: 4px; margin-bottom: 20px; background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 4px; width: fit-content; }}
        .tab {{ padding: 8px 18px; border-radius: 7px; font-size: 13px; font-weight: 500; cursor: pointer; border: none; color: #64748b; background: transparent; transition: all 0.15s; }}
        .tab.active {{ background: #2563eb; color: #fff; box-shadow: 0 1px 4px rgba(37,99,235,0.25); }}
        .tab:hover:not(.active) {{ color: #2563eb; background: #eff6ff; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}

        /* Recommendations */
        .recommendations {{ list-style: none; }}
        .recommendations li {{ padding: 12px 16px; background: #fff; border-radius: 8px; margin-bottom: 8px; border: 1px solid #e2e8f0; border-left: 3px solid #2563eb; font-size: 14px; color: #374151; }}

        /* Competitor grid */
        .competitor-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }}
        .competitor-card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; transition: box-shadow 0.15s; }}
        .competitor-card:hover {{ box-shadow: 0 4px 16px rgba(37,99,235,0.07); }}
        .competitor-card h3 {{ font-size: 15px; font-weight: 600; color: #0f172a; margin-bottom: 4px; }}
        .competitor-card .domain {{ font-size: 12px; color: #94a3b8; margin-bottom: 12px; }}
        .gap-tags {{ display: flex; flex-wrap: wrap; gap: 6px; }}
        .gap-tag {{ padding: 3px 10px; background: #eff6ff; color: #2563eb; border-radius: 20px; font-size: 11px; font-weight: 500; }}

        /* Footer */
        footer {{ padding: 24px 32px; text-align: center; color: #94a3b8; font-size: 12px; border-top: 1px solid #e2e8f0; background: #fff; margin-top: 16px; }}
        footer a {{ color: #2563eb; text-decoration: none; }}
        footer a:hover {{ text-decoration: underline; }}

        @media (max-width: 768px) {{
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .competitor-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <nav class="navbar">
        <a href="../" class="navbar-brand">Kubegraf</a>
        <div class="navbar-links">
            <a href="../">Home</a>
            <a href="../blog/">Blog</a>
            <a href="./" class="active">Dashboard</a>
            <a href="https://github.com/kubegraf/seo-automation" class="btn-primary">GitHub</a>
        </div>
    </nav>

    <div class="page-header">
        <h1>SEO Dashboard</h1>
        <p>AI-Driven SEO Automation — Last updated: {last_updated}</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="label">Published Articles</div>
            <div class="value">{published_count}</div>
            <div class="sub">{draft_count} drafts pending</div>
        </div>
        <div class="stat-card">
            <div class="label">Keywords Tracked</div>
            <div class="value">{keyword_count}</div>
            <div class="sub">Avg score: {avg_opportunity:.2f}</div>
        </div>
        <div class="stat-card">
            <div class="label">Competitors Analyzed</div>
            <div class="value">{competitor_count}</div>
            <div class="sub">{gap_keyword_count} gap keywords found</div>
        </div>
        <div class="stat-card">
            <div class="label">Avg SEO Score</div>
            <div class="value">{avg_seo_score:.0f}</div>
            <div class="sub">out of 100</div>
        </div>
    </div>

    <div class="section">
        <div class="tabs">
            <button class="tab active" onclick="showTab('articles', event)">Articles</button>
            <button class="tab" onclick="showTab('keywords', event)">Keywords</button>
            <button class="tab" onclick="showTab('competitors', event)">Competitors</button>
            <button class="tab" onclick="showTab('analytics', event)">Analytics</button>
        </div>

        <div id="articles" class="tab-content active">
            <h2>Generated Articles</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Type</th>
                        <th>Category</th>
                        <th>Words</th>
                        <th>SEO Score</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {articles_rows}
                </tbody>
            </table>
        </div>

        <div id="keywords" class="tab-content">
            <h2>Top Keyword Opportunities</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>Keyword</th>
                        <th>Category</th>
                        <th>Volume</th>
                        <th>Difficulty</th>
                        <th>Trend</th>
                        <th>Opportunity</th>
                    </tr>
                </thead>
                <tbody>
                    {keywords_rows}
                </tbody>
            </table>
        </div>

        <div id="competitors" class="tab-content">
            <h2>Competitor Analysis</h2>
            <div class="competitor-grid">
                {competitor_cards}
            </div>
        </div>

        <div id="analytics" class="tab-content">
            <h2>Recommendations</h2>
            {recommendations_html}

            <br>
            <h2>Recent Reports</h2>
            <table class="table">
                <thead>
                    <tr><th>Week</th><th>Articles Generated</th><th>Published</th><th>Keywords</th></tr>
                </thead>
                <tbody>
                    {reports_rows}
                </tbody>
            </table>
        </div>
    </div>

    <footer>
        Kubegraf SEO Automation — Generated by AI pipeline —
        <a href="https://github.com/kubegraf/seo-automation">View on GitHub</a>
        <br><br>© 2024 Kubegraf · AI-powered Kubernetes SRE Platform
    </footer>

    <script>
        function showTab(name, event) {{
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            document.getElementById(name).classList.add('active');
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>'''

STATUS_BADGE = {
    "published": '<span class="badge badge-green">published</span>',
    "optimized": '<span class="badge badge-blue">optimized</span>',
    "draft": '<span class="badge badge-yellow">draft</span>',
}

TREND_BADGE = {
    "rising": '<span class="badge badge-green">↑ rising</span>',
    "stable": '<span class="badge badge-blue">→ stable</span>',
    "declining": '<span class="badge badge-red">↓ declining</span>',
}


def generate():
    articles = storage.load_articles()
    keywords = storage.load_keywords()
    competitors = storage.load_competitors()
    reports = storage.load_reports()

    published = [a for a in articles if a.status == "published"]
    drafts = [a for a in articles if a.status == "draft"]
    avg_seo = sum(a.seo_score for a in articles) / max(len(articles), 1)
    gap_count = sum(len(c.gap_keywords) for c in competitors)
    avg_opp = sum(k.opportunity_score for k in keywords) / max(len(keywords), 1)

    # Articles rows
    articles_rows = ""
    for a in sorted(articles, key=lambda x: x.created_at, reverse=True)[:20]:
        score_pct = int(a.seo_score)
        articles_rows += f'''<tr>
            <td><a href="/blog/{a.slug}" style="color:#2563eb;">{a.title[:70]}</a></td>
            <td>{a.article_type}</td>
            <td>{a.category.replace("_"," ")}</td>
            <td>{a.word_count:,}</td>
            <td><div class="score-bar"><div class="score-fill" style="width:{score_pct}px;max-width:80px;"></div>{score_pct}</div></td>
            <td>{STATUS_BADGE.get(a.status, a.status)}</td>
        </tr>'''

    # Keywords rows
    keywords_rows = ""
    for k in sorted(keywords, key=lambda x: x.opportunity_score, reverse=True)[:20]:
        keywords_rows += f'''<tr>
            <td>{k.term}</td>
            <td>{k.category.replace("_"," ")}</td>
            <td>{k.search_volume_estimate}</td>
            <td>{k.difficulty}</td>
            <td>{TREND_BADGE.get(k.trend, k.trend)}</td>
            <td>{k.opportunity_score:.2f}</td>
        </tr>'''

    # Competitor cards
    competitor_cards = ""
    for c in competitors:
        gaps = "".join(f'<span class="gap-tag">{g}</span>' for g in c.gap_keywords[:6])
        tier_color = "green" if c.traffic_tier == "high" else ("yellow" if c.traffic_tier == "medium" else "red")
        tier_badge = f'<span class="badge badge-{tier_color}">{c.traffic_tier} traffic</span>'
        competitor_cards += f'''<div class="competitor-card">
            <h3>{c.name} {tier_badge}</h3>
            <div class="domain">{c.domain}</div>
            <div style="font-size:12px;color:#94a3b8;margin-bottom:8px;">Gap keywords:</div>
            <div class="gap-tags">{gaps if gaps else '<span style="color:#475569;">Not yet analyzed</span>'}</div>
        </div>'''

    # Recommendations
    recs = []
    if reports:
        latest_report = sorted(reports, key=lambda x: x.created_at, reverse=True)[0]
        recs = latest_report.recommendations
    if not recs:
        recs = ["Run the full pipeline to generate recommendations."]
    rec_items = "".join(f"<li>{r}</li>" for r in recs)
    recommendations_html = f'<ul class="recommendations">{rec_items}</ul>'

    # Reports rows
    reports_rows = ""
    for r in sorted(reports, key=lambda x: x.created_at, reverse=True)[:5]:
        reports_rows += f'<tr><td>{r.week}</td><td>{r.articles_generated}</td><td>{r.articles_published}</td><td>{r.keywords_discovered}</td></tr>'

    html = DASHBOARD_HTML.format(
        last_updated=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        published_count=len(published),
        draft_count=len(drafts),
        keyword_count=len(keywords),
        avg_opportunity=avg_opp,
        competitor_count=len(competitors),
        gap_keyword_count=gap_count,
        avg_seo_score=avg_seo,
        articles_rows=articles_rows or '<tr><td colspan="6" style="text-align:center;color:#94a3b8;padding:32px;">No articles yet</td></tr>',
        keywords_rows=keywords_rows or '<tr><td colspan="6" style="text-align:center;color:#94a3b8;padding:32px;">No keywords yet</td></tr>',
        competitor_cards=competitor_cards or '<div style="color:#94a3b8;">No competitors analyzed yet</div>',
        recommendations_html=recommendations_html,
        reports_rows=reports_rows or '<tr><td colspan="4" style="text-align:center;color:#94a3b8;padding:32px;">No reports yet</td></tr>',
    )

    # Write dashboard
    dashboard_dir = Path(__file__).parent.parent / "docs" / "dashboard"
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    with open(dashboard_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Dashboard generated: docs/dashboard/index.html")
    print(f"   {len(articles)} articles | {len(keywords)} keywords | {len(competitors)} competitors")


# Alias so run_step.py can call module.run() consistently
run = generate

if __name__ == "__main__":
    generate()
