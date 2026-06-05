"""One-time corpus acquisition (evergreen datasets): triggered manually.

Downloads are resumable/idempotent (skip if already on disk); the loaders
re-emit the raw JSONL layer. The daily DAG's transform->load chain then
picks the records up. Kept separate from the daily DAG because the corpus
layer is static content with a one-shot lifecycle (schedule=None: run on
demand, e.g. on a fresh machine).
"""

from datetime import datetime, timedelta, timezone

from airflow.sdk import dag, task


@dag(
    dag_id="checkit_corpus_once",
    schedule=None,
    start_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
    catchup=False,
    dagrun_timeout=timedelta(hours=6),
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["checkit", "corpus"],
)
def checkit_corpus_once():

    @task
    def fakenewsnet() -> str:
        from checkit.config import Settings
        from checkit.corpus.fakenewsnet import download_fakenewsnet, load_fakenewsnet
        from checkit.storage import append_jsonl, raw_path

        settings = Settings()
        settings.ensure_dirs()
        target = settings.corpora_dir / "fakenewsnet"
        if not (target / "politifact_fake.csv").exists():
            download_fakenewsnet(settings.corpora_dir)
        records = load_fakenewsnet(settings.corpora_dir)
        path = raw_path(settings.raw_dir, "fakenewsnet", "snapshot")
        path.unlink(missing_ok=True)
        append_jsonl(records, path)
        return str(path)

    @task
    def fakeddit() -> str:
        from checkit.config import Settings
        from checkit.corpus.fakeddit import download_fakeddit, load_fakeddit
        from checkit.storage import append_jsonl, raw_path

        settings = Settings()
        settings.ensure_dirs()
        marker = settings.corpora_dir / "fakeddit" / "multimodal_only_samples"
        if not marker.exists():
            download_fakeddit(settings.corpora_dir)
        records = load_fakeddit(settings.corpora_dir)
        path = raw_path(settings.raw_dir, "fakeddit", "snapshot")
        path.unlink(missing_ok=True)
        append_jsonl(records, path)
        return str(path)

    @task
    def dgm4() -> str:
        from checkit.config import Settings
        from checkit.corpus.dgm4 import download_dgm4, load_dgm4
        from checkit.storage import append_jsonl, raw_path

        settings = Settings()
        settings.ensure_dirs()
        marker = settings.corpora_dir / "dgm4" / "metadata" / "train.json"
        if not marker.exists():
            download_dgm4(settings.corpora_dir)
        records = load_dgm4(settings.corpora_dir)
        path = raw_path(settings.raw_dir, "dgm4", "snapshot")
        path.unlink(missing_ok=True)
        append_jsonl(records, path)
        return str(path)

    [fakenewsnet(), fakeddit(), dgm4()]


checkit_corpus_once()
