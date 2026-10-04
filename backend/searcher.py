"""
Evidence Searcher for VERITO
Searches the web for relevant sources about the extracted claim.

Search strategy (priority order):
  1. DuckDuckGo via the `ddgs` library (no API key required — free, best-effort)
  2. Google Custom Search JSON API (optional, requires API key + CSE ID)
"""

import os
from typing import List
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

SEARCH_TIMEOUT = 12
MAX_RESULTS = 10
GOOGLE_CSE_URL = "https://www.googleapis.com/customsearch/v1"


def search_evidence(claim: str) -> List[dict]:
    results: List[dict] = []

    ddg_results = _duckduckgo_search(claim)
    results.extend(ddg_results)

    if len(results) < 5:
        google_results = _google_custom_search(claim)
        existing_urls = {r["url"] for r in results}

        for r in google_results:
            if r["url"] not in existing_urls:
                results.append(r)

    return results[:MAX_RESULTS]


def _duckduckgo_search(claim: str) -> List[dict]:
    try:
        from ddgs import DDGS

        results = []

        with DDGS() as ddgs:
            for r in ddgs.text(
                claim[:150],
                max_results=10,
                safesearch="moderate",
            ):
                href = (r.get("href") or "").strip()

                if not href:
                    continue

                try:
                    domain = urlparse(href).netloc
                except Exception:
                    domain = href

                results.append({
                    "title": (r.get("title") or "").strip(),
                    "url": href,
                    "source": domain,
                    "snippet": (r.get("body") or "").strip(),
                })

        return results

    except ImportError:
        print(
            "[searcher] WARNING: `ddgs` not installed. "
            "Run: pip install ddgs"
        )
        return []

    except Exception as e:
        err_str = str(e).lower()

        if any(
            k in err_str
            for k in ("ratelimit", "202", "rate limit", "blocked")
        ):
            print(
                "[searcher] WARNING: DuckDuckGo rate-limited the search. "
                "Try again shortly."
            )
        else:
            print(
                f"[searcher] WARNING: DuckDuckGo search error: {e}"
            )

        return []


def _google_custom_search(claim: str) -> List[dict]:
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY", "").strip()
    cse_id = os.getenv("GOOGLE_CSE_ID", "").strip()

    if not api_key or not cse_id:
        return []

    try:
        import requests

        params = {
            "key": api_key,
            "cx": cse_id,
            "q": claim[:200],
            "num": 10,
            "safe": "active",
            "lr": "lang_en",
        }

        response = requests.get(
            GOOGLE_CSE_URL,
            params=params,
            timeout=SEARCH_TIMEOUT,
        )

        if response.status_code == 429:
            print(
                "[searcher] WARNING: Google Custom Search daily quota exceeded."
            )
            return []

        if response.status_code == 403:
            print(
                "[searcher] WARNING: Google Custom Search 403 — "
                "check credentials."
            )
            return []

        if not response.ok:
            print(
                f"[searcher] WARNING: Google Custom Search "
                f"HTTP {response.status_code}."
            )
            return []

        data = response.json()
        results = []

        for item in data.get("items", []):
            url = (item.get("link") or "").strip()

            if url:
                results.append({
                    "title": (item.get("title") or "").strip(),
                    "url": url,
                    "source": (item.get("displayLink") or "").strip(),
                    "snippet": (
                        item.get("snippet") or ""
                    ).replace("\n", " ").strip(),
                })

        return results

    except Exception as e:
        print(
            f"[searcher] WARNING: Google Custom Search error: {e}"
        )
        return []