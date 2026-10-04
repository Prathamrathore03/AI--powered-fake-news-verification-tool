"""
VERITO Backend — Flask API
Main application entry point.

Endpoint: POST /verify
  Request:  { "url": "https://..." }
  Response: see README.md for full response schema

Run locally:
  python app.py
  (Server will start on http://localhost:5000)
"""

import os
import logging
import time

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env before anything else
load_dotenv()

# --- Module imports (after env load so they can read env) ---
from ssrf_guard import validate_url
from extractor import extract_article
from claim_extractor import extract_claim
from fact_checker import search_fact_checks
from searcher import search_evidence
from evidence_classifier import classify_evidence
from analyzer import synthesize_analysis

# ---------------------------------------------------------------------------
# Flask app setup
# ---------------------------------------------------------------------------

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

logger = logging.getLogger('verito')

# CORS — allow the frontend dev server (Vite) and its preview mode
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:4173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:4173",
]

# Allow additional origins from environment (for production deployment)
extra_origin = os.getenv('ALLOWED_ORIGIN', '').strip()

if extra_origin:
    ALLOWED_ORIGINS.append(extra_origin)

CORS(
    app,
    resources={r"/verify": {"origins": ALLOWED_ORIGINS}},
    supports_credentials=False,
)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.route('/health', methods=['GET'])
def health():
    """Simple liveness check — can be polled by frontend or ops tooling."""
    return jsonify({
        "status": "ok",
        "service": "verito-backend"
    }), 200


# ---------------------------------------------------------------------------
# Main verification endpoint
# ---------------------------------------------------------------------------

@app.route('/verify', methods=['POST'])
def verify():
    """
    POST /verify

    Accepts a JSON body:
        { "url": "https://..." }

    Returns a structured verification result or an error object.
    """

    # --- Parse request body ---
    try:
        data = request.get_json(silent=True)

    except Exception:
        return _error(
            "Invalid request body. Expected JSON with a 'url' field.",
            400
        )

    if not isinstance(data, dict):
        return _error(
            "Request body must be a JSON object with a 'url' field.",
            400
        )

    url = data.get('url', '')

    if not isinstance(url, str):
        return _error(
            "The 'url' field must be a string.",
            400
        )

    url = url.strip()

    # --- SSRF / URL validation ---
    url_error = validate_url(url)

    if url_error:
        return _error(url_error, 400)

    logger.info(f"Verification request: {url}")

    # -----------------------------------------------------------------------
    # Pipeline execution
    # -----------------------------------------------------------------------

    try:

        # ================================================================
        # Stage 1: Extract article content
        # ================================================================

        start = time.perf_counter()

        logger.info(
            "Stage 1/6 — Extracting article content..."
        )

        article = extract_article(url)

        logger.info(
            f"  Extracted {len(article.get('text', ''))} chars. "
            f"Title: {article.get('title', '')[:60]}"
        )

        logger.info(
            f"  [TIMING] Stage 1: "
            f"{time.perf_counter() - start:.2f}s"
        )

        # ================================================================
        # Stage 2: Extract main factual claim
        # ================================================================

        start = time.perf_counter()

        logger.info(
            "Stage 2/6 — Extracting main claim..."
        )

        claim = extract_claim(article)

        logger.info(
            f"  Claim: {claim}"
        )

        logger.info(
            f"  [TIMING] Stage 2: "
            f"{time.perf_counter() - start:.2f}s"
        )

        # ================================================================
        # Stage 3: Search fact-check databases
        # ================================================================

        start = time.perf_counter()

        logger.info(
            "Stage 3/6 — Searching fact-check databases..."
        )

        fact_checks = search_fact_checks(claim)

        logger.info(
            f"  Found {len(fact_checks)} fact-check result(s)."
        )

        logger.info(
            f"  [TIMING] Stage 3: "
            f"{time.perf_counter() - start:.2f}s"
        )

        # ================================================================
        # Stage 4: Search general web evidence
        # ================================================================

        start = time.perf_counter()

        logger.info(
            "Stage 4/6 — Searching web for evidence..."
        )

        web_results = search_evidence(claim)

        logger.info(
            f"  Found {len(web_results)} web result(s)."
        )

        logger.info(
            f"  [TIMING] Stage 4: "
            f"{time.perf_counter() - start:.2f}s"
        )

        # Combine all raw results
        all_raw = fact_checks + web_results

        # ================================================================
        # Stage 5: Classify evidence
        # ================================================================

        start = time.perf_counter()

        logger.info(
            "Stage 5/6 — Classifying evidence..."
        )

        supporting, contradicting = classify_evidence(
            claim,
            all_raw
        )

        logger.info(
            f"  Supporting: {len(supporting)} | "
            f"Contradicting: {len(contradicting)}"
        )

        logger.info(
            f"  [TIMING] Stage 5: "
            f"{time.perf_counter() - start:.2f}s"
        )

        # ================================================================
        # Stage 6: Synthesize analysis
        # ================================================================

        start = time.perf_counter()

        logger.info(
            "Stage 6/6 — Synthesizing analysis..."
        )

        # synthesize_analysis() returns a dictionary:
        # {
        #     "status": "...",
        #     "analysis": "..."
        # }
        analysis_result = synthesize_analysis(
            claim,
            supporting,
            contradicting,
        )

        analysis = analysis_result["analysis"]
        status = analysis_result["status"]

        logger.info(
            f"  Status: {status}"
        )

        logger.info(
            f"  [TIMING] Stage 6: "
            f"{time.perf_counter() - start:.2f}s"
        )

        # ================================================================
        # Build deduplicated sources list
        # ================================================================

        sources = _build_sources(
            supporting,
            contradicting
        )

        # ================================================================
        # Final response
        # ================================================================

        response_payload = {
            "claim": claim,
            "status": status,
            "supporting_evidence": supporting,
            "contradicting_evidence": contradicting,
            "analysis": analysis,
            "sources": sources,
        }

        logger.info(
            f"Verification complete for: {url}"
        )

        return jsonify(response_payload), 200

    # -------------------------------------------------------------------
    # Known error conditions
    # -------------------------------------------------------------------

    except EnvironmentError as e:

        logger.error(
            f"Environment/configuration error: {e}"
        )

        return _error(
            str(e),
            503
        )

    except ValueError as e:

        logger.warning(
            f"Processing error: {e}"
        )

        return _error(
            str(e),
            422
        )

    except Exception as e:

        logger.exception(
            f"Unexpected error processing {url}: {e}"
        )

        return _error(
            "An unexpected error occurred during verification. "
            "Please try again. If the problem persists, check "
            "the backend logs.",
            500
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _error(message: str, status_code: int):
    """Return a consistent JSON error response."""

    return jsonify({
        "error": message
    }), status_code


def _build_sources(
    supporting: list,
    contradicting: list
) -> list:

    """
    Build a deduplicated sources list from all classified evidence items.

    Only includes items that have a URL.
    """

    seen_urls = set()
    sources = []

    for item in supporting + contradicting:

        url = (item.get('url') or '').strip()

        if not url or url in seen_urls:
            continue

        seen_urls.add(url)

        sources.append({
            "title": (item.get('title') or '').strip(),
            "url": url,
            "source": (item.get('source') or '').strip(),
        })

    return sources


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':

    port = int(
        os.getenv(
            'FLASK_PORT',
            '5000'
        )
    )

    debug = (
        os.getenv(
            'FLASK_DEBUG',
            'false'
        ).lower()
        in ('1', 'true', 'yes')
    )

    logger.info(
        f"Starting VERITO backend on "
        f"http://localhost:{port}"
    )

    logger.info(
        f"CORS allowed origins: {ALLOWED_ORIGINS}"
    )

    logger.info(
        f"Debug mode: {debug}"
    )

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )