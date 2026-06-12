import json
import zipfile

from checkit.corpus.webz_fakenews import article_to_record, load_webz

ARTICLE = {
    "thread": {
        "uuid": "d0ab7f8022590891",
        "url": "https://www.flagged-site.com/article-1",
        "site": "flagged-site.com",
        "country": "US",
        "main_image": "https://img.flagged-site.com/img/1.jpg",
        "domain_rank": "3021",
        "site_categories": ["news"],
    },
    "uuid": "d0ab7f8022590891",
    "url": "https://www.flagged-site.com/article-1",
    "author": "A Journalist",
    "published": "2026-05-28T05:59:00.000+03:00",
    "title": "Shocking claim about a public figure",
    "text": "Full body text of the flagged article…",
    "language": "english",
    "sentiment": "negative",
    "categories": ["Politics"],
    "ai_allow": True,
    "trust": {"categories": ["fake_news"], "bias": "right"},
}


def make(overrides: dict) -> dict:
    article = json.loads(json.dumps(ARTICLE))
    article.update(overrides)
    return article


def test_mapping_pairs_text_and_main_image():
    record = article_to_record(make({}), drop="trust_category_fake_news_20260531.zip")
    assert record.raw_source == "webz-fakenews"
    assert record.headline == "Shocking claim about a public figure"
    assert record.image_url == "https://img.flagged-site.com/img/1.jpg"
    assert record.body_text.startswith("Full body")
    assert record.language == "en"
    assert record.publish_date.year == 2026
    assert record.extras["site"] == "flagged-site.com"
    assert record.extras["drop"] == "trust_category_fake_news_20260531.zip"


def test_author_never_stored():
    record = article_to_record(make({}), drop="d.zip")
    assert "A Journalist" not in record.model_dump_json()


def test_trust_bias_kept_raw_never_a_label():
    record = article_to_record(make({}), drop="d.zip")
    assert record.extras["trust_bias"] == "right"
    assert "label" not in record.extras or record.extras.get("label") is None


def test_ai_allow_false_is_skipped():
    assert article_to_record(make({"ai_allow": False}), drop="d.zip") is None


def test_entertainment_flagged_ambiguous_candidate():
    record = article_to_record(
        make({"categories": ["Arts, Culture and Entertainment"]}), drop="d.zip")
    assert record.extras["entertainment"] is True
    politics = article_to_record(make({}), drop="d.zip")
    assert politics.extras["entertainment"] is False


def test_russian_language_mapped():
    record = article_to_record(make({"language": "russian"}), drop="d.zip")
    assert record.language == "ru"


def test_load_webz_reads_zip_members_and_counts_ai_optouts(tmp_path):
    drop_dir = tmp_path / "webz-fakenews"
    drop_dir.mkdir(parents=True)
    zip_path = drop_dir / "trust_category_fake_news_20260531071619.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("drop/article_1.json", json.dumps(make({})))
        zf.writestr("drop/article_2.json", json.dumps(make({"ai_allow": False})))
        zf.writestr("drop/article_3.json",
                     json.dumps(make({"url": "https://other.example/x",
                                      "title": "Another one"})))
    records = load_webz(tmp_path)
    assert len(records) == 2  # ai_allow=False excluded
    assert {r.headline for r in records} == {"Shocking claim about a public figure",
                                             "Another one"}
