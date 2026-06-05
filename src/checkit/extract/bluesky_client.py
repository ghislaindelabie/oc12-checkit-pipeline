import hashlib
import logging
from datetime import datetime

import requests

from checkit.extract.http import get
from checkit.extract.throttle import THROTTLE
from checkit.schema import RawRecord

logger = logging.getLogger(__name__)

# api.bsky.app, not public.api.bsky.app — the latter 403s server IPs (checked 2026-06-05)
BSKY_SEARCH_URL = "https://api.bsky.app/xrpc/app.bsky.feed.searchPosts"
# Published AppView limits ~3000 req/5min (~10/s); 1 req/s keeps us 10x under
# and also softens the WAF that 403s fast pagination from server IPs
BSKY_MIN_INTERVAL = 1.0


def pseudonymize(identifier: str, salt: str) -> str:
    # GDPR posture: author identity never stored, only a salted hash
    # so same-author dedup/analysis stays possible.
    return hashlib.sha256(f"{salt}:{identifier}".encode()).hexdigest()[:16]


def _post_url(did: str, uri: str) -> str:
    rkey = uri.rsplit("/", 1)[-1]
    return f"https://bsky.app/profile/{did}/post/{rkey}"


def fetch_bluesky(
    query: str,
    salt: str,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = 100,
) -> list[RawRecord]:
    """Search public Bluesky posts (no auth needed), keep only image-bearing ones."""
    records: list[RawRecord] = []
    cursor: str | None = None
    while len(records) < limit:
        params = {"q": query, "limit": str(min(limit, 100))}
        if since:
            params["since"] = since.isoformat()
        if until:
            params["until"] = until.isoformat()
        if cursor:
            params["cursor"] = cursor

        THROTTLE.wait("bluesky", BSKY_MIN_INTERVAL)
        try:
            payload = get(BSKY_SEARCH_URL, params=params).json()
        except requests.HTTPError as exc:
            # WAF can 403 mid-pagination; keep what we have
            logger.warning("bluesky pagination stopped: %s", exc)
            break
        posts = payload.get("posts", [])
        for post in posts:
            record = _to_record(post, salt)
            if record is not None:
                records.append(record)
        cursor = payload.get("cursor")
        if not cursor or not posts:
            break
    logger.info("bluesky kept %d image posts for query=%r", len(records), query)
    return records[:limit]


def _to_record(post: dict, salt: str) -> RawRecord | None:
    embed = post.get("embed", {})
    if embed.get("$type") != "app.bsky.embed.images#view" or not embed.get("images"):
        return None
    image = embed["images"][0]
    body = post.get("record", {})
    did = post.get("author", {}).get("did", "")
    langs = body.get("langs") or []
    return RawRecord(
        raw_source="bluesky",
        headline=body.get("text", ""),
        url=_post_url(did, post.get("uri", "")),
        caption=image.get("alt") or None,
        image_url=image.get("fullsize") or image.get("thumb"),
        publish_date=body.get("createdAt"),
        language=langs[0] if langs else None,
        raw_source_id=post.get("uri"),
        author_pseudo_id=pseudonymize(did, salt) if did else None,
        extras={"image_count": len(embed["images"])},
    )
