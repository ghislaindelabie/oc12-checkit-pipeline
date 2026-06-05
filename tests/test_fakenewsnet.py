from pathlib import Path

import responses

from checkit.corpus.fakenewsnet import (
    FAKENEWSNET_FILES,
    csv_to_records,
    download_fakenewsnet,
)

SAMPLE_CSV = """id,news_url,title,tweet_ids
politifact14064,speedtalk.proboards.com/thread/4160/donald-lifelong-democrat,BREAKING: First NFL Team Declares Bankruptcy Over Kneeling Thugs,937349434668498944\t937379378006282240
politifact15371,https://www.nscdscamps.org/blog/category/awareness/,Court Orders Obama To Pay $400 Million In Restitution,972666281441878016
politifact14355,,Empty url row must be kept without url,
"""


def test_csv_to_records_maps_labels_and_provenance(tmp_path):
    csv_path = tmp_path / "politifact_fake.csv"
    csv_path.write_text(SAMPLE_CSV, encoding="utf-8")
    records = csv_to_records(csv_path, label="fake", label_source="politifact")
    assert len(records) == 3
    first = records[0]
    assert first.raw_source == "fakenewsnet"
    assert first.raw_source_id == "politifact14064"
    assert first.headline.startswith("BREAKING")
    assert first.extras["label"] == "fake"
    assert first.extras["label_source"] == "politifact"
    assert first.image_url is None  # images come from the later screen step


def test_scheme_less_urls_are_normalized():
    records = csv_to_records_from_text()
    assert records[0].url.startswith("http://")
    assert records[1].url == "https://www.nscdscamps.org/blog/category/awareness/"


def csv_to_records_from_text(tmp_path=None):
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "x.csv"
        p.write_text(SAMPLE_CSV, encoding="utf-8")
        return csv_to_records(p, label="fake", label_source="politifact")


def test_row_without_url_kept_with_null_url():
    records = csv_to_records_from_text()
    assert records[2].url is None
    assert records[2].record_id  # identity falls back to source + native id


def test_registry_covers_both_fact_checkers_and_labels():
    names = {(f.label_source, f.label) for f in FAKENEWSNET_FILES}
    assert names == {("politifact", "fake"), ("politifact", "real"),
                     ("gossipcop", "fake"), ("gossipcop", "real")}


def test_huge_tweet_ids_field_does_not_break_csv_parsing(tmp_path):
    # real gossipcop rows exceed the 131072-byte default csv field limit
    huge = "\t".join(str(900000000000000000 + i) for i in range(20000))
    csv_path = tmp_path / "big.csv"
    csv_path.write_text(
        f"id,news_url,title,tweet_ids\ngossipcop1,https://ex.com/a,Viral story,{huge}\n",
        encoding="utf-8")
    records = csv_to_records(csv_path, label="fake", label_source="gossipcop")
    assert records[0].extras["tweet_count"] == 20000


@responses.activate
def test_download_writes_csvs_and_returns_paths(tmp_path):
    for f in FAKENEWSNET_FILES:
        responses.get(f.url, body=SAMPLE_CSV)
    paths = download_fakenewsnet(tmp_path)
    assert len(paths) == 4
    assert all(p.exists() and p.stat().st_size > 0 for p in paths)
    assert (tmp_path / "fakenewsnet" / "politifact_fake.csv") in paths
