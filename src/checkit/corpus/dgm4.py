"""DGM4 downloader (decision #4: primary labeled corpus).

10.7 GB HF dataset (rshaojimmy/DGM4): 230K news image-text pairs, 152K with
exactly-grounded synthetic manipulations. Binding license is S-Lab 1.0
(research-only, non-commercial) — the HF card's apache-2.0 YAML tag is wrong;
trust the LICENSE file (verified 2026-06-05). Record mapping happens after
download, once the on-disk layout is inspected.
"""

import json
import logging
from pathlib import Path

from checkit.schema import RawRecord

logger = logging.getLogger(__name__)

HF_REPO = "rshaojimmy/DGM4"
SPLITS = ("train", "val", "test")


def download_dgm4(corpora_dir: Path) -> Path:
    from huggingface_hub import snapshot_download

    dest = corpora_dir / "dgm4"
    dest.mkdir(parents=True, exist_ok=True)
    logger.info("dgm4 snapshot download starting to %s (~10.7 GB)", dest)
    snapshot_download(repo_id=HF_REPO, repo_type="dataset", local_dir=str(dest))
    logger.info("dgm4 snapshot complete")
    return dest


def metadata_to_records(json_path: Path, split: str,
                        limit: int | None = None) -> list[RawRecord]:
    """Map DGM4 metadata to RawRecords.

    Images are bundled locally (paths into origin/ and manipulation/ zips) —
    extras carry the path; image bytes are resolved at transform time. Labels
    are synthetic-by-construction: exact ground truth for manipulation
    detection, recorded with their grounding flags.
    """
    entries = json.loads(json_path.read_text(encoding="utf-8"))
    if limit:
        entries = entries[:limit]
    records = []
    for entry in entries:
        fake_cls = entry.get("fake_cls", "orig")
        records.append(RawRecord(
            raw_source="dgm4",
            headline=entry.get("text", ""),
            raw_source_id=str(entry.get("id")),
            language="en",
            extras={
                "split": split,
                "image_path": entry.get("image", ""),
                "label": "real" if fake_cls == "orig" else "fake",
                "fine_grained_label": f"dgm4:{fake_cls}",
                "label_source": "dgm4-synthetic",
                "grounded_image_manipulation": bool(entry.get("fake_image_box")),
                "grounded_text_manipulation": bool(entry.get("fake_text_pos")),
            },
        ))
    return records


def load_dgm4(corpora_dir: Path, limit_per_split: int | None = None) -> list[RawRecord]:
    records = []
    for split in SPLITS:
        path = corpora_dir / "dgm4" / "metadata" / f"{split}.json"
        if not path.exists():
            logger.warning("dgm4 missing %s — run download first", path)
            continue
        loaded = metadata_to_records(path, split=split, limit=limit_per_split)
        logger.info("dgm4 %s: %d records", split, len(loaded))
        records.extend(loaded)
    return records
