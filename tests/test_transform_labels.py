from checkit.schema import RawRecord
from checkit.transform import labels as labels_mod
from checkit.transform.labels import normalize_label


def rec(source: str, **extras) -> RawRecord:
    return RawRecord(raw_source=source, headline="t", url="https://ex.fr/a",
                     extras=extras)


def test_fakeddit_6way_empirical_pinning():
    # pinned by the subreddit crosstab: theonion -> 6way=1, usnews -> 6way=0,
    # subredditsimulator (bots) -> 6way=3
    assert normalize_label(rec("fakeddit", label_6way_raw="0")).label == "real"
    satire = normalize_label(rec("fakeddit", label_6way_raw="1"))
    assert satire.label == "satire"
    assert satire.fine_grained == "fakeddit:satire-parody"
    assert normalize_label(rec("fakeddit", label_6way_raw="3")).label == "fake"
    assert normalize_label(rec("fakeddit", label_6way_raw="0")).confidence == 0.6


def test_fakeddit_unknown_int_is_unverified_ambiguous():
    verdict = normalize_label(rec("fakeddit", label_6way_raw="9"))
    assert verdict.label == "unverified"
    assert verdict.ambiguous


def test_dgm4_exact_synthetic_labels():
    verdict = normalize_label(rec("dgm4", label="fake",
                                  fine_grained_label="dgm4:face_swap"))
    assert verdict.label == "fake"
    assert verdict.confidence == 1.0


def test_fakenewsnet_human_factchecker():
    verdict = normalize_label(rec("fakenewsnet", label="fake",
                                  fine_grained_label="politifact:fake",
                                  label_source="politifact"))
    assert verdict.label == "fake"
    assert verdict.confidence == 0.9


def test_claimreview_known_ratings():
    base = dict(fine_grained_label="claimreview:x", label_source="claimreview:Y")
    assert normalize_label(rec("claimreview", rating_raw="FALSE", **base)).label == "fake"
    mostly = normalize_label(rec("claimreview", rating_raw="Mostly False", **base))
    assert mostly.label == "fake" and mostly.ambiguous
    assert normalize_label(rec("claimreview", rating_raw="Vrai", **base)).label == "real"
    half = normalize_label(rec("claimreview", rating_raw="Half True", **base))
    assert half.label == "unverified" and half.ambiguous


def test_claimreview_unmapped_counted_not_dropped():
    labels_mod.unmapped_ratings.clear()
    verdict = normalize_label(rec("claimreview", rating_raw="Très exagéré",
                                  fine_grained_label="claimreview:x",
                                  label_source="claimreview:Y"))
    assert verdict.label == "unverified"
    assert labels_mod.unmapped_ratings["très exagéré"] == 1


def test_rss_satire_first_class():
    verdict = normalize_label(rec("rss:legorafi", category="satire"))
    assert verdict.label == "satire"
    assert verdict.confidence == 0.95


def test_live_sources_unverified():
    assert normalize_label(rec("rss:franceinfo", category="news")).label == "unverified"
    assert normalize_label(rec("api:guardian")).label == "unverified"
    assert normalize_label(rec("gdelt-doc", sourcecountry="France")).label == "unverified"
