"""Article-content enrichment for URL-only corpora (EUvsDisinfo, FakeNewsNet).

Fetches each article URL with our own stack — trafilatura for title+text,
og:image for a paired image — throttled per domain. Dead/geoblocked URLs are
the expected case (rot), counted and reported, never fatal. No third-party key.
"""

import logging
from urllib.parse import urlparse

import requests
import trafilatura
from bs4 import BeautifulSoup

from checkit.extract.http import USER_AGENT
from checkit.extract.throttle import THROTTLE
from checkit.schema import RawRecord

logger = logging.getLogger(__name__)

FETCH_TIMEOUT = 12.0
HOST_MIN_INTERVAL = 1.0


def fetch_article(url: str) -> dict:
    """Return {title, text, image_url} or {error}. Single attempt, short timeout."""
    THROTTLE.wait(f"host:{urlparse(url).netloc}", HOST_MIN_INTERVAL)
    try:
        response = requests.get(url, timeout=FETCH_TIMEOUT, allow_redirects=True,
                                headers={"User-Agent": USER_AGENT})
        response.raise_for_status()
    except requests.RequestException as exc:
        return {"error": exc.__class__.__name__}

    html = response.text
    text = trafilatura.extract(html, include_comments=False) or None
    soup = BeautifulSoup(html, "lxml")
    og_title = soup.find("meta", property="og:title")
    og_image = soup.find("meta", property="og:image")
    title = (og_title.get("content") if og_title else None) or (
        soup.title.get_text(strip=True) if soup.title else None)
    return {
        "title": title,
        "text": text,
        "image_url": og_image.get("content") if og_image else None,
    }


def enrich_records(records: list[RawRecord]) -> dict:
    """Fill headline/body_text/image_url in place; return rot/yield stats."""
    fetched = with_text = with_image = 0
    for record in records:
        if not record.url:
            continue
        result = fetch_article(record.url)
        if "error" in result:
            record.extras["fetch_error"] = result["error"]
            continue
        fetched += 1
        if result.get("title"):
            record.headline = result["title"]
        if result.get("text"):
            record.body_text = result["text"]
            with_text += 1
        if result.get("image_url"):
            record.image_url = result["image_url"]
            with_image += 1
        record.extras["text_fetched"] = True
    total = len(records)
    stats = {
        "records": total,
        "reachable": fetched,
        "with_text": with_text,
        "with_image": with_image,
        "text_rate": round(with_text / total, 3) if total else 0.0,
        "image_rate": round(with_image / total, 3) if total else 0.0,
    }
    logger.info("enrich: %d/%d reachable, text %d, image %d", fetched, total,
                with_text, with_image)
    return stats
