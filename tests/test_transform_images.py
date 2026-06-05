import io

import pytest
import responses
from PIL import Image

from checkit.transform import images as images_mod
from checkit.transform.images import valide_image


@pytest.fixture(autouse=True)
def no_throttle(monkeypatch):
    monkeypatch.setattr(images_mod, "IMG_MIN_INTERVAL", 0.0)


def png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), color=(200, 30, 30)).save(buffer, format="PNG")
    return buffer.getvalue()


@responses.activate
def test_valid_image_downloaded_hashed_and_stored(tmp_path):
    responses.get("https://ex.fr/img.png", body=png_bytes(),
                  content_type="image/png")
    result = valide_image("https://ex.fr/img.png", tmp_path)
    assert "error" not in result
    assert result["image_hash"]
    assert result["image_phash"]
    assert result["local_image_path"].endswith(".png")
    assert (tmp_path / result["local_image_path"].split("/")[-1]).exists()


@responses.activate
def test_http_error_reported_not_raised(tmp_path):
    responses.get("https://ex.fr/dead.png", status=404)
    assert valide_image("https://ex.fr/dead.png", tmp_path)["error"].startswith("fetch")


@responses.activate
def test_html_masquerading_as_image_rejected(tmp_path):
    responses.get("https://ex.fr/fake.jpg", body="<html>not an image</html>")
    assert valide_image("https://ex.fr/fake.jpg", tmp_path)["error"] == "not-an-image"


@responses.activate
def test_content_addressed_dedup_on_disk(tmp_path):
    body = png_bytes()
    responses.get("https://ex.fr/a.png", body=body, content_type="image/png")
    responses.get("https://ex.fr/b.png", body=body, content_type="image/png")
    r1 = valide_image("https://ex.fr/a.png", tmp_path)
    r2 = valide_image("https://ex.fr/b.png", tmp_path)
    assert r1["local_image_path"] == r2["local_image_path"]  # same sha -> same file
    assert len(list(tmp_path.iterdir())) == 1
