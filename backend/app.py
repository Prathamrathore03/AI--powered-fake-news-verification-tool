"""
VERITO Backend — Flask API
Main application entry point.

Endpoint: POST /verify
  Request:  { "url": "https://..." }
  Response: structured verification result with claim, evidence, analysis, and sources
"""

import os
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# --- Module imports ---
from ssrf_guard import validate_url
from extractor import extract_article
from claim_extractor import extract_claim
from fact_checker import search_fact_checks
from searcher import search_evidence
from evidence_classifier import classify_evidence
from analyzer import synthesize_analysis

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger('verito')

# CORS — allow deployed Render frontend as well as local Vite dev servers
ALLOWED_ORIGINS = [
    "https://verito.onrender.com",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:4173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:4173",
]

extra_origin = os.getenv('ALLOWED_ORIGIN', '').strip()
if extra_origin and extra_origin not in ALLOWED_ORIGINS:
    ALLOWED_ORIGINS.append(extra_origin)

CORS(
    app,
    resources={r"/verify": {"origins": ALLOWED_ORIGINS}},
    supports_credentials=False,
)

# ---------------------------------------------------------------------------
# Simple In-Memory Result Cache (TTL = 10 minutes, max 100 entries)
# ---------------------------------------------------------------------------
_CACHE = {}
_CACHE_TTL = 600  # seconds
_CACHE_MAX_ENTRIES = 100


def _get_cached_result(url: str):
    now = time.time()
    entry = _CACHE.get(url)
    if entry:
        cached_time, payload = entry
        if now - cached_time < _CACHE_TTL:
            return payload
        else:
            _CACHE.pop(url, None)
    return None


def _set_cached_result(url: str, payload: dict):
    if len(_CACHE) >= _CACHE_MAX_ENTRIES:
        # Evict oldest entry
        oldest_url = min(_CACHE.keys(), key=lambda k: _CACHE[k][0], default=None)
        if oldest_url:
            _CACHE.pop(oldest_url, None)
    _CACHE[url] = (time.time(), payload)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.route('/health', methods=['GET'])
def health():
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
    Body: { "url": "https://..." }
    """
    total_start = time.perf_counter()

    # --- Parse request body ---
    try:
        data = request.get_json(silent=True)
    except Exception:
        return _error("Invalid request body. Expected JSON with a 'url' field.", 400)

    if not isinstance(data, dict):
        return _error("Request body must be a JSON object with a 'url' field.", 400)

    url = data.get('url', '')
    if not isinstance(url, str):
        return _error("The 'url' field must be a string.", 400)

    url = url.strip()

    # --- SSRF / URL validation ---
    url_error = validate_url(url)
    if url_error:
        return _error(url_error, 400)

    logger.info(f"Verification request: {url}")

    # Check in-memory cache
    cached_payload = _get_cached_result(url)
    if cached_payload:
        logger.info(f"Returning cached verification result for: {url}")
        return jsonify(cached_payload), 200

    # -----------------------------------------------------------------------
    # Pipeline execution
    # -----------------------------------------------------------------------
    try:
        # Stage 1: Extract article content
        stage_start = time.perf_counter()
        logger.info("Stage 1/6 - Extracting article content...")
        article = extract_article(url)
        logger.info(
            f"  Extracted {len(article.get('text', ''))} chars. "
            f"Title: {article.get('title', '')[:60]} "
            f"({time.perf_counter() - stage_start:.2f}s)"
        )

        # Stage 2: Extract main factual claim
        stage_start = time.perf_counter()
        logger.info("Stage 2/6 - Extracting main claim...")
        claim = extract_claim(article)
        logger.info(
            f"  Claim: {claim} "
            f"({time.perf_counter() - stage_start:.2f}s)"
        )

        # Stage 3 & 4: Search fact-check registries and web evidence in parallel
        stage_start = time.perf_counter()
        logger.info("Stage 3 & 4/6 - Searching fact-checks and web evidence concurrently...")

        fact_checks = []
        web_results = []

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_fact = executor.submit(search_fact_checks, claim)
            future_web = executor.submit(search_evidence, claim)

            try:
                fact_checks = future_fact.result(timeout=12)
            except Exception as e:
                logger.warning(f"Fact-check search error: {e}")

            try:
                web_results = future_web.result(timeout=12)
            except Exception as e:
                logger.warning(f"Web evidence search error: {e}")

        logger.info(
            f"  Retrieved {len(fact_checks)} fact-check(s) and {len(web_results)} web result(s) "
            f"({time.perf_counter() - stage_start:.2f}s)"
        )

        all_raw = fact_checks + web_results

        # Stage 5: Classify evidence
        stage_start = time.perf_counter()
        logger.info("Stage 5/6 - Classifying evidence...")
        supporting, contradicting = classify_evidence(claim, all_raw)
        logger.info(
            f"  Supporting: {len(supporting)} | Contradicting: {len(contradicting)} "
            f"({time.perf_counter() - stage_start:.2f}s)"
        )

        # Stage 6: Synthesize analysis
        stage_start = time.perf_counter()
        logger.info("Stage 6/6 - Synthesizing analysis...")
        analysis_result = synthesize_analysis(claim, supporting, contradicting)
        analysis = analysis_result.get("analysis", "")
        status = analysis_result.get("status", "inconclusive")
        logger.info(
            f"  Status: {status} "
            f"({time.perf_counter() - stage_start:.2f}s)"
        )

        # Build deduplicated sources list
        sources = _build_sources(supporting, contradicting)

        response_payload = {
            "claim": claim,
            "status": status,
            "supporting_evidence": supporting,
            "contradicting_evidence": contradicting,
            "analysis": analysis,
            "sources": sources,
        }

        # Cache valid result
        _set_cached_result(url, response_payload)

        total_elapsed = time.perf_counter() - total_start
        logger.info(f"Verification completed in {total_elapsed:.2f}s for: {url}")

        return jsonify(response_payload), 200

    except EnvironmentError as e:
        logger.error(f"Environment/configuration error: {e}")
        return _error(str(e), 503)

    except ValueError as e:
        logger.warning(f"Processing error: {e}")
        return _error(str(e), 422)

    except Exception as e:
        logger.exception(f"Unexpected error processing {url}: {e}")
        return _error(
            "An unexpected error occurred during verification. "
            "Please verify the article URL is public and accessible.",
            500
        )


def _error(message: str, status_code: int):
    """Return a consistent JSON error response without leaking internal secrets."""
    return jsonify({"error": message}), status_code


def _build_sources(supporting: list, contradicting: list) -> list:
    """Build a deduplicated sources list from classified evidence."""
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


if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', '5000'))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() in ('1', 'true', 'yes')

    logger.info(f"Starting VERITO backend on http://localhost:{port}")
    logger.info(f"CORS allowed origins: {ALLOWED_ORIGINS}")
    logger.info(f"Debug mode: {debug}")

    app.run(host='0.0.0.0', port=port, debug=debug)