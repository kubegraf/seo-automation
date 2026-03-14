"""
Competitor Analysis Engine for SEO Automation Platform.
Analyzes competitors, finds keyword gaps, and generates article ideas.
"""
import logging
import random
from datetime import datetime
from typing import Optional

from .competitors import (
    CompetitorConfig,
    COMPETITORS,
    get_all_competitors,
    get_competitor_by_name,
    get_all_competitor_keywords,
)

logger = logging.getLogger(__name__)

# Kubegraf's current target keywords
OUR_KEYWORDS = [
    "kubernetes alerting",
    "sre automation",
    "ai incident response",
    "kubernetes root cause analysis",
    "prometheus alert management",
    "grafana automation",
    "kubernetes ops",
    "incident remediation ai",
    "k8s troubleshooting",
    "devops ai",
    "kubernetes monitoring",
    "sre platform",
    "ai sre",
    "kubernetes incident management",
    "automated remediation",
    "kubegraf",
    "kubernetes ai monitoring",
    "safefix kubernetes",
    "kubernetes anomaly detection",
    "intelligent kubernetes alerting",
]

# Our product strengths for comparison articles
KUBEGRAF_STRENGTHS = [
    "AI-powered root cause analysis in seconds",
    "SafeFix automated remediation engine",
    "Deep Kubernetes-native integration",
    "Natural language incident investigation",
    "Proactive anomaly detection before incidents occur",
    "Automated runbook execution",
    "Multi-cluster support",
    "GitOps-native workflow integration",
    "Cost optimization recommendations",
    "Intelligent alert correlation and deduplication",
]


class CompetitorAnalysisEngine:
    """
    Analyzes competitors and identifies content and keyword opportunities.
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        logger.info("CompetitorAnalysisEngine initialized")

    async def analyze_competitor(self, competitor_name: str) -> dict:
        """
        Analyze a specific competitor and return keyword gaps and opportunities.

        Args:
            competitor_name: Name of the competitor to analyze

        Returns:
            Analysis dict with gap_keywords, opportunities, article_ideas
        """
        competitor = get_competitor_by_name(competitor_name)
        if not competitor:
            # Try to find by domain
            competitor = self._find_competitor_fuzzy(competitor_name)

        if not competitor:
            logger.warning(f"Competitor '{competitor_name}' not found, using generic analysis")
            competitor = CompetitorConfig(
                name=competitor_name,
                domain=f"{competitor_name.lower().replace(' ', '')}.com",
                keywords=[competitor_name.lower()],
            )

        logger.info(f"Analyzing competitor: {competitor.name} ({competitor.domain})")

        # Find keyword gaps
        gap_keywords = self.find_keyword_gaps(OUR_KEYWORDS, competitor.keywords)

        # Generate article ideas
        article_ideas = self.generate_comparison_article_ideas(competitor)

        # Calculate SERP overlap
        our_set = set(OUR_KEYWORDS)
        their_set = set(competitor.keywords)
        shared = our_set.intersection(their_set)
        overlap_pct = (len(shared) / max(len(our_set), 1)) * 100

        # Use LLM for deeper analysis if available
        llm_analysis = {}
        if self.llm_client:
            try:
                llm_analysis = await self.llm_client.analyze_competitor(
                    competitor_name=competitor.name,
                    competitor_domain=competitor.domain,
                    our_keywords=OUR_KEYWORDS,
                    their_known_keywords=competitor.keywords,
                )
                # Merge LLM gap keywords
                if llm_analysis.get("gap_keywords"):
                    gap_keywords.extend(llm_analysis["gap_keywords"])
                    gap_keywords = list(set(gap_keywords))
                # Merge article ideas
                if llm_analysis.get("article_ideas"):
                    article_ideas.extend(llm_analysis["article_ideas"])
            except Exception as e:
                logger.warning(f"LLM analysis failed, using rule-based: {e}")

        result = {
            "competitor_name": competitor.name,
            "domain": competitor.domain,
            "gap_keywords": gap_keywords,
            "shared_keywords": list(shared),
            "serp_overlap_percentage": round(overlap_pct, 1),
            "their_keywords": competitor.keywords,
            "article_ideas": article_ideas,
            "their_strengths": llm_analysis.get("their_strengths", self._get_generic_strengths(competitor)),
            "their_weaknesses": llm_analysis.get("their_weaknesses", self._get_generic_weaknesses(competitor)),
            "recommended_strategy": llm_analysis.get("recommended_strategy", self._get_generic_strategy(competitor)),
            "opportunities": llm_analysis.get("opportunities", self._get_generic_opportunities(competitor)),
            "traffic_estimate": competitor.traffic_estimate,
            "domain_authority": competitor.domain_authority,
            "category": competitor.category,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Completed analysis for {competitor.name}: {len(gap_keywords)} gap keywords found")
        return result

    def find_keyword_gaps(self, our_keywords: list[str], their_keywords: list[str]) -> list[str]:
        """
        Find keywords they target that we don't.

        Args:
            our_keywords: Keywords we currently target
            their_keywords: Keywords the competitor targets

        Returns:
            List of gap keywords we should target
        """
        our_set = set(kw.lower() for kw in our_keywords)
        gaps = []

        for kw in their_keywords:
            kw_lower = kw.lower()
            # Direct match
            if kw_lower not in our_set:
                # Check for partial overlap
                has_partial = any(
                    our_kw in kw_lower or kw_lower in our_kw
                    for our_kw in our_set
                )
                if not has_partial:
                    gaps.append(kw)

        # Also check expanded keyword variations
        expanded_gaps = self._expand_gap_keywords(gaps)
        all_gaps = list(set(gaps + expanded_gaps))

        logger.debug(f"Found {len(all_gaps)} keyword gaps")
        return all_gaps

    def _expand_gap_keywords(self, gap_keywords: list[str]) -> list[str]:
        """Generate keyword variations from gap keywords."""
        expanded = []
        for kw in gap_keywords:
            # Add common variations
            if "incident" in kw and "kubernetes" not in kw:
                expanded.append(f"kubernetes {kw}")
            if "management" in kw and "platform" not in kw:
                expanded.append(f"{kw} platform")
            if "automation" in kw and "ai" not in kw:
                expanded.append(f"ai {kw}")
        return expanded

    def generate_comparison_article_ideas(self, competitor: CompetitorConfig) -> list[str]:
        """
        Generate article ideas for head-to-head comparison content.

        Args:
            competitor: CompetitorConfig object

        Returns:
            List of article title ideas
        """
        name = competitor.name
        domain = competitor.domain

        articles = [
            f"Kubegraf vs {name}: Which AI-Powered Kubernetes Platform is Right for You?",
            f"{name} Alternative: How Kubegraf Compares for Kubernetes Incident Management",
            f"Why Engineers Switch from {name} to Kubegraf",
            f"Kubegraf vs {name}: Feature Comparison 2024",
            f"{name} Review: Strengths, Weaknesses, and Alternatives",
            f"Best {name} Alternatives for Kubernetes Monitoring in 2024",
            f"Kubegraf vs {name}: AI-Powered Root Cause Analysis Comparison",
        ]

        # Category-specific article ideas
        if competitor.category == "kubernetes_ops":
            articles.extend([
                f"{name} vs Kubegraf: Kubernetes Troubleshooting Platform Deep Dive",
                f"How Kubegraf's AI Outperforms {name} for K8s Debugging",
            ])
        elif competitor.category == "incident_management":
            articles.extend([
                f"Incident Management Showdown: Kubegraf vs {name}",
                f"{name} vs Kubegraf: Which Has Better On-Call Automation?",
            ])
        elif competitor.category == "ai_sre":
            articles.extend([
                f"AI SRE Platform Comparison: Kubegraf vs {name}",
                f"{name} vs Kubegraf: Comparing AI-Powered SRE Automation",
            ])
        elif competitor.category == "observability":
            articles.extend([
                f"Kubernetes Observability: Kubegraf vs {name}",
                f"Beyond Observability: How Kubegraf Adds AI to {name}'s Monitoring",
            ])

        return articles

    async def analyze_all_competitors(self) -> list[dict]:
        """
        Analyze all configured competitors.

        Returns:
            List of analysis results for each competitor
        """
        results = []
        for competitor in COMPETITORS:
            try:
                analysis = await self.analyze_competitor(competitor.name)
                results.append(analysis)
                logger.info(f"Analyzed competitor: {competitor.name}")
            except Exception as e:
                logger.error(f"Failed to analyze {competitor.name}: {e}")

        return results

    async def find_all_keyword_gaps(self) -> list[str]:
        """
        Find all keyword gaps across all competitors.

        Returns:
            Sorted list of unique gap keywords
        """
        all_competitor_keywords = get_all_competitor_keywords()
        gaps = self.find_keyword_gaps(OUR_KEYWORDS, all_competitor_keywords)
        return sorted(set(gaps))

    async def generate_content_calendar(self, weeks: int = 4) -> list[dict]:
        """
        Generate a content calendar based on competitor analysis.

        Args:
            weeks: Number of weeks to plan for

        Returns:
            List of content items with week, topic, type, and target keyword
        """
        calendar = []
        all_articles = []

        for competitor in COMPETITORS[:4]:  # Focus on top 4 competitors
            ideas = self.generate_comparison_article_ideas(competitor)
            for idea in ideas[:2]:  # 2 articles per competitor
                all_articles.append({
                    "title": idea,
                    "competitor": competitor.name,
                    "type": "comparison",
                    "priority": competitor.priority,
                })

        # Add keyword-focused articles
        gaps = await self.find_all_keyword_gaps()
        for gap_kw in gaps[:10]:
            all_articles.append({
                "title": f"Complete Guide to {gap_kw.title()}",
                "target_keyword": gap_kw,
                "type": "guide",
                "priority": 2,
            })

        # Assign to weeks
        articles_per_week = max(1, len(all_articles) // weeks)
        for i, article in enumerate(all_articles[:weeks * articles_per_week]):
            week = (i // articles_per_week) + 1
            calendar.append({
                "week": week,
                **article,
            })

        return calendar

    def _find_competitor_fuzzy(self, name: str) -> Optional[CompetitorConfig]:
        """Fuzzy search for a competitor by name."""
        name_lower = name.lower()
        for competitor in get_all_competitors():
            if name_lower in competitor.name.lower() or competitor.name.lower() in name_lower:
                return competitor
            if name_lower in competitor.domain:
                return competitor
        return None

    def _get_generic_strengths(self, competitor: CompetitorConfig) -> list[str]:
        """Get generic strength assessment for a competitor."""
        strengths = []
        if competitor.domain_authority > 60:
            strengths.append("Strong domain authority and brand recognition")
        if competitor.traffic_estimate > 100000:
            strengths.append("High organic traffic and market presence")
        if competitor.funding_stage in ["Series B", "Series C", "Series D", "Public"]:
            strengths.append("Well-funded with strong investor backing")
        strengths.append(f"Established presence in {competitor.category.replace('_', ' ')} space")
        strengths.append("Existing customer base and case studies")
        return strengths

    def _get_generic_weaknesses(self, competitor: CompetitorConfig) -> list[str]:
        """Get generic weakness assessment for a competitor."""
        weaknesses = []
        if competitor.category != "kubernetes_ops":
            weaknesses.append("Less Kubernetes-native compared to Kubegraf")
        if competitor.category != "ai_incident_management":
            weaknesses.append("Limited AI-powered root cause analysis capabilities")
        weaknesses.extend([
            "No automated remediation (SafeFix equivalent)",
            "Reactive rather than proactive incident prevention",
            "Less integration with GitOps workflows",
        ])
        return weaknesses

    def _get_generic_strategy(self, competitor: CompetitorConfig) -> str:
        """Generate a generic strategy recommendation."""
        return (
            f"Target keywords that {competitor.name} ranks for but where we have better AI capabilities. "
            f"Create comparison content highlighting Kubegraf's SafeFix automated remediation and "
            f"AI root cause analysis advantages. Focus on kubernetes-specific use cases where "
            f"{competitor.name}'s generic approach falls short."
        )

    def _get_generic_opportunities(self, competitor: CompetitorConfig) -> list[str]:
        """Get generic opportunity list."""
        return [
            f"Create detailed comparison article: Kubegraf vs {competitor.name}",
            f"Target long-tail keywords combining '{competitor.category}' with 'kubernetes'",
            f"Write case studies showing superiority in Kubernetes-specific scenarios",
            "Publish technical tutorials that {competitor.name} hasn't covered",
            f"Create 'switching from {competitor.name}' migration guide",
        ]
