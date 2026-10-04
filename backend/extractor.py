"""
Article Extractor for VERITO
Extracts clean article text from a submitted URL using trafilatura.
Enforces timeout, content size limits, and safe download headers.
"""

import requests
import trafilatura
from trafilatura.settings import use_config

REQUEST_TIMEOUT = 20          # seconds per HTTP request
MAX_CONTENT_BYTES = 5_000_000 # 5 MB cap — prevents memory exhaustion
MIN_ARTICLE_LENGTH = 150      # chars — shorter content is likely not an article
MAX_TEXT_FOR_LLM = 8_000      # chars sent to LLM to stay within token budgets

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (compatible; VERITO/1.0; +https://github.com/Prathamrathore03/'
        'AI--powered-fake-news-verification-tool)'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Trafilatura config: no comments, no tables, include metadata
_trafilatura_config = use_config()
_trafilatura_config.set("DEFAULT", "EXTRACTION_TIMEOUT", "0")


def extract_article(url: str) -> dict:
    """
    Download and extract the article at `url`.

    Returns a dict with keys:
        text (str)      — extracted plain text
        title (str)     — article title (may be empty)
        author (str)    — author name (may be empty)
        date (str)      — publication date string (may be empty)

    Raises ValueError with a human-readable message on failure.
    """
    html = _download_html(url)
    return _parse_html(html, url)


def _download_html(url: str) -> str:
    """Download raw HTML from `url` with size and timeout limits."""
    try:
        session = requests.Session()
        session.max_redirects = 5

        response = session.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            stream=True,
            allow_redirects=True,
        )
        response.raise_for_status()

        # Check content-type — warn on clearly non-HTML responses
        content_type = response.headers.get('Content-Type', '').lower()
        if content_type and 'html' not in content_type and 'text' not in content_type:
            raise ValueError(
                f"URL does not appear to point to an article page "
                f"(Content-Type: {content_type}). Please submit a news article URL."
            )

        # Stream content with size cap
        chunks = []
        total = 0
        for chunk in response.iter_content(chunk_size=32_768):
            chunks.append(chunk)
            total += len(chunk)
            if total >= MAX_CONTENT_BYTES:
                break

        raw = b''.join(chunks)
        return raw.decode('utf-8', errors='replace')

    except requests.exceptions.Timeout:
        raise ValueError(
            f"The article server did not respond within {REQUEST_TIMEOUT} seconds. "
            "The site may be slow or the URL may be unreachable."
        )
    except requests.exceptions.TooManyRedirects:
        raise ValueError(
            "The article URL resulted in too many redirects. "
            "Please check that the URL is correct and publicly accessible."
        )
    except requests.exceptions.ConnectionError as e:
        raise ValueError(
            f"Could not connect to the article server. "
            f"Please verify the URL is correct and the server is reachable. Detail: {e}"
        )
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response is not None else "unknown"
        if code == 403:
            raise ValueError(
                "Access denied (HTTP 403). The article may be behind a login wall or blocked access."
            )
        if code == 404:
            raise ValueError(
                "Article not found (HTTP 404). The URL may be broken or the article may have been removed."
            )
        if code == 429:
            raise ValueError(
                "The article server rate-limited the request (HTTP 429). Please try again later."
            )
        raise ValueError(f"HTTP error {code} while accessing the article.")
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Unexpected error downloading article: {e}")


def _parse_html(html: str, url: str) -> dict:
    """Parse article content from HTML using trafilatura."""
    try:
        # First pass: with metadata
        extracted = trafilatura.extract(
            html,
            url=url,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
            with_metadata=True,
            config=_trafilatura_config,
        )

        if extracted and isinstance(extracted, dict):
            text = extracted.get('text') or extracted.get('body') or ''
            title = extracted.get('title') or ''
            author = extracted.get('author') or ''
            date = extracted.get('date') or ''
        else:
            # Fallback: plain text extraction
            text = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=False,
                config=_trafilatura_config,
            ) or ''
            title = ''
            author = ''
            date = ''

        text = (text or '').strip()

        if len(text) < MIN_ARTICLE_LENGTH:
            raise ValueError(
                "Could not extract meaningful article content from this URL. "
                "The page may be paywalled, JavaScript-rendered, heavily dynamic, "
                "or not an article at all. Please try a different URL."
            )

        return {
            'text': text[:MAX_TEXT_FOR_LLM],
            'title': (title or '').strip(),
            'author': (author or '').strip(),
            'date': (date or '').strip(),
        }

    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Article content extraction failed: {e}")
