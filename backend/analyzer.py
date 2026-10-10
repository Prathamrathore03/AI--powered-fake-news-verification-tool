import json
import os
import re

from dotenv import load_dotenv
from google import genai

load_dotenv()

PRIMARY_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite")

VALID_STATUSES = {
    "supported",
    "contradicted",
    "mixed",
    "inconclusive",
}

MAX_SNIPPET_CHARS = 250

SENSITIVE_KEYWORDS = {
    "death", "dead", "died", "dies", "kill", "killed", "killing",
    "murder", "murdered", "arrest", "arrested", "cancer", "hospital",
    "hospitalized", "stroke", "overdose", "suicide", "shooting",
}


def _heuristic_analysis(claim, supporting, contradicting):
    support_count = len(supporting)
    contradiction_count = len(contradicting)

    claim_lower = str(claim or "").lower()
    is_sensitive = any(kw in claim_lower for kw in SENSITIVE_KEYWORDS)

    if support_count == 0 and contradiction_count == 0:
        return {
            "status": "inconclusive",
            "analysis": (
                "The available evidence does not provide sufficient information "
                "to verify this claim. No authoritative fact-checks or independent "
                "corroborations were found in the examined sources."
            ),
        }

    if contradiction_count > 0 and support_count == 0:
        return {
            "status": "contradicted",
            "analysis": (
                f"The claim is contradicted by {contradiction_count} identified source(s). "
                "Available reporting and fact-check records refute or debunk the assertion, "
                "and no credible supporting evidence was located."
            ),
        }

    if contradiction_count > 0 and support_count > 0:
        return {
            "status": "mixed",
            "analysis": (
                f"Available evidence is mixed ({support_count} supporting vs. "
                f"{contradiction_count} contradicting source(s)). Conflicting reports "
                "prevent a definitive conclusion without further independent investigation."
            ),
        }

    # support_count > 0 and contradiction_count == 0
    if is_sensitive and support_count < 2:
        return {
            "status": "inconclusive",
            "analysis": (
                "This claim involves a sensitive event (such as a death, medical condition, or arrest). "
                "While preliminary mentions were identified, the evidence lacks multiple independent, "
                "authoritative corroborations required for verification. The verdict remains inconclusive."
            ),
        }

    if support_count >= 2:
        return {
            "status": "supported",
            "analysis": (
                f"The claim is corroborated by {support_count} independent source(s). "
                "Reporting aligns with the assertion, and no contradicting evidence "
                "was found among the examined sources."
            ),
        }

    return {
        "status": "inconclusive",
        "analysis": (
            "Only a single source was identified supporting the claim, lacking "
            "independent secondary corroboration. Evidence is currently insufficient to confirm."
        ),
    }


def synthesize_analysis(claim, supporting, contradicting):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        return _heuristic_analysis(claim, supporting, contradicting)

    evidence_lines = []
    for item in supporting[:5]:
        evidence_lines.append(
            f"SUPPORTING: {item.get('title', '')} | "
            f"{item.get('source', '')} | "
            f"{item.get('snippet', '')[:MAX_SNIPPET_CHARS]}"
        )

    for item in contradicting[:5]:
        evidence_lines.append(
            f"CONTRADICTING: {item.get('title', '')} | "
            f"{item.get('source', '')} | "
            f"{item.get('snippet', '')[:MAX_SNIPPET_CHARS]}"
        )

    evidence_text = "\n".join(evidence_lines) if evidence_lines else "No specific evidence items retrieved."

    prompt = f"""
You are the analysis component of VERITO, an evidence-based news verification system.

Analyze the claim using ONLY the evidence supplied below.

CRITICAL INTEGRITY PRINCIPLES:
1. Ground your reasoning strictly on what the provided evidence establishes. Do not assume or extrapolate.
2. Differentiate between verified authoritative reporting and rumors or uncorroborated claims.
3. For sensitive claims about deaths, medical crises, disasters, or arrests:
   - If credible independent news organizations or official statements have not confirmed the claim, choose 'inconclusive' (or 'contradicted' if debunked).
   - NEVER mark a death or disaster claim as 'supported' without solid, corroborating reporting from credible news agencies.
4. If evidence is ambiguous, conflicting, or sparse, the status MUST be 'inconclusive' or 'mixed'.
5. DO NOT assign numerical truth percentages or arbitrary probability scores.
6. Choose EXACTLY one status:
   - supported (well-corroborated by reliable sources without contradiction)
   - contradicted (refuted by reliable sources or fact-checks)
   - mixed (conflicting evidence from credible sources)
   - inconclusive (insufficient, ambiguous, or unverified evidence)

Return ONLY valid JSON in this exact structure:
{{
  "status": "supported|contradicted|mixed|inconclusive",
  "analysis": "3 to 5 sentences explaining what the evidence proves, what it refutes, and what remains unverified."
}}

CLAIM:
{claim}

EVIDENCE:
{evidence_text}
"""

    models_to_try = [PRIMARY_MODEL, FALLBACK_MODEL]
    models_to_try = list(dict.fromkeys(models_to_try))

    client = genai.Client(api_key=api_key)

    for model in models_to_try:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )

            raw = (response.text or "").strip()
            if not raw:
                continue

            raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
            raw = re.sub(r"\s*```$", "", raw, flags=re.IGNORECASE).strip()

            result = json.loads(raw)
            status = str(result.get("status", "")).lower().strip()
            analysis = str(result.get("analysis", "")).strip()

            if status in VALID_STATUSES and analysis:
                return {
                    "status": status,
                    "analysis": analysis,
                }

        except Exception as e:
            print(f"[analyzer] Synthesis error with model {model}: {e}")

    return _heuristic_analysis(claim, supporting, contradicting)