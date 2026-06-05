import json

from checkit.schema import RawRecord
from checkit.storage import append_jsonl, raw_path


def rec(i: int) -> RawRecord:
    return RawRecord(raw_source="test", headline=f"títre n°{i} — éàç",
                     url=f"https://ex.fr/{i}", image_url=f"https://ex.fr/{i}.jpg")


def test_append_returns_count_and_writes_one_line_per_record(tmp_path):
    path = tmp_path / "out.jsonl"
    n = append_jsonl([rec(1), rec(2)], path)
    assert n == 2
    assert len(path.read_text(encoding="utf-8").splitlines()) == 2


def test_successive_appends_accumulate(tmp_path):
    path = tmp_path / "out.jsonl"
    append_jsonl([rec(1)], path)
    append_jsonl([rec(2), rec(3)], path)
    assert len(path.read_text(encoding="utf-8").splitlines()) == 3


def test_unicode_preserved_not_escaped_to_ascii(tmp_path):
    path = tmp_path / "out.jsonl"
    append_jsonl([rec(1)], path)
    line = path.read_text(encoding="utf-8").splitlines()[0]
    assert "títre n°1 — éàç" in json.loads(line)["headline"]


def test_parent_directories_created(tmp_path):
    path = tmp_path / "deep" / "nested" / "out.jsonl"
    append_jsonl([rec(1)], path)
    assert path.exists()


def test_raw_path_layout(tmp_path):
    p = raw_path(tmp_path, source="gdelt", run_date="2026-06-05")
    assert p == tmp_path / "gdelt" / "2026-06-05.jsonl"
