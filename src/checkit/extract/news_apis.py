"""Keyed news-API adapters, one declarative spec per provider.

Field mappings follow each provider's public documentation; they are covered
by hermetic fixture tests but still PENDING first live validation (keys not
yet registered) — see KNOWN_ISSUES.md. Single page per run for now;
pagination tuning comes with live quotas.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from checkit.extract.http import get
from checkit.schema import RawRecord

logger = logging.getLogger(__name__)

_DT_FORMATS = (
    "%Y-%m-%d %H:%M:%S %z",   # currents
    "%Y-%m-%d %H:%M:%S",      # newsdata, worldnews (UTC implied)
)


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        parsed = None
    if parsed is None:
        for fmt in _DT_FORMATS:
            try:
                parsed = datetime.strptime(value, fmt)
                break
            except ValueError:
                continue
    if parsed is None:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _clean(value: str | None) -> str | None:
    # Some providers send literal "None"/"" for missing fields
    return value if value and value != "None" else None


@dataclass(frozen=True)
class NewsApiSpec:
    name: str
    url: str
    build_params: Callable[[str, datetime, datetime, int, str], dict]
    items: Callable[[dict], list]
    to_record: Callable[[dict], RawRecord]


def fetch_news_api(
    spec: NewsApiSpec,
    query: str,
    start: datetime,
    end: datetime,
    limit: int,
    api_key: str,
) -> list[RawRecord]:
    params = spec.build_params(query, start, end, limit, api_key)
    payload = get(spec.url, params=params).json()
    try:
        items = spec.items(payload) or []
    except (KeyError, TypeError, AttributeError):
        logger.warning("api:%s unexpected payload shape: %s", spec.name, str(payload)[:200])
        return []
    records = [spec.to_record(item) for item in items][:limit]
    logger.info("api:%s fetched %d articles for query=%r", spec.name, len(records), query)
    return records


def _d(dt: datetime) -> str:
    return dt.astimezone(UTC).strftime("%Y-%m-%d")


def _iso(dt: datetime) -> str:
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


SPECS: dict[str, NewsApiSpec] = {
    # Free tier serves recent news only (no date filtering) — the window is
    # narrowed by run frequency instead.
    "newsdata": NewsApiSpec(
        name="newsdata",
        url="https://newsdata.io/api/1/latest",
        build_params=lambda q, s, e, n, k: {
            "apikey": k, "q": q, "language": "fr", "image": "1",
        },
        items=lambda p: p["results"],
        to_record=lambda a: RawRecord(
            raw_source="api:newsdata",
            headline=a.get("title", ""),
            url=a.get("link"),
            body_text=_clean(a.get("description")),
            image_url=_clean(a.get("image_url")),
            publish_date=parse_dt(a.get("pubDate")),
            language="fr",
            raw_source_id=a.get("article_id"),
            extras={"source_id": a.get("source_id"), "category": a.get("category")},
        ),
    ),
    "guardian": NewsApiSpec(
        name="guardian",
        url="https://content.guardianapis.com/search",
        build_params=lambda q, s, e, n, k: {
            "api-key": k, "q": q, "from-date": _d(s), "to-date": _d(e),
            "page-size": str(min(n, 50)), "show-fields": "thumbnail,trailText",
        },
        items=lambda p: p["response"]["results"],
        to_record=lambda a: RawRecord(
            raw_source="api:guardian",
            headline=a.get("webTitle", ""),
            url=a.get("webUrl"),
            body_text=_clean(a.get("fields", {}).get("trailText")),
            image_url=_clean(a.get("fields", {}).get("thumbnail")),
            publish_date=parse_dt(a.get("webPublicationDate")),
            language="en",
            raw_source_id=a.get("id"),
            extras={"section": a.get("sectionName")},
        ),
    ),
    "gnews": NewsApiSpec(
        name="gnews",
        url="https://gnews.io/api/v4/search",
        build_params=lambda q, s, e, n, k: {
            "apikey": k, "q": q, "lang": "fr", "from": _iso(s), "to": _iso(e),
            "max": str(min(n, 10)),
        },
        items=lambda p: p["articles"],
        to_record=lambda a: RawRecord(
            raw_source="api:gnews",
            headline=a.get("title", ""),
            url=a.get("url"),
            body_text=_clean(a.get("description")),
            image_url=_clean(a.get("image")),
            publish_date=parse_dt(a.get("publishedAt")),
            language="fr",
            extras={"source_name": a.get("source", {}).get("name")},
        ),
    ),
    "currents": NewsApiSpec(
        name="currents",
        url="https://api.currentsapi.services/v1/search",
        build_params=lambda q, s, e, n, k: {
            "apiKey": k, "keywords": q, "language": "fr",
            "start_date": _iso(s), "end_date": _iso(e),
        },
        items=lambda p: p["news"],
        to_record=lambda a: RawRecord(
            raw_source="api:currents",
            headline=a.get("title", ""),
            url=a.get("url"),
            body_text=_clean(a.get("description")),
            image_url=_clean(a.get("image")),
            publish_date=parse_dt(a.get("published")),
            language=a.get("language") or "fr",
            raw_source_id=a.get("id"),
            extras={"category": a.get("category")},
        ),
    ),
    # Free tier is HTTP-only (https is a paid feature on mediastack)
    "mediastack": NewsApiSpec(
        name="mediastack",
        url="http://api.mediastack.com/v1/news",
        build_params=lambda q, s, e, n, k: {
            "access_key": k, "keywords": q, "languages": "fr",
            "date": f"{_d(s)},{_d(e)}", "limit": str(min(n, 100)),
        },
        items=lambda p: p["data"],
        to_record=lambda a: RawRecord(
            raw_source="api:mediastack",
            headline=a.get("title", ""),
            url=a.get("url"),
            body_text=_clean(a.get("description")),
            image_url=_clean(a.get("image")),
            publish_date=parse_dt(a.get("published_at")),
            language=a.get("language") or "fr",
            extras={"source": a.get("source"), "country": a.get("country")},
        ),
    ),
    "thenewsapi": NewsApiSpec(
        name="thenewsapi",
        url="https://api.thenewsapi.com/v1/news/all",
        build_params=lambda q, s, e, n, k: {
            "api_token": k, "search": q, "language": "fr",
            "published_after": _iso(s), "published_before": _iso(e),
            "limit": str(min(n, 100)),
        },
        items=lambda p: p["data"],
        to_record=lambda a: RawRecord(
            raw_source="api:thenewsapi",
            headline=a.get("title", ""),
            url=a.get("url"),
            body_text=_clean(a.get("description") or a.get("snippet")),
            image_url=_clean(a.get("image_url")),
            publish_date=parse_dt(a.get("published_at")),
            language=a.get("language"),
            raw_source_id=a.get("uuid"),
            extras={"source": a.get("source"), "categories": a.get("categories")},
        ),
    ),
    "worldnews": NewsApiSpec(
        name="worldnews",
        url="https://api.worldnewsapi.com/search-news",
        build_params=lambda q, s, e, n, k: {
            "api-key": k, "text": q, "language": "fr",
            "earliest-publish-date": _d(s), "latest-publish-date": _d(e),
            "number": str(min(n, 100)),
        },
        items=lambda p: p["news"],
        to_record=lambda a: RawRecord(
            raw_source="api:worldnews",
            headline=a.get("title", ""),
            url=a.get("url"),
            body_text=_clean(a.get("summary") or a.get("text")),
            image_url=_clean(a.get("image")),
            publish_date=parse_dt(a.get("publish_date")),
            language=a.get("language") or "fr",
            raw_source_id=str(a.get("id", "")) or None,
            extras={"source_country": a.get("source_country")},
        ),
    ),
}
