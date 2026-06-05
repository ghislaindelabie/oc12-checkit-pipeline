"""Fakeddit metadata downloader (decision #4: full metadata, sampled images).

Multimodal TSVs come from the official Google Drive folder. Label semantics
(2/3/6-way integer conventions) are deliberately NOT interpreted here — raw
values land in extras and the transform step resolves them against the paper's
documented mapping. No LICENSE file upstream: research-use-by-convention,
non-commercial only, never redistribute (see research/sweep/labeled-datasets.md).
"""

import csv
import logging
from pathlib import Path

from checkit.schema import RawRecord

# viral rows here too can exceed the default csv field limit
csv.field_size_limit(64 * 1024 * 1024)

logger = logging.getLogger(__name__)

DRIVE_FOLDER_ID = "1jU7qgDqU1je9Y0PMKJ_f31yXRo5uWGFm"
MULTIMODAL_FILES = ["multimodal_train.tsv", "multimodal_validate.tsv",
                    "multimodal_test_public.tsv"]


def download_fakeddit(corpora_dir: Path) -> Path:
    import gdown

    dest = corpora_dir / "fakeddit"
    dest.mkdir(parents=True, exist_ok=True)
    logger.info("fakeddit downloading metadata folder to %s", dest)
    gdown.download_folder(id=DRIVE_FOLDER_ID, output=str(dest), quiet=False,
                          skip_download=False, resume=True)
    return dest


def tsv_to_records(tsv_path: Path, split: str, limit: int | None = None) -> list[RawRecord]:
    records = []
    with tsv_path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            if row.get("hasImage", "").lower() != "true" or not row.get("image_url"):
                continue
            records.append(RawRecord(
                raw_source="fakeddit",
                headline=row.get("clean_title") or row.get("title", ""),
                url=f"https://www.reddit.com/comments/{row['id']}" if row.get("id") else None,
                image_url=row.get("image_url"),
                publish_date=None if not row.get("created_utc")
                             else _from_epoch(row["created_utc"]),
                language="en",
                raw_source_id=row.get("id"),
                extras={
                    "split": split,
                    "subreddit": row.get("subreddit"),
                    "domain": row.get("domain"),
                    "label_2way_raw": row.get("2_way_label"),
                    "label_3way_raw": row.get("3_way_label"),
                    "label_6way_raw": row.get("6_way_label"),
                    "label_source": "fakeddit-distant",
                },
            ))
            if limit and len(records) >= limit:
                break
    return records


def _from_epoch(value: str):
    from datetime import UTC, datetime
    try:
        return datetime.fromtimestamp(float(value), tz=UTC)
    except (ValueError, TypeError):
        return None


def load_fakeddit(corpora_dir: Path, limit_per_split: int | None = None) -> list[RawRecord]:
    records = []
    for filename in MULTIMODAL_FILES:
        # the Drive folder nests TSVs under multimodal_only_samples/
        path = corpora_dir / "fakeddit" / "multimodal_only_samples" / filename
        if not path.exists():
            path = corpora_dir / "fakeddit" / filename
        if not path.exists():
            logger.warning("fakeddit missing %s — run download first", filename)
            continue
        split = filename.replace("multimodal_", "").replace(".tsv", "")
        loaded = tsv_to_records(path, split=split, limit=limit_per_split)
        logger.info("fakeddit %s: %d multimodal records", split, len(loaded))
        records.extend(loaded)
    return records
