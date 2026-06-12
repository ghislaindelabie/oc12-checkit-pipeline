"""EUvsDisinfo — pro-Kremlin disinformation cases (EU East StratCom Task Force).

The live site (euvsdisinfo.eu) is behind a Cloudflare managed challenge and its
robots.txt disallows the search/sort/pagination params — so per our legal
posture (prefer official channels, obey robots, don't defeat anti-bot
protections) we do NOT scrape it. Instead we use the OPEN, DOI'd mirror:

  Zenodo 10514307 — euvsdisinfo_base.csv, CC-BY-4.0 (Aleite et al., CIKM 2024),
  the labeled article-URL list of the full EUvsDisinfo database.

The base file carries only labeled URLs + metadata (no article text). Content
is recovered by fetching each article with our own trafilatura + og:image
stack (no third-party key; the upstream repo uses DiffBot, we don't need it).
Article rot is expected (pro-Kremlin outlets, dead/geoblocked) and reported as
a KPI, exactly like the FakeNewsNet image screen.

Labels are EU-analyst curated → high confidence (0.9): class=disinformation→fake,
class=trustworthy→real.

Incremental note: the Zenodo snapshot is FROZEN. Re-pull + idempotent load means
"only new rows insert", but genuinely new cases appear only when the upstream
mirror refreshes — true daily-fresh would require the (rejected) live route.
"""

import csv
import logging
from datetime import UTC, datetime
from pathlib import Path

from checkit.extract.http import get
from checkit.lang import to_code
from checkit.schema import RawRecord

logger = logging.getLogger(__name__)

ZENODO_URL = "https://zenodo.org/records/10514307/files/euvsdisinfo_base.csv?download=1"


def download_euvsdisinfo(corpora_dir: Path) -> Path:
    dest = corpora_dir / "euvsdisinfo"
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / "euvsdisinfo_base.csv"
    logger.info("euvsdisinfo downloading base CSV from Zenodo (CC-BY-4.0)")
    response = get(ZENODO_URL, timeout=120)
    target.write_bytes(response.content)
    logger.info("euvsdisinfo base saved (%d bytes)", target.stat().st_size)
    return target


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), "%d-%m-%Y").replace(tzinfo=UTC)
    except (ValueError, TypeError):
        return None


def csv_to_records(csv_path: Path, limit: int | None = None) -> list[RawRecord]:
    records = []
    with csv_path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            records.append(RawRecord(
                raw_source="euvsdisinfo",
                headline="",  # filled by enrichment (article title)
                url=(row.get("article_url") or "").strip() or None,
                publish_date=_parse_date(row.get("debunk_date")),
                language=to_code(row.get("article_language")),
                source_domain=(row.get("article_domain") or "").strip() or None,
                raw_source_id=row.get("article_id"),
                extras={
                    "debunk_id": row.get("debunk_id"),
                    "keywords": row.get("keywords", ""),
                    "class": row.get("class"),  # disinformation | trustworthy
                    "article_publisher": row.get("article_publisher"),
                    "label_source": "euvsdisinfo",
                    "debunk_date_raw": row.get("debunk_date"),
                    "text_fetched": False,
                },
            ))
            if limit and len(records) >= limit:
                break
    return records


def load_euvsdisinfo(corpora_dir: Path, limit: int | None = None) -> list[RawRecord]:
    path = corpora_dir / "euvsdisinfo" / "euvsdisinfo_base.csv"
    if not path.exists():
        logger.warning("euvsdisinfo missing %s — run download first", path)
        return []
    records = csv_to_records(path, limit=limit)
    logger.info("euvsdisinfo: %d labeled cases loaded", len(records))
    return records
