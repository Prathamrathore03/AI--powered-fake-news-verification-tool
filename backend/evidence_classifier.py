import json
import os
import re
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()

PRIMARY_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite")

MAX_EVIDENCE_ITEMS = 15
MAX_SNIPPET_CHARS = 350


def _rating_classification(item):
    """
    Classify an evidence item immediately when it already contains
    an explicit fact-check rating from a known registry.
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
        "untrue",
        "false context",
        "missing context",
        "altered",
        "out of context",
        "pants on fire",
    ]

    if any(term in rating for term in contradicting_terms):
        return "contradicting"

    if any(term in rating for term in supporting_terms):
        return "supporting"

    return None


def _gemini_classify(client, prompt):
    """
    Classify evidence items using fast Gemini models.
    429 quota errors break immediately without looping retries.
    """
    models = [
        PRIMARY_MODEL,
        FALLBACK_MODEL,
    ]
    # Deduplicate while preserving order
    models = list(dict.fromkeys(models))

    last_error = None

    for model in models:
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

            quota_error = (
                "429" in error_text
                or "resource_exhausted" in error_text
                or "quota" in error_text
            )

            if quota_error:
                print(f"[classifier] Gemini model {model} quota exhausted. Trying next model.")
                continue

            temporary_error = (
                "503" in error_text
                or "unavailable" in error_text
                or "high demand" in error_text
                or "overloaded" in error_text
            )

            if temporary_error:
                time.sleep(1)
                try:
                    retry_resp = client.models.generate_content(
                        model=model,
                        contents=prompt,
                    )
                    raw = (retry_resp.text or "").strip()
                    if raw:
                        return raw
                except Exception:
                    pass

            print(f"[classifier] Gemini model {model} failed. Trying next model.")

    if last_error:
        raise last_error

    raise RuntimeError("Gemini classification failed on all candidate models.")


def _extract_json_array(raw):
    """
    Safely extract a JSON array from Gemini's response text.
    """
    if not raw:
        return None

    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text, flags=re.IGNORECASE).strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            for key in ("classifications", "results", "evidence", "items"):
                value = parsed.get(key)
                if isinstance(value, list):
                    return value
    except json.JSONDecodeError:
        pass

    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end + 1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

    return None


def _normalize_classification(value):
    """
    Normalize LLM classification string into VERITO labels.
    """
    classification = str(value or "").upper().strip()
    classification = classification.replace("-", "_").replace(" ", "_")

    if classification in (
        "SUPPORTING", "SUPPORT", "SUPPORTED", "TRUE", "CONFIRMS", "CONFIRMING"
    ):
        return "SUPPORTING"

    if classification in (
        "CONTRADICTING", "CONTRADICT", "CONTRADICTS", "CONTRADICTORY",
        "FALSE", "REFUTES", "REFUTING", "DEBUNKS", "DEBUNKED"
    ):
        return "CONTRADICTING"

    if classification in (
        "IRRELEVANT", "NEUTRAL", "UNCLEAR", "UNRELATED", "INSUFFICIENT", "UNVERIFIED"
    ):
        return "IRRELEVANT"

    return None


def _meaningful_words(text):
    """Extract content words for fallback analysis."""
    words = re.findall(r"[a-zA-Z]{3,}", str(text or "").lower())
    stop_words = {
        "about", "after", "against", "being", "between", "could", "from",
        "have", "into", "more", "other", "said", "that", "their", "there",
        "these", "they", "this", "those", "through", "under", "were",
        "which", "with", "would", "news", "article", "report", "reports",
        "reported", "today", "yesterday", "recent",
    }
    return {w for w in words if w not in stop_words}


def _local_fallback_classify(claim, remaining):
    """
    Trustworthy conservative non-AI fallback.

    CRITICAL SAFETY RULES:
    1. A source is NEVER classified as supporting merely because it repeats
       the claim words or has lexical overlap.
    2. Clickbait, questions, social media rumors, and vague mentions
       are classified as IRRELEVANT.
    3. Explicit debunking / denial / hoax mentions are classified as CONTRADICTING.
    4. Explicit affirmative confirmation by authoritative entities with no
       question or rumor markers may be classified as SUPPORTING.
    5. When in doubt, items remain unclassified / IRRELEVANT.
    """
    supporting = []
    contradicting = []

    claim_words = _meaningful_words(claim)
    if not claim_words:
        return supporting, contradicting

    contradiction_phrases = [
        "false", "fake", "hoax", "debunked", "fact check", "fact-check",
        "incorrect", "misleading", "not true", "untrue", "denied",
        "denies", "refuted", "refutes", "contradicts", "fabricated",
        "misinformation", "disinformation", "death hoax", "alive and well",
        "still alive", "not dead", "falsely claimed", "no truth",
    ]

    # Explicit phrases that indicate rumors, questions, or clickbait
    rumor_or_question_phrases = [
        "did ", "is it true", "rumor", "rumour", "rumors", "rumours",
        "viral claim", "viral post", "social media claims", "tiktok claims",
        "fans react to rumor", "fans fear", "death rumor", "unconfirmed",
        "alleged", "allegedly", "claims circulate",
    ]

    # Explicit affirmative confirmation markers required for SUPPORTING in fallback
    affirmative_confirmation_phrases = [
        "officially confirmed", "authorities confirmed", "police confirmed",
        "family confirmed", "hospital confirmed", "statement confirms",
        "reuters confirms", "ap confirms", "confirmed by", "passed away at age",
        "died Tuesday", "died Wednesday", "died Thursday", "died Friday",
        "died Saturday", "died Sunday", "died Monday", "obituary for",
    ]

    for item in remaining:
        title = str(item.get("title", "")).strip()
        snippet = str(item.get("snippet", "")).strip()
        combined = f"{title} {snippet}".lower()

        evidence_words = _meaningful_words(combined)
        if not evidence_words:
            continue

        overlap = claim_words.intersection(evidence_words)
        overlap_ratio = len(overlap) / len(claim_words)

        # 1. Contradiction takes first priority
        if any(phrase in combined for phrase in contradiction_phrases):
            contradicting.append(item)
            continue

        # 2. Questions or rumor markers -> IRRELEVANT (never supporting!)
        if "?" in title or any(phrase in combined for phrase in rumor_or_question_phrases):
            continue

        # 3. Require strict affirmative confirmation to support without LLM
        if overlap_ratio >= 0.40 and any(phrase in combined for phrase in affirmative_confirmation_phrases):
            supporting.append(item)
        else:
            # All other matching items are treated as neutral/unverified, NOT supporting!
            continue

    return supporting, contradicting


def classify_evidence(claim, evidence):
    """
    Classify evidence as supporting or contradicting.

    Priority:
      1. Explicit fact-check registry ratings.
      2. High-precision Gemini classification.
      3. Conservative local fallback when Gemini is unavailable.
    """
    supporting = []
    contradicting = []
    remaining = []

    # 1. Explicit fact-check ratings
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

    # 2. Gemini classification
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        print("[classifier] WARNING: GEMINI_API_KEY not set. Using conservative local fallback.")
        fb_sup, fb_con = _local_fallback_classify(claim, remaining)
        supporting.extend(fb_sup)
        contradicting.extend(fb_con)
        return supporting[:5], contradicting[:5]

    # Prepare evidence lines for Gemini
    evidence_lines = []
    for index, item in enumerate(remaining, start=1):
        title = str(item.get("title", "")).strip()
        source = str(item.get("source", "")).strip()
        url = str(item.get("url", "")).strip()
        snippet = str(item.get("snippet", "")).strip()

        evidence_lines.append(
            f"ITEM {index}\n"
            f"Title: {title}\n"
            f"Source: {source}\n"
            f"URL: {url}\n"
            f"Snippet: {snippet[:MAX_SNIPPET_CHARS]}\n"
        )

    evidence_text = "\n".join(evidence_lines)

    prompt = f"""
You are the evidence classification component of VERITO, an evidence-based
news verification system.

Evaluate each evidence item in relation to the CLAIM.

DEFINITIONS:
- SUPPORTING: The evidence independently confirms or corroborates the factual claim with authoritative reporting or verified facts.
- CONTRADICTING: The evidence explicitly refutes, disproves, denies, or contradicts the claim (e.g. confirms a report is a hoax, false, or denied by officials/representatives).
- IRRELEVANT: The evidence does NOT meaningfully prove or disprove the claim.

STRICT VERIFICATION RULES (PREVENT FALSE VERDICTS):
1. A source is NOT SUPPORTING merely because it repeats the claim, quotes a rumor, or shares keywords with the claim.
2. Headlines asking questions (e.g., 'Did X die?', 'Is X in hospital?') are IRRELEVANT, NEVER SUPPORTING.
3. Social media rumors, viral claims, and clickbait speculation are IRRELEVANT, NEVER SUPPORTING.
4. For sensitive claims about deaths, medical emergencies, disasters, or arrests:
   - ONLY classify as SUPPORTING if the item represents authoritative reporting (major news agency, official obituary, police/government statement) explicitly confirming the event occurred.
   - If the item reports that the rumor is false, debunked, or that the subject is alive, classify as CONTRADICTING.
   - If the item merely notes that a rumor exists without independent confirmation, classify as IRRELEVANT.
5. Base your decision EXCLUSIVELY on the text in the provided Title and Snippet.
6. When uncertain, classify as IRRELEVANT.

Return ONLY a valid JSON array in this exact format:
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
        raw = _gemini_classify(client, prompt)
        classifications = _extract_json_array(raw)

        if not classifications:
            raise ValueError("Could not parse JSON classification array from Gemini response.")

        classified_indices = set()
        for res in classifications:
            if not isinstance(res, dict):
                continue
            try:
                item_num = int(res.get("item"))
            except (TypeError, ValueError):
                continue

            if item_num < 1 or item_num > len(remaining):
                continue

            cls = _normalize_classification(res.get("classification"))
            if not cls or item_num in classified_indices:
                continue

            classified_indices.add(item_num)
            item = remaining[item_num - 1]

            if cls == "SUPPORTING":
                supporting.append(item)
            elif cls == "CONTRADICTING":
                contradicting.append(item)

        return supporting[:5], contradicting[:5]

    except Exception as error:
        print(f"[classifier] Gemini classification fallback triggered: {error}")
        fb_sup, fb_con = _local_fallback_classify(claim, remaining)
        supporting.extend(fb_sup)
        contradicting.extend(fb_con)
        return supporting[:5], contradicting[:5]