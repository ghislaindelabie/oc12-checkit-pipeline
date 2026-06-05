"""Label normalization: every source's native taxonomy → {real, fake, satire,
unverified} + fine_grained_label + label_source + label_confidence + ambiguous.

Confidence encodes label provenance (decision #16): synthetic-by-construction
(DGM4) = 1.0 > human fact-checker = 0.9 > self-declared satire = 0.95 >
distant supervision (Fakeddit) = 0.6 > none = None.
"""

import logging
from collections import Counter
from dataclasses import dataclass

from checkit.schema import RawRecord

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Verdict:
    label: str
    fine_grained: str | None
    source: str | None
    confidence: float | None
    ambiguous: bool = False


# Pinned EMPIRICALLY on the 680K-row corpus (2026-06-05): every subreddit maps
# to exactly one (2way,3way,6way) combo — e.g. theonion/satire → 6way=1,
# mildlyinteresting/usnews → 6way=0, subredditsimulator (bots) → 6way=3.
# Class names follow the Fakeddit paper's 6-way taxonomy.
FAKEDDIT_6WAY: dict[str, Verdict] = {
    "0": Verdict("real", "fakeddit:true", "fakeddit-distant", 0.6),
    "1": Verdict("satire", "fakeddit:satire-parody", "fakeddit-distant", 0.6),
    "2": Verdict("fake", "fakeddit:misleading-content", "fakeddit-distant", 0.6),
    "3": Verdict("fake", "fakeddit:imposter-content", "fakeddit-distant", 0.6),
    "4": Verdict("fake", "fakeddit:false-connection", "fakeddit-distant", 0.6),
    "5": Verdict("fake", "fakeddit:manipulated-content", "fakeddit-distant", 0.6),
}

# High-frequency ClaimReview ratings (matched lowercase). The long multilingual
# tail stays unverified and is COUNTED, not dropped.
CLAIMREVIEW_MAP: dict[str, tuple[str, bool]] = {
    # rating -> (label, ambiguous)
    "false": ("fake", False),
    "false.": ("fake", False),
    "fake": ("fake", False),
    "pants on fire!": ("fake", False),
    "pants on fire": ("fake", False),
    "faux": ("fake", False),
    "نادرست": ("fake", False),          # Persian: false
    "misleading": ("fake", True),
    "missing context": ("fake", True),
    "falso": ("fake", False),           # Spanish/Portuguese/Italian: false
    "yanlış": ("fake", False),          # Turkish: false
    "keliru": ("fake", False),          # Indonesian: false
    "誤り": ("fake", False),            # Japanese: false
    "مضلل": ("fake", True),             # Arabic: misleading
    "گمراه‌کننده": ("fake", True),      # Persian: misleading
    "mostly false": ("fake", True),
    "altered": ("fake", False),
    "altered photo": ("fake", False),
    "altered video": ("fake", False),
    "distorts the facts": ("fake", True),
    "true": ("real", False),
    "vrai": ("real", False),
    "correct": ("real", False),
    "درست": ("real", False),            # Persian: true
    "mostly true": ("real", True),
    "half true": ("unverified", True),
    "mixture": ("unverified", True),
    "unproven": ("unverified", True),
    "satire": ("satire", False),
    "labeled satire": ("satire", False),
}

unmapped_ratings: Counter = Counter()


def normalize_label(record: RawRecord) -> Verdict:
    extras = record.extras
    source = record.raw_source

    if source == "dgm4":
        return Verdict(extras["label"], extras["fine_grained_label"],
                       "dgm4-synthetic", 1.0)

    if source == "fakenewsnet":
        return Verdict(extras["label"], extras["fine_grained_label"],
                       extras["label_source"], 0.9)

    if source == "fakeddit":
        verdict = FAKEDDIT_6WAY.get(str(extras.get("label_6way_raw")))
        if verdict:
            return verdict
        return Verdict("unverified", None, "fakeddit-distant", None, ambiguous=True)

    if source == "claimreview":
        rating = (extras.get("rating_raw") or "").strip().lower()
        mapped = CLAIMREVIEW_MAP.get(rating)
        if mapped:
            label, ambiguous = mapped
            return Verdict(label, extras["fine_grained_label"],
                           extras["label_source"], 0.9, ambiguous)
        unmapped_ratings[rating or "(empty)"] += 1
        return Verdict("unverified", extras.get("fine_grained_label"),
                       extras.get("label_source"), None, ambiguous=True)

    if source == "webz-fakenews":
        # SOURCE-level distant supervision (publisher flagged, content not
        # fact-checked) -> low confidence; entertainment items ambiguous
        return Verdict("fake", "webz:source-flagged", "webz-source-flagged",
                       0.5, ambiguous=bool(extras.get("entertainment")))

    if source.startswith("rss:") and extras.get("category") == "satire":
        return Verdict("satire", "satire:self-declared", "satire-self-declared", 0.95)

    # live feeds (rss news, gdelt, bluesky, api:*) carry no veracity label
    return Verdict("unverified", None, None, None)
