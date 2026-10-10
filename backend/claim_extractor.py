import os
import re
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()

PRIMARY_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite")

MAX_ARTICLE_CHARS = 6000
MAX_ATTEMPTS = 2


def _generate_with_retry(client, prompt):
    models_to_try = [
        PRIMARY_MODEL,
        FALLBACK_MODEL,
    ]

    # Deduplicate while preserving order
    models_to_try = list(dict.fromkeys(models_to_try))
    last_error = None

    for model in models_to_try:
        for attempt in range(MAX_ATTEMPTS):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                )

                text = (response.text or "").strip()
                if text:
                    # Clean up quotes or formatting
                    text = re.sub(r'^["\']|["\']$', '', text).strip()
                    return text

                raise ValueError(
                    f"Gemini returned an empty response from {model}."
                )

            except Exception as error:
                last_error = error
                error_text = str(error).lower()

                quota_exhausted = (
                    "429" in error_text
                    or "resource_exhausted" in error_text
                    or "quota" in error_text
                )

                is_temporary = (
                    "503" in error_text
                    or "unavailable" in error_text
                    or "high demand" in error_text
                    or "overloaded" in error_text
                )

                if quota_exhausted:
                    print(f"[claim_extractor] Model {model} quota exhausted. Trying next model.")
                    break  # Don't retry same model if quota is exhausted

                if not is_temporary:
                    break  # Non-retryable error, try next model

                if attempt < MAX_ATTEMPTS - 1:
                    time.sleep(1)

        print(f"[claim_extractor] Model {model} unavailable or exhausted. Trying next model.")

    if last_error:
        raise last_error

    raise RuntimeError("Failed to extract claim from available models.")


def extract_claim(article):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set. Add it to backend/.env."
        )

    client = genai.Client(api_key=api_key)

    title = article.get("title", "")
    text = article.get("text", "")

    prompt = f"""
You are the claim extraction component of VERITO, an evidence-based
news verification system.

Extract ONE specific, factual, verifiable and falsifiable claim from
the article.

Do not give an opinion.
Do not summarize the entire article.
Do not include multiple claims.

Return ONLY the single claim sentence, with no quotation marks and no explanation.

Article title:
{title}

Article text:
{text[:MAX_ARTICLE_CHARS]}
"""

    claim = _generate_with_retry(client, prompt)

    if not claim:
        raise ValueError("Gemini returned an empty claim.")

    return claim[:250]