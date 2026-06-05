"""FakeNewsNet metadata downloader.

The public repo ships only metadata CSVs (id, news_url, title, tweet_ids) —
images and bodies must be fetched from the live article URLs, which rot.
That fetch is the screen step (decision #7): pairing yield is measured before
the corpus is admitted into the training set. Labels are human fact-checker
verdicts (PolitiFact, GossipCop) — the highest label_confidence tier.
"""

import csv
import logging
from dataclasses import dataclass
from pathlib import Path

# viral gossipcop rows carry >128KB of tweet_ids (default csv limit: 131072)
csv.field_size_limit(64 * 1024 * 1024)

from checkit.extract.http import get
from checkit.schema import RawRecord

logger = logging.getLogger(__name__)

_BASE = "https://raw.githubusercontent.com/KaiDMML/FakeNewsNet/master/dataset"


@dataclass(frozen=True)
class CorpusFile:
    filename: str
    label_source: str
    label: str

    @property
    def url(self) -> str:
        return f"{_BASE}/{self.filename}"


FAKENEWSNET_FILES = [
    CorpusFile("politifact_fake.csv", "politifact", "fake"),
    CorpusFile("politifact_real.csv", "politifact", "real"),
    CorpusFile("gossipcop_fake.csv", "gossipcop", "fake"),
    CorpusFile("gossipcop_real.csv", "gossipcop", "real"),
]


def _normalize_url(value: str) -> str | None:
    value = value.strip()
    if not value:
        return None
    if not value.startswith(("http://", "https://")):
        return f"http://{value}"
    return value


def csv_to_records(csv_path: Path, label: str, label_source: str) -> list[RawRecord]:
    records = []
    with csv_path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            records.append(RawRecord(
                raw_source="fakenewsnet",
                headline=row.get("title", ""),
                url=_normalize_url(row.get("news_url", "")),
                raw_source_id=row.get("id"),
                language="en",
                extras={
                    "label": label,
                    "label_source": label_source,
                    "fine_grained_label": f"{label_source}:{label}",
                    "tweet_count": len((row.get("tweet_ids") or "").split("\t"))
                                   if row.get("tweet_ids") else 0,
                },
            ))
    return records


def download_fakenewsnet(corpora_dir: Path) -> list[Path]:
    dest = corpora_dir / "fakenewsnet"
    dest.mkdir(parents=True, exist_ok=True)
    paths = []
    for corpus_file in FAKENEWSNET_FILES:
        target = dest / corpus_file.filename
        response = get(corpus_file.url, timeout=60)
        target.write_bytes(response.content)
        logger.info("fakenewsnet downloaded %s (%d bytes)", corpus_file.filename,
                    target.stat().st_size)
        paths.append(target)
    return paths


def load_fakenewsnet(corpora_dir: Path) -> list[RawRecord]:
    records = []
    for corpus_file in FAKENEWSNET_FILES:
        path = corpora_dir / "fakenewsnet" / corpus_file.filename
        if not path.exists():
            logger.warning("fakenewsnet missing %s — run download first", path.name)
            continue
        records.extend(csv_to_records(path, corpus_file.label, corpus_file.label_source))
    return records
