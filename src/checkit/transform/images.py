import hashlib
import io
import logging
from pathlib import Path

import requests
from PIL import Image

from checkit.extract.http import USER_AGENT

logger = logging.getLogger(__name__)

MAX_BYTES = 10 * 1024 * 1024
FETCH_TIMEOUT = 15.0


def valide_image(url: str, images_dir: Path) -> dict:
    """Download and validate one image; returns hashes + content-addressed path.

    Pillow verification is the only reliable proof the link is an exploitable
    image (an image_url that 404s or serves HTML is not a pairing).
    """
    try:
        response = requests.get(url, timeout=FETCH_TIMEOUT, stream=True,
                                headers={"User-Agent": USER_AGENT})
        response.raise_for_status()
        content = response.raw.read(MAX_BYTES + 1, decode_content=True)
    except requests.RequestException as exc:
        return {"error": f"fetch: {exc.__class__.__name__}"}
    if len(content) > MAX_BYTES:
        return {"error": "too-large"}

    try:
        image = Image.open(io.BytesIO(content))
        image.verify()
        image = Image.open(io.BytesIO(content))  # verify() invalidates the object
        fmt = (image.format or "bin").lower()
    except Exception:
        return {"error": "not-an-image"}

    import imagehash

    sha = hashlib.sha256(content).hexdigest()
    phash = str(imagehash.phash(image))
    images_dir.mkdir(parents=True, exist_ok=True)
    path = images_dir / f"{sha[:12]}.{fmt}"
    if not path.exists():
        path.write_bytes(content)
    return {"local_image_path": str(path), "image_hash": sha, "image_phash": phash}
