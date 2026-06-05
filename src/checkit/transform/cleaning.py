import hashlib
import html
import re
import unicodedata

_WHITESPACE = re.compile(r"\s+")
_ALNUM = re.compile(r"[^a-z0-9]+")


def nettoie_texte(text: str | None) -> str | None:
    """Clean a text field: HTML entities, control characters, whitespace."""
    if text is None:
        return None
    text = html.unescape(text)
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C" or ch in "\n\t ")
    text = _WHITESPACE.sub(" ", text).strip()
    return text or None


def text_fingerprint(headline: str | None, body: str | None = None) -> str:
    """Exact-duplicate key, robust to case/punctuation/spacing variants
    (syndicated articles republished under different URLs)."""
    canonical = _ALNUM.sub(" ", f"{headline or ''} {body or ''}".lower()).strip()
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
