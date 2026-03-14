import os
import re
import time
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

_client = None

# Model fallback order — tried in sequence until one works
MODELS = [
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash-001",
    "gemini-pro",
]


def _make_client(model: str):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model)


def _parse_retry_delay(error_str: str) -> float:
    """Extract the 'retry in Xs' hint from a 429 error. Default 60s."""
    match = re.search(r"retry in ([\d.]+)s", str(error_str))
    if match:
        return min(float(match.group(1)) + 3.0, 120.0)
    return 60.0


def _is_rate_limit(err: str) -> bool:
    return "429" in err or "quota" in err.lower() or (
        "rate" in err.lower() and "limit" in err.lower()
    )


def _is_model_not_found(err: str) -> bool:
    return "404" in err or "not found" in err.lower() or "not supported" in err.lower()


def _call_with_retry(prompt: str, temperature: float, max_tokens: int, max_retries: int = 4) -> str:
    """
    Try each model in MODELS list. Within each model, retry on rate limits.
    Never retry on 404/model-not-found — move to next model immediately.
    """
    last_error = None

    for model_name in MODELS:
        client = _make_client(model_name)
        logger.info(f"Trying model: {model_name}")

        for attempt in range(max_retries):
            try:
                response = client.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                    ),
                )
                logger.info(f"Success with model: {model_name}")
                return response.text

            except Exception as e:
                err = str(e)
                last_error = e

                if _is_model_not_found(err):
                    logger.warning(f"Model {model_name} not available: {err[:80]}. Trying next model...")
                    break  # stop retrying this model, move to next

                elif _is_rate_limit(err):
                    if attempt < max_retries - 1:
                        wait = _parse_retry_delay(err)
                        logger.warning(f"Rate limited on {model_name} (attempt {attempt + 1}/{max_retries}). Waiting {wait:.0f}s...")
                        time.sleep(wait)
                    else:
                        logger.warning(f"Rate limit retries exhausted for {model_name}. Trying next model...")
                        break

                else:
                    if attempt < max_retries - 1:
                        wait = 2 ** attempt
                        logger.warning(f"Error on {model_name} attempt {attempt + 1}: {err[:80]}. Retrying in {wait}s...")
                        time.sleep(wait)
                    else:
                        logger.warning(f"Retries exhausted for {model_name}. Trying next model...")
                        break

    raise RuntimeError(f"All models failed. Last error: {last_error}")


def generate(prompt: str) -> str:
    """Generate text using the best available Gemini model."""
    return _call_with_retry(prompt, temperature=0.7, max_tokens=8192)


def generate_json(prompt: str) -> str:
    """Generate a JSON response, stripping any markdown code fences."""
    full_prompt = f"{prompt}\n\nRespond ONLY with valid JSON. No markdown code blocks, no explanation."
    text = _call_with_retry(full_prompt, temperature=0.3, max_tokens=4096)
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])
        if text.strip().endswith("```"):
            text = text[:text.rfind("```")]
    return text.strip()
