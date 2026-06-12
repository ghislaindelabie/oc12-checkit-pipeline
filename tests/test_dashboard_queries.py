import json
from datetime import UTC, datetime

import pandas as pd

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dashboard"))
from queries import kpis_from_metrics, per_source_of_latest  # noqa: E402


def metrics_frame(rows):
    return pd.DataFrame(rows, columns=[
        "run_id", "run_at", "dag_id", "rows_processed", "rows_loaded",
        "rows_skipped", "valid_rate", "pairing_strict", "pairing_declared",
        "dup_removed_id", "dup_removed_text", "duration_s", "per_source"])


def row(run_id, loaded, valid, declared, duration=100.0, per_source="{}"):
    return (run_id, datetime(2026, 6, 5, 12, run_id, tzinfo=UTC), "dag",
            1000, loaded, 1000 - loaded, valid, 0.25, declared, 1, 2,
            duration, per_source)


def test_empty_metrics_yield_none():
    assert kpis_from_metrics(metrics_frame([])) is None


def test_single_run_has_no_deltas():
    kpis = kpis_from_metrics(metrics_frame([row(1, 900, 0.97, 0.96)]))
    assert kpis["rows_loaded"] == 900
    assert kpis["rows_loaded_delta"] is None
    assert kpis["valid_rate_delta"] is None


def test_deltas_computed_against_previous_run():
    kpis = kpis_from_metrics(metrics_frame([
        row(1, 900, 0.95, 0.90), row(2, 950, 0.97, 0.96)]))
    assert kpis["rows_loaded"] == 950
    assert kpis["rows_loaded_delta"] == 50
    assert round(kpis["valid_rate_delta"], 4) == 0.02


def test_rows_per_second_derived_from_duration():
    kpis = kpis_from_metrics(metrics_frame([row(1, 900, 0.97, 0.96, duration=50.0)]))
    assert kpis["rows_per_s"] == 20.0


def test_per_source_of_latest_parses_jsonb():
    per_source = json.dumps({"rss:franceinfo": {"count": 30, "valid": 30},
                             "dgm4": {"count": 230000, "valid": 230000}})
    frame = per_source_of_latest(metrics_frame([row(1, 1, 1, 1, per_source=per_source)]))
    assert list(frame.iloc[0][["source", "count"]]) == ["dgm4", 230000]
    assert len(frame) == 2


def test_per_source_empty_metrics():
    assert per_source_of_latest(metrics_frame([])).empty
