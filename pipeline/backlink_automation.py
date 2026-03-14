"""
Backlink Automation Engine
Generates outreach drafts, cross-post content, and tracks link-building opportunities.
Creates GitHub Issues for high-priority outreach tracking.
"""
import os
import json
import logging
import requests
from datetime import datetime
from shared.gemini_client import generate_json, generate
from shared import storage

logger = logging.getLogger(__name__)

BACKLINK_TARGETS = [
    {
        "site": "dev.to",
        "type": "developer_community",
        "approach": "cross_post",
        "audience": "developers and DevOps engineers",
        "url": "https://dev.to",
        "priority": "high",
    },
    {
        "site": "medium.com",
        "type": "technical_blog",
        "approach": "cross_post",
        "audience": "technical practitioners",
        "url": "https://medium.com",
        "priority": "high",
    },
    {
        "site": "dzone.com",
        "type": "developer_news",
        "approach": "syndication",
        "audience": "enterprise developers and architects",
        "url": "https://dzone.com",
        "priority": "high",
    },
    {
        "site": "reddit.com/r/kubernetes",
        "type": "community",
        "approach": "engagement",
        "audience": "Kubernetes practitioners",
        "url": "https://reddit.com/r/kubernetes",
        "priority": "medium",
    },
    {
        "site": "reddit.com/r/devops",
        "type": "community",
        "approach": "engagement",
        "audience": "DevOps engineers",
        "url": "https://reddit.com/r/devops",
        "priority": "medium",
    },
    {
        "site": "reddit.com/r/sre",
        "type": "community",
        "approach": "engagement",
        "audience": "Site Reliability Engineers",
        "url": "https://reddit.com/r/sre",
        "priority": "medium",
    },
    {
        "site": "hashnode.com",
        "type": "developer_blog",
        "approach": "cross_post",
        "audience": "developers",
        "url": "https://hashnode.com",
        "priority": "medium",
    },
    {
        "site": "hackernews",
        "type": "tech_news",
        "approach": "submission",
        "audience": "tech community",
        "url": "https://news.ycombinator.com/submit",
        "priority": "high",
    },
    {
        "site": "cncf.io",
        "type": "foundation",
        "approach": "contribute",
        "audience": "cloud-native community",
        "url": "https://cncf.io",
        "priority": "high",
    },
    {
        "site": "kubernetes.io/blog",
        "type": "official_docs",
        "approach": "contribute",
        "audience": "Kubernetes community",
        "url": "https://kubernetes.io/blog",
        "priority": "high",
    },
]


def generate_outreach_email(article, target: dict) -> str:
    """Use Gemini to generate a personalized outreach email draft."""
    prompt = f"""You are a developer relations manager at Kubegraf, an AI-powered Kubernetes SRE platform.

Write a short, genuine outreach email to submit/cross-post our article to {target['site']}.

Article details:
- Title: {article.title}
- Category: {article.category}
- Keywords: {', '.join(article.keywords)}
- URL: https://kubegraf.github.io/seo-automation/blog/{article.slug}
- Word count: {article.word_count}
- Approach: {target['approach']}
- Target audience: {target['audience']}

Write a {target['approach']} outreach message that:
1. Is genuine and not spammy (2-3 short paragraphs max)
2. Explains the value for their audience
3. Includes the article URL
4. Has a clear call to action
5. Sounds like a real person wrote it

Return just the email body (no subject line needed). Be concise."""

    try:
        return generate(prompt)
    except Exception as e:
        logger.warning(f"Failed to generate outreach for {target['site']}: {e}")
        return f"Hi,\n\nWe published a technical article on '{article.title}' that may interest your {target['audience']} audience.\n\nURL: https://kubegraf.github.io/seo-automation/blog/{article.slug}\n\nWould love to cross-post / share with your community.\n\nThanks,\nKubegraf Team"


def generate_cross_post_intro(article) -> str:
    """Generate a platform-optimized intro for cross-posting on dev.to/Medium/Hashnode."""
    prompt = f"""Write a 2-sentence intro to add at the top of a cross-posted article for dev.to / Medium / Hashnode.

Article: {article.title}
Original URL: https://kubegraf.github.io/seo-automation/blog/{article.slug}

The intro should:
- Mention this is originally published on the Kubegraf blog
- Include a link back to the original
- Be 1-2 sentences only
Return just the intro text."""

    try:
        return generate(prompt)
    except Exception as e:
        logger.warning(f"Failed to generate cross-post intro: {e}")
        return f"*This article was originally published on the [Kubegraf Engineering Blog](https://kubegraf.github.io/seo-automation/blog/{article.slug}).*\n\n---\n"


def create_github_issue(title: str, body: str, labels: list = None) -> dict | None:
    """Create a GitHub Issue to track backlink outreach. Requires GITHUB_TOKEN."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        logger.info("GITHUB_TOKEN not set — skipping GitHub issue creation")
        return None

    repo = os.environ.get("GITHUB_REPOSITORY", "kubegraf/seo-automation")

    try:
        resp = requests.post(
            f"https://api.github.com/repos/{repo}/issues",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json",
            },
            json={
                "title": title,
                "body": body,
                "labels": labels or ["backlink", "outreach"],
            },
            timeout=15,
        )
        if resp.status_code == 201:
            data = resp.json()
            logger.info(f"Created GitHub issue #{data['number']}: {title}")
            return {"number": data["number"], "url": data["html_url"]}
        else:
            logger.warning(f"Failed to create GitHub issue: {resp.status_code} {resp.text[:200]}")
            return None
    except Exception as e:
        logger.warning(f"GitHub issue creation failed: {e}")
        return None


def build_issue_body(article, target: dict, outreach_email: str) -> str:
    return f"""## Backlink Outreach Tracking

**Article:** [{article.title}](https://kubegraf.github.io/seo-automation/blog/{article.slug})
**Target:** {target['site']}
**Approach:** {target['approach']}
**Priority:** {target['priority']}
**SEO Score:** {article.seo_score:.0f}/100

---

### Outreach Draft

```
{outreach_email}
```

---

### Checklist

- [ ] Draft reviewed and personalized
- [ ] Submitted / sent
- [ ] Follow-up sent (if no response after 1 week)
- [ ] Link acquired ✅

---
*Auto-generated by Kubegraf SEO Pipeline*
"""


def save_backlinks(opportunities: list):
    """Persist backlink data to data/backlinks.json."""
    import json
    from pathlib import Path

    path = Path(__file__).parent.parent / "data" / "backlinks.json"
    path.parent.mkdir(exist_ok=True)

    existing = []
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Merge by (article_slug, target_site) key
    existing_keys = {(o.get("article_slug"), o.get("target_site")) for o in existing}
    new_entries = [
        o for o in opportunities
        if (o.get("article_slug"), o.get("target_site")) not in existing_keys
    ]
    all_entries = existing + new_entries

    path.write_text(json.dumps(all_entries, indent=2, ensure_ascii=False), encoding="utf-8")
    return len(new_entries)


def run():
    """Main entrypoint for backlink automation pipeline step."""
    from rich.console import Console
    console = Console()

    console.print("[bold blue]🔗 Backlink Automation Engine[/bold blue]")

    articles = storage.load_articles()
    published = [a for a in articles if a.status == "published"]

    if not published:
        console.print("[yellow]No published articles yet — backlink automation will run after first publish.[/yellow]")
        return []

    # Pick top articles by SEO score for outreach
    top_articles = sorted(published, key=lambda a: a.seo_score, reverse=True)[:5]
    high_priority_targets = [t for t in BACKLINK_TARGETS if t["priority"] == "high"]

    all_opportunities = []
    issues_created = 0

    for article in top_articles:
        console.print(f"\n  📄 {article.title[:60]}...")

        for target in high_priority_targets:
            # Generate personalized outreach
            console.print(f"     ✍️  Generating outreach for {target['site']}...")
            outreach = generate_outreach_email(article, target)
            cross_post_intro = ""
            if target["approach"] == "cross_post":
                cross_post_intro = generate_cross_post_intro(article)

            opportunity = {
                "article_title": article.title,
                "article_slug": article.slug,
                "article_url": f"https://kubegraf.github.io/seo-automation/blog/{article.slug}",
                "target_site": target["site"],
                "approach": target["approach"],
                "priority": target["priority"],
                "outreach_draft": outreach,
                "cross_post_intro": cross_post_intro,
                "status": "draft",
                "created_at": datetime.utcnow().isoformat(),
                "issue_url": None,
            }

            # Create GitHub issue for tracking (only for high-priority + high SEO score)
            if article.seo_score >= 65 and target["priority"] == "high":
                issue_title = f"[Backlink] {target['approach'].title()}: {article.title[:60]} → {target['site']}"
                issue_body = build_issue_body(article, target, outreach)
                issue = create_github_issue(issue_title, issue_body)
                if issue:
                    opportunity["issue_url"] = issue["url"]
                    issues_created += 1

            all_opportunities.append(opportunity)

    # Save to data/backlinks.json
    new_count = save_backlinks(all_opportunities)

    console.print(f"\n[green]✅ Backlink automation complete:[/green]")
    console.print(f"   Articles processed: {len(top_articles)}")
    console.print(f"   Outreach drafts generated: {len(all_opportunities)}")
    console.print(f"   New opportunities saved: {new_count}")
    console.print(f"   GitHub issues created: {issues_created}")

    return all_opportunities


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
