import json

from checkit.corpus.dgm4 import metadata_to_records

SAMPLE = [
    {
        "id": 995762,
        "image": "DGM4/manipulation/infoswap/995762-043201-infoswap.jpg",
        "text": "A Victorian court decided on Friday that the book can be published",
        "fake_cls": "face_swap",
        "fake_image_box": [178, 35, 226, 99],
        "fake_text_pos": [],
        "mtcnn_boxes": [[178, 35, 226, 99]],
    },
    {
        "id": 12,
        "image": "DGM4/origin/guardian/0001/12.jpg",
        "text": "An untouched news photo caption",
        "fake_cls": "orig",
        "fake_image_box": [],
        "fake_text_pos": [],
        "mtcnn_boxes": [],
    },
]


def write_sample(tmp_path):
    p = tmp_path / "train.json"
    p.write_text(json.dumps(SAMPLE), encoding="utf-8")
    return p


def test_manipulated_record_mapped_with_fine_grained_label(tmp_path):
    records = metadata_to_records(write_sample(tmp_path), split="train")
    first = records[0]
    assert first.raw_source == "dgm4"
    assert first.raw_source_id == "995762"
    assert first.headline.startswith("A Victorian court")
    assert first.extras["label"] == "fake"
    assert first.extras["fine_grained_label"] == "dgm4:face_swap"
    assert first.extras["label_source"] == "dgm4-synthetic"
    assert first.extras["image_path"].endswith("infoswap.jpg")
    assert first.extras["grounded_image_manipulation"] is True


def test_orig_record_is_real(tmp_path):
    records = metadata_to_records(write_sample(tmp_path), split="train")
    second = records[1]
    assert second.extras["label"] == "real"
    assert second.extras["fine_grained_label"] == "dgm4:orig"
    assert second.extras["grounded_image_manipulation"] is False


def test_identity_stable_without_url(tmp_path):
    a = metadata_to_records(write_sample(tmp_path), split="train")
    b = metadata_to_records(write_sample(tmp_path), split="train")
    assert [r.record_id for r in a] == [r.record_id for r in b]


def test_limit(tmp_path):
    records = metadata_to_records(write_sample(tmp_path), split="train", limit=1)
    assert len(records) == 1
