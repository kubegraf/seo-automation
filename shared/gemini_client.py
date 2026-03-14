import os
import time
import logging
from typing import Optional
import google.generativeai as genai

logger = logging.getLogger(__name__)

_client = None


def get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        genai.configure(api_key=api_key)
        _client = genai.GenerativeModel("gemini-2.0-flash")
    return _client


def generate(prompt: str, max_retries: int = 3) -> str:
    """Generate text with retry logic."""
    client = get_client()
    for attempt in range(max_retries):
        try:
            response = client.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=8192,
                )
            )
            return response.text
        except Exception as e:
            logger.warning(f"Gemini attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise
    return ""


def generate_json(prompt: str) -> str:
    """Generate JSON response."""
    client = get_client()
    full_prompt = f"{prompt}\n\nRespond ONLY with valid JSON, no markdown code blocks, no explanation."
    for attempt in range(3):
        try:
            response = client.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=4096,
                )
            )
            text = response.text.strip()
            # Strip markdown code blocks if present
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1])
            return text
        except Exception as e:
            logger.warning(f"Gemini JSON attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                raise
    return "{}"
