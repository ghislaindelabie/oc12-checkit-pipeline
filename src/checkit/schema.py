import uuid
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, model_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


class RawRecord(BaseModel):
    """Common envelope every extractor emits; one JSONL line in the raw layer.

    Heterogeneous source-specific fields go in `extras` untouched —
    normalization beyond this envelope belongs to the transform step.
    """

    record_id: str = ""
    raw_source: str
    headline: str
    url: str | None = None
    body_text: str | None = None
    caption: str | None = None
    image_url: str | None = None
    publish_date: datetime | None = None
    language: str | None = None
    source_domain: str | None = None
    raw_source_id: str | None = None
    author_pseudo_id: str | None = None
    crawl_date: datetime = Field(default_factory=utc_now)
    extras: dict[str, Any] = Field(default_factory=dict)

    @field_validator("publish_date", "crawl_date")
    @classmethod
    def force_utc(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return None
        if v.tzinfo is None:
            return v.replace(tzinfo=UTC)
        return v.astimezone(UTC)

    @model_validator(mode="after")
    def derive_identity(self) -> "RawRecord":
        if self.source_domain is None and self.url:
            self.source_domain = urlparse(self.url).netloc or None
        if not self.record_id:
            basis = self.url or f"{self.raw_source}:{self.raw_source_id}"
            self.record_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{basis}|{self.image_url or ''}"))
        return self
