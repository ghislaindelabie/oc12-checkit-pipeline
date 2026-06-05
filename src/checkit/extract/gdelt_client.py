import logging
import time
from datetime import UTC, datetime

from checkit.extract.http import get
from checkit.schema import RawRecord

logger = logging.getLogger(__name__)

GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_DT_FORMAT = "%Y%m%d%H%M%S"
# GDELT enforces one request per 5 seconds (verified live 2026-06-05;
# bursts trigger a multi-minute penalty window)
GDELT_MIN_INTERVAL = 5.5
_last_call = 0.0

LANGUAGE_CODES = {
    "french": "fr",
    "english": "en",
    "spanish": "es",
    "german": "de",
    "italian": "it",
    "portuguese": "pt",
}


def _parse_seendate(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
    except (ValueError, TypeError):
        return None


def fetch_gdelt(
    query: str,
    start: datetime | None = None,
    end: datetime | None = None,
    max_records: int = 250,
) -> list[RawRecord]:
    """Query the GDELT DOC 2.0 API (free, no key, ~3-month rolling window).

    Attribution: data from the GDELT Project (https://www.gdeltproject.org).
    """
    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": str(min(max_records, 250)),
    }
    if start:
        params["startdatetime"] = start.astimezone(UTC).strftime(GDELT_DT_FORMAT)
    if end:
        params["enddatetime"] = end.astimezone(UTC).strftime(GDELT_DT_FORMAT)

    global _last_call
    wait = GDELT_MIN_INTERVAL - (time.monotonic() - _last_call)
    if wait > 0:
        time.sleep(wait)
    _last_call = time.monotonic()

    response = get(GDELT_DOC_URL, params=params)
    try:
        articles = response.json().get("articles", [])
    except ValueError:
        # GDELT signals throttling/errors as plain text with HTTP 200
        logger.warning("gdelt non-json response: %s", response.text[:200])
        return []

    records = []
    for article in articles:
        language = article.get("language", "").lower()
        records.append(RawRecord(
            raw_source="gdelt-doc",
            headline=article.get("title", ""),
            url=article.get("url"),
            image_url=article.get("socialimage") or None,
            publish_date=_parse_seendate(article.get("seendate", "")),
            language=LANGUAGE_CODES.get(language, language[:2] or None),
            source_domain=article.get("domain") or None,
            extras={"sourcecountry": article.get("sourcecountry", "")},
        ))
    logger.info("gdelt fetched %d articles for query=%r", len(records), query)
    return records
