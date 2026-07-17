"""Best-effort retrieval of public article context for the summary model."""

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin
from urllib.request import Request, urlopen

_JSON_LD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    flags=re.IGNORECASE | re.DOTALL,
)
_OG_IMAGE_RE = re.compile(
    r'<meta[^>]+(?:property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']'
    r'|content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\'])',
    flags=re.IGNORECASE,
)
_EMPTY_CONTEXT: dict[str, Any] = {
    "image_url": None,
    "article_text": None,
    "article_fetched": False,
}


class _ArticleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.image_url: str | None = None
        self.description: str | None = None
        self.body_text_parts: list[str] = []
        self.article_text_parts: list[str] = []
        self.ignored_depth = 0
        self.article_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attributes = {name.lower(): value for name, value in attrs}
        if tag == "meta":
            property_name = (attributes.get("property") or attributes.get("name") or "").lower()
            content = attributes.get("content")
            if content and property_name in {"og:image", "twitter:image"}:
                self.image_url = self.image_url or content
            if content and property_name in {"og:description", "description", "twitter:description"}:
                self.description = self.description or content
        if tag in {"article", "main"}:
            self.article_depth += 1
        if tag in {"script", "style", "noscript", "svg", "nav", "footer", "header", "aside"}:
            self.ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"article", "main"}:
            self.article_depth = max(0, self.article_depth - 1)
        if tag in {"script", "style", "noscript", "svg", "nav", "footer", "header", "aside"}:
            self.ignored_depth = max(0, self.ignored_depth - 1)

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if self.ignored_depth > 0 or len(text) <= 2:
            return
        self.body_text_parts.append(text)
        if self.article_depth > 0:
            self.article_text_parts.append(text)


def _extract_json_ld_article_body(html: str) -> str | None:
    for match in _JSON_LD_RE.finditer(html):
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue

        candidates = payload if isinstance(payload, list) else [payload]
        for item in candidates:
            if not isinstance(item, dict):
                continue
            article_body = item.get("articleBody")
            if isinstance(article_body, str) and article_body.strip():
                return " ".join(article_body.split())
    return None


def _extract_og_image(html: str, article_url: str) -> str | None:
    match = _OG_IMAGE_RE.search(html)
    if not match:
        return None
    image_url = match.group(1) or match.group(2)
    return urljoin(article_url, image_url) if image_url else None


def _build_context(
    article_url: str,
    html: str,
    max_chars: int,
) -> dict[str, Any]:
    article_text = _extract_json_ld_article_body(html)
    if article_text:
        return {
            "image_url": _extract_og_image(html, article_url),
            "article_text": article_text[:max_chars],
            "article_fetched": True,
        }

    parser = _ArticleParser()
    parser.feed(html)

    article_text = " ".join(parser.article_text_parts)
    if not article_text:
        article_text = parser.description or " ".join(parser.body_text_parts)

    article_text = " ".join(article_text.split())[:max_chars] or None
    return {
        "image_url": urljoin(article_url, parser.image_url) if parser.image_url else None,
        "article_text": article_text,
        "article_fetched": bool(article_text),
    }


def fetch_article_context(
    article_url: str | None,
    max_chars: int = 10_000,
    timeout: float = 8.0,
) -> dict[str, Any]:
    """Fetch public page text and its Open Graph image URL without failing the app."""
    if not article_url:
        return dict(_EMPTY_CONTEXT)

    try:
        request = Request(
            article_url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; MarketPulse/1.0)"},
        )
        with urlopen(request, timeout=timeout) as response:
            html = response.read(1_000_000).decode("utf-8", errors="ignore")
        return _build_context(article_url, html, max_chars)
    except Exception:
        return dict(_EMPTY_CONTEXT)


def add_article_context(
    records: list[dict[str, Any]],
    max_workers: int = 8,
) -> list[dict[str, Any]]:
    """Fetch public article text and image URLs for every record in the batch."""
    if not records:
        return []

    unique_urls = {
        record.get("url")
        for record in records
        if record.get("url")
    }
    context_by_url: dict[str, dict[str, Any]] = {}

    if unique_urls:
        worker_count = min(max_workers, len(unique_urls))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = {
                executor.submit(fetch_article_context, url): url
                for url in unique_urls
            }
            for future in as_completed(futures):
                url = futures[future]
                try:
                    context_by_url[url] = future.result()
                except Exception:
                    context_by_url[url] = dict(_EMPTY_CONTEXT)

    enriched_records = []
    for record in records:
        enriched = dict(record)
        context = context_by_url.get(record.get("url"), _EMPTY_CONTEXT)
        enriched["image_url"] = context.get("image_url")
        enriched["article_text"] = context.get("article_text")
        enriched["article_fetched"] = context.get("article_fetched", False)
        enriched_records.append(enriched)
    return enriched_records


def add_article_image_urls(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Backward-compatible alias for callers that only expect image enrichment."""
    return add_article_context(records)
