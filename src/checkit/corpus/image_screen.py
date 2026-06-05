"""Pairing screen for URL-only corpora (decision #7).

FakeNewsNet ships no images — they must be fetched from live article pages,
which rot. This module measures, on a deterministic stratified sample, how
many pages are still reachable and expose an og:image. The resulting rates
decide whether the corpus is admitted to the training set, and the rot rate
itself is a reported KPI.
"""

import logging
import random
import time
from collections import defaultdict

import requests
from bs4 import BeautifulSoup

from checkit.extract.http import USER_AGENT
from checkit.schema import RawRecord

logger = logging.getLogger(__name__)

FETCH_TIMEOUT = 8.0


def fetch_og_image(url: str) -> tuple[bool, str | None]:
    """Single attempt, short timeout — dead domains are the expected case."""
    try:
        response = requests.get(url, timeout=FETCH_TIMEOUT, allow_redirects=True,
                                headers={"User-Agent": USER_AGENT})
        response.raise_for_status()
    except requests.RequestException:
        return False, None
    meta = BeautifulSoup(response.text, "lxml").find("meta", property="og:image")
    return True, (meta.get("content") if meta else None)


def screen_records(records: list[RawRecord], sample_per_label: int,
                   delay: float = 0.3) -> dict:
    by_label: dict[str, list[RawRecord]] = defaultdict(list)
    for record in records:
        by_label[record.extras.get("fine_grained_label", "unknown")].append(record)

    rng = random.Random(42)
    groups = {}
    total = {"sampled": 0, "reachable": 0, "with_image": 0}
    for label, group in sorted(by_label.items()):
        sample = sorted(group, key=lambda r: r.record_id)
        if len(sample) > sample_per_label:
            sample = rng.sample(sample, sample_per_label)
        stats = {"sampled": len(sample), "reachable": 0, "with_image": 0,
                 "sampled_ids": [r.raw_source_id for r in sample]}
        for record in sample:
            if record.url:
                reachable, image = fetch_og_image(record.url)
                stats["reachable"] += int(reachable)
                stats["with_image"] += int(image is not None)
                if delay:
                    time.sleep(delay)
        stats["image_rate"] = (round(stats["with_image"] / stats["sampled"], 3)
                               if stats["sampled"] else 0.0)
        groups[label] = stats
        for key in total:
            total[key] += stats[key]
        logger.info("screen %s: %d/%d with image (%.0f%%)", label,
                    stats["with_image"], stats["sampled"], 100 * stats["image_rate"])

    total["image_rate"] = (round(total["with_image"] / total["sampled"], 3)
                           if total["sampled"] else 0.0)
    return {"groups": groups, "overall": total}
