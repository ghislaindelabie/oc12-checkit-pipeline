"""Weekly fact-check label refresh: the ClaimReview aggregate dump is
republished continuously upstream — a weekly re-download keeps the label-join
surface fresh (dump-preferred rule: no per-query API, no permanent-DB ToS
issue). The raw snapshot is REPLACED (not appended): record identity is
(url + claim), so the downstream load stays idempotent either way.
"""

from datetime import datetime, timedelta, timezone

from airflow.sdk import dag, task


@dag(
    dag_id="checkit_factcheck_weekly",
    schedule="@weekly",
    start_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(hours=1),
    default_args={"retries": 3, "retry_delay": timedelta(minutes=5)},
    tags=["checkit", "factcheck"],
)
def checkit_factcheck_weekly():

    @task
    def refresh_claimreview() -> str:
        from checkit.config import Settings
        from checkit.corpus.claimreview import download_claimreview, load_claimreview
        from checkit.storage import append_jsonl, raw_path

        settings = Settings()
        settings.ensure_dirs()
        download_claimreview(settings.corpora_dir)
        records = load_claimreview(settings.corpora_dir)
        path = raw_path(settings.raw_dir, "claimreview", "snapshot")
        path.unlink(missing_ok=True)
        count = append_jsonl(records, path)
        print(f"claimreview refreshed: {count} verdicts")
        return str(path)

    refresh_claimreview()


checkit_factcheck_weekly()
