import pytest
import responses

from checkit.corpus import enrich as enrich_mod
from checkit.corpus.enrich import enrich_records, fetch_article
from checkit.schema import RawRecord


@pytest.fixture(autouse=True)
def no_throttle(monkeypatch):
    monkeypatch.setattr(enrich_mod, "HOST_MIN_INTERVAL", 0.0)

ARTICLE_HTML = """
<html><head>
  <meta property="og:title" content="Titre de l'article"/>
  <meta property="og:image" content="https://ex.fr/img/a.jpg"/>
</head><body><article><p>Le corps complet de l'article de presse, assez long pour
être extrait par trafilatura sans problème particulier ici.</p></article></body></html>
"""


@responses.activate
def test_fetch_article_returns_title_text_image():
    responses.get("https://ex.fr/a", body=ARTICLE_HTML)
    result = fetch_article("https://ex.fr/a")
    assert result["title"] == "Titre de l'article"
    assert result["image_url"] == "https://ex.fr/img/a.jpg"
    assert "corps complet" in (result["text"] or "")


@responses.activate
def test_fetch_article_dead_url_is_error_not_raise():
    responses.get("https://dead.example/x", status=404)
    assert "error" in fetch_article("https://dead.example/x")


@responses.activate
def test_enrich_fills_records_and_reports_rates():
    responses.get("https://ex.fr/a", body=ARTICLE_HTML)
    responses.get("https://dead.example/x", status=404)
    records = [
        RawRecord(raw_source="euvsdisinfo", headline="", url="https://ex.fr/a",
                  raw_source_id="1", extras={"class": "disinformation"}),
        RawRecord(raw_source="euvsdisinfo", headline="", url="https://dead.example/x",
                  raw_source_id="2", extras={"class": "disinformation"}),
        RawRecord(raw_source="euvsdisinfo", headline="", url=None,
                  raw_source_id="3", extras={"class": "trustworthy"}),
    ]
    stats = enrich_records(records)
    assert stats["records"] == 3
    assert stats["reachable"] == 1
    assert stats["with_text"] == 1
    assert stats["with_image"] == 1
    assert records[0].headline == "Titre de l'article"
    assert records[0].extras["text_fetched"] is True
    assert records[1].extras["fetch_error"] == "HTTPError"
