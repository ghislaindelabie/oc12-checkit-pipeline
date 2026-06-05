"""Load step: clean Parquet -> secured PostgreSQL (idempotent).

Untargeted ON CONFLICT DO NOTHING makes re-runs free AND absorbs re-crawls:
a live article re-fetched with a rotated image URL has a new record_id but
the same url — either unique constraint skips it (first version wins). Metrics from the
transform RunReport land in pipeline_metrics at the end of every load —
which is exactly what the Step 5 dashboard reads.
"""

import json
import logging
from pathlib import Path

import pandas as pd
import psycopg

logger = logging.getLogger(__name__)

INSERT_ARTICLE = """
INSERT INTO articles (
    record_id, raw_source, headline, body_text, caption, url, source_domain,
    image_url, local_image_path, image_hash, image_phash, paired_ok,
    pairing_basis, label, fine_grained_label, label_source, label_confidence,
    ambiguous, language, publish_date, crawl_date, raw_source_id,
    text_fingerprint, author_pseudo_enc, is_valid, validation_errors
) VALUES (
    %(record_id)s, %(raw_source)s, %(headline)s, %(body_text)s, %(caption)s,
    %(url)s, %(source_domain)s, %(image_url)s, %(local_image_path)s,
    %(image_hash)s, %(image_phash)s, %(paired_ok)s, %(pairing_basis)s,
    %(label)s, %(fine_grained_label)s, %(label_source)s, %(label_confidence)s,
    %(ambiguous)s, %(language)s, %(publish_date)s, %(crawl_date)s,
    %(raw_source_id)s, %(text_fingerprint)s,
    CASE WHEN %(author_pseudo_id)s::text IS NULL THEN NULL
         ELSE pgp_sym_encrypt(%(author_pseudo_id)s::text, %(enc_key)s::text) END,
    %(is_valid)s, %(validation_errors)s::jsonb
) ON CONFLICT DO NOTHING
"""

INSERT_METRICS = """
INSERT INTO pipeline_metrics (
    dag_id, rows_processed, rows_loaded, rows_skipped, valid_rate,
    pairing_strict, pairing_declared, dup_removed_id, dup_removed_text,
    duration_s, per_source
) VALUES (
    %(dag_id)s, %(rows_processed)s, %(rows_loaded)s, %(rows_skipped)s,
    %(valid_rate)s, %(pairing_strict)s, %(pairing_declared)s,
    %(dup_removed_id)s, %(dup_removed_text)s, %(duration_s)s, %(per_source)s
)
"""


def row_params(row: dict, enc_key: str) -> dict:
    errors = row.get("validation_errors")
    if hasattr(errors, "tolist"):  # numpy array out of parquet
        errors = errors.tolist()
    params = {k: (None if pd.isna(v) else v) if not isinstance(v, (list, dict))
              else v
              for k, v in row.items() if k != "validation_errors"}
    params["validation_errors"] = json.dumps(list(errors or []))
    params.setdefault("author_pseudo_id", None)
    params["enc_key"] = enc_key
    return params


def load_parquet(parquet_path: Path, dsn: str, enc_key: str,
                 only_valid: bool = True, batch_size: int = 5000) -> dict:
    frame = pd.read_parquet(parquet_path)
    total = len(frame)
    if only_valid:
        frame = frame[frame.is_valid]
    logger.info("load: %d rows read, %d valid to load", total, len(frame))

    loaded = 0
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            rows = frame.to_dict(orient="records")
            for start in range(0, len(rows), batch_size):
                batch = [row_params(r, enc_key) for r in rows[start:start + batch_size]]
                cur.executemany(INSERT_ARTICLE, batch)
                loaded += cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
        conn.commit()
    skipped = len(frame) - loaded
    logger.info("load: %d inserted, %d already present (idempotent skip)",
                loaded, skipped)
    return {"rows_processed": total, "rows_loaded": loaded, "rows_skipped": skipped}


def record_metrics(report_path: Path, load_stats: dict, dsn: str,
                   dag_id: str | None = None) -> None:
    report = json.loads(report_path.read_text())
    params = {
        "dag_id": dag_id,
        "rows_processed": load_stats["rows_processed"],
        "rows_loaded": load_stats["rows_loaded"],
        "rows_skipped": load_stats["rows_skipped"],
        "valid_rate": report["valid_rate"],
        "pairing_strict": report["pairing_rate_strict"],
        "pairing_declared": report["pairing_rate_declared"],
        "dup_removed_id": report["dup_removed"]["dup_by_id"],
        "dup_removed_text": report["dup_removed"]["dup_by_content"],
        "duration_s": report["duration_s"],
        "per_source": json.dumps(report["per_source"]),
    }
    with psycopg.connect(dsn) as conn:
        conn.execute(INSERT_METRICS, params)
        conn.commit()
    logger.info("metrics recorded (dag_id=%s)", dag_id)


def quality_gate(report_path: Path, min_valid_rate: float = 0.5) -> float:
    """The DAG aborts the load if transform quality collapsed."""
    report = json.loads(report_path.read_text())
    rate = report["valid_rate"]
    if rate < min_valid_rate:
        raise ValueError(
            f"quality gate: valid_rate {rate} < {min_valid_rate} — load aborted")
    logger.info("quality gate passed: valid_rate=%s >= %s", rate, min_valid_rate)
    return rate
