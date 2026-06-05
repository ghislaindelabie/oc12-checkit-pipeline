# OC12 — Tools & Techniques by Source

_Scope: concrete extraction and handling techniques for each shortlisted data source in the CheckIt.AI multimodal fake-news detection pipeline. Covers REST APIs, Reddit/Fakeddit dumps, research dataset ingestion, RSS feeds, and web scraping as a last resort, plus cross-cutting concerns (image download/validation, text cleaning, dedup, serialisation, config, logging, testing). As of May 2026._

---

## 1. REST API Extraction — NewsData.io (and Currents as fallback)

### 1.1 Official Python client (recommended)

NewsData.io ships a first-party SDK ([`newsdataapi`](https://pypi.org/project/newsdataapi/)) that wraps pagination, retry, and error handling:

```python
from newsdataapi import NewsDataApiClient

api = NewsDataApiClient(
    apikey=settings.NEWSDATA_API_KEY,   # from pydantic-settings / .env
    max_retries=5,
    retry_backoff=2.0,          # exponential: 2, 4, 8, 16, 32 s
    retry_backoff_max=60.0,     # cap each sleep at 60 s
)

# Generator-based pagination — memory-efficient for large pulls
for page in api.latest_api(
    q="politics misinformation",
    language="en",
    paginate=True,
    max_pages=10,
):
    for article in page.get("results", []):
        image_url = article.get("image_url")   # first-class field
        text      = article.get("content") or article.get("description", "")
        yield article
```

`paginate=True` returns a generator; each `page` is one JSON response. `scroll=True` + `max_result` fetches everything into memory — avoid for large pulls. The client raises `NewsdataRateLimitError` (HTTP 429) with a `retry_after` attribute; the built-in backoff handles this automatically, but you can also catch it manually.

### 1.2 Raw `requests` + `tenacity` (for Currents or any JSON API without SDK)

```python
import os, requests, time
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type

CURRENTS_KEY = os.environ["CURRENTS_API_KEY"]

@retry(
    wait=wait_random_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(6),
    retry=retry_if_exception_type((requests.exceptions.ConnectionError,
                                   requests.exceptions.Timeout)),
)
def _get(url: str, params: dict) -> dict:
    resp = requests.get(url, params=params, timeout=(5, 30))
    if resp.status_code == 429:
        retry_after = int(resp.headers.get("Retry-After", 60))
        time.sleep(retry_after)
        resp.raise_for_status()   # force tenacity to retry
    resp.raise_for_status()
    return resp.json()
```

Key conventions:
- **API key** always from `os.environ` or `pydantic-settings`, never hard-coded.
- `timeout=(5, 30)` — 5 s connect, 30 s read; prevents infinite hangs.
- `wait_random_exponential` adds jitter to prevent thundering-herd after a shared outage ([tenacity docs](https://tenacity.readthedocs.io/en/stable/)).
- Respect `Retry-After` header on 429 before tenacity retries.

### 1.3 Where the image URL lives

| API | JSON field |
|-----|------------|
| NewsData.io | `article["image_url"]` |
| Currents API | `article["image"]` |
| NYT API | `article["multimedia"][0]["url"]` (filter `type=="image"`) |

Validate before downloading: skip `None`, empty string, or non-HTTP schemes.

---

## 2. Reddit / Fakeddit

### 2.1 When to use the static dump (preferred)

The Fakeddit dataset ships as TSV files + a Google Drive image archive. **Use the static dump** for all training/validation work. It is faster, reproducible, quota-free, and pre-split.

```python
import pandas as pd

# Load the multimodal-only split (paper-comparable subset)
df = pd.read_csv(
    "multimodal_only_samples/train.tsv",
    sep="\t",
    dtype={"id": str},
)

# Core columns
# clean_title  — filtered text
# image_url    — Reddit-hosted image URL
# 2_way_label  — 0=real, 1=fake
# 3_way_label  — 0=real, 1=fake, 2=satire
# 6_way_label  — 0=true, 1=satire, 2=false-connection,
#                3=imposter, 4=manipulated, 5=fake

# Drop rows missing either modality
df = df.dropna(subset=["clean_title", "image_url"])
df = df[df["image_url"].str.startswith("http")]
```

**Label convention**: for disinformation (not satire) experiments, filter `6_way_label != 1` or simply use `2_way_label`.

### 2.2 Downloading images from the TSV

The official `image_downloader.py` does the bulk work. For custom pipelines, mirror the pattern:

```python
from pathlib import Path
import requests

IMG_DIR = Path("data/fakeddit/images")
IMG_DIR.mkdir(parents=True, exist_ok=True)

def download_fakeddit_image(row: dict) -> Path | None:
    dest = IMG_DIR / f"{row['id']}.jpg"
    if dest.exists():
        return dest
    try:
        r = requests.get(row["image_url"], timeout=(5, 20), stream=True)
        r.raise_for_status()
        ct = r.headers.get("Content-Type", "")
        if not ct.startswith("image/"):
            return None
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 16):
                f.write(chunk)
        return dest
    except Exception:
        return None
```

The Google Drive archive (`public_image_set.tar.gz`) is preferable to re-downloading all URLs — some Reddit-hosted images have link-rotted since 2019.

### 2.3 PRAW for live Reddit acquisition

Use PRAW only when you need **fresh, unlabeled Reddit posts** (e.g., to augment or test the live pipeline). It is not needed for the static Fakeddit dump.

```python
import praw

reddit = praw.Reddit(
    client_id=settings.REDDIT_CLIENT_ID,
    client_secret=settings.REDDIT_CLIENT_SECRET,
    user_agent="CheckIt.AI research bot/0.1",
)

for submission in reddit.subreddit("worldnews+politics").new(limit=100):
    if submission.url.endswith((".jpg", ".jpeg", ".png", ".gif")):
        yield {
            "id": submission.id,
            "title": submission.title,
            "image_url": submission.url,
            "subreddit": submission.subreddit.display_name,
        }
```

Rate limit: 100 requests/minute on OAuth. The 1 000-post hard cap per subreddit listing applies ([Reddit API limits](https://data365.co/blog/reddit-api-limits)); use Pushshift/Arctic Shift archives for historical bulk pulls.

---

## 3. Research Dataset Ingestion — FakeNewsNet, MMFakeBench, COSMOS

### 3.1 FakeNewsNet (GitHub crawler script)

FakeNewsNet is not downloadable as a static archive — you run the ingestion script against live publisher pages.

```bash
# 1. Clone and configure
git clone https://github.com/KaiDMML/FakeNewsNet
cd FakeNewsNet
cp code/resources/tweet_keys_file.json.example code/resources/tweet_keys_file.json
# Edit tweet_keys_file.json with your Twitter API credentials

# 2. Configure config.json
# "data_collection_choice": [
#   {"news_source": "politifact", "label": "fake"},
#   {"news_source": "politifact", "label": "real"}
# ]
# "data_features_to_collect": ["news_articles"]  # skip tweets if no Twitter key

# 3. Run
python -m resource_server.app &   # key management server
python main.py
```

Images are extracted from article HTML during the `news_articles` phase and stored under `images` in each article's `news_content.json`. Key gotchas:

- **Link rot**: ~15–30% of older article URLs return 404; add retry with exponential backoff and log failures.
- **Twitter keys required** for social features; you can skip those by setting `data_features_to_collect` to `["news_articles"]` only.
- **Parallel processes**: `num_process: 4` is the default; increase to 8–16 on a fast connection.

Post-download, load into pandas:

```python
import json
from pathlib import Path

records = []
for json_path in Path("fakenewsnet_dataset/politifact/fake").rglob("news_content.json"):
    content = json.loads(json_path.read_text())
    records.append({
        "id": json_path.parent.name,
        "title": content.get("title"),
        "text": content.get("text"),
        "images": content.get("images", []),
        "label": "fake",
        "source": "politifact",
    })
```

### 3.2 MMFakeBench (Hugging Face gated dataset)

MMFakeBench is hosted on Hugging Face under `liuxuannan/MMFakeBench` with a data-usage agreement.

```python
# 1. Accept the usage agreement at https://huggingface.co/datasets/liuxuannan/MMFakeBench
# 2. Set HF_TOKEN in your environment
from datasets import load_dataset
import os

ds = load_dataset(
    "liuxuannan/MMFakeBench",
    token=os.environ["HF_TOKEN"],   # required for gated datasets
    split="test",
)

# Key fields: "text", "image_path", "gt_answers" (0/1), "fake_cls" (0-11 subtypes)
for sample in ds:
    text      = sample["text"]
    image_pil = sample["image"]    # PIL.Image loaded automatically by HF
    label     = sample["gt_answers"]
    subtype   = sample["fake_cls"]
```

The `datasets` library streams and caches the images locally; `sample["image"]` is already a PIL object, so no separate download step is needed. HF token must be provided programmatically in scripts ([HF gated datasets docs](https://huggingface.co/docs/hub/en/datasets-gated)).

### 3.3 COSMOS (Google Form access)

```
1. Fill the request form: https://docs.google.com/forms/d/13kJQ2wlv7sxyXoaM1Ddon6Nq7dUJY_oftl-6xzwTGow/
2. You receive download scripts by email from shivangi.aneja@tum.de
3. Run the provided download script — it fetches 160K train / 40K val / 1.7K test images
```

The COSMOS dataset structure: each sample has an image and two captions (one contextually consistent, one out-of-context). Load the manifest JSON:

```python
import json

with open("cosmos/annotations/train.json") as f:
    annotations = json.load(f)

for item in annotations:
    img_path = f"cosmos/images/{item['image_id']}.jpg"
    caption_consistent   = item["caption1"]
    caption_inconsistent = item["caption2"]
    label = item["label"]   # 0=consistent, 1=out-of-context
```

**Gotcha**: image filenames must be verified to exist; a small fraction of scraped images fail to download. Use `Path(img_path).exists()` checks before adding to the training set.

---

## 4. RSS Feeds

### 4.1 Parsing with feedparser

```python
import feedparser, hashlib, requests
from bs4 import BeautifulSoup

def parse_feed(feed_url: str) -> list[dict]:
    feed = feedparser.parse(feed_url)
    seen_guids: set[str] = set()
    records = []

    for entry in feed.entries:
        guid = entry.get("id") or entry.get("link", "")
        if guid in seen_guids:
            continue
        seen_guids.add(guid)

        title    = entry.get("title", "")
        text     = entry.get("summary", "")
        pub_date = entry.get("published", "")
        link     = entry.get("link", "")
        image_url = _extract_image(entry, link)

        records.append({
            "guid": guid,
            "title": title,
            "text": text,
            "pub_date": pub_date,
            "link": link,
            "image_url": image_url,
        })
    return records
```

### 4.2 Image extraction cascade (priority order)

```python
def _extract_image(entry: dict, article_url: str) -> str | None:
    # 1. media:content (most reliable in news feeds)
    for m in entry.get("media_content", []):
        if m.get("medium") == "image" or m.get("url", "").endswith(
            (".jpg", ".jpeg", ".png", ".webp")
        ):
            return m["url"]

    # 2. media:thumbnail
    thumb = entry.get("media_thumbnail")
    if thumb:
        return thumb[0].get("url")

    # 3. enclosures
    for enc in entry.get("enclosures", []):
        if enc.get("type", "").startswith("image/"):
            return enc.get("href")

    # 4. First <img> inside content:encoded
    content_html = entry.get("content", [{}])[0].get("value", "")
    if content_html:
        soup = BeautifulSoup(content_html, "lxml")
        img = soup.find("img", src=True)
        if img:
            return img["src"]

    # 5. Fallback: fetch the article page and read og:image
    if article_url:
        return _og_image_from_url(article_url)

    return None


def _og_image_from_url(url: str) -> str | None:
    try:
        r = requests.get(url, timeout=(5, 15), headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.content, "lxml")
        tag = soup.find("meta", property="og:image") or \
              soup.find("meta", attrs={"name": "twitter:image"})
        return tag["content"] if tag else None
    except Exception:
        return None
```

### 4.3 Dedup across feed runs

Use a SHA-256 hash of `guid.strip()` as the dedup key, persisted in a small SQLite table or a `set` loaded from a flat file between runs. Do not rely on titles — headlines get edited.

---

## 5. Web Scraping (last resort)

The brief identifies scraping as a fallback. Apply it only when no API or dataset dump exists (e.g., fetching article pages to retrieve full text and images for FakeNewsNet during download, or augmenting RSS feeds that lack `og:image`).

### 5.1 Decision tree

```
Is the content in static HTML?
  YES → requests + BeautifulSoup (fast, no JS overhead)
        Use trafilatura for main-text extraction (see §6.2)
  NO  → Is it a one-off or small crawl?
          YES → Playwright (async, built-in waiting, lower mem than Selenium)
          NO  → Large-scale crawl of thousands of pages?
                  YES → Scrapy (async pipeline, built-in middleware, robots.txt middleware)
                  NO  → Playwright or Selenium
```

Playwright is preferred over Selenium for new code: ~12% faster page load and ~15% lower memory in benchmarks ([ScrapingBee, 2025](https://www.scrapingbee.com/blog/playwright-for-python-web-scraping/)); auto-waiting reduces flakiness.

### 5.2 robots.txt compliance (required)

```python
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin

_rp_cache: dict[str, RobotFileParser] = {}

def is_allowed(url: str, user_agent: str = "*") -> bool:
    from urllib.parse import urlparse
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    if base not in _rp_cache:
        rp = RobotFileParser()
        rp.set_url(urljoin(base, "/robots.txt"))
        rp.read()
        _rp_cache[base] = rp
    return _rp_cache[base].can_fetch(user_agent, url)
```

Scrapy enables `ROBOTSTXT_OBEY = True` in `settings.py` automatically. Always set a descriptive `User-Agent` identifying your project and email.

### 5.3 Polite crawl

- Minimum 1–2 s delay between requests to the same domain (`DOWNLOAD_DELAY` in Scrapy; `time.sleep` in requests loops).
- Cache responses with `requests_cache` or vcrpy during development.
- Never scrape sites whose ToS explicitly prohibit it.

---

## 6. Cross-Cutting Techniques

### 6.1 Image download and validation

```python
import io
from PIL import Image, UnidentifiedImageError
import requests

MAX_IMAGE_BYTES = 10 * 1024 * 1024   # 10 MB hard cap

def download_and_validate_image(url: str, dest_path: str) -> bool:
    try:
        r = requests.get(url, stream=True, timeout=(5, 30))
        r.raise_for_status()
        ct = r.headers.get("Content-Type", "")
        if not ct.startswith("image/"):
            return False

        buf = bytearray()
        for chunk in r.iter_content(4096):
            buf.extend(chunk)
            if len(buf) > MAX_IMAGE_BYTES:
                return False   # size cap

        # Pillow verify — raises on truncated/corrupt files
        img = Image.open(io.BytesIO(bytes(buf)))
        img.verify()

        # Re-open after verify (verify() leaves the file pointer exhausted)
        img = Image.open(io.BytesIO(bytes(buf)))
        img.save(dest_path)
        return True
    except (UnidentifiedImageError, OSError, requests.RequestException):
        return False
```

Notes:
- `img.verify()` detects truncated/corrupt images; after calling it, you **must** re-open for further use ([Pillow docs](https://pillow.readthedocs.io/en/stable/)).
- Check `Content-Type` header first to skip PDF/HTML responses masquerading as images.
- Size cap prevents runaway downloads of video or multi-GB assets.

### 6.2 Text cleaning

```python
import trafilatura
import langdetect
import re, unicodedata

def extract_and_clean_text(html_or_url: str, is_url: bool = False) -> str | None:
    if is_url:
        downloaded = trafilatura.fetch_url(html_or_url)
    else:
        downloaded = html_or_url

    # trafilatura removes nav, ads, boilerplate; falls back to readability-lxml
    text = trafilatura.extract(downloaded, favor_precision=True, with_metadata=False)
    if not text:
        return None

    # Unicode normalisation
    text = unicodedata.normalize("NFKC", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def detect_language(text: str) -> str:
    try:
        return langdetect.detect(text)
    except langdetect.lang_detect_exception.LangDetectException:
        return "unknown"
```

Trafilatura outperforms html2text for news articles: F1 0.883 on the SIGIR benchmark, with readability-lxml and jusText as automatic fallbacks ([Trafilatura evaluation](https://trafilatura.readthedocs.io/en/latest/evaluation.html)).

### 6.3 Text↔image pairing integrity check

Before serialising a record, enforce that both modalities are present:

```python
def is_valid_pair(record: dict) -> bool:
    has_text  = bool(record.get("text", "").strip())
    has_image = bool(record.get("local_image_path")) and \
                Path(record["local_image_path"]).exists()
    return has_text and has_image
```

Log and count skipped unpaired records per source in a pipeline run summary.

### 6.4 Deduplication

```python
import hashlib
import imagehash
from PIL import Image

def text_fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

def image_phash(image_path: str) -> str:
    img = Image.open(image_path).convert("L").resize((64, 64))
    return str(imagehash.phash(img))

# Two records are near-duplicates if:
# text_fingerprint matches exactly  (exact text dup)
# OR image phash Hamming distance < 10  (near-visual dup)
```

[`imagehash`](https://github.com/JohannesBuchner/imagehash) implements average hash, perceptual hash (pHash), difference hash, and wavelet hash. pHash (DCT-based) is the most robust for news images. SHA-256 on the canonical article URL is the cheapest first-pass dedup; pHash catches re-compressed or re-hosted versions of the same image.

### 6.5 Output serialisation — when to use what format

| Format | When to use | Python |
|--------|-------------|--------|
| **JSON Lines** (`.jsonl`) | Raw ingest output; streaming writes; human-inspectable; heterogeneous schemas | `json.dumps(record) + "\n"` per line |
| **CSV** | Flat tabular data for sharing/debugging; labels-only index files | `pandas.to_csv(index=False)` |
| **Parquet** | Training-ready feature tables; column-selective reads; long-term storage; ML frameworks | `pandas.to_parquet("out.parquet", engine="pyarrow", compression="snappy")` |

**Recommended pipeline layering:**
```
raw/       ← JSONL (one file per source per day, unmodified)
processed/ ← Parquet (cleaned, validated, paired, deduped)
index/     ← CSV  (per-record labels + local_image_path for audit)
```

Parquet is ~4× smaller than CSV and 13× faster for column-selective reads ([DriveDataScience, 2024](https://www.drivedatascience.com/parquet-csv-json-file-format-comparison/)).

### 6.6 Config management

```python
# settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    newsdata_api_key: SecretStr
    hf_token: SecretStr
    currents_api_key: SecretStr = ""
    max_articles_per_run: int = 2000
    image_dir: str = "data/images"
    output_dir: str = "data/processed"

settings = Settings()
api_key = settings.newsdata_api_key.get_secret_value()
```

`SecretStr` prevents the value from appearing in logs or `repr()` output. `.env` file is never committed; `.env.example` with empty placeholders is ([pydantic-settings docs](https://docs.pydantic.dev/latest/api/pydantic_settings/)).

### 6.7 Structured logging

```python
import logging
import json

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

log = get_logger("checkit.ingest")
log.info("article fetched", extra={"source": "newsdata", "image_url": url})
```

For production pipelines, [structlog](https://www.structlog.org/) provides processor-chain-based context propagation and automatic JSON rendering with lower boilerplate. The standard `logging` module with a `JsonFormatter` is adequate for a junior pipeline and avoids extra dependencies.

### 6.8 Error handling patterns

```python
import logging
from contextlib import contextmanager

log = logging.getLogger(__name__)

@contextmanager
def safe_record(source: str, record_id: str):
    """Wrap per-record processing; log and continue on any failure."""
    try:
        yield
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        log.warning(
            "record_failed",
            extra={"source": source, "id": record_id, "error": str(exc)},
        )
```

Usage:
```python
for record in records:
    with safe_record("fakeddit", record["id"]):
        process(record)
```

Rules:
- Catch broadly inside `safe_record` — never let a single bad record crash the pipeline.
- Always re-raise `KeyboardInterrupt` (and `SystemExit`).
- Log source + record ID at `WARNING`; reserve `ERROR` for unrecoverable failures.

### 6.9 Unit-testing transform functions

```python
# tests/test_transforms.py
import responses   # or vcrpy for cassette-based tests
import pytest
from checkit.ingest.text import extract_and_clean_text
from checkit.ingest.image import download_and_validate_image

@responses.activate
def test_extract_text_from_article():
    responses.add(
        responses.GET,
        "https://example.com/article",
        body="<html><body><p>Main content here.</p></body></html>",
        status=200,
    )
    result = extract_and_clean_text("https://example.com/article", is_url=True)
    assert "Main content" in result


@responses.activate
def test_download_image_wrong_content_type():
    responses.add(
        responses.GET,
        "https://example.com/image.jpg",
        body=b"not an image",
        headers={"Content-Type": "text/html"},
        status=200,
    )
    assert download_and_validate_image("https://example.com/image.jpg", "/tmp/test.jpg") is False
```

- [`responses`](https://github.com/getsentry/responses): intercepts `requests` calls; best for unit tests of single functions.
- [`vcrpy`](https://github.com/kevin1024/vcrpy): records real HTTP to YAML cassettes and replays them; best for integration tests or testing full ingestion flows ([vcrpy docs](https://vcrpy.readthedocs.io/en/latest/)).
- Run with: `python -m pytest tests/ -v --tb=short`.

---

## 7. Library Stack Table

| Library | Role | Why / Notes | Brief-named? |
|---------|------|-------------|--------------|
| [`requests`](https://pypi.org/project/requests/) | Synchronous HTTP client | Universal, simple API; pair with urllib3 `Retry` for basic retry | **Yes** |
| [`httpx`](https://pypi.org/project/httpx/) | Async HTTP client | Requests-compatible API + async; 7× faster for parallel fetches; use for image batch downloads | No |
| [`tenacity`](https://pypi.org/project/tenacity/) | Retry decorator | Cleaner than urllib3 `Retry` for arbitrary code paths; `wait_random_exponential` adds jitter | No |
| [`urllib3`](https://pypi.org/project/urllib3/) | urllib3 `Retry` adapter | Pairs with `requests.Session` for connection-level retry; no extra dependency | No |
| [`feedparser`](https://pypi.org/project/feedparser/) | RSS/Atom parsing | Handles all feed dialects; `media_content`, `enclosures`, `media_thumbnail` | **Yes** |
| [`BeautifulSoup4`](https://pypi.org/project/beautifulsoup4/) + `lxml` | HTML parsing / og:image | Fast, CSS selectors; use `lxml` parser for speed | **Yes** |
| [`Scrapy`](https://pypi.org/project/Scrapy/) | Large-scale crawling | Async pipeline, `ROBOTSTXT_OBEY`, `DOWNLOAD_DELAY`, built-in middleware | **Yes** |
| [`Selenium`](https://pypi.org/project/selenium/) / [`Playwright`](https://pypi.org/project/playwright/) | JS-rendered pages | Playwright preferred (faster, lower mem, auto-wait) for new code | **Yes (Selenium)** |
| [`trafilatura`](https://pypi.org/project/trafilatura/) | Main-text extraction | Best F1 for news boilerplate removal; falls back to readability/jusText | No |
| [`Pillow`](https://pypi.org/project/Pillow/) | Image validation | `Image.verify()`, format checks, corrupt detection | No |
| [`imagehash`](https://pypi.org/project/ImageHash/) | Perceptual image dedup | pHash detects re-hosted/re-compressed duplicates; Hamming distance threshold | No |
| [`pandas`](https://pypi.org/project/pandas/) | Tabular data loading | TSV→DataFrame for Fakeddit; CSV/Parquet I/O | No |
| [`pyarrow`](https://pypi.org/project/pyarrow/) | Parquet I/O | `pandas.to_parquet` backend; Snappy compression | No |
| [`datasets`](https://pypi.org/project/datasets/) (HuggingFace) | HF dataset loading | `load_dataset` for MMFakeBench and gated datasets | No |
| [`pydantic-settings`](https://pypi.org/project/pydantic-settings/) | Config + secrets | `BaseSettings` + `.env`; `SecretStr` hides keys in logs | No |
| [`newsdataapi`](https://pypi.org/project/newsdataapi/) | NewsData.io SDK | Official client; built-in pagination/retry; `image_url` in every response | No |
| [`PRAW`](https://pypi.org/project/praw/) | Reddit API | OAuth auth; for live Reddit collection only (not needed for Fakeddit dump) | No |
| [`langdetect`](https://pypi.org/project/langdetect/) | Language detection | Filter non-target-language articles post-extraction | No |
| [`pytest`](https://pypi.org/project/pytest/) + [`responses`](https://pypi.org/project/responses/) | Unit testing | `responses` mocks `requests` calls; avoid real HTTP in unit tests | No |
| [`vcrpy`](https://pypi.org/project/vcrpy/) | Integration testing | YAML cassettes for full-flow HTTP mocking | No |
| `logging` (stdlib) | Structured logging | JSON formatter; no extra dep; structlog if you need context propagation | No |
| `urllib.robotparser` (stdlib) | robots.txt compliance | `can_fetch()` before any scrape request | No |

---

## Sources

- [newsdataapi PyPI](https://pypi.org/project/newsdataapi/)
- [NewsData.io pagination blog](https://newsdata.io/blog/newsdata-pagination/)
- [NewsData.io Python client guide](https://newsdata.io/blog/news-api-python-client/)
- [NewsData.io rate limits](https://newsdata.io/blog/newsdata-rate-limit/)
- [Fakeddit GitHub](https://github.com/entitize/Fakeddit)
- [Fakeddit paper](https://arxiv.org/abs/1911.03854)
- [FakeNewsNet GitHub](https://github.com/KaiDMML/FakeNewsNet)
- [MMFakeBench HuggingFace](https://huggingface.co/datasets/liuxuannan/MMFakeBench)
- [HuggingFace gated datasets docs](https://huggingface.co/docs/hub/en/datasets-gated)
- [COSMOS GitHub](https://github.com/shivangi-aneja/COSMOS)
- [COSMOS data request form](https://docs.google.com/forms/d/13kJQ2wlv7sxyXoaM1Ddon6Nq7dUJY_oftl-6xzwTGow/)
- [COSMOS docs](https://cosmos-dataset.readthedocs.io/en/latest/tutorials/info.html)
- [tenacity docs](https://tenacity.readthedocs.io/en/stable/)
- [tenacity retry exponential backoff guide](https://oneuptime.com/blog/post/2025-01-06-python-retry-exponential-backoff/view)
- [Python requests retry (ScrapeOps)](https://scrapeops.io/python-web-scraping-playbook/python-requests-retry-failed-requests/)
- [Trafilatura usage-python docs](https://trafilatura.readthedocs.io/en/latest/usage-python.html)
- [Trafilatura evaluation](https://trafilatura.readthedocs.io/en/latest/evaluation.html)
- [Pillow image verify docs](https://pc-pillow.readthedocs.io/en/latest/Image_class/Image_verify.html)
- [imagehash GitHub (JohannesBuchner)](https://github.com/JohannesBuchner/imagehash)
- [imagehash PyPI](https://pypi.org/project/ImageHash/)
- [Duplicate image detection with pHash](https://benhoyt.com/writings/duplicate-image-detection/)
- [pydantic-settings docs](https://docs.pydantic.dev/latest/api/pydantic_settings/)
- [Parquet vs CSV vs JSON (DriveDataScience)](https://www.drivedatascience.com/parquet-csv-json-file-format-comparison/)
- [vcrpy GitHub](https://github.com/kevin1024/vcrpy)
- [pytest-recording + vcrpy](https://github.com/kiwicom/pytest-recording)
- [responses library (Getsentry)](https://github.com/getsentry/responses)
- [Playwright for Python (ScrapingBee)](https://www.scrapingbee.com/blog/playwright-for-python-web-scraping/)
- [Web scraping tools 2026 (DEV Community)](https://dev.to/agenthustler/top-web-scraping-tools-and-frameworks-in-2026-scrapy-selenium-playwright-beautifulsoup-and-more-3fai)
- [urllib.robotparser Python docs](https://docs.python.org/3/library/urllib.robotparser.html)
- [httpx vs requests vs aiohttp (Oxylabs)](https://oxylabs.io/blog/httpx-vs-requests-vs-aiohttp)
- [Structured logging Python (New Relic)](https://newrelic.com/blog/log/python-structured-logging)
- [PRAW Reddit API wrapper](https://praw.readthedocs.io/)
- [Reddit API rate limits](https://data365.co/blog/reddit-api-limits)
- [Feedparser PyPI](https://pypi.org/project/feedparser/)
- [fastfeedparser PyPI](https://pypi.org/project/fastfeedparser/)
