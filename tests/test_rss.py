from pathlib import Path

import responses

from checkit.extract.feeds import FEEDS, Feed
from checkit.extract.rss_source import parse_feed, probe_report

FIXTURE = (Path(__file__).parent / "fixtures" / "rss_sample.xml").read_bytes()
FEED = Feed(name="exemple-actu", url="https://exemple-actu.fr/rss",
            lang="fr", category="news")


def test_all_entries_parsed():
    records = parse_feed(FIXTURE, FEED)
    assert len(records) == 4
    assert all(r.raw_source == "rss:exemple-actu" for r in records)
    assert all(r.language == "fr" for r in records)


def test_image_cascade_media_content_then_enclosure_then_inline_img():
    records = parse_feed(FIXTURE, FEED)
    by_title = {r.headline: r.image_url for r in records}
    assert by_title["Canicule précoce : records battus dans trois régions"].endswith("canicule.jpg")
    assert by_title["Élections locales : ce qu'il faut retenir"].endswith("elections.png")
    assert by_title["Reportage : le marché aux fleurs rouvre"].endswith("fleurs.gif")
    assert by_title["Brève sans aucune image"] is None


def test_category_recorded_in_extras_for_satire_class():
    satire_feed = Feed(name="gorafi-like", url="https://satire.example/rss",
                       lang="fr", category="satire")
    records = parse_feed(FIXTURE, satire_feed)
    assert all(r.extras["category"] == "satire" for r in records)


def test_publish_date_parsed_from_pubdate():
    records = parse_feed(FIXTURE, FEED)
    assert records[0].publish_date is not None
    assert records[0].publish_date.year == 2026


def test_probe_report_counts_pairing_yield():
    report = probe_report(FIXTURE, FEED)
    assert report["entries"] == 4
    assert report["with_image"] == 3
    assert report["image_rate"] == 0.75


def test_registry_has_french_news_and_satire_feeds():
    categories = {f.category for f in FEEDS}
    assert {"news", "satire"} <= categories
    assert any(f.lang == "fr" for f in FEEDS)


def test_satire_feeds_have_og_fallback_enabled():
    assert all(f.og_fallback for f in FEEDS if f.category == "satire")


@responses.activate
def test_og_image_fallback_fetches_article_page_when_feed_has_no_image():
    article_html = (
        '<html><head><meta property="og:image" '
        'content="https://exemple-actu.fr/og/breve.jpg"/></head><body/></html>'
    )
    responses.get("https://exemple-actu.fr/breve-texte", body=article_html)
    og_feed = Feed(name="exemple-actu", url="https://exemple-actu.fr/rss",
                   lang="fr", category="news", og_fallback=True)
    records = parse_feed(FIXTURE, og_feed)
    by_title = {r.headline: r.image_url for r in records}
    assert by_title["Brève sans aucune image"] == "https://exemple-actu.fr/og/breve.jpg"
    # entries that already had an image must not trigger page fetches
    assert len(responses.calls) == 1


@responses.activate
def test_og_fallback_failure_yields_none_not_crash():
    responses.get("https://exemple-actu.fr/breve-texte", status=404)
    og_feed = Feed(name="exemple-actu", url="https://exemple-actu.fr/rss",
                   lang="fr", category="news", og_fallback=True)
    records = parse_feed(FIXTURE, og_feed)
    by_title = {r.headline: r.image_url for r in records}
    assert by_title["Brève sans aucune image"] is None
