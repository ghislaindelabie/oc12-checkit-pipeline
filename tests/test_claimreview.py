import json

from checkit.corpus.claimreview import feed_to_records

SAMPLE_FEED = {
    "@type": "DataFeed",
    "dataFeedElement": [
        {
            "@type": "DataFeedItem",
            "item": [{
                "@type": "ClaimReview",
                "author": {"name": "PolitiFact", "url": "https://www.politifact.com/"},
                "claimReviewed": "Cannabis users outnumber coffee buyers in New York.",
                "datePublished": "2026-06-05",
                "url": "https://www.politifact.com/factchecks/2026/jun/05/cannabis",
                "reviewRating": {"alternateName": "Mostly False"},
                "itemReviewed": {
                    "appearance": [
                        {"url": "https://www.politico.com/news/2026/04/02/some-article"},
                        {"url": "https://example.social/post/123"},
                    ],
                },
            }],
        },
        {
            "@type": "DataFeedItem",
            "item": [{
                "@type": "ClaimReview",
                "author": {"name": "AFP Factuel"},
                "claimReviewed": "Une vidéo montre une inondation à Paris en 2026.",
                "url": "https://factuel.afp.com/doc.123",
                "reviewRating": {},
            }],
        },
        {"@type": "DataFeedItem"},
    ],
}


def write_feed(tmp_path):
    p = tmp_path / "data.json"
    p.write_text(json.dumps(SAMPLE_FEED), encoding="utf-8")
    return p


def test_claims_mapped_with_verdict_kept_raw(tmp_path):
    records = feed_to_records(write_feed(tmp_path))
    assert len(records) == 2
    first = records[0]
    assert first.raw_source == "claimreview"
    assert first.headline.startswith("Cannabis users")
    assert first.url == "https://www.politifact.com/factchecks/2026/jun/05/cannabis"
    assert first.publish_date.year == 2026
    assert first.extras["rating_raw"] == "Mostly False"
    assert first.extras["fact_checker"] == "PolitiFact"
    assert first.extras["label_source"] == "claimreview:PolitiFact"
    assert first.extras["fine_grained_label"] == "claimreview:Mostly False"


def test_appearance_urls_kept_for_future_joins(tmp_path):
    records = feed_to_records(write_feed(tmp_path))
    assert records[0].extras["appearance_urls"] == [
        "https://www.politico.com/news/2026/04/02/some-article",
        "https://example.social/post/123",
    ]


def test_missing_rating_and_empty_elements_survive(tmp_path):
    records = feed_to_records(write_feed(tmp_path))
    second = records[1]
    assert second.extras["rating_raw"] is None
    assert second.extras["appearance_urls"] == []
    assert second.headline.startswith("Une vidéo")


def test_no_images_expected_label_feed_not_multimodal(tmp_path):
    records = feed_to_records(write_feed(tmp_path))
    assert all(r.image_url is None for r in records)


def test_malformed_dates_in_the_wild_become_none(tmp_path):
    # seen live in the dump: datePublished '20204-08-02' (five-digit year)
    feed = {"dataFeedElement": [{"item": [{
        "claimReviewed": "Some claim",
        "author": {"name": "X"},
        "datePublished": "20204-08-02",
    }]}]}
    p = tmp_path / "data.json"
    p.write_text(json.dumps(feed), encoding="utf-8")
    records = feed_to_records(p)
    assert records[0].publish_date is None
