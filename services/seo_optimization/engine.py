"""
SEO Optimization Engine for SEO Automation Platform.
Optimizes article content for search engine ranking.
"""
import json
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class SEOOptimizationEngine:
    """
    Optimizes articles for SEO by improving title, meta, keyword density,
    internal links, headings, and adding schema markup.
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        logger.info("SEOOptimizationEngine initialized")

    async def optimize_article(self, article: dict) -> dict:
        """
        Full SEO optimization pass on an article.

        Args:
            article: Dict with title, content, meta_description, keywords

        Returns:
            Optimized article dict with seo_score added
        """
        logger.info(f"Optimizing article: '{article.get('title', 'Unknown')}'")

        content = article.get("content", "")
        title = article.get("title", "")
        primary_keyword = article.get("primary_keyword", "")
        keywords = article.get("keywords", [])

        # Run all optimization passes
        title = self._optimize_title(title, primary_keyword)
        meta = await self._optimize_meta_description(article)
        content = self.optimize_headings(content)
        content = self._optimize_keyword_density(content, primary_keyword, keywords)
        schema = self.add_schema_markup(article)

        # Calculate final SEO score
        optimized_article = {
            **article,
            "title": title,
            "meta_description": meta,
            "content": content,
            "schema_markup": schema,
        }
        seo_score = self.calculate_seo_score(optimized_article)
        optimized_article["seo_score"] = seo_score

        logger.info(f"Article optimized. SEO score: {seo_score}/100")
        return optimized_article

    def calculate_seo_score(self, article: dict) -> float:
        """
        Calculate SEO score for an article (0-100).

        Scoring criteria:
        - Title optimization (20 pts)
        - Meta description (15 pts)
        - Keyword usage (20 pts)
        - Content length (15 pts)
        - Heading structure (15 pts)
        - Readability (15 pts)

        Args:
            article: Article dict

        Returns:
            SEO score 0-100
        """
        score = 0.0
        content = article.get("content", "")
        title = article.get("title", "")
        meta = article.get("meta_description", "")
        primary_keyword = article.get("primary_keyword", "").lower()
        word_count = article.get("word_count", len(content.split()))

        # --- Title Score (20 pts) ---
        title_score = 0.0
        if title:
            title_lower = title.lower()
            if primary_keyword and primary_keyword in title_lower:
                title_score += 10
            title_len = len(title)
            if 30 <= title_len <= 60:
                title_score += 7
            elif 20 <= title_len <= 70:
                title_score += 4
            if not title.endswith('.'):
                title_score += 3
        score += title_score

        # --- Meta Description Score (15 pts) ---
        meta_score = 0.0
        if meta:
            meta_len = len(meta)
            if 150 <= meta_len <= 160:
                meta_score += 8
            elif 120 <= meta_len <= 165:
                meta_score += 5
            if primary_keyword and primary_keyword in meta.lower():
                meta_score += 5
            if any(word in meta.lower() for word in ["learn", "discover", "guide", "how", "best"]):
                meta_score += 2
        score += meta_score

        # --- Keyword Usage Score (20 pts) ---
        keyword_score = 0.0
        if primary_keyword and content:
            content_lower = content.lower()
            kw_count = content_lower.count(primary_keyword)
            word_count_val = word_count or 1

            # Keyword density (ideal: 0.5-2%)
            density = (kw_count / word_count_val) * 100
            if 0.5 <= density <= 2.0:
                keyword_score += 10
            elif 0.3 <= density <= 3.0:
                keyword_score += 6
            elif kw_count > 0:
                keyword_score += 3

            # Keyword in first 100 words
            first_100_words = " ".join(content.split()[:100]).lower()
            if primary_keyword in first_100_words:
                keyword_score += 5

            # Keyword in H2 headings
            h2_matches = re.findall(r'^## .+$', content, re.MULTILINE)
            if any(primary_keyword in h.lower() for h in h2_matches):
                keyword_score += 5
        score += keyword_score

        # --- Content Length Score (15 pts) ---
        length_score = 0.0
        if word_count >= 2000:
            length_score = 15
        elif word_count >= 1500:
            length_score = 12
        elif word_count >= 1000:
            length_score = 8
        elif word_count >= 500:
            length_score = 4
        score += length_score

        # --- Heading Structure Score (15 pts) ---
        heading_score = 0.0
        h1_count = len(re.findall(r'^# [^#]', content, re.MULTILINE))
        h2_count = len(re.findall(r'^## ', content, re.MULTILINE))
        h3_count = len(re.findall(r'^### ', content, re.MULTILINE))

        if h1_count == 1:
            heading_score += 6
        elif h1_count == 0:
            heading_score += 0
        else:
            heading_score += 2  # Multiple H1s is bad

        if h2_count >= 3:
            heading_score += 6
        elif h2_count >= 2:
            heading_score += 4
        elif h2_count >= 1:
            heading_score += 2

        if h3_count >= 2:
            heading_score += 3

        score += heading_score

        # --- Readability Score (15 pts) ---
        readability_score = 0.0
        if content:
            # Check for code blocks (technical content)
            code_blocks = len(re.findall(r'```', content)) // 2
            if code_blocks >= 2:
                readability_score += 5

            # Check for bullet points
            bullet_points = len(re.findall(r'^[-*+] ', content, re.MULTILINE))
            if bullet_points >= 5:
                readability_score += 4

            # Check for numbered lists
            numbered = len(re.findall(r'^\d+\. ', content, re.MULTILINE))
            if numbered >= 3:
                readability_score += 3

            # Check for internal links
            internal_links = len(re.findall(r'\[.*?\]\(/blog/', content))
            if internal_links >= 2:
                readability_score += 3

        score += readability_score

        return round(min(100.0, score), 1)

    def add_schema_markup(self, article: dict) -> dict:
        """
        Generate JSON-LD schema markup for an article.

        Args:
            article: Article dict

        Returns:
            JSON-LD schema dict
        """
        title = article.get("title", "")
        meta = article.get("meta_description", "")
        keywords = article.get("keywords", [])
        slug = article.get("slug", "")

        # Article schema
        article_schema = {
            "@context": "https://schema.org",
            "@type": "TechArticle",
            "headline": title,
            "description": meta,
            "keywords": ", ".join(keywords[:10]),
            "url": f"https://kubegraf.com/blog/{slug}",
            "publisher": {
                "@type": "Organization",
                "name": "Kubegraf",
                "url": "https://kubegraf.com",
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://kubegraf.com/logo.png",
                },
            },
            "author": {
                "@type": "Organization",
                "name": "Kubegraf Team",
                "url": "https://kubegraf.com",
            },
            "inLanguage": "en-US",
            "about": {
                "@type": "Thing",
                "name": keywords[0] if keywords else "Kubernetes",
            },
        }

        # Add FAQ schema if article has FAQ section
        faq_items = self._extract_faq(article.get("content", ""))
        if faq_items:
            faq_schema = {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": item["question"],
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": item["answer"],
                        },
                    }
                    for item in faq_items
                ],
            }
            return {"article": article_schema, "faq": faq_schema}

        return {"article": article_schema}

    def optimize_headings(self, content: str) -> str:
        """
        Ensure proper H1-H4 heading hierarchy in the article.

        Rules:
        - Only one H1 per article
        - H2s must come before H3s
        - H3s must come before H4s
        - No skipping levels

        Args:
            content: Article markdown content

        Returns:
            Content with corrected heading hierarchy
        """
        lines = content.split('\n')
        result_lines = []
        h1_count = 0
        last_level = 0

        for line in lines:
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                hashes = heading_match.group(1)
                heading_text = heading_match.group(2)
                level = len(hashes)

                # Enforce single H1
                if level == 1:
                    h1_count += 1
                    if h1_count > 1:
                        # Downgrade extra H1s to H2
                        level = 2
                        hashes = '##'

                # Fix skipped levels (e.g., H1 -> H3 should be H1 -> H2)
                if level > last_level + 1 and last_level > 0:
                    level = last_level + 1
                    hashes = '#' * level

                last_level = level
                result_lines.append(f"{hashes} {heading_text}")
            else:
                # Reset tracking on non-heading, non-empty lines
                if line.strip() and not line.startswith('#'):
                    pass  # Don't reset last_level in headings tracking
                result_lines.append(line)

        return '\n'.join(result_lines)

    def _optimize_title(self, title: str, primary_keyword: str) -> str:
        """Optimize the article title for SEO."""
        if not title:
            return title

        # Ensure title is not too long
        if len(title) > 65:
            # Try to shorten while keeping keyword
            words = title.split()
            short_title = ' '.join(words[:8])
            if primary_keyword.lower() in short_title.lower():
                return short_title
            # Keep keyword but trim other parts
            return title[:62] + "..."

        # Ensure primary keyword is in title (if not already)
        if primary_keyword and primary_keyword.lower() not in title.lower():
            # Add keyword to beginning if title is short enough
            if len(title) + len(primary_keyword) + 2 <= 65:
                return f"{primary_keyword.title()}: {title}"

        return title

    async def _optimize_meta_description(self, article: dict) -> str:
        """Optimize meta description for click-through rate."""
        current_meta = article.get("meta_description", "")
        title = article.get("title", "")
        primary_keyword = article.get("primary_keyword", "")

        # If meta is already good, return it
        if current_meta and 140 <= len(current_meta) <= 160:
            if primary_keyword.lower() in current_meta.lower():
                return current_meta

        # Generate new meta using LLM if available
        if self.llm_client and article.get("content"):
            try:
                content_preview = article["content"][:500]
                new_meta = await self.llm_client.generate_meta_description(title, content_preview)
                if 140 <= len(new_meta) <= 160:
                    return new_meta
            except Exception as e:
                logger.warning(f"LLM meta optimization failed: {e}")

        # Fallback: fix existing meta
        if current_meta:
            if len(current_meta) > 160:
                return current_meta[:157] + "..."
            if len(current_meta) < 100:
                return current_meta + f" Learn more at Kubegraf."
            return current_meta

        # Generate from title
        return f"Learn about {primary_keyword or title}. Kubegraf provides AI-powered Kubernetes monitoring and automated incident management."[:160]

    def _optimize_keyword_density(
        self,
        content: str,
        primary_keyword: str,
        keywords: list[str],
        target_density: float = 1.0,
    ) -> str:
        """
        Adjust keyword density to target level.
        Currently ensures keyword is present but doesn't add artificial stuffing.
        """
        if not primary_keyword or not content:
            return content

        word_count = len(content.split())
        current_count = content.lower().count(primary_keyword.lower())
        current_density = (current_count / max(word_count, 1)) * 100

        # If density is already in good range, don't modify
        if 0.5 <= current_density <= 2.5:
            return content

        # If keyword is missing entirely, add it to introduction
        if current_count == 0:
            # Add keyword to first paragraph naturally
            paragraphs = content.split('\n\n')
            for i, para in enumerate(paragraphs):
                if para.strip() and not para.startswith('#') and len(para) > 100:
                    paragraphs[i] = para + f"\n\nUnderstanding {primary_keyword} is crucial for modern Kubernetes operations."
                    break
            content = '\n\n'.join(paragraphs)

        return content

    def _extract_faq(self, content: str) -> list[dict]:
        """Extract FAQ questions and answers from content."""
        faq_items = []
        in_faq = False

        lines = content.split('\n')
        current_question = None
        current_answer_lines = []

        for line in lines:
            # Detect FAQ section
            if re.match(r'^##?\s*(FAQ|Frequently Asked Questions)', line, re.IGNORECASE):
                in_faq = True
                continue

            if in_faq:
                # New section ends FAQ
                if re.match(r'^## ', line) and not re.match(r'^### ', line):
                    in_faq = False
                    if current_question and current_answer_lines:
                        faq_items.append({
                            "question": current_question,
                            "answer": ' '.join(current_answer_lines).strip(),
                        })
                    break

                # Question (H3 or H4)
                q_match = re.match(r'^#{2,4}\s+(.+?\?)', line)
                if q_match:
                    if current_question and current_answer_lines:
                        faq_items.append({
                            "question": current_question,
                            "answer": ' '.join(current_answer_lines).strip(),
                        })
                    current_question = q_match.group(1)
                    current_answer_lines = []
                elif current_question and line.strip() and not line.startswith('#'):
                    clean_line = re.sub(r'[*_`]', '', line).strip()
                    if clean_line:
                        current_answer_lines.append(clean_line)

        if current_question and current_answer_lines:
            faq_items.append({
                "question": current_question,
                "answer": ' '.join(current_answer_lines).strip(),
            })

        return faq_items[:10]  # Limit to 10 FAQ items
