import json
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

MODEL_NAME = "gemini-3.8-flash"

VALID_STATUSES = {
    "supported",
    "contradicted",
    "mixed",
    "inconclusive",
}

MAX_SNIPPET_CHARS = 250


def _heuristic_analysis(claim, supporting, contradicting):
    support_count = len(supporting)
    contradiction_count = len(contradicting)

    if support_count == 0 and contradiction_count == 0:
        return {
            "status": "inconclusive",
            "analysis": (
                "The available evidence does not provide enough information "
                "to determine whether the claim is supported or contradicted."
            ),
        }

    if support_count > 0 and contradiction_count == 0:
        return {
            "status": "supported",
            "analysis": (
                "The available evidence supports the claim. "
                "No directly contradicting evidence was identified in the "
                "sources examined."
            ),
        }

    if contradiction_count > 0 and support_count == 0:
        return {
            "status": "contradicted",
            "analysis": (
                "The available evidence contradicts the claim. "
                "No directly supporting evidence was identified in the "
                "sources examined."
            ),
        }

    return {
        "status": "mixed",
        "analysis": (
            "The available evidence is mixed. Some sources support the "
            "claim while other sources provide contradictory evidence."
        ),
    }


def synthesize_analysis(claim, supporting, contradicting):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return _heuristic_analysis(
            claim,
            supporting,
            contradicting,
        )

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

    evidence_text = "\n".join(evidence_lines)

    prompt = f"""
You are the analysis component of VERITO, an evidence-based
news verification system.

Analyze the claim using ONLY the evidence supplied below.

Do not invent facts.
Do not use outside knowledge.
Do not assign a numerical confidence percentage.

Choose exactly one status:
supported
contradicted
mixed
inconclusive

Return ONLY valid JSON in this format:

{{
  "status": "supported",
  "analysis": "Brief evidence-based explanation."
}}

The analysis should be 3 to 5 sentences and should clearly explain
why the evidence supports, contradicts, or fails to establish the claim.

CLAIM:
{claim}

EVIDENCE:
{evidence_text}
"""

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )

        raw = (response.text or "").strip()

        if not raw:
            return _heuristic_analysis(
                claim,
                supporting,
                contradicting,
            )

        # Handle models that wrap JSON in markdown fences.
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.startswith("json"):
                raw = raw[4:].strip()

        result = json.loads(raw)

        status = str(result.get("status", "")).lower().strip()
        analysis = str(result.get("analysis", "")).strip()

        if status not in VALID_STATUSES or not analysis:
            return _heuristic_analysis(
                claim,
                supporting,
                contradicting,
            )

        return {
            "status": status,
            "analysis": analysis,
        }

    except Exception:
        return _heuristic_analysis(
            claim,
            supporting,
            contradicting,
        )