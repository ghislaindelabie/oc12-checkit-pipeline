import json
from pathlib import Path

import responses

from checkit.factcheck_query import FCT_URL, format_results, main, search_claims

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "google_fct.json").read_text())


@responses.activate
def test_search_flattens_one_row_per_review():
    responses.get(FCT_URL, json=FIXTURE)
    rows = search_claims("inondation paris", api_key="k", language="fr", limit=10)
    assert len(rows) == 3  # claim 1 has 1 review, claim 2 has 2
    first = rows[0]
    assert first["publisher"] == "AFP Factuel"
    assert first["rating"] == "Faux"
    assert first["claim"].startswith("Une vidéo")
    assert first["review_url"].startswith("https://factuel.afp.com")


@responses.activate
def test_request_carries_key_language_and_query():
    responses.get(FCT_URL, json={"claims": []})
    search_claims("test claim", api_key="secret-key", language="fr", limit=5)
    params = responses.calls[0].request.params
    assert params["key"] == "secret-key"
    assert params["languageCode"] == "fr"
    assert params["query"] == "test claim"
    assert params["pageSize"] == "5"


@responses.activate
def test_empty_results_return_empty_list():
    responses.get(FCT_URL, json={})
    assert search_claims("nothing", api_key="k") == []


def test_format_results_human_readable_and_mentions_no_storage():
    rows = [{"claim": "Une vidéo montre une inondation", "claimant": "Posts",
             "claim_date": "2026-06-01", "publisher": "AFP Factuel",
             "rating": "Faux", "review_title": "Non, cette vidéo…",
             "review_url": "https://factuel.afp.com/doc.x", "language": "fr"}]
    text = format_results("inondation", rows)
    assert "AFP Factuel" in text
    assert "Faux" in text
    assert "https://factuel.afp.com/doc.x" in text
    # the compliance contract is part of the output, every time
    assert "Aucun résultat n'est stocké" in text


def test_format_results_empty():
    text = format_results("xyz", [])
    assert "Aucun verdict" in text


def test_main_without_key_explains_and_exits_cleanly(monkeypatch, capsys):
    monkeypatch.delenv("CHECKIT_GOOGLE_FCT_API_KEY", raising=False)
    code = main(["une affirmation", "--env-file", "/nonexistent"])
    out = capsys.readouterr().out
    assert code == 2
    assert "CHECKIT_GOOGLE_FCT_API_KEY" in out
