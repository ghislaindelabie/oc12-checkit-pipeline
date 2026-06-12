"""Webz.io fake-news dataset (github.com/Webhose/fake-news-dataset).

Weekly ~1,000-article drops from sites flagged as fake-news publishers
(Wikipedia curated lists + Webz trust filter), Feb 2025 →, actively updated.
Measured on the 2026-05-31 drop: 94% of articles carry `thread.main_image`
paired with full body text in the same JSON record.

Label posture: SOURCE-level distant supervision — the article is labeled by
its publisher, not by a fact-check of its content. Confidence stays low (0.5)
and entertainment items are flagged ambiguous. `trust.bias` (political bias)
is kept in extras and NEVER used as a veracity label.

Consent: records carry a per-article `ai_allow` flag; opted-out articles are
skipped at ingestion, not stored.

Rights: Webz.io ToU = service license (no PII harvesting, no commercial
solicitation; crawled content is the originators' responsibility). Suitable
for this non-commercial research exercise; attribution given.
"""

import json
import logging
import zipfile
from pathlib import Path

from checkit.extract.http import get
from checkit.extract.throttle import THROTTLE
from checkit.lang import to_code
from checkit.schema import RawRecord

logger = logging.getLogger(__name__)

GITHUB_LIST_URL = ("https://api.github.com/repos/Webhose/fake-news-dataset"
                   "/contents/Datasets")
RAW_BASE = "https://github.com/Webhose/fake-news-dataset/raw/master/Datasets"
ENTERTAINMENT_CATEGORIES = {"Arts, Culture and Entertainment", "Sports"}


def download_webz(corpora_dir: Path) -> list[Path]:
    """Incremental: fetch every drop not already on disk (resumable)."""
    dest = corpora_dir / "webz-fakenews"
    dest.mkdir(parents=True, exist_ok=True)
    listing = get(GITHUB_LIST_URL, timeout=60).json()
    names = sorted(f["name"] for f in listing if f["name"].endswith(".zip"))
    new_paths = []
    for name in names:
        target = dest / name
        if target.exists() and target.stat().st_size > 0:
            continue
        THROTTLE.wait("host:github.com", 0.5)
        response = get(f"{RAW_BASE}/{name}", timeout=120)
        target.write_bytes(response.content)
        new_paths.append(target)
    logger.info("webz: %d drops on disk (%d newly downloaded)",
                len(names), len(new_paths))
    return new_paths


def article_to_record(article: dict, drop: str) -> RawRecord | None:
    if article.get("ai_allow") is False:
        return None  # per-record AI-use opt-out respected at ingestion
    thread = article.get("thread") or {}
    categories = article.get("categories") or []
    trust = article.get("trust") or {}
    return RawRecord(
        raw_source="webz-fakenews",
        headline=article.get("title", ""),
        body_text=article.get("text") or None,
        url=article.get("url"),
        image_url=thread.get("main_image") or None,
        publish_date=article.get("published") or None,
        language=to_code(article.get("language")),
        source_domain=thread.get("site") or None,
        raw_source_id=article.get("uuid"),
        extras={
            "drop": drop,
            "site": thread.get("site"),
            "country": thread.get("country"),
            "categories": categories,
            "trust_categories": trust.get("categories", []),
            "trust_bias": trust.get("bias"),  # NEVER used as veracity label
            "sentiment": article.get("sentiment"),
            "domain_rank": thread.get("domain_rank"),
            "entertainment": any(c in ENTERTAINMENT_CATEGORIES for c in categories),
        },
    )


def load_webz(corpora_dir: Path, limit: int | None = None) -> list[RawRecord]:
    records: list[RawRecord] = []
    skipped_optout = bad = 0
    zips = sorted((corpora_dir / "webz-fakenews").glob("*.zip"))
    for zip_path in zips:
        with zipfile.ZipFile(zip_path) as zf:
            for member in zf.namelist():
                if not member.endswith(".json"):
                    continue
                try:
                    article = json.loads(zf.read(member))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    bad += 1
                    continue
                record = article_to_record(article, drop=zip_path.name)
                if record is None:
                    skipped_optout += 1
                    continue
                records.append(record)
                if limit and len(records) >= limit:
                    break
        if limit and len(records) >= limit:
            break
    logger.info("webz: %d records from %d drops (%d ai_allow opt-outs skipped, "
                "%d unparseable)", len(records), len(zips), skipped_optout, bad)
    return records
