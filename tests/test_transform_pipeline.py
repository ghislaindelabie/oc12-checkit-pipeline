import json

import pandas as pd

from checkit.schema import RawRecord
from checkit.transform.pipeline import run


def write_raw(raw_dir, source: str, records: list[RawRecord]):
    d = raw_dir / source
    d.mkdir(parents=True)
    with (d / "2026-06-05.jsonl").open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(r.model_dump_json() + "\n")


def seed(tmp_path):
    raw = tmp_path / "raw"
    write_raw(raw, "rss", [
        RawRecord(raw_source="rss:franceinfo", headline="Une  annonce &amp; choc",
                  url="https://fi.fr/a1", image_url="https://fi.fr/a1.jpg",
                  language="fr", extras={"category": "news"}),
        RawRecord(raw_source="rss:legorafi", headline="Un scoop satirique",
                  url="https://gorafi.fr/s1", image_url="https://gorafi.fr/s1.jpg",
                  language="fr", extras={"category": "satire"}),
        # duplicate of the first by url+image -> same record_id
        RawRecord(raw_source="rss:franceinfo", headline="Une annonce & choc",
                  url="https://fi.fr/a1", image_url="https://fi.fr/a1.jpg",
                  language="fr", extras={"category": "news"}),
    ])
    write_raw(raw, "dgm4", [
        RawRecord(raw_source="dgm4", headline="Caption manipulée", raw_source_id="1",
                  extras={"label": "fake", "fine_grained_label": "dgm4:face_swap",
                          "label_source": "dgm4-synthetic",
                          "image_path": "DGM4/manipulation/x.jpg"}),
    ])
    write_raw(raw, "fakenewsnet", [
        RawRecord(raw_source="fakenewsnet", headline="Claim politifact",
                  url="http://dead.example/x", raw_source_id="p1",
                  extras={"label": "fake", "fine_grained_label": "politifact:fake",
                          "label_source": "politifact"}),
    ])
    write_raw(raw, "claimreview", [
        RawRecord(raw_source="claimreview", headline="Une affirmation vérifiée",
                  url="https://factuel.afp.com/d1",
                  extras={"rating_raw": "Faux", "fact_checker": "AFP",
                          "label_source": "claimreview:AFP",
                          "fine_grained_label": "claimreview:Faux",
                          "appearance_urls": []}),
    ])
    return raw


def test_end_to_end_no_network(tmp_path):
    report = run(raw_dir=seed(tmp_path), out_dir=tmp_path / "out",
                 images_dir=tmp_path / "img", image_mode="none")

    assert report["rows"] == 5  # 6 raw - 1 duplicate
    assert report["dup_removed"]["dup_by_id"] == 1

    frame = pd.read_parquet(tmp_path / "out" / "dataset.parquet")
    assert len(frame) == 5
    by_source = frame.set_index("record_id")

    rss_news = frame[frame.raw_source == "rss:franceinfo"].iloc[0]
    assert rss_news.headline == "Une annonce & choc"  # cleaned
    assert rss_news.label == "unverified"
    assert rss_news.pairing_basis == "declared"  # image_mode=none -> not validated
    assert rss_news.modality == "text_image"     # has an image URL

    satire = frame[frame.raw_source == "rss:legorafi"].iloc[0]
    assert satire.label == "satire"

    dgm4 = frame[frame.raw_source == "dgm4"].iloc[0]
    assert dgm4.pairing_basis == "bundled"
    assert bool(dgm4.paired_ok) is True
    assert dgm4.modality == "text_image"

    # Option B: a content record without an image is KEPT as modality=text,
    # valid, paired_ok=False — no longer dropped as "not-paired"
    fnn = frame[frame.raw_source == "fakenewsnet"].iloc[0]
    assert fnn.pairing_basis == "none"
    assert fnn.modality == "text"
    assert bool(fnn.paired_ok) is False
    assert bool(fnn.is_valid) is True
    assert "not-paired" not in list(fnn.validation_errors)

    claim = frame[frame.raw_source == "claimreview"].iloc[0]
    assert claim.label == "fake"
    assert claim.modality == "claim"
    assert bool(claim.is_valid) is True  # label feed: no pairing required

    # outputs exist
    assert (tmp_path / "out" / "dataset_index.csv").exists()
    report_disk = json.loads((tmp_path / "out" / "run_report.json").read_text())
    assert report_disk["rows"] == 5
    assert "rss:legorafi" in report_disk["per_source"]
    assert report_disk["modality"]["text"] == 1       # the fakenewsnet record
    assert report_disk["modality"]["claim"] == 1       # claimreview


def test_pairing_rates_exclude_label_feed(tmp_path):
    report = run(raw_dir=seed(tmp_path), out_dir=tmp_path / "out",
                 images_dir=tmp_path / "img", image_mode="none")
    # content records: 2 rss kept + 1 dgm4 + 1 fnn = 4; paired declared = 3
    assert report["pairing_rate_declared"] == 0.75
    # strict counts bundled only here (no validation ran)
    assert report["pairing_rate_strict"] == 0.25
