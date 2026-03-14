"""
Publishing Engine for SEO Automation Platform.
Publishes articles to GitHub Pages / Hugo / Docusaurus via GitHub API.
"""
import base64
import json
import logging
import os
import re
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO_OWNER = os.getenv("GITHUB_REPO_OWNER", "kubegraf")
GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME", "kubegraf.com")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
GITHUB_CONTENT_PATH = os.getenv("GITHUB_CONTENT_PATH", "content/blog")
SITE_URL = os.getenv("SITE_URL", "https://kubegraf.com")


class PublishingEngine:
    """
    Publishes articles to GitHub repository for Hugo/Docusaurus/GitHub Pages.
    """

    def __init__(self):
        self.github_token = GITHUB_TOKEN
        self.repo_owner = GITHUB_REPO_OWNER
        self.repo_name = GITHUB_REPO_NAME
        self.branch = GITHUB_BRANCH
        self.content_path = GITHUB_CONTENT_PATH

        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json",
                "X-GitHub-Api-Version": "2022-11-28",
            } if self.github_token else {},
        )
        logger.info(f"PublishingEngine initialized for {self.repo_owner}/{self.repo_name}")

    async def publish_to_github(self, article: dict) -> dict:
        """
        Publish an article to GitHub repository as a markdown file.

        Args:
            article: Article dict with title, content, slug, meta_description, etc.

        Returns:
            Dict with published_url, github_sha, file_path
        """
        if not self.github_token:
            logger.warning("No GitHub token configured, simulating publish")
            return self._simulate_publish(article)

        slug = article.get("slug") or self.create_slug(article.get("title", "untitled"))
        frontmatter = self.generate_frontmatter(article)
        content = article.get("content", "")

        # Build full markdown file content
        full_content = f"{frontmatter}\n\n{content}"

        # File path in repo
        file_path = f"{self.content_path}/{slug}/index.md"
        encoded_content = base64.b64encode(full_content.encode("utf-8")).decode("utf-8")

        # Check if file already exists to get SHA for update
        existing_sha = await self._get_file_sha(file_path)

        payload = {
            "message": f"Add/Update SEO article: {article.get('title', slug)}",
            "content": encoded_content,
            "branch": self.branch,
        }
        if existing_sha:
            payload["sha"] = existing_sha

        try:
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/contents/{file_path}"
            response = await self.http_client.put(url, json=payload)
            response.raise_for_status()
            data = response.json()

            sha = data.get("content", {}).get("sha", "")
            published_url = f"{SITE_URL}/blog/{slug}/"

            logger.info(f"Published article to GitHub: {file_path} (SHA: {sha[:8]}...)")
            return {
                "published_url": published_url,
                "github_sha": sha,
                "file_path": file_path,
                "repo": f"{self.repo_owner}/{self.repo_name}",
                "branch": self.branch,
                "published_at": datetime.utcnow().isoformat(),
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API error publishing {slug}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Failed to publish {slug}: {e}")
            raise

    def generate_frontmatter(self, article: dict) -> str:
        """
        Generate Hugo/Jekyll/Docusaurus compatible YAML frontmatter.

        Args:
            article: Article dict

        Returns:
            YAML frontmatter string
        """
        title = article.get("title", "")
        meta_description = article.get("meta_description", "")
        keywords = article.get("keywords", [])
        primary_keyword = article.get("primary_keyword", "")
        slug = article.get("slug", self.create_slug(title))
        article_type = article.get("article_type", "standard")
        seo_score = article.get("seo_score", 0)
        word_count = article.get("word_count", 0)
        competitor_target = article.get("competitor_target", "")
        schema_markup = article.get("schema_markup", {})

        now = datetime.utcnow()
        date_str = now.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        year = now.year

        # Build frontmatter
        frontmatter_lines = [
            "---",
            f'title: "{self._escape_yaml_string(title)}"',
            f'description: "{self._escape_yaml_string(meta_description)}"',
            f"date: {date_str}",
            f"lastmod: {date_str}",
            f'draft: false',
            f'slug: "{slug}"',
            f'type: "blog"',
            f'layout: "post"',
            "",
            "# SEO",
            f'keywords:',
        ]

        for kw in (keywords or [])[:10]:
            frontmatter_lines.append(f'  - "{self._escape_yaml_string(kw)}"')

        frontmatter_lines.extend([
            "",
            "# Taxonomy",
            f'categories:',
            f'  - "Kubernetes"',
            f'  - "SRE"',
            f'tags:',
        ])

        # Add relevant tags
        tags = self._generate_tags(article)
        for tag in tags:
            frontmatter_lines.append(f'  - "{tag}"')

        # Article metadata
        frontmatter_lines.extend([
            "",
            "# Article metadata",
            f'author: "Kubegraf Team"',
            f'seo_score: {seo_score}',
            f'word_count: {word_count}',
            f'article_type: "{article_type}"',
        ])

        if competitor_target:
            frontmatter_lines.append(f'competitor_target: "{competitor_target}"')

        # Open Graph
        frontmatter_lines.extend([
            "",
            "# Open Graph",
            f'og_title: "{self._escape_yaml_string(title)}"',
            f'og_description: "{self._escape_yaml_string(meta_description)}"',
            f'og_type: "article"',
            "",
            "# Twitter Card",
            f'twitter_card: "summary_large_image"',
            f'twitter_title: "{self._escape_yaml_string(title)}"',
            f'twitter_description: "{self._escape_yaml_string(meta_description)}"',
        ])

        if schema_markup:
            frontmatter_lines.extend([
                "",
                "# Schema.org",
                f'schema_markup: true',
            ])

        frontmatter_lines.append("---")

        return "\n".join(frontmatter_lines)

    def create_slug(self, title: str) -> str:
        """
        Create a URL-friendly slug from a title.

        Args:
            title: Article title

        Returns:
            URL-friendly slug
        """
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        slug = slug.strip('-')
        if len(slug) > 80:
            slug = slug[:80].rstrip('-')
        return slug

    def build_internal_links(self, article: dict, all_articles: list[dict]) -> dict:
        """
        Add internal links to an article by replacing [INTERNAL_LINK: topic] placeholders.

        Args:
            article: Article dict with content
            all_articles: List of all published articles

        Returns:
            Article dict with internal links populated
        """
        content = article.get("content", "")
        pattern = r'\[INTERNAL_LINK: ([^\]]+)\]'

        def replace_link(match):
            topic = match.group(1)
            best_match = None
            best_score = 0
            topic_words = set(topic.lower().split())

            for pub_article in all_articles:
                if pub_article.get("slug") == article.get("slug"):
                    continue
                title_words = set(pub_article.get("title", "").lower().split())
                keyword_words = set(
                    " ".join(pub_article.get("keywords", [])).lower().split()
                )
                combined = title_words | keyword_words
                score = len(topic_words.intersection(combined))
                if score > best_score:
                    best_score = score
                    best_match = pub_article

            if best_match and best_score > 0:
                slug = best_match.get("slug", "#")
                link_title = best_match.get("title", topic)
                return f"[{link_title}]({SITE_URL}/blog/{slug}/)"
            else:
                slug = self.create_slug(topic)
                return f"[{topic}]({SITE_URL}/blog/{slug}/)"

        updated_content = re.sub(pattern, replace_link, content)
        internal_links = re.findall(r'\[([^\]]+)\]\(' + re.escape(SITE_URL) + r'/blog/[^\)]+\)', updated_content)

        return {
            **article,
            "content": updated_content,
            "internal_links": internal_links,
        }

    async def _get_file_sha(self, file_path: str) -> Optional[str]:
        """Get the SHA of an existing file in the repository."""
        if not self.github_token:
            return None
        try:
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/contents/{file_path}"
            response = await self.http_client.get(url, params={"ref": self.branch})
            if response.status_code == 200:
                return response.json().get("sha")
            return None
        except Exception:
            return None

    def _simulate_publish(self, article: dict) -> dict:
        """Simulate publishing for development/testing."""
        slug = article.get("slug", self.create_slug(article.get("title", "untitled")))
        logger.info(f"[SIMULATED] Publishing article: {slug}")
        return {
            "published_url": f"{SITE_URL}/blog/{slug}/",
            "github_sha": "simulated_sha_" + slug[:20],
            "file_path": f"{self.content_path}/{slug}/index.md",
            "repo": f"{self.repo_owner}/{self.repo_name}",
            "branch": self.branch,
            "published_at": datetime.utcnow().isoformat(),
            "simulated": True,
        }

    def _generate_tags(self, article: dict) -> list[str]:
        """Generate relevant tags for an article."""
        tags = []
        title = (article.get("title", "") + " " + " ".join(article.get("keywords", []))).lower()

        tag_mapping = {
            "kubernetes": "Kubernetes",
            "k8s": "Kubernetes",
            "sre": "SRE",
            "devops": "DevOps",
            "incident": "Incident Management",
            "monitoring": "Monitoring",
            "alerting": "Alerting",
            "ai": "AI/ML",
            "prometheus": "Prometheus",
            "grafana": "Grafana",
            "helm": "Helm",
            "docker": "Docker",
            "observability": "Observability",
            "remediation": "Automation",
            "comparison": "Comparison",
            "tutorial": "Tutorial",
        }

        for keyword, tag in tag_mapping.items():
            if keyword in title and tag not in tags:
                tags.append(tag)

        return tags[:6]

    def _escape_yaml_string(self, s: str) -> str:
        """Escape special characters in YAML strings."""
        if not s:
            return ""
        return s.replace('"', '\\"').replace('\n', ' ')

    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()
