import json
from pathlib import Path

import pytest
import responses

from checkit.extract import bluesky_client
from checkit.extract.bluesky_client import BSKY_SEARCH_URL, fetch_bluesky, pseudonymize


@pytest.fixture(autouse=True)
def no_throttle(monkeypatch):
    monkeypatch.setattr(bluesky_client, "BSKY_MIN_INTERVAL", 0.0)

FIXTURE = Path(__file__).parent / "fixtures" / "bluesky_search.json"


@responses.activate
def test_only_posts_with_images_are_kept():
    responses.get(BSKY_SEARCH_URL, json=json.loads(FIXTURE.read_text()))
    records = fetch_bluesky(query="inondations", salt="s")
    assert len(records) == 1
    r = records[0]
    assert r.raw_source == "bluesky"
    assert r.image_url.endswith("@jpeg")
    assert r.caption == "Rue inondée à Valence, eau jusqu'aux genoux"
    assert r.language == "fr"


@responses.activate
def test_author_identity_pseudonymized():
    responses.get(BSKY_SEARCH_URL, json=json.loads(FIXTURE.read_text()))
    records = fetch_bluesky(query="inondations", salt="s")
    record = records[0]
    dumped = record.model_dump_json()
    # Handle and display name must never be stored; the author field is a
    # salted hash. The DID itself survives only inside provenance URLs
    # (post + image), which embed it by AT Protocol design.
    assert "journaliste.bsky.social" not in dumped
    assert "Une Journaliste" not in dumped
    assert record.author_pseudo_id == pseudonymize("did:plc:abc123", salt="s")
    assert record.author_pseudo_id != "did:plc:abc123"
    fields_with_did = [k for k, v in record.model_dump().items()
                       if isinstance(v, str) and "did:plc:abc123" in v]
    assert set(fields_with_did) <= {"url", "image_url", "raw_source_id"}


def test_pseudonymize_is_stable_per_salt_and_changes_with_salt():
    assert pseudonymize("did:plc:x", salt="a") == pseudonymize("did:plc:x", salt="a")
    assert pseudonymize("did:plc:x", salt="a") != pseudonymize("did:plc:x", salt="b")
    assert "did:plc:x" not in pseudonymize("did:plc:x", salt="a")


@responses.activate
def test_post_url_built_from_did_and_rkey():
    responses.get(BSKY_SEARCH_URL, json=json.loads(FIXTURE.read_text()))
    records = fetch_bluesky(query="q", salt="s")
    assert records[0].url == "https://bsky.app/profile/did:plc:abc123/post/3kxyz22"


@responses.activate
def test_pagination_stops_gracefully_on_mid_run_403():
    # observed live 2026-06-05: page 1 OK, paginated request WAF-403'd —
    # partial results must be returned, not an exception
    page1 = json.loads(FIXTURE.read_text())
    page1["cursor"] = "10"
    responses.get(BSKY_SEARCH_URL, json=page1)
    responses.get(BSKY_SEARCH_URL, status=403)
    records = fetch_bluesky(query="q", salt="s", limit=50)
    assert len(records) == 1
