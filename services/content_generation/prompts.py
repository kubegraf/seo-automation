"""
Prompt templates for content generation.
All prompts are designed for SEO-optimized technical content about Kubernetes, SRE, and DevOps.
"""

# =============================================================================
# Full Article Generation Prompt
# =============================================================================

ARTICLE_GENERATION_PROMPT = """
Write a comprehensive, SEO-optimized technical article for the Kubegraf blog.

Kubegraf is an AI-powered Kubernetes monitoring and incident management platform with these key features:
- AI-powered root cause analysis (analyzes incidents in seconds)
- SafeFix: automated remediation engine that safely fixes common Kubernetes issues
- Intelligent alert correlation and deduplication
- Natural language incident investigation
- Proactive anomaly detection
- Multi-cluster support
- GitOps-native workflow integration

ARTICLE REQUIREMENTS:

## Structure:
1. **SEO Title** (H1): Include primary keyword, compelling, under 60 characters
2. **Meta Description**: 150-160 characters, include keyword, call-to-action
3. **Introduction** (150-200 words): Hook the reader, mention the problem, hint at solution
4. **Main Body** (organized with H2/H3/H4):
   - H2: Major sections (3-5 sections)
   - H3: Subsections within each H2
   - H4: Detailed subsections where needed
5. **Code Examples**: Include relevant YAML, bash commands, or Python code
6. **Conclusion** (100-150 words): Summarize, call-to-action, mention Kubegraf
7. **Internal Links**: Add placeholders like [INTERNAL_LINK: topic description]

## SEO Requirements:
- Use primary keyword in H1 title, first paragraph, at least 2 H2s, and conclusion
- Natural keyword density (1-2% for primary keyword)
- Use related/LSI keywords throughout
- Include FAQ section with 3-5 questions if appropriate

## Content Quality:
- Technical accuracy is paramount
- Include practical, actionable advice
- Use concrete examples and real-world scenarios
- Kubernetes/DevOps engineering audience

## Formatting:
- Use markdown formatting
- Include code blocks with language specification
- Use numbered lists for steps, bullet points for features
- Bold important terms on first use
"""

# =============================================================================
# Keyword-Targeted Article Prompt
# =============================================================================

KEYWORD_ARTICLE_PROMPT = """
Write a comprehensive article specifically optimized for the keyword: "{primary_keyword}"

Target audience: {target_audience}
Secondary keywords to include: {secondary_keywords}
Target word count: approximately {word_count} words
Article type: {article_type}

CONTENT STRATEGY:
- The article must answer the search intent behind "{primary_keyword}" completely
- Use the primary keyword in: title, first 100 words, at least 2 H2 headings, meta description, conclusion
- Include secondary keywords naturally throughout the content
- Address common questions searchers have about this topic

KUBEGRAF INTEGRATION:
- Naturally integrate how Kubegraf solves the problems discussed
- Include at least one concrete example or use case with Kubegraf
- Add a section or call-out box about Kubegraf's relevant features
- Don't make it a pure sales pitch - be helpful first, promotional second

TECHNICAL DEPTH:
- Include at least 2-3 code examples (YAML, bash, kubectl commands)
- Reference real tools, best practices, and industry standards
- Mention related technologies (Prometheus, Grafana, Helm, etc.)
- Include a diagram description or ASCII art where helpful

FORMAT:
---
title: [SEO-optimized title]
meta_description: [150-160 character meta description]
primary_keyword: {primary_keyword}
---

# [H1 Title with keyword]

[Introduction with keyword in first paragraph]

## [H2 Section 1]
[Content...]

## [H2 Section 2]
[Content...]

## [H2 Section 3 - Kubegraf Solution]
[Content integrating Kubegraf...]

## Frequently Asked Questions

### [Question 1]?
[Answer...]

### [Question 2]?
[Answer...]

## Conclusion
[Summary with keyword and CTA...]
"""

# =============================================================================
# Competitor Comparison Article Prompt
# =============================================================================

COMPARISON_ARTICLE_PROMPT = """
Write a detailed, balanced, and SEO-optimized comparison article between Kubegraf and {competitor_name}.

ARTICLE GOAL: Help engineers and DevOps teams choose the right platform by giving them an honest comparison.
This should read as objective analysis, not pure marketing.

PRIMARY TARGET KEYWORD: "Kubegraf vs {competitor_name}" or "{competitor_name} alternative"
TARGET AUDIENCE: DevOps engineers, SREs, platform engineers evaluating tools

ABOUT KUBEGRAF:
- AI-powered Kubernetes monitoring and incident management
- SafeFix: automated remediation that fixes common K8s issues automatically
- Natural language root cause analysis ("Why did my pod crash?")
- Proactive anomaly detection
- Deep Kubernetes-native integrations
- Multi-cluster support
- GitOps-native workflow

ABOUT {competitor_name} ({competitor_domain}):
- {competitor_description}
- Key features: {competitor_features}
- Primary use case: {competitor_use_case}

ARTICLE STRUCTURE:

1. **Introduction** (150-200 words)
   - Both tools solve [specific problem]
   - Key question readers are trying to answer
   - What this article covers

2. **Quick Summary Table**
   | Feature | Kubegraf | {competitor_name} |
   - 8-10 key comparison points

3. **What is Kubegraf?**
   - Core capabilities, ideal user, pricing model hint

4. **What is {competitor_name}?**
   - Core capabilities, ideal user, pricing model hint

5. **Feature-by-Feature Comparison**
   - Root Cause Analysis
   - Automated Remediation
   - Kubernetes Integration
   - Alert Management
   - Incident Management
   - Reporting & Analytics
   - Pricing & Value

6. **When to Choose Kubegraf**
   - Specific scenarios where Kubegraf wins

7. **When to Choose {competitor_name}**
   - Be honest - give legitimate use cases where they might be better

8. **Migration Guide** (if applicable)
   - How to switch from {competitor_name} to Kubegraf

9. **Conclusion**
   - Summary recommendation
   - Call to action (start free trial with Kubegraf)

TONE: Professional, objective, technically credible. Slight lean toward Kubegraf but not at the cost of credibility.
"""

# =============================================================================
# Tutorial/How-To Article Prompt
# =============================================================================

TUTORIAL_PROMPT = """
Write a comprehensive, step-by-step technical tutorial about: "{tutorial_topic}"

TARGET KEYWORD: {primary_keyword}
SKILL LEVEL: {skill_level} (beginner/intermediate/advanced)
ESTIMATED TIME: {time_estimate} minutes to complete

TUTORIAL REQUIREMENTS:

## Prerequisites Section
- List all required tools, versions, and knowledge
- Include links to prerequisite tutorials as [INTERNAL_LINK: topic]

## Overview
- What the reader will build/achieve
- Why this matters for Kubernetes/SRE work
- How Kubegraf can help automate or monitor this

## Step-by-Step Instructions
Each step must include:
1. What you're doing and why
2. The exact command or YAML/code
3. Expected output (show what success looks like)
4. Common errors and how to fix them

## Code Quality
- All YAML must be valid and production-ready
- Include comments in code examples
- Provide complete, copy-paste-ready examples
- Use realistic values (not just "example.com" or "my-namespace")

## Validation Steps
- After key steps, include how to verify it worked
- Include `kubectl get`, `kubectl describe`, `kubectl logs` commands as appropriate

## Cleanup
- How to remove resources when done
- Estimated cost if using cloud resources

## Troubleshooting Section
- Top 5 common issues and solutions

## Next Steps
- Where to go from here
- Related tutorials as [INTERNAL_LINK: topic]
- How Kubegraf automates this process

FORMAT:
- Use numbered lists for sequential steps
- Use code blocks with appropriate language tags (yaml, bash, python)
- Include output examples in separate code blocks
- Bold important warnings or notes
- Use callout boxes for tips: > **Tip:** ...
"""

# =============================================================================
# System prompts for different content types
# =============================================================================

SYSTEM_PROMPT_TECHNICAL_WRITER = """You are an expert technical writer specializing in Kubernetes,
SRE (Site Reliability Engineering), DevOps, and cloud-native technologies. You write for
the Kubegraf engineering blog.

Your audience: DevOps engineers, SREs, platform engineers, and software developers who work with Kubernetes.
Your writing style: Technically accurate, practical, and engaging. You balance depth with accessibility.
You always include working code examples, real-world scenarios, and actionable advice.

About Kubegraf (your employer):
- AI-powered Kubernetes monitoring and incident management platform
- Key differentiator: SafeFix automated remediation + AI root cause analysis
- Competitors: Komodor, Incident.io, PagerDuty, Rootly, Deductive AI
- Website: kubegraf.com
- Tone: Professional, technically credible, helpful first

Content guidelines:
- Never make up product features or capabilities
- Always include practical code examples
- Use H1-H4 heading hierarchy properly
- Write meta descriptions that are exactly 150-160 characters
- Include internal link placeholders as [INTERNAL_LINK: description]"""

SYSTEM_PROMPT_SEO_OPTIMIZER = """You are an SEO expert specializing in technical B2B SaaS content.
You optimize articles for search engines while maintaining technical quality and readability.

Your expertise:
- Keyword placement and density optimization
- Heading hierarchy and structure
- Meta description optimization
- Schema markup (Article, FAQ, HowTo)
- Internal and external linking strategy
- Featured snippet optimization

Always ensure:
- Primary keyword in H1, first paragraph, at least 2 H2s
- Meta description 150-160 characters
- Proper heading hierarchy (only one H1)
- Natural keyword usage (avoid stuffing)"""

SYSTEM_PROMPT_COMPETITOR_ANALYST = """You are a competitive intelligence analyst for Kubegraf,
an AI-powered Kubernetes monitoring and incident management platform.

You research and analyze competitors in the DevOps/SRE/Kubernetes space to:
1. Identify keyword gaps and opportunities
2. Find content gaps we should fill
3. Generate honest comparison articles
4. Develop competitive positioning strategies

Be objective and honest - the goal is to help engineers make informed decisions,
not just to promote Kubegraf. When competitors have genuine advantages, acknowledge them."""

# =============================================================================
# Mermaid diagram templates
# =============================================================================

MERMAID_INCIDENT_FLOW = """```mermaid
graph TD
    A[Alert Triggered] --> B{Kubegraf AI Analysis}
    B --> C[Root Cause Identified]
    C --> D{SafeFix Available?}
    D -->|Yes| E[Automated Remediation]
    D -->|No| F[Runbook Suggested]
    E --> G[Issue Resolved]
    F --> H[Engineer Reviews]
    H --> I[Manual Fix Applied]
    G --> J[Post-incident Report]
    I --> J
    J --> K[Prevention Rules Updated]
```"""

MERMAID_K8S_MONITORING = """```mermaid
graph LR
    A[Kubernetes Cluster] --> B[Kubegraf Agent]
    B --> C[Metrics Collection]
    B --> D[Log Collection]
    B --> E[Event Collection]
    C --> F[AI Analysis Engine]
    D --> F
    E --> F
    F --> G[Anomaly Detection]
    F --> H[Root Cause Analysis]
    G --> I[Smart Alerts]
    H --> J[SafeFix Remediation]
    I --> K[On-call Engineer]
    J --> L[Auto-resolved]
```"""

MERMAID_SEO_PIPELINE = """```mermaid
graph TD
    A[Keyword Discovery] --> B[Competitor Analysis]
    B --> C[Content Brief Generation]
    C --> D[AI Article Writing]
    D --> E[SEO Optimization]
    E --> F[Human Review]
    F --> G{Approved?}
    G -->|Yes| H[Publishing to GitHub Pages]
    G -->|No| I[Revisions]
    I --> F
    H --> J[Rank Tracking]
    J --> K[Performance Analytics]
    K --> A
```"""
