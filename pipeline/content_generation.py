"""
Content Generation Engine
Uses Gemini to generate high-quality SEO-optimized articles.
"""
import json
import os
import logging
from datetime import datetime
from slugify import slugify
from shared.gemini_client import generate
from shared.models import Article, Keyword, Competitor
from shared import storage

logger = logging.getLogger(__name__)

ARTICLE_TOPICS = [
    {
        "title": "AI Root Cause Analysis for Kubernetes: How Kubegraf Automates Incident Investigation",
        "keywords": ["kubernetes root cause analysis", "ai incident investigation", "kubernetes debugging"],
        "type": "deep_dive",
        "category": "ai_operations",
    },
    {
        "title": "Automatic Kubernetes Incident Remediation with SafeFix",
        "keywords": ["kubernetes incident remediation", "automated kubernetes fix", "safefix kubernetes"],
        "type": "tutorial",
        "category": "kubernetes_ops",
    },
    {
        "title": "AI SRE Platforms Comparison 2024: Kubegraf vs Komodor vs Deductive AI",
        "keywords": ["ai sre platform comparison", "kubegraf vs komodor", "kubernetes sre tools"],
        "type": "comparison",
        "category": "sre",
        "competitor_target": "Komodor",
    },
    {
        "title": "How AI Can Fix Production Kubernetes Incidents in Minutes",
        "keywords": ["ai kubernetes production incidents", "automated incident resolution", "kubernetes ai fix"],
        "type": "deep_dive",
        "category": "ai_operations",
    },
    {
        "title": "Kubernetes Troubleshooting Automation: From Alert to Fix",
        "keywords": ["kubernetes troubleshooting automation", "prometheus to fix", "kubernetes alert remediation"],
        "type": "tutorial",
        "category": "kubernetes_ops",
    },
    {
        "title": "Kubegraf vs Rootly: Which Incident Management Platform is Right for You?",
        "keywords": ["kubegraf vs rootly", "incident management kubernetes", "rootly alternative kubernetes"],
        "type": "comparison",
        "category": "sre",
        "competitor_target": "Rootly",
    },
    {
        "title": "Kubernetes OOMKilled: Automatic Detection and Remediation with AI",
        "keywords": ["kubernetes oomkilled", "oomkilled remediation", "kubernetes memory limit fix"],
        "type": "incident_example",
        "category": "kubernetes_ops",
    },
    {
        "title": "CrashLoopBackOff Root Cause Analysis with AI",
        "keywords": ["crashloopbackoff root cause", "kubernetes crashloopbackoff fix", "crashloopbackoff ai"],
        "type": "incident_example",
        "category": "kubernetes_ops",
    },
    {
        "title": "Prometheus Alert to Auto-Remediation: The Complete Guide",
        "keywords": ["prometheus alert remediation", "prometheus to fix automation", "alertmanager automation"],
        "type": "tutorial",
        "category": "monitoring",
    },
    {
        "title": "Building a Kubernetes AI SRE Stack in 2024",
        "keywords": ["kubernetes ai sre stack", "sre automation kubernetes", "ai sre tools"],
        "type": "deep_dive",
        "category": "sre",
    },
    {
        "title": "Kubegraf vs Incident.io: Kubernetes-Native vs General Incident Management",
        "keywords": ["kubegraf vs incident.io", "kubernetes incident management", "incident.io alternative"],
        "type": "comparison",
        "category": "sre",
        "competitor_target": "Incident.io",
    },
    {
        "title": "How to Reduce Mean Time to Resolution (MTTR) for Kubernetes Incidents",
        "keywords": ["kubernetes mttr", "reduce mttr kubernetes", "kubernetes incident resolution time"],
        "type": "deep_dive",
        "category": "sre",
    },
]

ARTICLE_PROMPT = '''You are a senior DevOps engineer and technical writer for Kubegraf.
Kubegraf is an AI-powered Kubernetes SRE platform that:
- Receives alerts from Prometheus, Grafana, and Slack
- Automatically investigates Kubernetes workloads using AI
- Performs root cause analysis across pods, deployments, logs, and metrics
- Suggests SafeFix remediations with risk assessment
- Can automatically apply fixes to the cluster after human approval

Write a comprehensive, SEO-optimized technical article with this specification:

Title: {title}
Primary Keywords: {keywords}
Article Type: {article_type}
Target Audience: Senior DevOps engineers, SREs, platform engineers

ARTICLE STRUCTURE (follow exactly):

---
title: "{title}"
description: "{meta_description_placeholder}"
date: {date}
keywords: [{keywords_csv}]
category: {category}
author: Kubegraf Team
---

# {title}

[Write a compelling 2-3 sentence intro that includes the primary keyword and hooks the reader]

## The Problem: [Describe the pain point in 150-200 words]

[Explain the challenge, why it matters, include real-world scenario]

## How Kubegraf Solves This

[2-3 paragraphs explaining Kubegraf's approach]

## Architecture Overview

```mermaid
[Include a relevant mermaid diagram showing the architecture/flow]
```

## Step-by-Step: {article_type_heading}

### Step 1: [First step]
[Explanation with code example]

```yaml
# Example Kubernetes manifest or config
```

### Step 2: [Second step]
[Explanation]

```bash
# Example commands
```

### Step 3: [Third step]
[Explanation]

## Real-World Example

[Concrete scenario: "Imagine your e-commerce platform is seeing CrashLoopBackOff on checkout service..."]
[Walk through exactly what Kubegraf does, step by step]
[Include example Kubegraf output/analysis]

```json
// Example Kubegraf investigation output
{{
  "incident": "...",
  "root_cause": "...",
  "confidence": 0.94,
  "safefix": {{...}}
}}
```

## Comparison: Manual vs AI-Automated

| Approach | Time to Detect | Time to RCA | Time to Fix | Risk |
|----------|---------------|-------------|-------------|------|
| Manual | ... | ... | ... | ... |
| Kubegraf AI | ... | ... | ... | ... |

## Key Takeaways

- [3-5 bullet points summarizing key learnings]

## Related Articles

- [Internal link 1]
- [Internal link 2]
- [Internal link 3]

## Getting Started with Kubegraf

[Brief call to action with link to kubegraf.io]

---
*This article was written by the Kubegraf engineering team. [Related: link to another article]*

IMPORTANT REQUIREMENTS:
1. Article must be 1500-2500 words
2. Include at least 2 code blocks (YAML, bash, or JSON)
3. Include exactly 1 mermaid diagram
4. Include primary keyword in: title, first paragraph, at least 2 H2 headings, conclusion
5. Write in authoritative but approachable tone
6. Be technically accurate about Kubernetes concepts
7. Kubegraf should be presented positively but not as perfect - acknowledge tradeoffs
'''

COMPARISON_PROMPT = '''Write a detailed, balanced comparison article between Kubegraf and {competitor_name}.

Kubegraf: AI-native Kubernetes SRE platform. Receives Prometheus/Grafana/Slack alerts, uses AI to investigate K8s workloads, performs root cause analysis, applies SafeFix remediations automatically.

{competitor_name}: {competitor_focus}

Write a 1800+ word comparison article structured as:

---
title: "Kubegraf vs {competitor_name}: [Compelling subtitle about the comparison angle]"
description: "Detailed comparison of Kubegraf and {competitor_name} for Kubernetes incident management. Which platform is right for your team in 2024?"
date: {date}
keywords: ["kubegraf vs {competitor_name_lower}", "{competitor_name_lower} alternative", "kubernetes incident management comparison"]
category: comparison
---

# Kubegraf vs {competitor_name}: [subtitle]

[Hook paragraph about the challenge of choosing the right platform]

## Quick Summary

| Feature | Kubegraf | {competitor_name} |
|---------|----------|{competitor_name}|
| Focus | Kubernetes-native AI SRE | [their focus] |
| AI Capabilities | [kubegraf] | [competitor] |
| Root Cause Analysis | Yes, automated | [competitor] |
| Auto-Remediation | Yes, SafeFix | [competitor] |
| Kubernetes-native | Yes | [competitor] |
| Best For | [describe] | [describe] |

## What is Kubegraf?
[200 words about Kubegraf, how it works, key features]

## What is {competitor_name}?
[200 words about competitor, how it works, key features, be fair and accurate]

## Head-to-Head Comparison

### Incident Detection & Alerting
[Compare both platforms]

### Root Cause Analysis
[Compare - Kubegraf's AI RCA vs competitor approach]

### Auto-Remediation
[Kubegraf's SafeFix vs competitor]

### Kubernetes-Native Features
[How well each handles K8s specifically]

### Ease of Use & Setup
[Compare setup complexity]

### Pricing & Scalability
[Compare if known]

## When to Choose Kubegraf
[3-5 specific scenarios where Kubegraf wins]

## When to Choose {competitor_name}
[2-3 honest scenarios where competitor might be better]

## The Verdict
[Fair, balanced conclusion. Kubegraf is better for Kubernetes-heavy AI-driven RCA, competitor may win for non-K8s use cases]

## Getting Started

[How to try Kubegraf]

---
*Compare more platforms: [internal links to other comparison articles]*
'''


def generate_article(topic: dict, existing_articles: list) -> Article:
    """Generate a full SEO article using Gemini."""
    title = topic["title"]
    keywords = topic["keywords"]
    article_type = topic["type"]
    category = topic.get("category", "kubernetes_ops")
    competitor_target = topic.get("competitor_target")
    date = datetime.utcnow().strftime("%Y-%m-%d")

    logger.info(f"Generating article: {title}")

    # Choose prompt based on article type
    if article_type == "comparison" and competitor_target:
        competitors = storage.load_competitors()
        comp = next((c for c in competitors if c.name == competitor_target), None)
        focus = comp.focus_areas[0] if comp else "incident management platform"

        prompt = COMPARISON_PROMPT.format(
            competitor_name=competitor_target,
            competitor_name_lower=competitor_target.lower().replace(" ", "-"),
            competitor_focus=focus,
            date=date,
        )
    else:
        type_heading_map = {
            "tutorial": "Getting It Working",
            "deep_dive": "Understanding the System",
            "incident_example": "Investigating the Incident",
        }
        prompt = ARTICLE_PROMPT.format(
            title=title,
            keywords=", ".join(keywords),
            keywords_csv=", ".join(f'"{k}"' for k in keywords),
            article_type=article_type,
            article_type_heading=type_heading_map.get(article_type, "Implementation"),
            date=date,
            category=category,
            meta_description_placeholder="[SEO meta description will be filled]",
        )

    # Generate content
    content = generate(prompt)

    # Extract or generate meta description
    meta_desc = _extract_meta_description(content, title, keywords)

    # Build article
    slug = slugify(title)
    article = Article(
        title=title,
        slug=slug,
        meta_description=meta_desc,
        content=content,
        keywords=keywords,
        category=category,
        article_type=article_type,
        status="draft",
        competitor_target=competitor_target,
        word_count=len(content.split()),
        diagram_included="mermaid" in content.lower(),
        created_at=datetime.utcnow().isoformat(),
    )

    return article


def _extract_meta_description(content: str, title: str, keywords: list) -> str:
    """Extract or generate a meta description."""
    # Look for description in frontmatter
    for line in content.split("\n"):
        if line.strip().startswith("description:"):
            desc = line.split(":", 1)[1].strip().strip('"').strip("'")
            if len(desc) > 50:
                return desc[:160]

    # Generate one
    first_para = ""
    in_frontmatter = False
    for line in content.split("\n"):
        if line.strip() == "---":
            in_frontmatter = not in_frontmatter
            continue
        if not in_frontmatter and line.strip() and not line.startswith("#"):
            first_para = line.strip()
            break

    if first_para:
        return first_para[:160]

    return f"Learn how Kubegraf automates {keywords[0]} using AI. Automatic root cause analysis and remediation for Kubernetes incidents."


def run():
    """Main entrypoint for content generation pipeline step."""
    import os
    from rich.console import Console
    console = Console()

    console.print("[bold blue]✍️  Content Generation Engine[/bold blue]")

    # Load existing
    existing_articles = storage.load_articles()
    existing_slugs = {a.slug for a in existing_articles}

    # Also get keyword-driven topics from discovery
    keywords = storage.load_keywords()
    top_keywords = [k for k in keywords if k.opportunity_score > 0.75][:5]

    # Add keyword-driven topics
    extra_topics = []
    for kw in top_keywords:
        kw_title = f"Complete Guide to {kw.term.title()} for Kubernetes"
        kw_slug = slugify(kw_title)
        if kw_slug not in existing_slugs:
            extra_topics.append({
                "title": kw_title,
                "keywords": [kw.term],
                "type": "deep_dive",
                "category": kw.category,
            })

    # Combine hardcoded + keyword-driven topics
    all_topics = ARTICLE_TOPICS + extra_topics

    # Filter out already-generated articles
    new_topics = [t for t in all_topics if slugify(t["title"]) not in existing_slugs]

    num_to_generate = int(os.environ.get("ARTICLES_PER_RUN", "3"))
    topics_to_generate = new_topics[:num_to_generate]

    console.print(f"Existing articles: {len(existing_articles)}")
    console.print(f"Generating {len(topics_to_generate)} new articles...")

    generated = []
    for topic in topics_to_generate:
        try:
            console.print(f"  📝 {topic['title'][:60]}...")
            article = generate_article(topic, existing_articles)
            existing_articles.append(article)
            generated.append(article)
            console.print(f"     [green]✓ {article.word_count} words, SEO score pending[/green]")
        except Exception as e:
            console.print(f"     [red]✗ Failed: {e}[/red]")
            logger.error(f"Failed to generate article '{topic['title']}': {e}")

    # Save all articles
    storage.save_articles(existing_articles)
    console.print(f"\n[green]✅ Generated {len(generated)} articles. Total: {len(existing_articles)}[/green]")

    return generated


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
