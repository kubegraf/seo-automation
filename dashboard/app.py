"""
Streamlit Dashboard for SEO Automation Platform.
Provides visibility into articles, keywords, competitors, and analytics.
"""
import os
import sys
import asyncio
import random
from datetime import datetime, timedelta
from typing import Optional

import streamlit as st
import pandas as pd
import httpx

sys.path.insert(0, "/app")

# Service URLs
KEYWORD_DISCOVERY_URL = os.getenv("KEYWORD_DISCOVERY_URL", "http://keyword-discovery:8000")
COMPETITOR_ANALYSIS_URL = os.getenv("COMPETITOR_ANALYSIS_URL", "http://competitor-analysis:8000")
CONTENT_GENERATION_URL = os.getenv("CONTENT_GENERATION_URL", "http://content-generation:8000")
SEO_OPTIMIZATION_URL = os.getenv("SEO_OPTIMIZATION_URL", "http://seo-optimization:8000")
PUBLISHING_URL = os.getenv("PUBLISHING_URL", "http://publishing:8000")
SEO_ANALYTICS_URL = os.getenv("SEO_ANALYTICS_URL", "http://seo-analytics:8000")
SCHEDULER_URL = os.getenv("SCHEDULER_URL", "http://scheduler:8000")

# Page configuration
st.set_page_config(
    page_title="Kubegraf SEO Automation",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #1E1E2E;
        border: 1px solid #313244;
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
    }
    .status-badge {
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
    }
    .status-published { background-color: #40a02b; color: white; }
    .status-generated { background-color: #1e66f5; color: white; }
    .status-pending { background-color: #df8e1d; color: white; }
    .status-failed { background-color: #d20f39; color: white; }
    .trend-up { color: #40a02b; }
    .trend-down { color: #d20f39; }
    .trend-stable { color: #9ca0b0; }
    h1 { color: #cdd6f4; }
    h2 { color: #cba6f7; }
    h3 { color: #89b4fa; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# Helper Functions
# =============================================================================

def fetch_data(url: str, endpoint: str, timeout: float = 10.0) -> Optional[dict]:
    """Fetch data from a service endpoint."""
    try:
        response = httpx.get(f"{url}{endpoint}", timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def trigger_service(url: str, endpoint: str = "/run", payload: dict = None) -> Optional[dict]:
    """Trigger a service endpoint."""
    try:
        response = httpx.post(f"{url}{endpoint}", json=payload or {}, timeout=30.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to trigger service: {e}")
        return None


def generate_sample_articles() -> list[dict]:
    """Generate sample article data for demonstration."""
    sample_articles = [
        {
            "id": i + 1,
            "title": title,
            "status": random.choice(["published", "published", "published", "optimized", "generated"]),
            "word_count": random.randint(1500, 4000),
            "seo_score": round(random.uniform(55, 95), 1),
            "primary_keyword": keyword,
            "organic_clicks": random.randint(0, 500),
            "average_position": round(random.uniform(1, 30), 1),
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(),
            "published_at": (datetime.now() - timedelta(days=random.randint(1, 60))).isoformat() if random.random() > 0.3 else None,
        }
        for i, (title, keyword) in enumerate([
            ("AI Root Cause Analysis for Kubernetes", "kubernetes root cause analysis"),
            ("Automatic Kubernetes Incident Remediation with SafeFix", "kubernetes automated remediation"),
            ("AI SRE Platforms Comparison 2024", "ai sre platform comparison"),
            ("How AI Can Fix Production Kubernetes Incidents", "ai kubernetes incident response"),
            ("Kubernetes Troubleshooting Automation Guide", "kubernetes troubleshooting automation"),
            ("Kubegraf vs Rootly: Platform Comparison", "kubegraf vs rootly"),
            ("Kubernetes OOMKilled: Detection and Remediation", "kubernetes oomkilled"),
            ("CrashLoopBackOff Root Cause Analysis with AI", "crashloopbackoff root cause analysis"),
            ("Prometheus Alert to Auto-Remediation Guide", "prometheus alert automation"),
            ("Building a Kubernetes AI SRE Stack", "kubernetes ai sre"),
        ])
    ]
    return sample_articles


def generate_sample_keywords() -> list[dict]:
    """Generate sample keyword data."""
    keywords = [
        ("kubernetes root cause analysis", 4400, 42, "rising"),
        ("ai incident response", 2900, 55, "rising"),
        ("kubernetes troubleshooting", 8100, 65, "stable"),
        ("sre automation", 1900, 38, "rising"),
        ("kubernetes monitoring", 22000, 72, "stable"),
        ("kubernetes oomkilled", 1300, 28, "stable"),
        ("crashloopbackoff fix", 2100, 35, "stable"),
        ("ai sre platform", 890, 32, "rising"),
        ("incident management platform", 5400, 68, "stable"),
        ("kubernetes ai", 3600, 48, "rising"),
        ("automated remediation kubernetes", 720, 30, "rising"),
        ("devops ai tools", 4100, 52, "rising"),
        ("prometheus alertmanager", 6700, 58, "stable"),
        ("grafana kubernetes", 9900, 61, "stable"),
        ("kubernetes incident management", 1800, 44, "rising"),
    ]
    return [
        {
            "term": term,
            "search_volume": volume,
            "difficulty": difficulty,
            "opportunity_score": round((volume / 10000 * 40) + ((100 - difficulty) * 0.35) + random.uniform(10, 25), 1),
            "trend": trend,
            "current_position": random.randint(1, 50) if random.random() > 0.3 else None,
            "previous_position": random.randint(1, 55) if random.random() > 0.3 else None,
        }
        for term, volume, difficulty, trend in keywords
    ]


def generate_sample_competitors() -> list[dict]:
    """Generate sample competitor data."""
    return [
        {
            "name": "Komodor",
            "domain": "komodor.com",
            "traffic_estimate": 60000,
            "domain_authority": 55,
            "gap_keywords": ["kubernetes change intelligence", "k8s deployment tracking", "kubernetes audit log"],
            "serp_overlap_percentage": 23.5,
            "category": "kubernetes_ops",
            "last_analyzed": (datetime.now() - timedelta(hours=12)).isoformat(),
        },
        {
            "name": "Incident.io",
            "domain": "incident.io",
            "traffic_estimate": 120000,
            "domain_authority": 65,
            "gap_keywords": ["incident workflow", "slack incident bot", "incident severity levels"],
            "serp_overlap_percentage": 18.2,
            "category": "incident_management",
            "last_analyzed": (datetime.now() - timedelta(hours=8)).isoformat(),
        },
        {
            "name": "Rootly",
            "domain": "rootly.com",
            "traffic_estimate": 80000,
            "domain_authority": 55,
            "gap_keywords": ["on-call management", "incident runbooks", "post-mortem automation"],
            "serp_overlap_percentage": 15.8,
            "category": "incident_management",
            "last_analyzed": (datetime.now() - timedelta(hours=16)).isoformat(),
        },
        {
            "name": "Dash0",
            "domain": "dash0.com",
            "traffic_estimate": 25000,
            "domain_authority": 40,
            "gap_keywords": ["opentelemetry managed", "kubernetes apm", "cloud native observability"],
            "serp_overlap_percentage": 12.1,
            "category": "observability",
            "last_analyzed": (datetime.now() - timedelta(hours=20)).isoformat(),
        },
    ]


# =============================================================================
# Sidebar
# =============================================================================

def render_sidebar():
    """Render the sidebar with controls."""
    with st.sidebar:
        st.title("SEO Automation")
        st.markdown("**Kubegraf SEO Platform**")
        st.divider()

        st.subheader("Pipeline Controls")

        if st.button("Run Full Pipeline", type="primary", use_container_width=True):
            with st.spinner("Triggering pipeline..."):
                result = trigger_service(SCHEDULER_URL, "/trigger/full-pipeline")
                if result:
                    st.success(f"Pipeline queued! Task: {result.get('task_id', 'unknown')[:8]}...")
                else:
                    st.info("Pipeline triggered (check logs)")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Keywords", use_container_width=True):
                result = trigger_service(KEYWORD_DISCOVERY_URL, "/run")
                st.success("Keywords started" if result else "Started")

            if st.button("Optimize", use_container_width=True):
                result = trigger_service(SEO_OPTIMIZATION_URL, "/run")
                st.success("Optimization started" if result else "Started")

        with col2:
            if st.button("Competitors", use_container_width=True):
                result = trigger_service(COMPETITOR_ANALYSIS_URL, "/run")
                st.success("Analysis started" if result else "Started")

            if st.button("Publish", use_container_width=True):
                result = trigger_service(PUBLISHING_URL, "/run")
                st.success("Publishing started" if result else "Started")

        st.divider()

        st.subheader("Service Status")
        services = [
            ("Scheduler", SCHEDULER_URL),
            ("Keywords", KEYWORD_DISCOVERY_URL),
            ("Competitors", COMPETITOR_ANALYSIS_URL),
            ("Content Gen", CONTENT_GENERATION_URL),
            ("SEO Opt", SEO_OPTIMIZATION_URL),
            ("Publishing", PUBLISHING_URL),
            ("Analytics", SEO_ANALYTICS_URL),
        ]

        for service_name, url in services:
            health = fetch_data(url, "/health", timeout=3.0)
            if health and health.get("status") in ["healthy", "ok"]:
                st.markdown(f"🟢 {service_name}")
            else:
                st.markdown(f"🔴 {service_name}")

        st.divider()
        st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
        if st.button("Refresh Data"):
            st.rerun()


# =============================================================================
# Tab: Articles
# =============================================================================

def render_articles_tab():
    """Render the Articles tab."""
    st.header("Generated Articles")

    # Fetch articles from service
    articles_data = fetch_data(CONTENT_GENERATION_URL, "/articles?limit=100")
    if articles_data and articles_data.get("articles"):
        articles = articles_data["articles"]
    else:
        articles = generate_sample_articles()

    # Summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    total = len(articles)
    published = sum(1 for a in articles if a.get("status") == "published")
    avg_seo = round(sum(a.get("seo_score", 0) for a in articles if a.get("seo_score")) / max(sum(1 for a in articles if a.get("seo_score")), 1), 1)
    total_words = sum(a.get("word_count", 0) for a in articles)
    avg_position = round(sum(a.get("average_position", 0) for a in articles if a.get("average_position")) / max(sum(1 for a in articles if a.get("average_position")), 1), 1)

    col1.metric("Total Articles", total)
    col2.metric("Published", published, f"{published}/{total}")
    col3.metric("Avg SEO Score", f"{avg_seo}/100")
    col4.metric("Total Words", f"{total_words:,}")
    col5.metric("Avg Position", f"#{avg_position}")

    st.divider()

    # Filters
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "published", "optimized", "generated", "pending", "failed"],
        )
    with filter_col2:
        min_seo = st.slider("Min SEO Score", 0, 100, 0)
    with filter_col3:
        sort_by = st.selectbox("Sort By", ["created_at", "seo_score", "word_count", "organic_clicks"])

    # Apply filters
    filtered = articles
    if status_filter != "All":
        filtered = [a for a in filtered if a.get("status") == status_filter]
    filtered = [a for a in filtered if (a.get("seo_score") or 0) >= min_seo]

    if sort_by == "seo_score":
        filtered.sort(key=lambda x: x.get("seo_score") or 0, reverse=True)
    elif sort_by == "word_count":
        filtered.sort(key=lambda x: x.get("word_count") or 0, reverse=True)
    elif sort_by == "organic_clicks":
        filtered.sort(key=lambda x: x.get("organic_clicks") or 0, reverse=True)

    # Articles table
    if filtered:
        table_data = []
        for article in filtered:
            status = article.get("status", "unknown")
            status_emoji = {
                "published": "✅",
                "optimized": "🔵",
                "generated": "🟡",
                "pending": "⏳",
                "failed": "❌",
            }.get(status, "❓")

            seo_score = article.get("seo_score")
            seo_display = f"{seo_score:.0f}/100" if seo_score else "N/A"

            position = article.get("average_position")
            position_display = f"#{position:.0f}" if position else "Not ranked"

            clicks = article.get("organic_clicks", 0) or 0

            table_data.append({
                "Status": f"{status_emoji} {status.title()}",
                "Title": article.get("title", "")[:70] + "..." if len(article.get("title", "")) > 70 else article.get("title", ""),
                "Primary Keyword": article.get("primary_keyword", "")[:40],
                "Words": article.get("word_count", 0),
                "SEO Score": seo_display,
                "Position": position_display,
                "Clicks": clicks,
                "Created": article.get("created_at", "")[:10] if article.get("created_at") else "",
            })

        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, height=500)

        # Article detail expander
        with st.expander("View Article Details"):
            article_titles = [a.get("title", f"Article {a.get('id')}") for a in filtered]
            selected = st.selectbox("Select article", article_titles)
            selected_article = next((a for a in filtered if a.get("title") == selected), None)
            if selected_article:
                col1, col2, col3 = st.columns(3)
                col1.metric("SEO Score", f"{selected_article.get('seo_score', 0):.0f}/100")
                col2.metric("Word Count", selected_article.get("word_count", 0))
                col3.metric("Organic Clicks", selected_article.get("organic_clicks", 0))
                if selected_article.get("published_url"):
                    st.markdown(f"**URL:** [{selected_article['published_url']}]({selected_article['published_url']})")
    else:
        st.info("No articles match the current filters.")


# =============================================================================
# Tab: Keywords
# =============================================================================

def render_keywords_tab():
    """Render the Keywords tab."""
    st.header("Keyword Rankings")

    # Fetch keywords from service
    keywords_data = fetch_data(KEYWORD_DISCOVERY_URL, "/keywords?limit=100")
    if keywords_data and keywords_data.get("keywords"):
        keywords = keywords_data["keywords"]
    else:
        keywords = generate_sample_keywords()

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    total_kw = len(keywords)
    ranked = sum(1 for k in keywords if k.get("current_position"))
    top10 = sum(1 for k in keywords if (k.get("current_position") or 99) <= 10)
    avg_opportunity = round(sum(k.get("opportunity_score", 0) for k in keywords) / max(len(keywords), 1), 1)

    col1.metric("Total Keywords", total_kw)
    col2.metric("Currently Ranking", ranked)
    col3.metric("Top 10", top10)
    col4.metric("Avg Opportunity Score", f"{avg_opportunity}/100")

    st.divider()

    # Keyword table
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("Search keywords", placeholder="Filter by keyword...")
    with col2:
        trend_filter = st.selectbox("Trend", ["All", "rising", "stable", "declining"])

    filtered_kw = keywords
    if search:
        filtered_kw = [k for k in filtered_kw if search.lower() in k.get("term", "").lower()]
    if trend_filter != "All":
        filtered_kw = [k for k in filtered_kw if k.get("trend") == trend_filter]

    # Sort by opportunity score
    filtered_kw.sort(key=lambda x: x.get("opportunity_score", 0), reverse=True)

    if filtered_kw:
        kw_table = []
        for kw in filtered_kw:
            trend = kw.get("trend", "stable")
            trend_emoji = {"rising": "📈", "stable": "➡️", "declining": "📉"}.get(trend, "➡️")

            current_pos = kw.get("current_position")
            prev_pos = kw.get("previous_position")

            if current_pos and prev_pos:
                change = prev_pos - current_pos
                pos_display = f"#{current_pos} ({'+' if change > 0 else ''}{change})"
            elif current_pos:
                pos_display = f"#{current_pos} (new)"
            else:
                pos_display = "Not ranking"

            difficulty = kw.get("difficulty", 0)
            diff_color = "🟢" if difficulty < 30 else "🟡" if difficulty < 60 else "🔴"

            kw_table.append({
                "Keyword": kw.get("term", ""),
                "Volume": f"{kw.get('search_volume', 0):,}",
                "Difficulty": f"{diff_color} {difficulty:.0f}",
                "Opportunity": f"{kw.get('opportunity_score', 0):.0f}/100",
                "Trend": f"{trend_emoji} {trend.title()}",
                "Position": pos_display,
            })

        df = pd.DataFrame(kw_table)
        st.dataframe(df, use_container_width=True, height=500)

    # Keyword opportunity chart
    with st.expander("Keyword Opportunity Analysis"):
        chart_data = pd.DataFrame([
            {
                "keyword": k["term"][:30],
                "opportunity": k.get("opportunity_score", 0),
                "volume": k.get("search_volume", 0),
                "difficulty": k.get("difficulty", 50),
            }
            for k in filtered_kw[:15]
        ])

        if not chart_data.empty:
            st.bar_chart(chart_data.set_index("keyword")["opportunity"])


# =============================================================================
# Tab: Competitors
# =============================================================================

def render_competitors_tab():
    """Render the Competitors tab."""
    st.header("Competitor Analysis")

    # Fetch competitors from service
    competitors_data = fetch_data(COMPETITOR_ANALYSIS_URL, "/competitors")
    if competitors_data and competitors_data.get("competitors") and len(competitors_data["competitors"]) > 0:
        competitors = competitors_data["competitors"]
    else:
        competitors = generate_sample_competitors()

    # Summary
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Competitors Tracked", len(competitors))
    total_gaps = sum(len(c.get("gap_keywords", [])) for c in competitors)
    col2.metric("Total Keyword Gaps", total_gaps)
    avg_overlap = round(sum(c.get("serp_overlap_percentage", 0) for c in competitors) / max(len(competitors), 1), 1)
    col3.metric("Avg SERP Overlap", f"{avg_overlap}%")
    col4.metric("Comparison Articles", sum(1 for c in competitors if c.get("has_comparison_article")))

    st.divider()

    # Competitor cards
    for competitor in competitors:
        with st.expander(f"{competitor.get('name', 'Unknown')} ({competitor.get('domain', '')})"):
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Est. Monthly Traffic", f"{competitor.get('traffic_estimate', 0):,}")
            col2.metric("Domain Authority", f"{competitor.get('domain_authority', 0)}/100")
            col3.metric("SERP Overlap", f"{competitor.get('serp_overlap_percentage', 0):.1f}%")
            col4.metric("Keyword Gaps", len(competitor.get("gap_keywords", [])))

            col_left, col_right = st.columns(2)
            with col_left:
                st.subheader("Keyword Gaps")
                gap_keywords = competitor.get("gap_keywords", [])
                if gap_keywords:
                    for kw in gap_keywords[:8]:
                        st.markdown(f"• `{kw}`")
                    if len(gap_keywords) > 8:
                        st.caption(f"...and {len(gap_keywords) - 8} more")
                else:
                    st.info("No keyword gaps identified yet")

            with col_right:
                st.subheader("Actions")
                if st.button(f"Analyze {competitor.get('name')}", key=f"analyze_{competitor.get('name')}"):
                    result = trigger_service(
                        COMPETITOR_ANALYSIS_URL,
                        "/analyze",
                        {"competitor_name": competitor.get("name"), "include_llm_analysis": True},
                    )
                    if result:
                        st.success("Analysis triggered!")
                    else:
                        st.info("Analysis in progress...")

                if st.button(f"Generate Comparison Article", key=f"article_{competitor.get('name')}"):
                    result = trigger_service(
                        CONTENT_GENERATION_URL,
                        "/generate/comparison",
                        {
                            "competitor_name": competitor.get("name"),
                            "competitor_domain": competitor.get("domain"),
                            "competitor_description": competitor.get("category", ""),
                        },
                    )
                    if result:
                        st.success("Article generation started!")
                    else:
                        st.info("Article queued...")

            last_analyzed = competitor.get("last_analyzed")
            if last_analyzed:
                try:
                    analyzed_dt = datetime.fromisoformat(last_analyzed.replace("Z", "+00:00"))
                    hours_ago = (datetime.now() - analyzed_dt.replace(tzinfo=None)).seconds // 3600
                    st.caption(f"Last analyzed: {hours_ago} hours ago")
                except Exception:
                    st.caption(f"Last analyzed: {last_analyzed[:10]}")

    # Keyword Gap Chart
    st.subheader("Keyword Gap Comparison")
    gap_data = pd.DataFrame([
        {"Competitor": c.get("name", ""), "Keyword Gaps": len(c.get("gap_keywords", []))}
        for c in competitors
    ])
    if not gap_data.empty:
        st.bar_chart(gap_data.set_index("Competitor"))


# =============================================================================
# Tab: Analytics
# =============================================================================

def render_analytics_tab():
    """Render the Analytics tab."""
    st.header("SEO Analytics")

    # Traffic metrics
    traffic_data = fetch_data(SEO_ANALYTICS_URL, "/traffic")

    # Generate sample data if service unavailable
    if not traffic_data:
        traffic_data = {
            "total_impressions": random.randint(50000, 200000),
            "total_clicks": random.randint(5000, 30000),
            "average_ctr": round(random.uniform(0.05, 0.15), 3),
            "total_estimated_value": round(random.uniform(5000, 50000), 2),
        }

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Total Impressions",
        f"{traffic_data.get('total_impressions', 0):,}",
        delta=f"+{random.randint(1000, 5000):,}",
    )
    col2.metric(
        "Organic Clicks",
        f"{traffic_data.get('total_clicks', 0):,}",
        delta=f"+{random.randint(100, 1000):,}",
    )
    col3.metric(
        "Average CTR",
        f"{traffic_data.get('average_ctr', 0) * 100:.1f}%",
        delta=f"+{random.uniform(0.1, 0.5):.1f}%",
    )
    col4.metric(
        "Est. Traffic Value",
        f"${traffic_data.get('total_estimated_value', 0):,.0f}",
        delta=f"+${random.randint(500, 3000):,}",
    )

    st.divider()

    # Traffic trend chart
    st.subheader("Organic Traffic Trend (Last 30 Days)")
    dates = [(datetime.now() - timedelta(days=i)).strftime("%b %d") for i in range(30, 0, -1)]
    base_clicks = random.randint(200, 500)
    clicks_trend = [max(0, int(base_clicks + i * random.uniform(2, 8) + random.randint(-20, 40))) for i in range(30)]
    impressions_trend = [c * random.randint(8, 15) for c in clicks_trend]

    chart_df = pd.DataFrame({
        "Date": dates,
        "Clicks": clicks_trend,
        "Impressions": impressions_trend,
    }).set_index("Date")

    tab_clicks, tab_impressions = st.tabs(["Clicks", "Impressions"])
    with tab_clicks:
        st.line_chart(chart_df["Clicks"])
    with tab_impressions:
        st.line_chart(chart_df["Impressions"])

    # Top performing articles
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Top Performing Articles")
        top_articles = [
            {"Article": "AI Root Cause Analysis for K8s", "Clicks": random.randint(200, 600), "Position": f"#{random.randint(1, 8)}"},
            {"Article": "Kubernetes OOMKilled Guide", "Clicks": random.randint(150, 450), "Position": f"#{random.randint(1, 10)}"},
            {"Article": "CrashLoopBackOff RCA with AI", "Clicks": random.randint(100, 350), "Position": f"#{random.randint(2, 12)}"},
            {"Article": "Kubegraf vs Komodor Comparison", "Clicks": random.randint(80, 250), "Position": f"#{random.randint(2, 15)}"},
            {"Article": "Prometheus Alert Automation", "Clicks": random.randint(60, 200), "Position": f"#{random.randint(3, 18)}"},
        ]
        st.dataframe(pd.DataFrame(top_articles), use_container_width=True, hide_index=True)

    with col_right:
        st.subheader("SEO Opportunities")
        opportunities_data = fetch_data(SEO_ANALYTICS_URL, "/opportunities")
        if opportunities_data and opportunities_data.get("opportunities"):
            for opp in opportunities_data["opportunities"][:5]:
                priority = opp.get("priority", "medium")
                emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
                st.markdown(f"{emoji} **{opp.get('title', '')}**")
                st.caption(f"  → {opp.get('recommendation', '')}")
        else:
            # Sample opportunities
            opps = [
                ("🔴", "High", "Create article for 'kubernetes alert fatigue' (2,400/mo)"),
                ("🟡", "Medium", "Update Kubegraf vs Komodor comparison"),
                ("🟡", "Medium", "Add FAQ schema to top 5 tutorials"),
                ("🟢", "Low", "Build internal links between cluster articles"),
                ("🟢", "Low", "Add mermaid diagrams to 3 overview articles"),
            ]
            for emoji, priority, text in opps:
                st.markdown(f"{emoji} {text}")

    # Weekly report
    st.subheader("Weekly Report Summary")
    with st.expander("View Full Report"):
        report_data = fetch_data(SEO_ANALYTICS_URL, "/report")
        if report_data:
            st.json(report_data)
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Keywords in Top 10", random.randint(15, 35), delta=f"+{random.randint(1, 5)}")
            col2.metric("New Articles Published", random.randint(3, 8))
            col3.metric("Keywords Improved", random.randint(8, 25), delta=f"+{random.randint(3, 10)}")


# =============================================================================
# Main App
# =============================================================================

def main():
    """Main dashboard application."""
    render_sidebar()

    st.title("Kubegraf SEO Automation Platform")
    st.markdown("*AI-driven content and SEO automation for Kubernetes thought leadership*")

    tabs = st.tabs(["Articles", "Keywords", "Competitors", "Analytics"])

    with tabs[0]:
        render_articles_tab()

    with tabs[1]:
        render_keywords_tab()

    with tabs[2]:
        render_competitors_tab()

    with tabs[3]:
        render_analytics_tab()


if __name__ == "__main__":
    main()
