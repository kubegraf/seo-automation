import os
import re
import time
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

_client = None
MODEL = "gemini-1.5-flash"  # Better free-tier support than gemini-2.0-flash


def get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        genai.configure(api_key=api_key)
        _client = genai.GenerativeModel(MODEL)
    return _client


def _parse_retry_delay(error_str: str) -> float:
    """Extract the 'retry in Xs' delay from a 429 error message."""
    match = re.search(r"retry in ([\d.]+)s", str(error_str))
    if match:
        return float(match.group(1)) + 2.0  # add 2s buffer
    return 65.0  # safe default: 65 seconds


def _call_with_retry(prompt: str, temperature: float, max_tokens: int, max_retries: int = 5) -> str:
    """Core retry loop — honours the retry-after hint from 429 responses."""
    client = get_client()
    for attempt in range(max_retries):
        try:
            response = client.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
            return response.text
        except Exception as e:
            err = str(e)
            is_quota = "429" in err or "quota" in err.lower() or "rate" in err.lower()
            if is_quota and attempt < max_retries - 1:
                wait = _parse_retry_delay(err)
                logger.warning(f"Rate limited (attempt {attempt + 1}/{max_retries}). Waiting {wait:.0f}s...")
                time.sleep(wait)
            elif attempt < max_retries - 1:
                wait = 2 ** attempt
                logger.warning(f"Gemini attempt {attempt + 1} failed: {e}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise
    return ""


def generate(prompt: str, max_retries: int = 5) -> str:
    """Generate text with rate-limit-aware retry logic."""
    return _call_with_retry(prompt, temperature=0.7, max_tokens=8192, max_retries=max_retries)


def generate_json(prompt: str, max_retries: int = 5) -> str:
    """Generate a JSON response, stripping any markdown code fences."""
    full_prompt = f"{prompt}\n\nRespond ONLY with valid JSON. No markdown code blocks, no explanation."
    text = _call_with_retry(full_prompt, temperature=0.3, max_tokens=4096, max_retries=max_retries)
    text = text.strip()
    # Strip ```json ... ``` fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])
        if text.endswith("```"):
            text = text[: text.rfind("```")]
    return text.strip()
