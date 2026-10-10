"""
Evidence Searcher for VERITO

Search strategy:
1. DuckDuckGo via ddgs — free, no API key required.
2. Focused queries generated from the claim so search engines return relevant corroboration/refutation.
3. Early exit if sufficient evidence is retrieved (avoids throttling and minimizes latency).
4. Google Custom Search used as optional fallback only if configured.
"""

import os
import re
from typing import List
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

SEARCH_TIMEOUT = 10
MAX_RESULTS = 10
GOOGLE_CSE_URL = "https://www.googleapis.com/customsearch/v1"

# Common words that add noise to web searches
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "for", "with", "from",
    "that", "this", "was", "were", "has", "have", "had", "been",
    "being", "is", "are", "to", "of", "in", "on", "at", "by",
    "as", "into", "after", "before", "against", "over", "under",
    "their", "they", "them", "his", "her", "its", "who", "which",
    "what", "when", "where", "why", "how", "will", "would", "could",
    "should", "can", "may", "also", "more", "than", "about",
    "according", "said", "says", "report", "reports", "news",
    "article", "claimed", "claims", "claiming",
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

    # 1. DuckDuckGo search
    ddg_results = _duckduckgo_search(claim)
    results.extend(ddg_results)

    # 2. Google fallback only if DDG produced fewer than 4 results and Google CSE is configured
    if len(results) < 4:
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


def _build_search_queries(claim: str) -> List[str]:
    """
    Build 2 short, focused search queries.
    Avoid long AI-generated text queries which search engines fail to match.
    """
    clean = re.sub(r"\s+", " ", claim).strip()

    # Strip attribution phrases like "According to reports..."
    clean = re.split(
        r"\b(?:demanding|claiming|saying|alleging|according to)\b",
        clean,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0].strip()

    words = re.findall(r"[A-Za-z0-9'-]+", clean)

    meaningful = []
    entities = []

    for word in words:
        lower = word.lower().strip("-'")
        if len(lower) < 3 or lower in STOP_WORDS:
            continue
        meaningful.append(word)
        if word[0].isupper() and len(word) >= 3:
            entities.append(word)

    entities = list(dict.fromkeys(entities))
    meaningful = list(dict.fromkeys(meaningful))

    queries = []

    # Query 1: Fact-check oriented (highest signal for verification)
    if meaningful:
        fact_core = " ".join(meaningful[:8])
        queries.append(f"{fact_core} fact check")

    # Query 2: Entities / Core event query
    if entities and len(entities) >= 2:
        queries.append(" ".join(entities[:6]))
    elif meaningful:
        queries.append(" ".join(meaningful[:10]))

    # Deduplicate queries
    final_queries = []
    for q in queries:
        q = re.sub(r"\s+", " ", q).strip()
        if q and q.lower() not in {fq.lower() for fq in final_queries}:
            final_queries.append(q)

    # Limit to at most 2 queries to avoid DDG throttling and reduce latency
    return final_queries[:2] if final_queries else [clean[:100]]


def _duckduckgo_search(claim: str) -> List[dict]:
    """
    Search DuckDuckGo using the ddgs library.
    Safe encoding, strict timeout, and early exit when enough results are found.
    """
    try:
        from ddgs import DDGS

        queries = _build_search_queries(claim)
        results: List[dict] = []
        seen_urls = set()

        with DDGS(timeout=SEARCH_TIMEOUT) as ddgs:
            for query in queries:
                try:
                    search_results = ddgs.text(
                        query,
                        max_results=6,
                        safesearch="moderate",
                    )
                    if not search_results:
                        continue

                    for item in search_results:
                        href = (item.get("href") or "").strip()
                        if not href:
                            continue

                        normalized_url = _normalize_url(href)
                        if not normalized_url or normalized_url in seen_urls:
                            continue

                        seen_urls.add(normalized_url)

                        try:
                            domain = urlparse(href).netloc
                        except Exception:
                            domain = href

                        title = (item.get("title") or "").strip()
                        snippet = (item.get("body") or "").replace("\n", " ").strip()

                        if not title and not snippet:
                            continue

                        results.append({
                            "title": title,
                            "url": href,
                            "source": domain,
                            "snippet": snippet,
                        })

                        if len(results) >= MAX_RESULTS:
                            return results[:MAX_RESULTS]

                    # If the first query already provided 5+ good results, exit early to save time
                    if len(results) >= 5:
                        break

                except Exception as query_error:
                    print(f"[searcher] Query error for '{query}': {query_error}")

        return results[:MAX_RESULTS]

    except ImportError:
        print("[searcher] WARNING: `ddgs` not installed.")
        return []
    except Exception as e:
        print(f"[searcher] WARNING: DuckDuckGo search error: {e}")
        return []


def _google_custom_search(claim: str) -> List[dict]:
    """
    Query Google Custom Search JSON API (optional fallback).
    """
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY", "").strip()
    cse_id = os.getenv("GOOGLE_CSE_ID", "").strip()

    if not api_key or not cse_id:
        return []

    try:
        import requests

        queries = _build_search_queries(claim)
        results = []

        for query in queries[:1]:
            params = {
                "key": api_key,
                "cx": cse_id,
                "q": query[:200],
                "num": 5,
                "safe": "active",
                "lr": "lang_en",
            }

            response = requests.get(
                GOOGLE_CSE_URL,
                params=params,
                timeout=SEARCH_TIMEOUT,
            )

            if not response.ok:
                continue

            data = response.json()
            for item in data.get("items", []):
                url = (item.get("link") or "").strip()
                if not url:
                    continue
                results.append({
                    "title": (item.get("title") or "").strip(),
                    "url": url,
                    "source": (item.get("displayLink") or "").strip(),
                    "snippet": (item.get("snippet") or "").replace("\n", " ").strip(),
                })

        return results[:MAX_RESULTS]

    except Exception as e:
        print(f"[searcher] WARNING: Google Custom Search error: {e}")
        return []


def _normalize_url(url: str) -> str:
    """Normalize URLs to prevent duplicate search results."""
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return ""

        scheme = parsed.scheme.lower() or "https"
        domain = parsed.netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        path = parsed.path.rstrip("/")
        return f"{scheme}://{domain}{path}".lower()
    except Exception:
        return url.strip().lower()