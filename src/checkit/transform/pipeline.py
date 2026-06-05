"""Transform pipeline — stages: lecture / traitement / export.

Reads the raw JSONL layer, applies cleaning + label normalization + pairing
qualification + deduplication, exports Parquet + CSV index, and emits a
RunReport (the numbers the Airflow quality gate and the dashboard consume).
Every stage logs what it did (journalisation requirement).
"""

import json
import logging
import time
from collections import Counter
from pathlib import Path

import pandas as pd

from checkit.schema import RawRecord
from checkit.transform import labels as labels_mod
from checkit.transform.cleaning import nettoie_texte, text_fingerprint
from checkit.transform.images import valide_image
from checkit.transform.labels import normalize_label
from checkit.transform.schema_out import CleanRecord

logger = logging.getLogger(__name__)

LIVE_SOURCES_PREFIXES = ("rss:", "api:", "bluesky", "gdelt")


# ---------- lecture ----------

def read_raw(raw_dir: Path, sources: list[str] | None = None,
             limit_per_source: int | None = None):
    """Yield (RawRecord, source_dir_name) across the raw layer."""
    bad_lines = 0
    for source_dir in sorted(p for p in raw_dir.iterdir() if p.is_dir()):
        name = source_dir.name
        if sources and name not in sources:
            continue
        count = 0
        for jsonl in sorted(source_dir.glob("*.jsonl")):
            with jsonl.open(encoding="utf-8") as fh:
                for line in fh:
                    if limit_per_source and count >= limit_per_source:
                        break
                    try:
                        yield RawRecord.model_validate_json(line), name
                        count += 1
                    except Exception:
                        bad_lines += 1
        logger.info("lecture %s: %d records", name, count)
    if bad_lines:
        logger.warning("lecture: %d unparseable lines skipped", bad_lines)


# ---------- traitement ----------

def is_live(raw_source: str) -> bool:
    return raw_source.startswith(LIVE_SOURCES_PREFIXES)


def transform_record(record: RawRecord, image_mode: str, images_dir: Path) -> CleanRecord:
    errors: list[str] = []
    headline = nettoie_texte(record.headline) or ""
    if not headline:
        errors.append("empty-headline")

    verdict = normalize_label(record)

    # pairing qualification (decision #10 + KPI definition)
    local_path = image_hash = image_phash = None
    if record.raw_source == "dgm4":
        basis = "bundled"  # images ship inside the corpus zips
        local_path = record.extras.get("image_path") or None
    elif record.image_url:
        basis = "declared"
        if image_mode == "live" and is_live(record.raw_source):
            result = valide_image(record.image_url, images_dir)
            if "error" in result:
                basis = "none"
                errors.append(f"image-{result['error']}")
            else:
                basis = "validated"
                local_path = result["local_image_path"]
                image_hash = result["image_hash"]
                image_phash = result["image_phash"]
    else:
        basis = "none"

    paired = basis in ("validated", "bundled", "declared")
    is_label_feed = record.raw_source == "claimreview"
    if not paired and not is_label_feed:
        errors.append("not-paired")

    # a content record must have a headline and a pairing; a label-feed record
    # (claimreview) must have a headline (the claim) and a verdict url
    valid = bool(headline) and (paired or (is_label_feed and record.url is not None))

    return CleanRecord(
        record_id=record.record_id,
        raw_source=record.raw_source,
        headline=headline,
        body_text=nettoie_texte(record.body_text),
        caption=nettoie_texte(record.caption),
        url=record.url,
        source_domain=record.source_domain,
        image_url=record.image_url,
        local_image_path=local_path,
        image_hash=image_hash,
        image_phash=image_phash,
        paired_ok=basis in ("validated", "bundled"),
        pairing_basis=basis,
        label=verdict.label,
        fine_grained_label=verdict.fine_grained,
        label_source=verdict.source,
        label_confidence=verdict.confidence,
        ambiguous=verdict.ambiguous,
        language=record.language,
        publish_date=record.publish_date,
        crawl_date=record.crawl_date,
        raw_source_id=record.raw_source_id,
        text_fingerprint=text_fingerprint(headline, record.body_text),
        is_valid=valid,
        validation_errors=errors,
    )


def dedup(records: list[CleanRecord]) -> tuple[list[CleanRecord], dict]:
    """Exact dedup on record_id, then on (text_fingerprint, image identity)."""
    seen_ids: set[str] = set()
    seen_content: set[tuple] = set()
    kept: list[CleanRecord] = []
    by_id = by_content = 0
    for record in records:
        if record.record_id in seen_ids:
            by_id += 1
            continue
        seen_ids.add(record.record_id)
        content_key = (record.text_fingerprint,
                       record.image_hash or record.image_url
                       or record.local_image_path or "")
        if content_key in seen_content:
            by_content += 1
            continue
        seen_content.add(content_key)
        kept.append(record)
    logger.info("traitement dedup: -%d by id, -%d by content", by_id, by_content)
    return kept, {"dup_by_id": by_id, "dup_by_content": by_content}


# ---------- export ----------

def export(records: list[CleanRecord], out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame([r.model_dump() for r in records])
    parquet_path = out_dir / "dataset.parquet"
    frame.to_parquet(parquet_path, engine="pyarrow", index=False)

    index_path = out_dir / "dataset_index.csv"
    index_cols = ["record_id", "raw_source", "label", "fine_grained_label",
                  "paired_ok", "pairing_basis", "language", "is_valid"]
    index = frame[index_cols].copy()
    index["headline"] = frame["headline"].str.slice(0, 80)
    index.to_csv(index_path, index=False)
    logger.info("export: %d rows -> %s (+ index csv)", len(frame), parquet_path)
    return {"parquet": str(parquet_path), "csv_index": str(index_path),
            "rows": len(frame)}


def run_report(records: list[CleanRecord], dup_stats: dict, exported: dict,
               started: float) -> dict:
    per_source: dict[str, dict] = {}
    for record in records:
        stats = per_source.setdefault(record.raw_source, Counter())
        stats["count"] += 1
        stats["valid"] += int(record.is_valid)
        stats["paired_strict"] += int(record.paired_ok)
        stats["paired_declared"] += int(record.pairing_basis != "none")
        stats[f"label:{record.label}"] += 1
    content = [r for r in records if r.raw_source != "claimreview"]
    report = {
        "rows": exported["rows"],
        "valid_rate": round(sum(r.is_valid for r in records) / max(len(records), 1), 4),
        "pairing_rate_strict": round(sum(r.paired_ok for r in content) / max(len(content), 1), 4),
        "pairing_rate_declared": round(
            sum(r.pairing_basis != "none" for r in content) / max(len(content), 1), 4),
        "dup_removed": dup_stats,
        "per_source": {k: dict(v) for k, v in sorted(per_source.items())},
        "unmapped_ratings_top": labels_mod.unmapped_ratings.most_common(15),
        "unmapped_ratings_total": sum(labels_mod.unmapped_ratings.values()),
        "duration_s": round(time.monotonic() - started, 1),
        "outputs": exported,
    }
    return report


def run(raw_dir: Path, out_dir: Path, images_dir: Path, image_mode: str = "live",
        sources: list[str] | None = None, limit_per_source: int | None = None) -> dict:
    started = time.monotonic()
    labels_mod.unmapped_ratings.clear()

    cleaned = [transform_record(record, image_mode, images_dir)
               for record, _ in read_raw(raw_dir, sources, limit_per_source)]
    logger.info("traitement: %d records transformed", len(cleaned))

    kept, dup_stats = dedup(cleaned)
    exported = export(kept, out_dir)
    report = run_report(kept, dup_stats, exported, started)

    report_path = out_dir / "run_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    logger.info("run report -> %s (valid_rate=%s, pairing strict=%s declared=%s)",
                report_path, report["valid_rate"], report["pairing_rate_strict"],
                report["pairing_rate_declared"])
    return report
