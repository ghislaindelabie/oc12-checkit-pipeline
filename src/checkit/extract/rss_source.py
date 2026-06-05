import logging
from datetime import UTC, datetime

import feedparser
from bs4 import BeautifulSoup

from checkit.extract.feeds import Feed
from checkit.extract.http import get
from checkit.schema import RawRecord

logger = logging.getLogger(__name__)


def _image_from_entry(entry) -> str | None:
    """Cascade documented in the sweep: media:content → media:thumbnail
    → enclosure → first <img> in the entry HTML."""
    for media in entry.get("media_content", []):
        if media.get("url") and media.get("type", "image").startswith("image"):
            return media["url"]
    for thumb in entry.get("media_thumbnail", []):
        if thumb.get("url"):
            return thumb["url"]
    for enclosure in entry.get("enclosures", []):
        if enclosure.get("href") and enclosure.get("type", "").startswith("image/"):
            return enclosure["href"]
    html = entry.get("summary", "") or ""
    for content in entry.get("content", []):
        html += content.get("value", "")
    img = BeautifulSoup(html, "lxml").find("img")
    if img and img.get("src"):
        return img["src"]
    return None


def _og_image(article_url: str) -> str | None:
    try:
        response = get(article_url)
    except Exception:
        logger.warning("og:image fetch failed for %s", article_url)
        return None
    meta = BeautifulSoup(response.text, "lxml").find("meta", property="og:image")
    return meta.get("content") if meta else None


def _publish_date(entry) -> datetime | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    return datetime(*parsed[:6], tzinfo=UTC)


def parse_feed(content: bytes, feed: Feed) -> list[RawRecord]:
    parsed = feedparser.parse(content)
    records = []
    for entry in parsed.entries:
        summary_html = entry.get("summary", "")
        body = BeautifulSoup(summary_html, "lxml").get_text(" ", strip=True) or None
        image_url = _image_from_entry(entry)
        if image_url is None and feed.og_fallback and entry.get("link"):
            image_url = _og_image(entry["link"])
        records.append(RawRecord(
            raw_source=f"rss:{feed.name}",
            headline=entry.get("title", ""),
            url=entry.get("link"),
            body_text=body,
            image_url=image_url,
            publish_date=_publish_date(entry),
            language=feed.lang,
            extras={"category": feed.category},
        ))
    return records


def fetch_rss(feed: Feed) -> list[RawRecord]:
    response = get(feed.url)
    records = parse_feed(response.content, feed)
    logger.info("rss:%s fetched %d entries", feed.name, len(records))
    return records


def probe_report(content: bytes, feed: Feed) -> dict:
    records = parse_feed(content, feed)
    with_image = sum(1 for r in records if r.image_url)
    return {
        "feed": feed.name,
        "entries": len(records),
        "with_image": with_image,
        "image_rate": round(with_image / len(records), 2) if records else 0.0,
    }


def probe_feed(feed: Feed) -> dict:
    try:
        response = get(feed.url)
    except Exception as exc:  # a dead feed is a result, not a crash
        return {"feed": feed.name, "error": str(exc), "entries": 0,
                "with_image": 0, "image_rate": 0.0}
    return probe_report(response.content, feed)
