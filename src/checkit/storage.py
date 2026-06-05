from collections.abc import Iterable
from pathlib import Path

from checkit.schema import RawRecord


def raw_path(root: Path, source: str, run_date: str) -> Path:
    return root / source / f"{run_date}.jsonl"


def append_jsonl(records: Iterable[RawRecord], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("a", encoding="utf-8") as fh:
        for record in records:
            fh.write(record.model_dump_json() + "\n")
            count += 1
    return count
