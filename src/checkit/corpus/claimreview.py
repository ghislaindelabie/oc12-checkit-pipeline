"""ClaimReview aggregate dump (DataCommons feed).

~93K fact-check verdicts in schema.org ClaimReview format from IFCN-aligned
fact-checkers worldwide. This is a LABEL feed, not a multimodal one: records
carry no image. Its value is the join surface — `appearance_urls` lists where
each debunked claim circulated, which later lets us label live-collected
content. Rating strings are heterogeneous per fact-checker ("Mostly False",
"Pants on Fire!", "Faux"…) and are kept raw; normalization happens in transform.
Refreshed upstream continuously → @weekly DAG re-downloads (dump-preferred rule).
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from checkit.extract.http import get
from checkit.schema import RawRecord


def _safe_date(value: str | None) -> datetime | None:
    # the live dump contains malformed dates (e.g. year '20204')
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).replace(tzinfo=UTC)
    except ValueError:
        return None

logger = logging.getLogger(__name__)

FEED_URL = "https://storage.googleapis.com/datacommons-feeds/claimreview/latest/data.json"


def download_claimreview(corpora_dir: Path) -> Path:
    dest = corpora_dir / "claimreview"
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / "data.json"
    logger.info("claimreview downloading feed (~200 MB) to %s", target)
    response = get(FEED_URL, timeout=300)
    target.write_bytes(response.content)
    logger.info("claimreview feed saved (%d bytes)", target.stat().st_size)
    return target


def feed_to_records(json_path: Path, limit: int | None = None) -> list[RawRecord]:
    feed = json.loads(json_path.read_text(encoding="utf-8"))
    records = []
    for element in feed.get("dataFeedElement", []):
        for item in element.get("item") or []:
            claim = item.get("claimReviewed") or ""
            if not claim:
                continue
            fact_checker = (item.get("author") or {}).get("name", "unknown")
            rating = (item.get("reviewRating") or {}).get("alternateName") or None
            appearances = [
                a.get("url") for a in (item.get("itemReviewed") or {}).get("appearance", [])
                if isinstance(a, dict) and a.get("url")
            ]
            records.append(RawRecord(
                raw_source="claimreview",
                headline=claim,
                url=item.get("url"),
                publish_date=_safe_date(item.get("datePublished")),
                extras={
                    "rating_raw": rating,
                    "fact_checker": fact_checker,
                    "label_source": f"claimreview:{fact_checker}",
                    "fine_grained_label": f"claimreview:{rating or 'unrated'}",
                    "appearance_urls": appearances,
                },
            ))
            if limit and len(records) >= limit:
                return records
    return records


def load_claimreview(corpora_dir: Path, limit: int | None = None) -> list[RawRecord]:
    path = corpora_dir / "claimreview" / "data.json"
    if not path.exists():
        logger.warning("claimreview missing %s — run download first", path)
        return []
    records = feed_to_records(path, limit=limit)
    logger.info("claimreview: %d verdicts loaded", len(records))
    return records
