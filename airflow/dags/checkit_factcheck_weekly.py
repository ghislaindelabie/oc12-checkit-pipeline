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

    @task
    def refresh_webz() -> str:
        from checkit.config import Settings
        from checkit.corpus.webz_fakenews import download_webz, load_webz
        from checkit.storage import append_jsonl, raw_path

        settings = Settings()
        settings.ensure_dirs()
        download_webz(settings.corpora_dir)  # incremental: new drops only
        records = load_webz(settings.corpora_dir)
        path = raw_path(settings.raw_dir, "webz-fakenews", "snapshot")
        path.unlink(missing_ok=True)
        count = append_jsonl(records, path)
        print(f"webz refreshed: {count} records")
        return str(path)

    @task
    def refresh_euvsdisinfo() -> str:
        from checkit.config import Settings
        from checkit.corpus.enrich import enrich_records
        from checkit.corpus.euvsdisinfo import download_euvsdisinfo, load_euvsdisinfo
        from checkit.storage import append_jsonl, raw_path

        settings = Settings()
        settings.ensure_dirs()
        download_euvsdisinfo(settings.corpora_dir)  # frozen snapshot; idempotent downstream
        records = load_euvsdisinfo(settings.corpora_dir)
        enrich_records(records)  # fetch article text+image (rot logged)
        path = raw_path(settings.raw_dir, "euvsdisinfo", "snapshot")
        path.unlink(missing_ok=True)
        count = append_jsonl(records, path)
        print(f"euvsdisinfo refreshed: {count} cases")
        return str(path)

    [refresh_claimreview(), refresh_webz(), refresh_euvsdisinfo()]


checkit_factcheck_weekly()
