import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import responses

from checkit.config import Settings
from checkit.extract.news_apis import SPECS, fetch_news_api

FIXTURES = Path(__file__).parent / "fixtures" / "news_apis"

WINDOW = (datetime(2026, 6, 4, 0, 0, tzinfo=UTC), datetime(2026, 6, 5, 0, 0, tzinfo=UTC))

# adapter name -> (request param carrying the key, expected image url ending)
KEY_PARAMS = {
    "newsdata": ("apikey", "campagne.jpg"),
    "guardian": ("api-key", "500.jpg"),
    "gnews": ("apikey", "plateforme.jpg"),
    "currents": ("apiKey", "hebdo.png"),
    "mediastack": ("access_key", "montage.jpg"),
    "thenewsapi": ("api_token", "deepfake.jpg"),
    "worldnews": ("api-key", "enquete.jpg"),
}


def test_registry_covers_the_seven_planned_apis():
    assert set(SPECS) == set(KEY_PARAMS)


def test_every_spec_has_a_matching_settings_key_field():
    fields = set(Settings.model_fields)
    for name in SPECS:
        assert f"{name}_api_key" in fields


@pytest.mark.parametrize("name", sorted(KEY_PARAMS))
@responses.activate
def test_fetch_maps_fixture_to_raw_records(name):
    spec = SPECS[name]
    fixture = json.loads((FIXTURES / f"{name}.json").read_text())
    responses.get(spec.url, json=fixture)

    records = fetch_news_api(spec, query="désinformation", start=WINDOW[0],
                             end=WINDOW[1], limit=10, api_key="test-key-123")

    assert records, f"{name}: no records parsed"
    first = records[0]
    assert first.raw_source == f"api:{name}"
    assert first.headline
    assert first.url and first.url.startswith("http")
    assert first.image_url and first.image_url.endswith(KEY_PARAMS[name][1])
    assert first.publish_date is not None
    assert first.publish_date.tzinfo is not None

    key_param = KEY_PARAMS[name][0]
    sent = responses.calls[0].request.params
    assert sent.get(key_param) == "test-key-123", f"{name}: key not sent as {key_param}"


@responses.activate
def test_currents_string_none_image_becomes_real_none():
    spec = SPECS["currents"]
    fixture = json.loads((FIXTURES / "currents.json").read_text())
    responses.get(spec.url, json=fixture)
    records = fetch_news_api(spec, query="q", start=WINDOW[0], end=WINDOW[1],
                             limit=10, api_key="k")
    assert records[1].image_url is None


@responses.activate
def test_limit_caps_returned_records():
    spec = SPECS["currents"]
    fixture = json.loads((FIXTURES / "currents.json").read_text())
    responses.get(spec.url, json=fixture)
    records = fetch_news_api(spec, query="q", start=WINDOW[0], end=WINDOW[1],
                             limit=1, api_key="k")
    assert len(records) == 1


@responses.activate
def test_malformed_payload_returns_empty_list_not_crash():
    spec = SPECS["newsdata"]
    responses.get(spec.url, json={"status": "error", "results": None})
    records = fetch_news_api(spec, query="q", start=WINDOW[0], end=WINDOW[1],
                             limit=10, api_key="k")
    assert records == []
