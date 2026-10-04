import json
import os
import re
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()

PRIMARY_MODEL = "gemini-3.5-flash-lite"
FALLBACK_MODEL = "gemini-3.8-flash"

MAX_EVIDENCE_ITEMS = 15
MAX_SNIPPET_CHARS = 350


def _rating_classification(item):
    """
    Classify an evidence item immediately when it already contains
    an explicit fact-check rating.
    """

    rating = str(
        item.get("_textual_rating", "")
    ).lower().strip()

    supporting_terms = [
        "mostly true",
        "true",
        "correct",
        "accurate",
        "verified",
        "confirmed",
        "supported",
        "legitimate",
    ]

    contradicting_terms = [
        "mostly false",
        "false",
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

    # Check contradiction first so terms such as
    # "mostly false" are never incorrectly treated as supporting.
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
                    print(
                        f"[classifier] Gemini response received "
                        f"from {model} ({len(raw)} chars)."
                    )
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

    if last_error:
        raise last_error

    raise RuntimeError(
        "Gemini classification failed without a specific error."
    )


def _extract_json_array(raw):
    """
    Extract a JSON array from Gemini's response.

    Handles:
      - plain JSON
      - ```json ... ```
      - ``` ... ```
      - extra text surrounding the JSON
    """

    if not raw:
        return None

    text = raw.strip()

    # Remove markdown code fences.
    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = text.strip()

    # First attempt: response is already valid JSON.
    try:
        parsed = json.loads(text)

        if isinstance(parsed, list):
            return parsed

        # Sometimes the model wraps the array in an object.
        if isinstance(parsed, dict):

            for key in (
                "classifications",
                "results",
                "evidence",
                "items",
            ):
                value = parsed.get(key)

                if isinstance(value, list):
                    return value

    except json.JSONDecodeError:
        pass

    # Second attempt: locate the first JSON array inside the response.
    start = text.find("[")

    if start == -1:
        return None

    end = text.rfind("]")

    if end == -1 or end <= start:
        return None

    candidate = text[start:end + 1]

    try:
        parsed = json.loads(candidate)

        if isinstance(parsed, list):
            return parsed

    except json.JSONDecodeError:
        return None

    return None


def _normalize_classification(value):
    """
    Convert common Gemini classification variants into
    VERITO's three allowed labels.
    """

    classification = str(
        value or ""
    ).upper().strip()

    classification = classification.replace("-", "_")
    classification = classification.replace(" ", "_")

    if classification in (
        "SUPPORTING",
        "SUPPORT",
        "SUPPORTED",
        "TRUE",
        "CONFIRMS",
        "CONFIRMING",
    ):
        return "SUPPORTING"

    if classification in (
        "CONTRADICTING",
        "CONTRADICT",
        "CONTRADICTS",
        "CONTRADICTORY",
        "FALSE",
        "REFUTES",
        "REFUTING",
    ):
        return "CONTRADICTING"

    if classification in (
        "IRRELEVANT",
        "NEUTRAL",
        "UNCLEAR",
        "UNRELATED",
        "INSUFFICIENT",
    ):
        return "IRRELEVANT"

    return None


def classify_evidence(claim, evidence):
    """
    Classify evidence as supporting or contradicting the claim.

    Existing fact-check ratings are handled first.
    Remaining evidence is classified by Gemini.
    """

    supporting = []
    contradicting = []
    remaining = []

    # ---------------------------------------------------------------
    # First: use explicit fact-check ratings where available
    # ---------------------------------------------------------------

    for item in evidence[:MAX_EVIDENCE_ITEMS]:

        rating_result = _rating_classification(item)

        if rating_result == "supporting":

            supporting.append(item)

        elif rating_result == "contradicting":

            contradicting.append(item)

        else:

            remaining.append(item)

    print(
        f"[classifier] Explicit ratings: "
        f"{len(supporting)} supporting, "
        f"{len(contradicting)} contradicting."
    )

    # ---------------------------------------------------------------
    # If everything was classified through explicit ratings,
    # return immediately.
    # ---------------------------------------------------------------

    if not remaining:
        return supporting[:5], contradicting[:5]

    # ---------------------------------------------------------------
    # Gemini configuration
    # ---------------------------------------------------------------

    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:

        print(
            "[classifier] WARNING: GEMINI_API_KEY is not configured."
        )

        return supporting[:5], contradicting[:5]

    # ---------------------------------------------------------------
    # Prepare evidence for Gemini
    # ---------------------------------------------------------------

    evidence_lines = []

    for index, item in enumerate(
        remaining,
        start=1
    ):

        title = str(
            item.get("title", "")
        ).strip()

        source = str(
            item.get("source", "")
        ).strip()

        url = str(
            item.get("url", "")
        ).strip()

        snippet = str(
            item.get("snippet", "")
        ).strip()

        evidence_lines.append(
            f"""
ITEM {index}
Title: {title}
Source: {source}
URL: {url}
Snippet: {snippet[:MAX_SNIPPET_CHARS]}
"""
        )

    evidence_text = "\n".join(evidence_lines)

    # ---------------------------------------------------------------
    # Gemini prompt
    # ---------------------------------------------------------------

    prompt = f"""
You are the evidence classification component of VERITO,
an evidence-based news claim verification system.

Your task is to classify EVERY evidence item below in relation
to the CLAIM.

Definitions:

SUPPORTING:
The evidence provides information that directly supports,
confirms, or independently corroborates the claim.

CONTRADICTING:
The evidence provides information that directly disputes,
refutes, disproves, or contradicts the claim.

IRRELEVANT:
The evidence does not provide meaningful support or contradiction.

IMPORTANT RULES:

1. Evaluate the evidence against the exact claim.
2. Use ONLY the supplied evidence.
3. Do NOT use outside knowledge.
4. Do NOT assume that a source agrees with the claim merely
   because its title contains similar words.
5. Do NOT classify an item as supporting or contradicting
   unless the supplied title or snippet provides meaningful
   evidence for that classification.
6. Every ITEM must receive exactly one classification.
7. Preserve the original item number.
8. Return ONLY valid JSON.
9. Do not use Markdown.
10. Do not include explanations outside the JSON.

Return exactly this structure:

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

    # ---------------------------------------------------------------
    # Call Gemini
    # ---------------------------------------------------------------

    try:

        client = genai.Client(
            api_key=api_key
        )

        raw = _gemini_classify(
            client,
            prompt,
        )

        print(
            "[classifier] Parsing Gemini classification response..."
        )

        classifications = _extract_json_array(
            raw
        )

        if classifications is None:

            print(
                "[classifier] WARNING: Could not parse "
                "Gemini response as a JSON classification array."
            )

            print(
                f"[classifier] Raw response: {raw[:1000]}"
            )

            return (
                supporting[:5],
                contradicting[:5],
            )

        print(
            f"[classifier] Gemini returned "
            f"{len(classifications)} classification(s)."
        )

        # -----------------------------------------------------------
        # Process Gemini classifications
        # -----------------------------------------------------------

        classified_item_numbers = set()

        for result in classifications:

            if not isinstance(result, dict):
                continue

            try:

                item_number = int(
                    result.get("item")
                )

            except (
                TypeError,
                ValueError,
            ):

                continue

            if (
                item_number < 1
                or item_number > len(remaining)
            ):
                continue

            classification = _normalize_classification(
                result.get("classification")
            )

            if classification is None:
                continue

            if item_number in classified_item_numbers:
                continue

            classified_item_numbers.add(
                item_number
            )

            item = remaining[
                item_number - 1
            ]

            if classification == "SUPPORTING":

                supporting.append(item)

            elif classification == "CONTRADICTING":

                contradicting.append(item)

        print(
            f"[classifier] Final classification: "
            f"{len(supporting)} supporting | "
            f"{len(contradicting)} contradicting | "
            f"{len(remaining) - len(classified_item_numbers)} irrelevant/unclassified."
        )

    except Exception as error:

        print(
            f"[classifier] WARNING: Gemini classification failed: {error}"
        )

    return (
        supporting[:5],
        contradicting[:5],
    )