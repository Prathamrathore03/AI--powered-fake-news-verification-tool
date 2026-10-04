"""
Fact-Check Searcher for VERITO
Queries the Google Fact Check Tools API to find existing professional fact-checks
for the extracted claim.

Free tier: Approximately 1,000 queries/day — no billing account required.
API key obtained from: https://console.cloud.google.com/apis/library/factchecktools.googleapis.com
"""

import os
import requests
from typing import List
from dotenv import load_dotenv

load_dotenv()

FACT_CHECK_API_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
FACT_CHECK_TIMEOUT = 10  # seconds


def search_fact_checks(claim: str) -> List[dict]:
    """
    Search the Google Fact Check Tools API for fact-checks about the given claim.

    Returns a list of evidence dicts (may be empty if API key not set or no results found).
    Degrades gracefully — never raises an exception that blocks the pipeline.
    """
    api_key = os.getenv('GOOGLE_FACT_CHECK_API_KEY', '').strip()

    if not api_key:
        # Silently skip — caller will use other search methods
        return []

    try:
        params = {
            'key': api_key,
            'query': claim[:250],
            'languageCode': 'en',
            'pageSize': 10,
        }

        response = requests.get(
            FACT_CHECK_API_URL,
            params=params,
            timeout=FACT_CHECK_TIMEOUT,
        )

        if response.status_code == 403:
            # Key exists but not authorized — log and skip
            print("[fact_checker] WARNING: GOOGLE_FACT_CHECK_API_KEY is set but returned 403 (Forbidden). "
                  "Ensure the Fact Check Tools API is enabled in your Google Cloud project.")
            return []

        if response.status_code == 429:
            print("[fact_checker] WARNING: Google Fact Check API daily quota reached.")
            return []

        if not response.ok:
            print(f"[fact_checker] WARNING: Fact Check API returned HTTP {response.status_code}.")
            return []

        data = response.json()
        return _parse_results(data)

    except requests.exceptions.Timeout:
        print("[fact_checker] WARNING: Fact Check API timed out.")
        return []
    except Exception as e:
        print(f"[fact_checker] WARNING: Fact Check API error: {e}")
        return []


def _parse_results(data: dict) -> List[dict]:
    """Parse raw Google Fact Check API response into VERITO evidence dicts."""
    results = []

    for claim_item in data.get('claims', []):
        claim_text = claim_item.get('text', '')

        for review in claim_item.get('claimReview', []):
            publisher = review.get('publisher', {})
            pub_name = publisher.get('name') or publisher.get('site') or 'Fact Check Source'
            review_url = review.get('url', '')
            review_title = review.get('title', '').strip()
            textual_rating = review.get('textualRating', '').strip()

            if not review_url:
                continue

            # Build a descriptive snippet from available data
            snippet_parts = []
            if claim_text:
                snippet_parts.append(f'Claim under review: "{claim_text[:200]}"')
            if textual_rating:
                snippet_parts.append(f'Fact-check rating: {textual_rating}')

            results.append({
                'title': review_title or f'Fact-check by {pub_name}',
                'url': review_url,
                'source': pub_name,
                'snippet': ' — '.join(snippet_parts) if snippet_parts else f'Reviewed by {pub_name}',
                '_textual_rating': textual_rating,   # internal — used by classifier
                '_is_fact_check': True,              # internal — flag for classifier
            })

    return results
