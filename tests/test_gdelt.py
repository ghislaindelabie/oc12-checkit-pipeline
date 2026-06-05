import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import responses

from checkit.extract import gdelt_client
from checkit.extract.gdelt_client import GDELT_DOC_URL, fetch_gdelt

FIXTURE = Path(__file__).parent / "fixtures" / "gdelt_artlist.json"


@pytest.fixture(autouse=True)
def no_throttle(monkeypatch):
    monkeypatch.setattr(gdelt_client, "GDELT_MIN_INTERVAL", 0.0)


@responses.activate
def test_fetch_maps_articles_to_raw_records():
    responses.get(GDELT_DOC_URL, json=json.loads(FIXTURE.read_text()))
    records = fetch_gdelt(query="inondations sourcelang:fre")
    assert len(records) == 2
    first = records[0]
    assert first.raw_source == "gdelt-doc"
    assert first.headline.startswith("Inondations")
    assert first.image_url == "https://www.exemple-presse.fr/img/inondations.jpg"
    assert first.source_domain == "exemple-presse.fr"
    assert first.language == "fr"
    assert first.publish_date == datetime(2026, 6, 4, 21, 30, tzinfo=UTC)
    assert first.extras["sourcecountry"] == "France"


@responses.activate
def test_empty_socialimage_becomes_none():
    responses.get(GDELT_DOC_URL, json=json.loads(FIXTURE.read_text()))
    records = fetch_gdelt(query="flood")
    assert records[1].image_url is None
    assert records[1].language == "en"


@responses.activate
def test_window_serialized_in_gdelt_datetime_format():
    responses.get(GDELT_DOC_URL, json={"articles": []})
    fetch_gdelt(query="q",
                start=datetime(2026, 6, 4, 0, 0, tzinfo=UTC),
                end=datetime(2026, 6, 5, 0, 0, tzinfo=UTC))
    params = responses.calls[0].request.params
    assert params["startdatetime"] == "20260604000000"
    assert params["enddatetime"] == "20260605000000"
    assert params["mode"] == "ArtList"
    assert params["format"] == "json"


@responses.activate
def test_non_json_response_returns_empty_list_not_crash():
    responses.get(GDELT_DOC_URL, body="Rate limit exceeded", status=200,
                  content_type="text/plain")
    assert fetch_gdelt(query="q") == []
