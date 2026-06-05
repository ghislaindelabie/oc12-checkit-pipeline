from datetime import UTC, datetime

from checkit.schema import RawRecord


def test_record_id_is_deterministic_over_url_and_image():
    a = RawRecord(raw_source="test", headline="t", url="https://ex.fr/a",
                  image_url="https://ex.fr/i.jpg")
    b = RawRecord(raw_source="test", headline="t", url="https://ex.fr/a",
                  image_url="https://ex.fr/i.jpg")
    assert a.record_id == b.record_id


def test_record_id_changes_when_image_changes():
    a = RawRecord(raw_source="test", headline="t", url="https://ex.fr/a",
                  image_url="https://ex.fr/i1.jpg")
    b = RawRecord(raw_source="test", headline="t", url="https://ex.fr/a",
                  image_url="https://ex.fr/i2.jpg")
    assert a.record_id != b.record_id


def test_record_id_falls_back_to_source_and_native_id_without_url():
    a = RawRecord(raw_source="dataset", headline="t", raw_source_id="row-42")
    b = RawRecord(raw_source="dataset", headline="t", raw_source_id="row-42")
    assert a.record_id == b.record_id


def test_source_domain_derived_from_url():
    r = RawRecord(raw_source="test", headline="t",
                  url="https://www.exemple-presse.fr/articles/a1")
    assert r.source_domain == "www.exemple-presse.fr"


def test_publish_date_normalized_to_utc():
    r = RawRecord(raw_source="test", headline="t", url="https://ex.fr/a",
                  publish_date=datetime(2026, 6, 4, 23, 0, tzinfo=UTC))
    assert r.publish_date.tzinfo is not None
    assert r.publish_date.utcoffset().total_seconds() == 0


def test_crawl_date_is_set_and_aware():
    r = RawRecord(raw_source="test", headline="t", url="https://ex.fr/a")
    assert r.crawl_date.tzinfo is not None


def test_extras_roundtrip_through_json():
    r = RawRecord(raw_source="test", headline="t", url="https://ex.fr/a",
                  extras={"sourcecountry": "France", "themes": ["FLOOD"]})
    restored = RawRecord.model_validate_json(r.model_dump_json())
    assert restored.extras["themes"] == ["FLOOD"]
    assert restored.record_id == r.record_id
