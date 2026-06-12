from pathlib import Path

from checkit.corpus.euvsdisinfo import csv_to_records

FIXTURE = Path(__file__).parent / "fixtures" / "euvsdisinfo_base.csv"


def test_rows_mapped_with_class_kept_raw():
    records = csv_to_records(FIXTURE)
    assert len(records) == 4
    first = records[0]
    assert first.raw_source == "euvsdisinfo"
    assert first.url == "https://rt.com/article-1"
    assert first.source_domain == "rt.com"
    assert first.language == "en"
    assert first.raw_source_id == "a1"
    assert first.extras["class"] == "disinformation"
    assert first.extras["label_source"] == "euvsdisinfo"
    assert first.extras["debunk_id"] == "EUVS-1"
    assert "Ukraine" in first.extras["keywords"]


def test_trustworthy_class_preserved():
    records = csv_to_records(FIXTURE)
    assert records[1].extras["class"] == "trustworthy"


def test_debunk_date_parsed_ddmmyyyy():
    records = csv_to_records(FIXTURE)
    assert records[0].publish_date.year == 2026
    assert records[0].publish_date.month == 3
    assert records[0].publish_date.day == 15


def test_russian_language_mapped():
    records = csv_to_records(FIXTURE)
    assert records[2].language == "ru"


def test_row_without_url_kept_with_null_url():
    records = csv_to_records(FIXTURE)
    assert records[3].url is None
    assert records[3].record_id  # identity falls back to source + article_id


def test_identity_deterministic():
    a = csv_to_records(FIXTURE)
    b = csv_to_records(FIXTURE)
    assert [r.record_id for r in a] == [r.record_id for r in b]


def test_pre_enrichment_records_have_no_text_yet():
    # base file carries only labeled URLs; text/image come from enrichment
    records = csv_to_records(FIXTURE)
    assert all(not r.headline for r in records)
    assert all(r.image_url is None for r in records)
