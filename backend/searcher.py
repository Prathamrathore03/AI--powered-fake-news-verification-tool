"""
Evidence Searcher for VERITO

Search strategy:
1. DuckDuckGo via ddgs — free, no API key required.
2. Multiple focused queries are generated from the claim so long claims
   do not produce useless search results.
3. Google Custom Search is used as a fallback if configured.
"""

import os
import re
from typing import List
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

SEARCH_TIMEOUT = 12
MAX_RESULTS = 10
GOOGLE_CSE_URL = "https://www.googleapis.com/customsearch/v1"


# Common words that add noise to web searches.
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "for", "with", "from",
    "that", "this", "was", "were", "has", "have", "had", "been",
    "being", "is", "are", "to", "of", "in", "on", "at", "by",
    "as", "into", "after", "before", "against", "over", "under",
    "their", "they", "them", "his", "her", "its", "who", "which",
    "what", "when", "where", "why", "how", "will", "would", "could",
    "should", "can", "may", "also", "more", "than", "about",
    "according", "said", "says", "report", "reports", "news",
}


def search_evidence(claim: str) -> List[dict]:
    """
    Search for evidence related to the claim.

    Multiple focused searches are combined and deduplicated.
    """

    claim = (claim or "").strip()

    if not claim:
        return []

    results: List[dict] = []

    # ---------------------------------------------------------
    # 1. DuckDuckGo
    # ---------------------------------------------------------
    ddg_results = _duckduckgo_search(claim)
    results.extend(ddg_results)

    # ---------------------------------------------------------
    # 2. Google fallback if DDG gives too few useful results
    # ---------------------------------------------------------
    if len(results) < 5:
        google_results = _google_custom_search(claim)

        existing_urls = {
            _normalize_url(r.get("url", ""))
            for r in results
        }

        for result in google_results:
            normalized = _normalize_url(result.get("url", ""))

            if normalized and normalized not in existing_urls:
                results.append(result)
                existing_urls.add(normalized)

    return results[:MAX_RESULTS]


# ============================================================
# QUERY GENERATION
# ============================================================

def _build_search_queries(claim: str) -> List[str]:
    """
    Build several short, focused search queries.

    A long AI-generated claim is usually a poor search query.
    We therefore create:
      1. Entity/event query
      2. Important-keyword query
      3. Fact-check query
    """

    clean = re.sub(r"\s+", " ", claim).strip()

    # Remove very long trailing clauses.
    clean = re.split(
        r"\b(?:demanding|claiming|saying|alleging|according to)\b",
        clean,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0].strip()

    words = re.findall(r"[A-Za-z0-9₹$%'-]+", clean)

    # Keep meaningful words.
    meaningful = []

    for word in words:
        lower = word.lower().strip("-'")

        if len(lower) < 3:
            continue

        if lower in STOP_WORDS:
            continue

        meaningful.append(word)

    # Preserve important names/entities.
    # Capitalized words are particularly useful for news searches.
    entities = []

    for word in words:
        if (
            len(word) >= 3
            and word[0].isupper()
            and word.lower() not in STOP_WORDS
        ):
            entities.append(word)

    # Remove duplicates while preserving order.
    entities = list(dict.fromkeys(entities))
    meaningful = list(dict.fromkeys(meaningful))

    queries = []

    # ---------------------------------------------------------
    # Query 1: Shortened original claim
    # ---------------------------------------------------------
    if meaningful:
        query1 = " ".join(meaningful[:14])
        queries.append(query1)

    # ---------------------------------------------------------
    # Query 2: Main entities + event
    # ---------------------------------------------------------
    if entities:
        entity_query = " ".join(entities[:8])

        if entity_query:
            queries.append(entity_query)

    # ---------------------------------------------------------
    # Query 3: Fact-check focused
    # ---------------------------------------------------------
    if meaningful:
        fact_words = " ".join(meaningful[:10])
        queries.append(f"{fact_words} fact check")

    # ---------------------------------------------------------
    # Query 4: Verify focused
    # ---------------------------------------------------------
    if meaningful:
        verify_words = " ".join(meaningful[:10])
        queries.append(f"{verify_words} verification")

    # ---------------------------------------------------------
    # Original claim as final fallback query.
    # Keep it short enough for search engines.
    # ---------------------------------------------------------
    if clean:
        queries.append(clean[:180])

    # Deduplicate.
    final_queries = []

    for query in queries:
        query = re.sub(r"\s+", " ", query).strip()

        if not query:
            continue

        if query.lower() not in {
            q.lower() for q in final_queries
        }:
            final_queries.append(query)

    # Maximum 4 queries so we don't hammer DDG.
    return final_queries[:4]


# ============================================================
# DUCKDUCKGO
# ============================================================

def _duckduckgo_search(claim: str) -> List[dict]:
    try:
        from ddgs import DDGS

        queries = _build_search_queries(claim)

        print("[searcher] Generated search queries:")

        for query in queries:
            print(f"[searcher]   → {query}")

        results: List[dict] = []
        seen_urls = set()

        with DDGS() as ddgs:

            for query in queries:

                try:
                    search_results = ddgs.text(
                        query,
                        max_results=5,
                        safesearch="moderate",
                    )

                    for item in search_results:

                        href = (item.get("href") or "").strip()

                        if not href:
                            continue

                        normalized_url = _normalize_url(href)

                        if not normalized_url:
                            continue

                        if normalized_url in seen_urls:
                            continue

                        seen_urls.add(normalized_url)

                        try:
                            domain = urlparse(href).netloc
                        except Exception:
                            domain = href

                        result = {
                            "title": (item.get("title") or "").strip(),
                            "url": href,
                            "source": domain,
                            "snippet": (
                                item.get("body") or ""
                            ).replace("\n", " ").strip(),
                        }

                        # Don't keep completely empty results.
                        if not result["title"] and not result["snippet"]:
                            continue

                        results.append(result)

                        # We already have enough.
                        if len(results) >= MAX_RESULTS:
                            return results[:MAX_RESULTS]

                except Exception as query_error:
                    print(
                        f"[searcher] Query failed: "
                        f"{query_error}"
                    )

        print(
            f"[searcher] DuckDuckGo returned "
            f"{len(results)} unique result(s)."
        )

        return results[:MAX_RESULTS]

    except ImportError:
        print(
            "[searcher] WARNING: `ddgs` not installed. "
            "Run: pip install ddgs"
        )
        return []

    except Exception as e:
        err_str = str(e).lower()

        if any(
            keyword in err_str
            for keyword in (
                "ratelimit",
                "202",
                "rate limit",
                "blocked",
            )
        ):
            print(
                "[searcher] WARNING: DuckDuckGo "
                "rate-limited the search."
            )
        else:
            print(
                f"[searcher] WARNING: DuckDuckGo "
                f"search error: {e}"
            )

        return []


# ============================================================
# GOOGLE CUSTOM SEARCH FALLBACK
# ============================================================

def _google_custom_search(claim: str) -> List[dict]:
    api_key = os.getenv(
        "GOOGLE_SEARCH_API_KEY",
        ""
    ).strip()

    cse_id = os.getenv(
        "GOOGLE_CSE_ID",
        ""
    ).strip()

    if not api_key or not cse_id:
        return []

    try:
        import requests

        queries = _build_search_queries(claim)

        results = []

        for query in queries[:2]:

            params = {
                "key": api_key,
                "cx": cse_id,
                "q": query[:200],
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
                    "[searcher] WARNING: Google Custom "
                    "Search daily quota exceeded."
                )
                return results

            if response.status_code == 403:
                print(
                    "[searcher] WARNING: Google Custom "
                    "Search 403 — check credentials."
                )
                return results

            if not response.ok:
                print(
                    f"[searcher] WARNING: Google Custom "
                    f"Search HTTP {response.status_code}."
                )
                continue

            data = response.json()

            for item in data.get("items", []):

                url = (item.get("link") or "").strip()

                if not url:
                    continue

                results.append({
                    "title": (
                        item.get("title") or ""
                    ).strip(),

                    "url": url,

                    "source": (
                        item.get("displayLink") or ""
                    ).strip(),

                    "snippet": (
                        item.get("snippet") or ""
                    ).replace("\n", " ").strip(),
                })

        return results[:MAX_RESULTS]

    except Exception as e:
        print(
            f"[searcher] WARNING: Google Custom "
            f"Search error: {e}"
        )
        return []


# ============================================================
# URL NORMALIZATION
# ============================================================

def _normalize_url(url: str) -> str:
    """
    Normalize URLs so duplicate search results are removed.
    """

    try:
        parsed = urlparse(url)

        if not parsed.netloc:
            return ""

        scheme = parsed.scheme.lower() or "https"
        domain = parsed.netloc.lower()

        # Remove www.
        if domain.startswith("www."):
            domain = domain[4:]

        path = parsed.path.rstrip("/")

        return f"{scheme}://{domain}{path}".lower()

    except Exception:
        return url.strip().lower()