"""
Content Generation Engine for SEO Automation Platform.
Uses LLM to generate SEO-optimized articles for Kubegraf blog.
"""
import logging
import re
import uuid
from datetime import datetime
from typing import Optional

from .prompts import (
    ARTICLE_GENERATION_PROMPT,
    KEYWORD_ARTICLE_PROMPT,
    COMPARISON_ARTICLE_PROMPT,
    TUTORIAL_PROMPT,
    SYSTEM_PROMPT_TECHNICAL_WRITER,
    MERMAID_INCIDENT_FLOW,
    MERMAID_K8S_MONITORING,
)

logger = logging.getLogger(__name__)

# Sample article topics for Kubegraf
SAMPLE_TOPICS = [
    {
        "title": "AI Root Cause Analysis for Kubernetes: How Kubegraf Automates Incident Investigation",
        "primary_keyword": "kubernetes root cause analysis",
        "secondary_keywords": ["k8s incident investigation", "ai devops", "kubernetes troubleshooting ai"],
        "type": "standard",
        "word_count": 2500,
    },
    {
        "title": "Automatic Kubernetes Incident Remediation with SafeFix",
        "primary_keyword": "kubernetes automated remediation",
        "secondary_keywords": ["safefix", "kubernetes self-healing", "automated incident response"],
        "type": "tutorial",
        "word_count": 2000,
    },
    {
        "title": "AI SRE Platforms Comparison 2024: Kubegraf vs Komodor vs Deductive AI",
        "primary_keyword": "ai sre platform comparison",
        "secondary_keywords": ["kubegraf vs komodor", "deductive ai alternative", "kubernetes ops platform"],
        "type": "comparison",
        "word_count": 3000,
    },
    {
        "title": "How AI Can Fix Production Kubernetes Incidents in Minutes",
        "primary_keyword": "ai kubernetes incident response",
        "secondary_keywords": ["kubernetes production incidents", "ai operations", "incident automation"],
        "type": "standard",
        "word_count": 2000,
    },
    {
        "title": "Kubernetes Troubleshooting Automation: From Alert to Fix",
        "primary_keyword": "kubernetes troubleshooting automation",
        "secondary_keywords": ["k8s debugging", "kubernetes alert to fix", "automated k8s troubleshooting"],
        "type": "tutorial",
        "word_count": 2500,
    },
    {
        "title": "Kubegraf vs Rootly: Which Incident Management Platform is Right for You?",
        "primary_keyword": "kubegraf vs rootly",
        "secondary_keywords": ["rootly alternative", "incident management platform comparison"],
        "type": "comparison",
        "competitor": "Rootly",
        "word_count": 3000,
    },
    {
        "title": "Kubernetes OOMKilled: Automatic Detection and Remediation",
        "primary_keyword": "kubernetes oomkilled",
        "secondary_keywords": ["oomkilled fix", "kubernetes memory limits", "k8s out of memory"],
        "type": "tutorial",
        "word_count": 2000,
    },
    {
        "title": "CrashLoopBackOff Root Cause Analysis with AI",
        "primary_keyword": "crashloopbackoff root cause analysis",
        "secondary_keywords": ["kubernetes crashloopbackoff fix", "k8s crash loop debug", "ai kubernetes debug"],
        "type": "tutorial",
        "word_count": 2000,
    },
    {
        "title": "Prometheus Alert to Auto-Remediation: The Complete Guide",
        "primary_keyword": "prometheus alert automation",
        "secondary_keywords": ["prometheus alertmanager automation", "alert to remediation", "automated alerting"],
        "type": "tutorial",
        "word_count": 2500,
    },
    {
        "title": "Building a Kubernetes AI SRE Stack",
        "primary_keyword": "kubernetes ai sre",
        "secondary_keywords": ["ai sre stack", "kubernetes sre tools", "intelligent sre platform"],
        "type": "standard",
        "word_count": 2500,
    },
]


class ContentGenerationEngine:
    """
    Generates SEO-optimized articles using LLM for the Kubegraf blog.
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        logger.info("ContentGenerationEngine initialized")

    async def generate_article(
        self,
        topic: str,
        keywords: list[str],
        article_type: str = "standard",
        word_count: int = 2000,
        custom_prompt: Optional[str] = None,
    ) -> dict:
        """
        Generate a complete SEO article.

        Args:
            topic: Article topic/title
            keywords: Target keywords (first is primary)
            article_type: Type of article (standard/comparison/tutorial/listicle)
            word_count: Target word count
            custom_prompt: Optional custom prompt override

        Returns:
            Dict with title, content, meta_description, slug, keywords, word_count
        """
        logger.info(f"Generating {article_type} article: '{topic}'")

        primary_keyword = keywords[0] if keywords else topic.lower()
        secondary_keywords = keywords[1:6] if len(keywords) > 1 else []

        if not self.llm_client:
            logger.warning("No LLM client available, returning sample content")
            return self._generate_sample_article(topic, keywords, article_type)

        prompt = custom_prompt or KEYWORD_ARTICLE_PROMPT.format(
            primary_keyword=primary_keyword,
            target_audience="DevOps engineers and SREs working with Kubernetes",
            secondary_keywords=", ".join(secondary_keywords),
            word_count=word_count,
            article_type=article_type,
        )

        try:
            content = await self.llm_client.generate_article(
                prompt=prompt + "\n\n" + ARTICLE_GENERATION_PROMPT,
                topic=topic,
                keywords=keywords,
                word_count=word_count,
            )

            # Extract components from generated content
            title = self._extract_title(content) or topic
            meta_description = await self._extract_or_generate_meta(content, title)
            slug = self.create_slug(title)
            actual_word_count = self._count_words(content)

            # Add diagrams if not present
            content = await self.add_diagrams(content, article_type)

            result = {
                "title": title,
                "slug": slug,
                "content": content,
                "meta_description": meta_description,
                "primary_keyword": primary_keyword,
                "keywords": keywords,
                "word_count": actual_word_count,
                "article_type": article_type,
                "generated_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"Generated article: '{title}' ({actual_word_count} words)")
            return result

        except Exception as e:
            logger.error(f"Article generation failed for '{topic}': {e}", exc_info=True)
            raise

    async def generate_comparison_article(
        self,
        our_product: str,
        competitor: str,
        competitor_domain: str,
        competitor_description: str = "",
        competitor_features: Optional[list[str]] = None,
    ) -> dict:
        """
        Generate a competitor comparison article.

        Args:
            our_product: Our product name (Kubegraf)
            competitor: Competitor name
            competitor_domain: Competitor domain
            competitor_description: Brief description of competitor
            competitor_features: List of competitor's key features

        Returns:
            Dict with generated article content
        """
        logger.info(f"Generating comparison article: {our_product} vs {competitor}")

        features_str = "\n".join(f"- {f}" for f in (competitor_features or [
            "Incident management",
            "Alert routing",
            "On-call scheduling",
        ]))

        prompt = COMPARISON_ARTICLE_PROMPT.format(
            competitor_name=competitor,
            competitor_domain=competitor_domain,
            competitor_description=competitor_description or f"Platform in the {competitor} space",
            competitor_features=features_str,
            competitor_use_case=f"DevOps and SRE teams using {competitor}",
        )

        keywords = [
            f"{our_product.lower()} vs {competitor.lower()}",
            f"{competitor.lower()} alternative",
            f"{competitor.lower()} competitor",
            f"best {competitor.lower()} alternative",
        ]

        return await self.generate_article(
            topic=f"{our_product} vs {competitor}: Complete Comparison",
            keywords=keywords,
            article_type="comparison",
            word_count=3000,
            custom_prompt=prompt,
        )

    async def generate_tutorial(
        self,
        topic: str,
        steps: list[str],
        primary_keyword: str,
        skill_level: str = "intermediate",
        time_estimate: int = 30,
    ) -> dict:
        """
        Generate a step-by-step technical tutorial.

        Args:
            topic: Tutorial topic
            steps: High-level steps to cover
            primary_keyword: Target keyword
            skill_level: beginner/intermediate/advanced
            time_estimate: Estimated minutes to complete

        Returns:
            Dict with generated tutorial content
        """
        logger.info(f"Generating tutorial: '{topic}'")

        steps_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps))

        prompt = TUTORIAL_PROMPT.format(
            tutorial_topic=topic,
            primary_keyword=primary_keyword,
            skill_level=skill_level,
            time_estimate=time_estimate,
        ) + f"\n\nCover these steps:\n{steps_str}"

        keywords = [primary_keyword, f"{primary_keyword} tutorial", f"how to {primary_keyword}"]

        return await self.generate_article(
            topic=topic,
            keywords=keywords,
            article_type="tutorial",
            word_count=2500,
            custom_prompt=prompt,
        )

    async def add_diagrams(self, article: str, article_type: str = "standard") -> str:
        """
        Add Mermaid diagram code blocks to an article.

        Args:
            article: Article content in markdown
            article_type: Type of article

        Returns:
            Article with diagrams added
        """
        # Only add diagrams if there aren't already mermaid blocks
        if "```mermaid" in article:
            return article

        # Add appropriate diagram based on article type
        diagram_insertion = ""
        if "incident" in article.lower() or "remediation" in article.lower():
            diagram_insertion = f"\n\n{MERMAID_INCIDENT_FLOW}\n\n"
        elif "monitoring" in article.lower() or "observability" in article.lower():
            diagram_insertion = f"\n\n{MERMAID_K8S_MONITORING}\n\n"

        if diagram_insertion:
            # Insert after first H2 section
            h2_match = re.search(r'\n## [^\n]+\n', article)
            if h2_match:
                insert_pos = h2_match.end()
                article = article[:insert_pos] + diagram_insertion + article[insert_pos:]

        return article

    async def batch_generate(
        self,
        topics: Optional[list[dict]] = None,
        max_articles: int = 5,
    ) -> list[dict]:
        """
        Generate multiple articles in batch.

        Args:
            topics: List of topic dicts. If None, uses SAMPLE_TOPICS.
            max_articles: Maximum number of articles to generate

        Returns:
            List of generated article dicts
        """
        topics_to_process = (topics or SAMPLE_TOPICS)[:max_articles]
        generated = []

        for topic_config in topics_to_process:
            try:
                if topic_config.get("type") == "comparison" and topic_config.get("competitor"):
                    article = await self.generate_comparison_article(
                        our_product="Kubegraf",
                        competitor=topic_config["competitor"],
                        competitor_domain=f"{topic_config['competitor'].lower().replace(' ', '')}.com",
                    )
                elif topic_config.get("type") == "tutorial":
                    article = await self.generate_tutorial(
                        topic=topic_config["title"],
                        steps=["Set up environment", "Configure Kubegraf", "Implement solution", "Test and verify"],
                        primary_keyword=topic_config["primary_keyword"],
                    )
                else:
                    article = await self.generate_article(
                        topic=topic_config["title"],
                        keywords=[topic_config["primary_keyword"]] + topic_config.get("secondary_keywords", []),
                        article_type=topic_config.get("type", "standard"),
                        word_count=topic_config.get("word_count", 2000),
                    )

                generated.append(article)
                logger.info(f"Generated: {article['title']}")

            except Exception as e:
                logger.error(f"Failed to generate article for topic '{topic_config.get('title')}': {e}")

        logger.info(f"Batch generation complete: {len(generated)}/{len(topics_to_process)} articles")
        return generated

    def create_slug(self, title: str) -> str:
        """
        Create a URL-friendly slug from a title.

        Args:
            title: Article title

        Returns:
            URL-friendly slug
        """
        # Remove special characters, convert to lowercase
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        slug = slug.strip('-')
        # Limit length
        if len(slug) > 100:
            slug = slug[:100].rstrip('-')
        return slug

    def build_internal_links(self, article: str, all_articles: list[dict]) -> str:
        """
        Replace [INTERNAL_LINK: topic] placeholders with actual links.

        Args:
            article: Article content with link placeholders
            all_articles: List of all published articles with slug and title

        Returns:
            Article with internal links populated
        """
        pattern = r'\[INTERNAL_LINK: ([^\]]+)\]'

        def replace_link(match):
            topic = match.group(1)
            # Find best matching article
            best_match = None
            best_score = 0
            topic_words = set(topic.lower().split())

            for pub_article in all_articles:
                title_words = set(pub_article.get("title", "").lower().split())
                score = len(topic_words.intersection(title_words))
                if score > best_score:
                    best_score = score
                    best_match = pub_article

            if best_match and best_score > 0:
                slug = best_match.get("slug", "#")
                title = best_match.get("title", topic)
                return f"[{title}](/blog/{slug})"
            else:
                # Fallback: create a link based on the topic
                slug = self.create_slug(topic)
                return f"[{topic}](/blog/{slug})"

        return re.sub(pattern, replace_link, article)

    def _extract_title(self, content: str) -> Optional[str]:
        """Extract the H1 title from article content."""
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return None

    async def _extract_or_generate_meta(self, content: str, title: str) -> str:
        """Extract meta description from content or generate one."""
        # Look for explicit meta description
        meta_match = re.search(r'[Mm]eta[_ ][Dd]escription[:\s]+(.+?)(?:\n|$)', content)
        if meta_match:
            meta = meta_match.group(1).strip()
            if 100 <= len(meta) <= 165:
                return meta

        # Use first paragraph as meta description
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip() and not p.startswith('#')]
        if paragraphs:
            first_para = re.sub(r'\[.*?\]\(.*?\)', '', paragraphs[0])  # Remove links
            first_para = re.sub(r'[*_`]', '', first_para)  # Remove markdown
            first_para = first_para.strip()
            if len(first_para) > 150:
                return first_para[:157] + "..."
            return first_para[:160]

        return f"Learn about {title}. Kubegraf provides AI-powered Kubernetes monitoring and automated incident management."[:160]

    def _count_words(self, content: str) -> int:
        """Count words in content, excluding code blocks."""
        # Remove code blocks
        no_code = re.sub(r'```[\s\S]*?```', '', content)
        no_code = re.sub(r'`[^`]+`', '', no_code)
        words = no_code.split()
        return len(words)

    def _generate_sample_article(self, topic: str, keywords: list[str], article_type: str) -> dict:
        """Generate a sample article when no LLM is available."""
        primary_keyword = keywords[0] if keywords else "kubernetes"
        slug = self.create_slug(topic)

        content = f"""# {topic}

Kubernetes has become the de facto standard for container orchestration, but managing it at scale
presents unique challenges. In this article, we'll explore {primary_keyword} and how modern
AI-powered platforms like Kubegraf are transforming the way teams handle Kubernetes operations.

## The Challenge of {primary_keyword.title()}

Modern Kubernetes environments are complex. With hundreds of microservices running across multiple
clusters, identifying the root cause of an incident can take hours or even days without the right tools.

```bash
# Example: Checking pod status
kubectl get pods -n production
kubectl describe pod <pod-name> -n production
kubectl logs <pod-name> -n production --previous
```

## How Kubegraf Solves This Problem

Kubegraf's AI-powered analysis engine can identify the root cause of Kubernetes incidents in seconds.
Here's what makes it different:

1. **Automatic log correlation**: Kubegraf automatically correlates logs, metrics, and events
2. **AI-powered analysis**: Natural language explanations of what went wrong and why
3. **SafeFix remediation**: Automated fixes for common issues with safety guardrails

## Step-by-Step Guide

### Step 1: Install Kubegraf

```bash
helm repo add kubegraf https://charts.kubegraf.com
helm install kubegraf kubegraf/kubegraf --namespace monitoring --create-namespace
```

### Step 2: Configure Alerting

```yaml
apiVersion: kubegraf.io/v1alpha1
kind: AlertRule
metadata:
  name: high-error-rate
  namespace: monitoring
spec:
  condition: "error_rate > 0.05"
  severity: critical
  aiAnalysis: true
  autoRemediate: true
```

### Step 3: Enable AI Analysis

Once configured, Kubegraf will automatically analyze incidents and provide:
- Root cause identification
- Impact assessment
- Recommended fixes
- Automated remediation options

## Best Practices

- Always test remediation rules in staging first
- Set up proper RBAC for Kubegraf's service account
- Configure alert thresholds based on your SLOs
- Review AI recommendations before enabling fully automatic remediation

## Conclusion

Managing Kubernetes incidents effectively requires the right tooling. With {primary_keyword},
teams can reduce MTTR from hours to minutes. Kubegraf's AI-powered platform makes this achievable
for teams of any size.

[Get started with Kubegraf free trial](https://kubegraf.com/trial)

[INTERNAL_LINK: kubernetes monitoring best practices]
[INTERNAL_LINK: prometheus alerting setup]
"""

        return {
            "title": topic,
            "slug": slug,
            "content": content,
            "meta_description": f"Learn about {primary_keyword} with Kubegraf's AI-powered Kubernetes platform. Reduce MTTR and automate incident response."[:160],
            "primary_keyword": primary_keyword,
            "keywords": keywords,
            "word_count": self._count_words(content),
            "article_type": article_type,
            "generated_at": datetime.utcnow().isoformat(),
            "is_sample": True,
        }
