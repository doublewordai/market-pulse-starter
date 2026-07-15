"""Small helpers for adding public article metadata to summary inputs."""

from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin
from urllib.request import Request, urlopen


class _OpenGraphImageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.image_url: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "meta" or self.image_url:
            return

        attributes = {name.lower(): value for name, value in attrs}
        if attributes.get("property", "").lower() == "og:image":
            self.image_url = attributes.get("content")


def fetch_article_image_url(article_url: str | None) -> str | None:
    """Return an article's public Open Graph image URL, when available."""
    if not article_url:
        return None

    try:
        request = Request(article_url, headers={"User-Agent": "MarketPulse/1.0"})
        with urlopen(request, timeout=8) as response:
            html = response.read(512_000).decode("utf-8", errors="ignore")

        parser = _OpenGraphImageParser()
        parser.feed(html)
        return urljoin(article_url, parser.image_url) if parser.image_url else None
    except Exception:
        return None


def add_article_image_urls(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Copy records and add image_url without failing a whole search on one URL."""
    enriched_records = []
    for record in records:
        enriched = dict(record)
        enriched["image_url"] = fetch_article_image_url(record.get("url"))
        enriched_records.append(enriched)
    return enriched_records
