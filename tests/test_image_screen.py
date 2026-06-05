import responses

from checkit.corpus.image_screen import screen_records
from checkit.schema import RawRecord


def rec(i: int, label: str, url: str | None) -> RawRecord:
    return RawRecord(raw_source="fakenewsnet", headline=f"t{i}", url=url,
                     raw_source_id=f"id{i}",
                     extras={"fine_grained_label": label, "label": label.split(":")[1],
                             "label_source": label.split(":")[0]})


@responses.activate
def test_screen_measures_reachability_and_image_yield():
    responses.get("https://alive.example/a",
                  body='<html><head><meta property="og:image" content="https://alive.example/og.jpg"/></head></html>')
    responses.get("https://noimage.example/b", body="<html><head></head></html>")
    responses.get("https://dead.example/c", status=404)

    records = [
        rec(1, "politifact:fake", "https://alive.example/a"),
        rec(2, "politifact:fake", "https://noimage.example/b"),
        rec(3, "politifact:fake", "https://dead.example/c"),
        rec(4, "politifact:fake", None),  # no url at all — counted, never fetched
    ]
    report = screen_records(records, sample_per_label=10, delay=0.0)

    group = report["groups"]["politifact:fake"]
    assert group["sampled"] == 4
    assert group["reachable"] == 2
    assert group["with_image"] == 1
    assert group["image_rate"] == 0.25
    assert report["overall"]["sampled"] == 4
    assert report["overall"]["with_image"] == 1


@responses.activate
def test_sampling_is_deterministic_and_capped_per_label():
    for i in range(20):
        responses.get(f"https://site.example/{i}", body="<html></html>")
    records = [rec(i, "gossipcop:real", f"https://site.example/{i}") for i in range(20)]
    r1 = screen_records(records, sample_per_label=5, delay=0.0)
    r2 = screen_records(records, sample_per_label=5, delay=0.0)
    assert r1["groups"]["gossipcop:real"]["sampled"] == 5
    assert r1["groups"]["gossipcop:real"]["sampled_ids"] == r2["groups"]["gossipcop:real"]["sampled_ids"]


@responses.activate
def test_fetch_exceptions_count_as_unreachable_not_crash():
    records = [rec(1, "politifact:real", "https://refused.example/x")]
    # no responses registered -> ConnectionError raised by responses
    report = screen_records(records, sample_per_label=5, delay=0.0)
    assert report["groups"]["politifact:real"]["reachable"] == 0
