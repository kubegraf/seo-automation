"""
Competitor Analysis Engine
Analyzes 8 competitors, identifies keyword gaps, generates comparison article ideas.
"""
import json
import time
import logging
from datetime import datetime
from shared.gemini_client import generate_json, generate
from shared.models import Competitor
from shared import storage

logger = logging.getLogger(__name__)

COMPETITORS_CONFIG = [
    {
        "name": "Deductive AI",
        "domain": "deductive.ai",
        "focus_areas": ["ai incident analysis", "root cause analysis", "incident triage", "alert correlation"],
        "target_keywords": ["ai incident analysis", "root cause analysis ai", "incident triage ai", "alert fatigue reduction", "automated postmortem"],
        "traffic_tier": "low",
    },
    {
        "name": "Rootly",
        "domain": "rootly.com",
        "focus_areas": ["incident management", "on-call management", "slack incident response", "incident retrospectives"],
        "target_keywords": ["incident management platform", "on-call management", "incident response slack", "incident retrospective tool", "pagerduty alternative"],
        "traffic_tier": "high",
    },
    {
        "name": "SRE.ai",
        "domain": "sre.ai",
        "focus_areas": ["sre automation", "ai reliability", "autonomous sre", "self-healing infrastructure"],
        "target_keywords": ["sre automation", "ai sre platform", "autonomous sre", "self-healing kubernetes", "reliability engineering ai"],
        "traffic_tier": "low",
    },
    {
        "name": "Resolve Systems",
        "domain": "resolve.io",
        "focus_areas": ["it automation", "itsm automation", "network automation", "incident automation"],
        "target_keywords": ["it automation platform", "itsm automation", "network incident automation", "it operations automation", "runbook automation"],
        "traffic_tier": "medium",
    },
    {
        "name": "Incident.io",
        "domain": "incident.io",
        "focus_areas": ["incident management", "on-call alerting", "status pages", "incident workflows"],
        "target_keywords": ["incident management platform", "on-call alerting", "status page software", "incident workflow", "incident.io"],
        "traffic_tier": "high",
    },
    {
        "name": "Komodor",
        "domain": "komodor.com",
        "focus_areas": ["kubernetes troubleshooting", "k8s debugging", "kubernetes change tracking", "kubernetes health monitor"],
        "target_keywords": ["kubernetes troubleshooting tool", "k8s debugging", "kubernetes change tracking", "komodor kubernetes", "kubernetes health monitoring"],
        "traffic_tier": "medium",
    },
    {
        "name": "Dash0",
        "domain": "dash0.com",
        "focus_areas": ["kubernetes observability", "opentelemetry platform", "cloud native monitoring", "perses dashboards"],
        "target_keywords": ["kubernetes observability platform", "opentelemetry kubernetes", "cloud native monitoring", "otel collector kubernetes", "dash0 observability"],
        "traffic_tier": "low",
    },
    {
        "name": "Harness",
        "domain": "harness.io",
        "focus_areas": ["ci/cd platform", "devops platform", "feature flags", "chaos engineering", "cloud cost management"],
        "target_keywords": ["ci cd platform", "harness io", "feature flags platform", "chaos engineering kubernetes", "devops automation platform"],
        "traffic_tier": "high",
    },
]

KUBEGRAF_KEYWORDS = [
    "kubernetes root cause analysis",
    "ai kubernetes incident response",
    "kubernetes automated remediation",
    "kubernetes safefix",
    "kubernetes alert investigation",
    "prometheus alert to fix",
    "kubernetes ai sre",
    "kubernetes incident automation",
    "grafana alert remediation",
    "kubernetes troubleshooting ai",
]


def analyze_competitor(competitor: Competitor) -> Competitor:
    """Use Gemini to analyze a competitor and find keyword gaps."""
    logger.info(f"Analyzing competitor: {competitor.name}")

    prompt = f"""You are an SEO strategist for Kubegraf, an AI Kubernetes SRE platform.
Kubegraf: receives Prometheus/Grafana/Slack alerts -> investigates Kubernetes workloads -> performs AI root cause analysis -> suggests and applies SafeFix remediations.

Analyze this competitor: {competitor.name} (domain: {competitor.domain})
Their focus areas: {', '.join(competitor.focus_areas)}
Their known keywords: {', '.join(competitor.target_keywords)}

Kubegraf's current keywords: {', '.join(KUBEGRAF_KEYWORDS)}

Return a JSON object with:
{{
  "gap_keywords": ["keyword1", "keyword2", ...],
  "comparison_article_ideas": ["title1", "title2", ...],
  "kubegraf_advantages": ["advantage1", "advantage2", ...],
  "competitor_strengths": ["strength1", ...],
  "recommended_content_angle": "one paragraph describing content strategy to beat this competitor"
}}

Focus on keywords where Kubegraf's AI + Kubernetes-native approach creates a unique angle.
Comparison articles should be honest but highlight Kubegraf's AI-driven auto-remediation as differentiator.
gap_keywords should be 8-12 keywords competitor ranks for but Kubegraf doesn't.
comparison_article_ideas should be 5 comparison article titles.
kubegraf_advantages should be 3-5 areas where Kubegraf is stronger.
competitor_strengths should be 2-3 areas where competitor is stronger.
"""

    try:
        raw = generate_json(prompt)
        data = json.loads(raw)
        competitor.gap_keywords = data.get("gap_keywords", [])[:12]
        competitor.comparison_article_ideas = data.get("comparison_article_ideas", [])[:5]
        competitor.last_analyzed = datetime.utcnow().isoformat()
    except Exception as e:
        logger.error(f"Failed to analyze {competitor.name}: {e}")
        # Fallback
        competitor.gap_keywords = [f"{competitor.name.lower()} alternative", f"kubegraf vs {competitor.name.lower()}"]
        competitor.comparison_article_ideas = [f"Kubegraf vs {competitor.name}: Which AI SRE Platform is Right for You?"]
        competitor.last_analyzed = datetime.utcnow().isoformat()

    return competitor


def run():
    """Main entrypoint for competitor analysis pipeline step."""
    from rich.console import Console
    console = Console()

    console.print("[bold blue]🔬 Competitor Analysis Engine[/bold blue]")

    # Load or initialize competitors
    existing = storage.load_competitors()
    existing_names = {c.name for c in existing}

    # Add any new competitors from config
    for cfg in COMPETITORS_CONFIG:
        if cfg["name"] not in existing_names:
            comp = Competitor(
                name=cfg["name"],
                domain=cfg["domain"],
                focus_areas=cfg["focus_areas"],
                target_keywords=cfg["target_keywords"],
                traffic_tier=cfg.get("traffic_tier", "medium"),
            )
            existing.append(comp)

    # Analyze each competitor (or re-analyze if not done recently)
    # Limit to 3 per run to stay within free-tier rate limits
    analyzed = 0
    max_per_run = 3
    for i, competitor in enumerate(existing):
        if not competitor.last_analyzed and analyzed < max_per_run:
            console.print(f"  Analyzing {competitor.name}...")
            existing[i] = analyze_competitor(competitor)
            analyzed += 1
            # Pause between competitor calls to avoid rate limits
            if analyzed < max_per_run:
                console.print(f"  ⏳ Waiting 15s before next competitor analysis...")
                time.sleep(15)

    # Save
    storage.save_competitors(existing)
    console.print(f"[green]✅ Analyzed {analyzed} competitors. Total: {len(existing)}[/green]")

    # Print summary
    console.print("\n[bold]Competitor Keyword Gaps:[/bold]")
    for comp in existing:
        gaps = ', '.join(comp.gap_keywords[:3]) if comp.gap_keywords else 'not yet analyzed'
        console.print(f"  {comp.name}: {gaps}")

    return existing


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
