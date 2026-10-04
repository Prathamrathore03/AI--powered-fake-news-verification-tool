import json
import os
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()

PRIMARY_MODEL = "gemini-3.5-flash-lite"
FALLBACK_MODEL = "gemini-3.8-flash"

MAX_EVIDENCE_ITEMS = 15
MAX_SNIPPET_CHARS = 350


def _rating_classification(item):
    rating = str(item.get("_textual_rating", "")).lower().strip()

    supporting_terms = [
        "true",
        "mostly true",
        "correct",
        "accurate",
        "verified",
        "confirmed",
        "supported",
        "legitimate",
    ]

    contradicting_terms = [
        "false",
        "mostly false",
        "misleading",
        "incorrect",
        "inaccurate",
        "fabricated",
        "hoax",
        "debunked",
        "fake",
        "misinformation",
        "disinformation",
        "not true",
        "false context",
        "missing context",
        "altered",
    ]

    if any(term in rating for term in contradicting_terms):
        return "contradicting"

    if any(term in rating for term in supporting_terms):
        return "supporting"

    return None


def _gemini_classify(client, prompt):
    """
    Try the primary Gemini model first.
    If it is temporarily unavailable, retry and then use the fallback model.
    """

    models = [
        PRIMARY_MODEL,
        FALLBACK_MODEL,
    ]

    last_error = None

    for model in models:

        for attempt in range(2):

            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                )

                raw = (response.text or "").strip()

                if raw:
                    return raw

                raise ValueError(
                    f"Gemini returned an empty response from {model}."
                )

            except Exception as error:

                last_error = error

                error_text = str(error).lower()

                temporary_error = (
                    "503" in error_text
                    or "unavailable" in error_text
                    or "high demand" in error_text
                    or "overloaded" in error_text
                    or "429" in error_text
                    or "resource_exhausted" in error_text
                )

                if not temporary_error:
                    raise

                if attempt == 0:
                    time.sleep(1)

        print(
            f"[classifier] Gemini model {model} unavailable. "
            f"Trying next model."
        )

    raise last_error


def classify_evidence(claim, evidence):
    """
    Classify evidence as supporting or contradicting the claim.

    Existing fact-check ratings are handled first.
    Remaining evidence is classified by Gemini.
    """

    supporting = []
    contradicting = []
    remaining = []

    for item in evidence[:MAX_EVIDENCE_ITEMS]:

        rating_result = _rating_classification(item)

        if rating_result == "supporting":
            supporting.append(item)

        elif rating_result == "contradicting":
            contradicting.append(item)

        else:
            remaining.append(item)

    if not remaining:
        return supporting[:5], contradicting[:5]

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return supporting[:5], contradicting[:5]

    evidence_lines = []

    for index, item in enumerate(remaining, start=1):

        evidence_lines.append(
            f"""
ITEM {index}
Title: {item.get('title', '')}
Source: {item.get('source', '')}
URL: {item.get('url', '')}
Snippet: {item.get('snippet', '')[:MAX_SNIPPET_CHARS]}
"""
        )

    evidence_text = "\n".join(evidence_lines)

    prompt = f"""
You are the evidence classification component of VERITO.

Determine whether each evidence item supports the claim,
contradicts the claim, or is irrelevant.

Use ONLY the supplied claim and evidence.
Do not use outside knowledge.
Do not invent information.

Return ONLY a JSON array.

Each item must have exactly this format:

[
  {{"item": 1, "classification": "SUPPORTING"}},
  {{"item": 2, "classification": "CONTRADICTING"}},
  {{"item": 3, "classification": "IRRELEVANT"}}
]

CLAIM:
{claim}

EVIDENCE:
{evidence_text}
"""

    try:

        client = genai.Client(api_key=api_key)

        raw = _gemini_classify(
            client,
            prompt,
        )

        if raw.startswith("```"):
            raw = raw.strip("`")

            if raw.startswith("json"):
                raw = raw[4:].strip()

        classifications = json.loads(raw)

        if not isinstance(classifications, list):
            return supporting[:5], contradicting[:5]

        for result in classifications:

            try:

                item_number = int(result.get("item"))

                classification = str(
                    result.get("classification", "")
                ).upper().strip()

                if (
                    item_number < 1
                    or item_number > len(remaining)
                ):
                    continue

                item = remaining[item_number - 1]

                if classification == "SUPPORTING":
                    supporting.append(item)

                elif classification == "CONTRADICTING":
                    contradicting.append(item)

            except (
                TypeError,
                ValueError,
                AttributeError,
            ):
                continue

    except Exception as error:

        print(
            f"[classifier] WARNING: Gemini classification failed: {error}"
        )

    return supporting[:5], contradicting[:5]