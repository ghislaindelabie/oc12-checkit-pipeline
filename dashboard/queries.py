"""Data access + KPI computation for the dashboard — kept UI-free so the
KPI logic is unit-testable. All reads go through the read-only
dashboard_reader role.
"""

import json

import pandas as pd
import psycopg

METRICS_SQL = """
    SELECT run_id, run_at, dag_id, rows_processed, rows_loaded, rows_skipped,
           valid_rate, pairing_strict, pairing_declared,
           dup_removed_id, dup_removed_text, duration_s, per_source
    FROM pipeline_metrics
    ORDER BY run_at
"""

LABELS_SQL = """
    SELECT label, count(*) AS n
    FROM articles
    GROUP BY label
"""

SOURCES_SQL = """
    SELECT raw_source, label, count(*) AS n,
           avg(paired_ok::int) AS pairing_strict_rate
    FROM articles
    GROUP BY raw_source, label
"""


def fetch_df(dsn: str, sql: str) -> pd.DataFrame:
    with psycopg.connect(dsn) as conn:
        cur = conn.execute(sql)
        columns = [d.name for d in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=columns)


def kpis_from_metrics(metrics: pd.DataFrame) -> dict | None:
    """Headline cards: latest run's KPIs + delta against the previous run."""
    if metrics.empty:
        return None
    latest = metrics.iloc[-1]
    previous = metrics.iloc[-2] if len(metrics) > 1 else None

    def delta(column: str):
        if previous is None:
            return None
        return float(latest[column]) - float(previous[column])

    duration = float(latest.duration_s) if pd.notna(latest.duration_s) else None
    rows_per_s = (round(latest.rows_processed / duration, 1)
                  if duration and duration > 0 else None)
    return {
        "run_at": latest.run_at,
        "dag_id": latest.dag_id,
        "rows_loaded": int(latest.rows_loaded),
        "rows_loaded_delta": delta("rows_loaded"),
        "valid_rate": float(latest.valid_rate),
        "valid_rate_delta": delta("valid_rate"),
        "pairing_declared": float(latest.pairing_declared),
        "pairing_strict": float(latest.pairing_strict),
        "pairing_delta": delta("pairing_declared"),
        "duration_s": duration,
        "rows_per_s": rows_per_s,
    }


def per_source_of_latest(metrics: pd.DataFrame) -> pd.DataFrame:
    """Per-source counts of the latest run (stored as JSONB in the row)."""
    if metrics.empty:
        return pd.DataFrame(columns=["source", "count", "valid"])
    raw = metrics.iloc[-1].per_source
    data = raw if isinstance(raw, dict) else json.loads(raw or "{}")
    rows = [{"source": source,
             "count": stats.get("count", 0),
             "valid": stats.get("valid", 0)}
            for source, stats in data.items()]
    return pd.DataFrame(rows).sort_values("count", ascending=False)
