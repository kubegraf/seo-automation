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
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #0f172a; color: #e2e8f0; }}
        .header {{ background: linear-gradient(135deg, #1e3a8a, #1e40af); padding: 24px 32px; border-bottom: 1px solid #334155; }}
        .header h1 {{ font-size: 24px; font-weight: 700; color: #fff; }}
        .header p {{ color: #94a3b8; margin-top: 4px; font-size: 14px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; padding: 24px 32px; }}
        .stat-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; }}
        .stat-card .label {{ font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }}
        .stat-card .value {{ font-size: 32px; font-weight: 700; color: #3b82f6; margin-top: 8px; }}
        .stat-card .sub {{ font-size: 12px; color: #94a3b8; margin-top: 4px; }}
        .section {{ padding: 0 32px 32px; }}
        .section h2 {{ font-size: 18px; font-weight: 600; color: #f1f5f9; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid #334155; }}
        .table {{ width: 100%; border-collapse: collapse; }}
        .table th {{ text-align: left; padding: 10px 12px; font-size: 12px; color: #64748b; text-transform: uppercase; border-bottom: 1px solid #334155; }}
        .table td {{ padding: 12px; font-size: 14px; border-bottom: 1px solid #1e293b; }}
        .table tr:hover td {{ background: #1e293b; }}
        .badge {{ display: inline-block; padding: 2px 8px; border-radius: 9999px; font-size: 11px; font-weight: 500; }}
        .badge-green {{ background: #064e3b; color: #34d399; }}
        .badge-blue {{ background: #1e3a5f; color: #60a5fa; }}
        .badge-yellow {{ background: #451a03; color: #fbbf24; }}
        .badge-red {{ background: #450a0a; color: #f87171; }}
        .score-bar {{ display: inline-flex; align-items: center; gap: 8px; }}
        .score-fill {{ height: 6px; border-radius: 3px; background: #3b82f6; }}
        .tabs {{ display: flex; gap: 4px; margin-bottom: 20px; }}
        .tab {{ padding: 8px 16px; border-radius: 8px; font-size: 14px; cursor: pointer; border: 1px solid #334155; color: #94a3b8; background: transparent; }}
        .tab.active {{ background: #1e3a8a; color: #fff; border-color: #3b82f6; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        .recommendations {{ list-style: none; }}
        .recommendations li {{ padding: 12px 16px; background: #1e293b; border-radius: 8px; margin-bottom: 8px; border-left: 3px solid #3b82f6; font-size: 14px; }}
        .competitor-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }}
        .competitor-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; }}
        .competitor-card h3 {{ font-size: 16px; font-weight: 600; color: #f1f5f9; margin-bottom: 8px; }}
        .competitor-card .domain {{ font-size: 12px; color: #64748b; margin-bottom: 12px; }}
        .gap-tags {{ display: flex; flex-wrap: wrap; gap: 6px; }}
        .gap-tag {{ padding: 3px 8px; background: #0f2942; color: #60a5fa; border-radius: 4px; font-size: 11px; }}
        footer {{ padding: 24px 32px; text-align: center; color: #475569; font-size: 12px; border-top: 1px solid #1e293b; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Kubegraf SEO Dashboard</h1>
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
            <button class="tab active" onclick="showTab('articles', event)">📝 Articles</button>
            <button class="tab" onclick="showTab('keywords', event)">🔍 Keywords</button>
            <button class="tab" onclick="showTab('competitors', event)">🔬 Competitors</button>
            <button class="tab" onclick="showTab('analytics', event)">📊 Analytics</button>
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
        Kubegraf SEO Automation — Generated by AI pipeline — <a href="https://github.com/kubegraf/seo-automation" style="color: #3b82f6;">View on GitHub</a>
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
            <td><a href="/blog/{a.slug}" style="color:#60a5fa;">{a.title[:70]}</a></td>
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
        articles_rows=articles_rows or '<tr><td colspan="6" style="text-align:center;color:#475569;">No articles yet</td></tr>',
        keywords_rows=keywords_rows or '<tr><td colspan="6" style="text-align:center;color:#475569;">No keywords yet</td></tr>',
        competitor_cards=competitor_cards or '<div style="color:#475569;">No competitors analyzed yet</div>',
        recommendations_html=recommendations_html,
        reports_rows=reports_rows or '<tr><td colspan="4" style="text-align:center;color:#475569;">No reports yet</td></tr>',
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
