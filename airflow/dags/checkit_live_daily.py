"""Daily live-acquisition ETL: extract (RSS + Bluesky + keyed APIs) ->
transform -> quality gate -> load into the secured PostgreSQL.

Design (per the project blueprint):
- thin @task functions that DELEGATE to the tested checkit package;
- XCom carries file-path strings only, never payloads;
- the extraction window IS the DAG run's data interval;
- quality gate raises (aborting the load) if valid_rate < 0.5;
- idempotent load (ON CONFLICT DO NOTHING) -> safe to re-trigger live.
GDELT is excluded until its FR query is tuned (KNOWN_ISSUES.md).
"""

from datetime import datetime, timedelta, timezone

from airflow.sdk import dag, task

DEFAULT_ARGS = {
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
}


@dag(
    dag_id="checkit_live_daily",
    schedule="@daily",
    start_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(hours=1),
    default_args=DEFAULT_ARGS,
    tags=["checkit", "live"],
)
def checkit_live_daily():

    @task
    def extract_live(data_interval_start=None, data_interval_end=None) -> str:
        import argparse

        from checkit.config import Settings
        from checkit.extract.__main__ import extract
        from checkit.storage import append_jsonl, raw_path

        # Airflow 3: MANUAL runs carry no data interval (None) — fall back
        # to a last-24h window so ad-hoc triggers behave like the CLI
        end = data_interval_end or datetime.now(timezone.utc)
        start = data_interval_start or end - timedelta(hours=24)

        settings = Settings()
        settings.ensure_dirs()
        run_date = end.strftime("%Y-%m-%d")
        written = 0
        for source in ("rss", "bluesky", "keyed"):
            args = argparse.Namespace(
                source=source, query="désinformation fake news",
                date_from=start, date_to=end,
                limit=100, probe=False)
            records = [r for r in extract(args, settings) if r.image_url]
            written += append_jsonl(records, raw_path(settings.raw_dir, source, run_date))
        print(f"extracted {written} paired records for window {start} -> {end}")
        return str(Settings().raw_dir)

    @task
    def transform(raw_dir: str) -> str:
        from checkit.config import Settings
        from checkit.transform.pipeline import run

        settings = Settings()
        run(raw_dir=settings.raw_dir, out_dir=settings.processed_dir,
            images_dir=settings.images_dir, image_mode="live")
        return str(settings.processed_dir / "run_report.json")

    @task
    def quality_gate(report_path: str) -> str:
        from pathlib import Path

        from checkit.load import quality_gate as gate

        gate(Path(report_path), min_valid_rate=0.5)
        return report_path

    @task
    def load(report_path: str) -> None:
        from pathlib import Path

        from checkit.config import Settings
        from checkit.load import load_parquet, record_metrics

        settings = Settings()
        dsn = settings.database_url.get_secret_value()
        stats = load_parquet(settings.processed_dir / "dataset.parquet", dsn,
                             settings.enc_key.get_secret_value())
        record_metrics(Path(report_path), stats, dsn, dag_id="checkit_live_daily")

    load(quality_gate(transform(extract_live())))


checkit_live_daily()
