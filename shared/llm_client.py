"""
LLM client wrapper for SEO Automation Platform.
Supports Anthropic Claude (primary) with retry logic and structured output.
"""
import os
import json
import logging
import asyncio
from typing import Optional, Any
from functools import wraps

import anthropic
import httpx

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
DEFAULT_MAX_TOKENS = 8192
DEFAULT_TEMPERATURE = 0.7
MAX_RETRIES = 3
RETRY_DELAY = 2.0


def with_retry(max_retries: int = MAX_RETRIES, delay: float = RETRY_DELAY):
    """Decorator for retry logic on LLM API calls."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (anthropic.RateLimitError, anthropic.APITimeoutError) as e:
                    last_exception = e
                    wait_time = delay * (2 ** attempt)
                    logger.warning(
                        f"LLM API error (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                except anthropic.APIError as e:
                    logger.error(f"LLM API error: {e}")
                    raise
            raise last_exception
        return wrapper
    return decorator


class LLMClient:
    """
    Anthropic Claude client wrapper with retry logic and structured output support.
    """

    def __init__(
        self,
        api_key: str = ANTHROPIC_API_KEY,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ):
        self.model = model
        self.max_tokens = max_tokens
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        logger.info(f"LLM client initialized with model: {model}")

    @with_retry()
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a text completion from the LLM.

        Args:
            prompt: User prompt text
            system: Optional system prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Override default max tokens

        Returns:
            Generated text string
        """
        messages = [{"role": "user", "content": prompt}]
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens or self.max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        logger.debug(f"Calling LLM with prompt length: {len(prompt)} chars")
        response = await self._client.messages.create(**kwargs)
        result = response.content[0].text
        logger.debug(f"LLM response length: {len(result)} chars")
        return result

    @with_retry()
    async def generate_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3,
    ) -> dict:
        """
        Generate a JSON response from the LLM.

        Args:
            prompt: User prompt requesting JSON output
            system: Optional system prompt
            temperature: Lower temperature for more consistent JSON

        Returns:
            Parsed JSON dictionary
        """
        json_system = (system or "") + "\nAlways respond with valid JSON only. No markdown, no explanations outside JSON."
        full_prompt = prompt + "\n\nRespond with valid JSON only."

        response = await self.generate(
            prompt=full_prompt,
            system=json_system,
            temperature=temperature,
        )

        # Clean response - remove potential markdown code blocks
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}\nResponse: {cleaned[:500]}")
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"LLM did not return valid JSON: {cleaned[:200]}")

    async def generate_article(
        self,
        prompt: str,
        topic: str,
        keywords: list[str],
        word_count: int = 2000,
    ) -> str:
        """
        Generate a full SEO article.

        Args:
            prompt: Full article generation prompt
            topic: Article topic/title
            keywords: Target keywords to include
            word_count: Target word count

        Returns:
            Full article markdown content
        """
        system = f"""You are an expert technical writer specializing in Kubernetes, SRE, DevOps, and AI operations.
Your articles are thorough, technically accurate, SEO-optimized, and engaging.
Target audience: DevOps engineers, SREs, and platform engineering teams.
Writing style: Professional but approachable, with practical examples and code snippets.
Always include: practical examples, code snippets where relevant, actionable advice.
Target word count: approximately {word_count} words."""

        keywords_str = ", ".join(keywords) if keywords else "Kubernetes, SRE, DevOps"
        full_prompt = f"""Write a comprehensive, SEO-optimized article about: {topic}

Target keywords (use naturally throughout the article): {keywords_str}

{prompt}

Requirements:
- Include an SEO-optimized H1 title
- Write a compelling meta description (150-160 characters)
- Use H2, H3, H4 headings for clear structure
- Include practical code examples (YAML, bash, Python as appropriate)
- Add a strong introduction and conclusion
- Include internal link placeholders: [INTERNAL_LINK: topic]
- Target approximately {word_count} words
- Use bullet points and numbered lists where appropriate
"""
        return await self.generate(full_prompt, system=system, temperature=0.7)

    async def generate_keywords(
        self,
        topic: str,
        seed_keywords: Optional[list[str]] = None,
        count: int = 20,
    ) -> list[dict]:
        """
        Generate keyword ideas for a given topic.

        Args:
            topic: Main topic to research
            seed_keywords: Optional seed keywords to expand from
            count: Number of keywords to generate

        Returns:
            List of keyword dicts with term, search_volume estimate, and difficulty
        """
        seeds_str = ""
        if seed_keywords:
            seeds_str = f"\nSeed keywords to expand: {', '.join(seed_keywords)}"

        prompt = f"""Generate {count} SEO keywords for the topic: "{topic}"
{seeds_str}

Focus on keywords relevant to:
- Kubernetes operations and monitoring
- SRE (Site Reliability Engineering)
- DevOps automation and AI
- Incident management and response
- Cloud-native technologies

For each keyword, estimate:
- search_volume: monthly search volume (integer, realistic estimate)
- difficulty: keyword difficulty score 0-100 (lower = easier to rank)
- intent: search intent (informational/navigational/commercial/transactional)
- trend: current trend (rising/stable/declining)

Return as JSON array:
{{
  "keywords": [
    {{
      "term": "keyword phrase",
      "search_volume": 1000,
      "difficulty": 45,
      "intent": "informational",
      "trend": "rising"
    }}
  ]
}}"""

        result = await self.generate_json(prompt)
        return result.get("keywords", [])

    async def analyze_competitor(
        self,
        competitor_name: str,
        competitor_domain: str,
        our_keywords: list[str],
        their_known_keywords: list[str],
    ) -> dict:
        """
        Analyze a competitor and identify keyword gaps.

        Args:
            competitor_name: Name of the competitor
            competitor_domain: Competitor's domain
            our_keywords: Keywords we currently target
            their_known_keywords: Known keywords the competitor targets

        Returns:
            Analysis dict with gap_keywords, opportunities, article_ideas
        """
        our_kw_str = ", ".join(our_keywords[:20])
        their_kw_str = ", ".join(their_known_keywords[:20])

        prompt = f"""Analyze competitor {competitor_name} ({competitor_domain}) for keyword gap analysis.

Our current target keywords: {our_kw_str}
Their known keywords: {their_kw_str}

As an SEO expert, analyze:
1. Keyword gaps (keywords they rank for that we don't target)
2. Content opportunities we're missing
3. Article ideas for head-to-head comparison content
4. Their likely content strategy weaknesses

Context: We are Kubegraf, an AI-powered Kubernetes monitoring and incident management platform
with features like AI root cause analysis, automated remediation (SafeFix), and intelligent alerting.

Return as JSON:
{{
  "gap_keywords": ["keyword1", "keyword2", ...],
  "opportunities": ["opportunity description 1", ...],
  "article_ideas": ["article title 1", ...],
  "their_strengths": ["strength 1", ...],
  "their_weaknesses": ["weakness 1", ...],
  "recommended_strategy": "strategic recommendation"
}}"""

        return await self.generate_json(prompt)

    async def generate_meta_description(self, title: str, content_preview: str) -> str:
        """Generate SEO meta description for an article."""
        prompt = f"""Write an SEO-optimized meta description for this article.

Article title: {title}
Content preview: {content_preview[:300]}

Requirements:
- Exactly 150-160 characters
- Include the primary keyword naturally
- Compelling, click-worthy
- Describes what the reader will learn
- No quotes in the output

Return ONLY the meta description text, nothing else."""

        result = await self.generate(prompt, temperature=0.5)
        return result.strip()[:160]

    async def improve_content(self, content: str, instructions: str) -> str:
        """Improve existing content based on instructions."""
        prompt = f"""Improve this article content based on the following instructions:

Instructions: {instructions}

Original content:
{content}

Return the improved content in the same format (markdown)."""

        return await self.generate(prompt, temperature=0.5)

    async def health_check(self) -> bool:
        """Verify LLM API connectivity."""
        try:
            result = await self.generate("Say 'ok' in one word.", max_tokens=10)
            return bool(result)
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return False


# Global instance
llm_client = LLMClient()
