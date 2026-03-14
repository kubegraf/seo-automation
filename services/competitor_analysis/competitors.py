"""
Competitor configuration for SEO Automation Platform.
Defines all competitors with their domains, keywords, and analysis metadata.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CompetitorConfig:
    """Configuration for a competitor."""
    name: str
    domain: str
    keywords: list[str]
    description: str = ""
    category: str = "general"
    priority: int = 1  # 1=high, 2=medium, 3=low
    traffic_estimate: int = 0
    domain_authority: int = 0
    founded_year: Optional[int] = None
    funding_stage: str = ""
    hq_location: str = ""


# =============================================================================
# Primary Competitors (Direct competition with Kubegraf)
# =============================================================================

COMPETITORS: list[CompetitorConfig] = [
    CompetitorConfig(
        name="Deductive AI",
        domain="deductive.ai",
        keywords=[
            "ai incident analysis",
            "root cause analysis ai",
            "incident triage ai",
            "automated incident investigation",
            "kubernetes incident ai",
            "devops ai assistant",
        ],
        description="AI-powered incident analysis and root cause determination platform",
        category="ai_incident_management",
        priority=1,
        traffic_estimate=15000,
        domain_authority=35,
        hq_location="San Francisco, CA",
    ),
    CompetitorConfig(
        name="Rootly",
        domain="rootly.com",
        keywords=[
            "incident management",
            "on-call management",
            "incident response platform",
            "slack incident management",
            "incident runbooks",
            "incident communication",
            "post-mortem automation",
        ],
        description="Incident management platform with Slack-native workflow",
        category="incident_management",
        priority=1,
        traffic_estimate=80000,
        domain_authority=55,
        founded_year=2021,
        funding_stage="Series B",
        hq_location="San Francisco, CA",
    ),
    CompetitorConfig(
        name="SRE.ai",
        domain="sre.ai",
        keywords=[
            "sre automation",
            "ai sre platform",
            "reliability engineering ai",
            "autonomous sre",
            "ai operations platform",
            "sre copilot",
        ],
        description="AI-powered SRE automation platform",
        category="ai_sre",
        priority=1,
        traffic_estimate=20000,
        domain_authority=30,
        hq_location="New York, NY",
    ),
    CompetitorConfig(
        name="Resolve Systems",
        domain="resolve.io",
        keywords=[
            "it automation",
            "incident automation",
            "itsm automation",
            "it process automation",
            "network automation",
            "automated runbooks",
        ],
        description="IT process automation and incident response platform",
        category="it_automation",
        priority=2,
        traffic_estimate=45000,
        domain_authority=60,
        founded_year=2017,
        funding_stage="Acquired",
        hq_location="San Jose, CA",
    ),
    CompetitorConfig(
        name="Incident.io",
        domain="incident.io",
        keywords=[
            "incident management platform",
            "on-call alerting",
            "incident response",
            "incident workflow",
            "incident slack bot",
            "incident severity levels",
        ],
        description="Incident management platform built for modern engineering teams",
        category="incident_management",
        priority=1,
        traffic_estimate=120000,
        domain_authority=65,
        founded_year=2020,
        funding_stage="Series B",
        hq_location="London, UK",
    ),
    CompetitorConfig(
        name="Komodor",
        domain="komodor.com",
        keywords=[
            "kubernetes troubleshooting",
            "k8s debugging",
            "kubernetes ops",
            "kubernetes change intelligence",
            "kubernetes health monitor",
            "k8s deployment tracking",
            "kubernetes audit log",
        ],
        description="Kubernetes troubleshooting and change intelligence platform",
        category="kubernetes_ops",
        priority=1,
        traffic_estimate=60000,
        domain_authority=55,
        founded_year=2020,
        funding_stage="Series B",
        hq_location="Tel Aviv, Israel",
    ),
    CompetitorConfig(
        name="Dash0",
        domain="dash0.com",
        keywords=[
            "kubernetes observability",
            "opentelemetry platform",
            "cloud native monitoring",
            "distributed tracing platform",
            "opentelemetry managed",
            "kubernetes apm",
        ],
        description="OpenTelemetry-native observability platform for cloud-native",
        category="observability",
        priority=2,
        traffic_estimate=25000,
        domain_authority=40,
        founded_year=2022,
        funding_stage="Seed",
        hq_location="Zurich, Switzerland",
    ),
    CompetitorConfig(
        name="Harness",
        domain="harness.io",
        keywords=[
            "ci cd platform",
            "devops platform",
            "software delivery",
            "continuous delivery platform",
            "feature flags platform",
            "cloud cost management",
            "harness cd",
        ],
        description="Complete software delivery platform with AI-powered insights",
        category="devops_platform",
        priority=2,
        traffic_estimate=500000,
        domain_authority=75,
        founded_year=2017,
        funding_stage="Series D",
        hq_location="San Francisco, CA",
    ),
]

# =============================================================================
# Secondary Competitors (Adjacent/related tools)
# =============================================================================

SECONDARY_COMPETITORS: list[CompetitorConfig] = [
    CompetitorConfig(
        name="PagerDuty",
        domain="pagerduty.com",
        keywords=[
            "pagerduty alternative",
            "on-call management",
            "alert management",
            "incident response software",
            "aiops pagerduty",
        ],
        description="Digital operations management platform",
        category="incident_management",
        priority=2,
        traffic_estimate=2000000,
        domain_authority=85,
        founded_year=2009,
        funding_stage="Public",
        hq_location="San Francisco, CA",
    ),
    CompetitorConfig(
        name="Datadog",
        domain="datadoghq.com",
        keywords=[
            "kubernetes monitoring",
            "infrastructure monitoring",
            "apm platform",
            "cloud monitoring",
            "datadog alternative",
        ],
        description="Cloud monitoring and security platform",
        category="observability",
        priority=3,
        traffic_estimate=5000000,
        domain_authority=90,
        founded_year=2010,
        funding_stage="Public",
        hq_location="New York, NY",
    ),
    CompetitorConfig(
        name="Grafana Labs",
        domain="grafana.com",
        keywords=[
            "grafana dashboard",
            "prometheus monitoring",
            "loki logging",
            "grafana cloud",
            "open source monitoring",
        ],
        description="Open and composable observability platform",
        category="observability",
        priority=3,
        traffic_estimate=3000000,
        domain_authority=88,
        founded_year=2019,
        funding_stage="Series D",
        hq_location="New York, NY",
    ),
]


def get_all_competitors() -> list[CompetitorConfig]:
    """Get all competitors (primary + secondary)."""
    return COMPETITORS + SECONDARY_COMPETITORS


def get_primary_competitors() -> list[CompetitorConfig]:
    """Get only primary high-priority competitors."""
    return [c for c in COMPETITORS if c.priority == 1]


def get_competitor_by_domain(domain: str) -> Optional[CompetitorConfig]:
    """Find competitor by domain name."""
    all_comps = get_all_competitors()
    for comp in all_comps:
        if comp.domain == domain:
            return comp
    return None


def get_competitor_by_name(name: str) -> Optional[CompetitorConfig]:
    """Find competitor by name."""
    all_comps = get_all_competitors()
    for comp in all_comps:
        if comp.name.lower() == name.lower():
            return comp
    return None


def get_all_competitor_keywords() -> list[str]:
    """Get a flat list of all competitor keywords."""
    all_keywords = []
    for comp in get_all_competitors():
        all_keywords.extend(comp.keywords)
    return list(set(all_keywords))
