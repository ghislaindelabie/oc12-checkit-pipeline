from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Label = Literal["real", "fake", "satire", "unverified"]
PairingBasis = Literal["validated", "bundled", "declared", "none"]
Modality = Literal["text_image", "text", "claim"]


class CleanRecord(BaseModel):
    """Target schema of the transform step — one row of the ML-ready dataset.

    `paired_ok` is the headline quality property. `pairing_basis` qualifies it:
    validated = image downloaded and Pillow-verified; bundled = ships locally
    with the corpus; declared = source provides an image URL not yet fetched;
    none = no image. Strict KPI counts validated+bundled; declared is reported
    separately.
    """

    record_id: str
    raw_source: str
    headline: str
    body_text: str | None = None
    caption: str | None = None
    url: str | None = None
    source_domain: str | None = None

    image_url: str | None = None
    local_image_path: str | None = None
    image_hash: str | None = None
    image_phash: str | None = None
    paired_ok: bool
    pairing_basis: PairingBasis
    modality: Modality

    label: Label
    fine_grained_label: str | None = None
    label_source: str | None = None
    label_confidence: float | None = None
    ambiguous: bool = False

    language: str | None = None
    publish_date: datetime | None = None
    crawl_date: datetime
    raw_source_id: str | None = None
    text_fingerprint: str
    is_valid: bool
    validation_errors: list[str] = Field(default_factory=list)
