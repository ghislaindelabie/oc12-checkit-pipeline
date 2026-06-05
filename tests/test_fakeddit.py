from checkit.corpus.fakeddit import MULTIMODAL_FILES, tsv_to_records

SAMPLE_TSV = (
    "id\tclean_title\timage_url\thasImage\tsubreddit\tdomain\tcreated_utc\t"
    "2_way_label\t3_way_label\t6_way_label\n"
    "abc1\ta viral fake story\thttps://i.redd.it/abc1.jpg\tTrue\tsavedyouaclick\t"
    "i.redd.it\t1551640000\t0\t2\t3\n"
    "abc2\ttext only post\t\tFalse\tnews\texample.com\t1551641000\t1\t0\t0\n"
    "abc3\tonion satire post\thttps://i.redd.it/abc3.jpg\tTrue\ttheonion\t"
    "i.redd.it\t1551642000\t0\t1\t1\n"
)


def write_sample(tmp_path):
    p = tmp_path / "multimodal_train.tsv"
    p.write_text(SAMPLE_TSV, encoding="utf-8")
    return p


def test_only_image_bearing_rows_kept(tmp_path):
    records = tsv_to_records(write_sample(tmp_path), split="train")
    assert [r.raw_source_id for r in records] == ["abc1", "abc3"]


def test_mapping_keeps_raw_label_values_uninterpreted(tmp_path):
    records = tsv_to_records(write_sample(tmp_path), split="train")
    first = records[0]
    assert first.raw_source == "fakeddit"
    assert first.headline == "a viral fake story"
    assert first.url == "https://www.reddit.com/comments/abc1"
    assert first.image_url == "https://i.redd.it/abc1.jpg"
    assert first.publish_date.year == 2019
    assert first.extras["label_2way_raw"] == "0"
    assert first.extras["label_6way_raw"] == "3"
    assert first.extras["subreddit"] == "savedyouaclick"
    assert first.extras["label_source"] == "fakeddit-distant"


def test_limit_caps_rows(tmp_path):
    records = tsv_to_records(write_sample(tmp_path), split="train", limit=1)
    assert len(records) == 1


def test_expected_multimodal_files():
    assert MULTIMODAL_FILES == ["multimodal_train.tsv", "multimodal_validate.tsv",
                                "multimodal_test_public.tsv"]
