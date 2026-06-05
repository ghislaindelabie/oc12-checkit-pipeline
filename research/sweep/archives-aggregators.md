# OC12 Source Sweep — Archives & Aggregators

_Category: bulk archives and meta-index aggregators. Question for each source: access mechanics, binding rights basis (license/ToS/robots, not marketing), exact text-image pairing mechanism (field name), label availability, FR/EN coverage, free-tier limits, available metadata, realistic effort-to-first-record for a student, and whether it fits the AUTOMATED daily-pipeline shape or only the bulk-corpus shape._

_Sweep date: 2026-06-05. Framing: non-commercial graded exercise; any source whose binding terms permit research/non-commercial use is acceptable. Rights judged on the binding document only._

**Headline correction to prior research:** `research/02-data-sources.md` (2026-05-29) lists GDELT as **"AVOID for images — no direct image field"** and **"Text metadata only"**. This is **stale and wrong**. The GDELT GKG **V2.1 codebook** documents three per-article image-URL fields — `V2.1SHARINGIMAGE`, `V2.1RELATEDIMAGES`, `V2.1SOCIALIMAGEEMBEDS` — each on the **same CSV row** as the article text/metadata. GDELT GKG 2.1 therefore **does** provide paired text+image, free, every 15 minutes, in 65 live-translated languages including French. It is reclassified below from AVOID to a genuine pipeline-shaped candidate (the single best free FR-capable daily feed in this category). Details in §1.

---

## Pairing-mechanism cheat sheet (the load-bearing question)

| Source | Pairing mechanism (exact field) | Same record? | Pipeline shape |
|---|---|---|---|
| GDELT GKG 2.1 | `V2.1SHARINGIMAGE` (og:image of the article) in the GKG CSV row, joined to `DocumentIdentifier` (article URL) + `V2.1QUOTATIONS`/themes | Yes — same CSV row | Daily feed (15-min) |
| GDELT VGKG 2.0 | `ImageProperties.URL` (image) + `ImageProperties` article URL it was "first seen in" | Yes — per-image JSON record carries the article URL | Daily feed (60-sec) |
| GDELT DOC 2.0 API (ImageCollage/Gallery) | image URL returned alongside the matching article in JSON | Yes — per-result | Daily feed (on-demand query) |
| Common Crawl CC-NEWS | none native; you parse `<img src>` out of the WARC HTTP-response HTML and bind to the page text yourself | No — you construct it | Bulk corpus only |
| Internet Archive / Wayback | none native; CDX lists snapshots, you fetch the WARC/snapshot and parse `<img>` vs page text | No — you construct it | Bulk / point-lookup |
| Academic Torrents | depends on the wrapped dataset (e.g. Fakeddit's `image_url`) | Inherited | Bulk corpus |
| HF Hub | depends on the dataset; many expose an `image` (PIL/bytes) column next to `text`/`caption` | Inherited | Bulk corpus (meta-index) |
| Google Dataset Search | n/a — meta-index; pairing is whatever the landed dataset offers | n/a | Discovery only |
| Kaggle | depends on the dataset (e.g. Fakeddit mirror `image_url` + JPEGs) | Inherited | Bulk corpus (meta-index) |
| Zenodo / figshare / IEEE DataPort | depends on the deposited dataset | Inherited | Bulk corpus (meta-index) |
| AWS Open Data Registry | n/a — meta-index over S3-hosted datasets (incl. CC-NEWS) | n/a | Discovery / bulk |

---

## 1. GDELT GKG 2.1 (Global Knowledge Graph) — RECLASSIFIED, new analysis

- **URL:** https://www.gdeltproject.org/data.html ; codebook: http://data.gdeltproject.org/documentation/GDELT-Global_Knowledge_Graph_Codebook-V2.1.pdf
- **What it is.** A near-real-time CSV stream (one file every 15 minutes) summarising every news article GDELT monitors worldwide, including 65 live-translated languages. Each row is one article with NLP-derived themes, entities, tone, quotations, **and image URLs**.
- **Pairing mechanism (corrected).** The V2.1 codebook documents three image fields on the **same row** as the article:
  - **`V2.1SHARINGIMAGE`** — the article's social-sharing / og:image. Codebook: GDELT "recognizes a variety of formats for specifying this image, including Open Graph, Twitter Cards, Google+, IMAGE_SRC, and SailThru formats, among others." This is the single canonical image-per-article — the cleanest text↔image pair.
  - **`V2.1RELATEDIMAGES`** — semicolon-delimited list of in-article image URLs ("ranging from a single illustrative photograph at top, to lengthy photo essays").
  - **`V2.1SOCIALIMAGEEMBEDS`** — semicolon-delimited URLs of embedded image-based Twitter/Instagram posts ("Only those posts containing imagery are included").
  The article URL is `DocumentIdentifier`; the article text is not stored, but title/themes/quotations/tone are, and you can fetch the article HTML from `DocumentIdentifier` if you want the body.
- **Labels.** None. Unlabeled feed. Use for the "real news" side or weak-label by cross-referencing fact-check feeds. (GDELT's GCAM tone is sentiment, not veracity.)
- **FR/EN.** Both, natively. French is among the 65 live-translated languages; for a French article the row carries the French `DocumentIdentifier` and its og:image, plus an English-translated GKG. ~98.4% of non-English volume is translated.
- **Binding rights.** GDELT terms (gdeltproject.org/about.html): _"All datasets released by the GDELT Project are available for unlimited and unrestricted use for any academic, commercial, or governmental use of any kind without fee."_ Attribution required: cite the GDELT Project + link the site. **Caveat (judge on the binding clause):** GDELT's own *metadata* is freely licensed, but `V2.1SHARINGIMAGE` is a **third-party publisher URL** — downloading and reusing the actual image is governed by that publisher's rights, not GDELT's grant. For a non-commercial research exercise this is acceptable; cache at ingest and record provenance.
- **Free-tier limits.** 100% free, no key, no quota. Files at `http://data.gdeltproject.org/gdeltv2/<YYYYMMDDHHMMSS>.gkg.csv.zip`; master pointer `http://data.gdeltproject.org/gdeltv2/lastupdate.txt` (English) and `lastupdate-translation.txt` (translingual), refreshed every 15 min.
- **Metadata fields.** `GKGRECORDID`, `V2.1DATE`, `V2SOURCECOMMONNAME`, `DocumentIdentifier`, `V1Themes`/`V2EnhancedThemes`, `V1Locations`, `V1Persons`, `V1Organizations`, `V1.5Tone`, `V2.1Quotations`, `V2.1AllNames`, `V2.1Amounts`, `V2.1SharingImage`, `V2.1RelatedImages`, `V2.1SocialImageEmbeds`, `V2.1SocialVideoEmbeds`, plus the GKG 2.0 article-metadata fields `PAGE_LINKS`, `PAGE_AUTHORS`, `PAGE_PRECISEPUBTIMESTAMP`, `PAGE_ALTURL_AMP`, `PAGE_ALTURL_MOBILE`.
- **Extraction.** Python: loop on `lastupdate.txt` → download the `.gkg.csv.zip` → `pandas.read_csv(sep='\t')` (tab-delimited despite the `.csv` name) → split `V2.1SHARINGIMAGE`/`V2.1RELATEDIMAGES` on `;` → download + cache images. Airflow: a 15-min or daily scheduled DAG. Mature wrappers exist (`gdeltdoc`, `gdeltPyR`), but the raw file loop is trivial and dependency-free.
- **Effort-to-first-record.** Very low — minutes; no account, one HTTP GET + a CSV parse.
- **Pipeline fit.** **Daily/15-min automated feed.** This is the strongest fit in the category for the OC12 "unattended daily pipeline" shape *and* the only free source here with native French + per-article image URL.
- **fit: 4.0** (paired text-ref+image in one row, free, FR+EN, fully automatable; minus: no veracity label, image is a third-party URL that can rot, article body needs a second fetch).

## 2. GDELT VGKG 2.0 (Visual Global Knowledge Graph) — new analysis

- **URL:** https://blog.gdeltproject.org/vgkg-2-0-released/ ; stream pointer `http://data.gdeltproject.org/gdeltv3/vgkg/lastupdate.txt`
- **What it is.** Every image GDELT finds in monitored news, run through Google Cloud Vision (labels, OCR, web entities, face/landmark detection, safe-search). VGKG 2.0 updates every 60 seconds (branded "GDELT 3.0").
- **Pairing mechanism.** Per-image JSON record. The `RawJSON.ImageProperties` block carries the timestamp GDELT first saw the image **and "the URL of the article it was first seen in"** — that article URL is the bind back to text. `RawJSON.EXIF` holds embedded EXIF/IPTC/XMP. Images are resized to ≤1500×1500 and re-encoded JPEG/WEBP; MD5 + perceptual hashes included for dedup/near-dup.
- **Labels.** No veracity label. Rich *content* annotations (Vision API labels/OCR/web tags) — useful as features for OOC/manipulation detection, not as ground truth.
- **FR/EN.** Both (rides the same multilingual monitoring); estimated image languages included.
- **Binding rights.** Same GDELT free-use terms + attribution as §1. The annotation metadata is GDELT's to license; the underlying image is a third-party URL — same caching/provenance caveat.
- **Free-tier limits.** Free, no key. 60-second cadence is high-volume; a student should sample, not ingest the firehose.
- **Extraction.** Poll `gdeltv3/vgkg/lastupdate.txt` → fetch the JSON file → parse per-image records → join to article via `ImageProperties` article URL. Heavier than GKG.
- **Pipeline fit.** Automated feed, but image-centric and high-volume; better as a *visual-features enrichment* side-feed than the primary text+image acquisition.
- **fit: 3.0** (image+article-URL pairing, free, FR+EN, automatable; minus: no veracity label, article text needs separate fetch, firehose volume, Vision tags ≠ truth).

## 3. GDELT DOC 2.0 API (ImageCollage / Gallery mode) — new analysis

- **URL:** https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/ ; gallery: https://blog.gdeltproject.org/gallery-mode-now-available-doc-2-0-api/ ; base `https://api.gdeltproject.org/api/v2/doc/doc`
- **What it is.** A keyword/full-text query API over the last ~3 months of GDELT coverage. `mode=ImageCollage`/`ImageCollageInfo`/Gallery returns the VGKG-processed images contained in matching articles; `mode=ArtList` returns articles. `format=json` (JSONFeed) supported. Searchable image operators: `imagewebtag:` (caption/web tags) and `imagetag:` (Vision ground-truth labels).
- **Pairing mechanism.** Per-result JSON pairs an image URL with its source article (and `socialimage` for ArtList). Lets you *query by image content* ("imagetag:protest") — unique for targeted OOC corpus building.
- **Labels.** None (veracity). Image content tags available as filters.
- **FR/EN.** Search across all 65 translated languages using English keywords; `sourcelang:fre` narrows to French. Strong FR fit.
- **Binding rights.** Free GDELT terms + attribution (§1). Third-party image-URL caveat applies.
- **Free-tier limits.** Free, no key. Soft fair-use throttling (the project asks for ~1 query/sec, ≤250 results/call). Rolling ~3-month window — not a deep historical archive.
- **Extraction.** Plain `requests.get` with query params; or the `gdeltdoc` Python client. Trivial.
- **Pipeline fit.** Automated daily *targeted* feed (query for topics/claims of interest), complements the GKG firehose.
- **fit: 3.5** (image↔article pairing in JSON, free, FR+EN, queryable by image content, fully automatable; minus: no veracity label, 3-month window, fair-use throttle).

## 4. Common Crawl CC-NEWS — new analysis (access mechanics changed in 2025)

- **URL:** https://commoncrawl.org/news-crawl ; data root https://data.commoncrawl.org/crawl-data/CC-NEWS/ ; ToU https://commoncrawl.org/terms-of-use
- **What it is.** Daily WARC files of crawled news articles since 2016, hundreds of GB/month. Full HTTP responses (headers + raw HTML).
- **Pairing mechanism.** **None native.** WARC stores the page's raw HTML; you parse `<img src>` (and og:image) with BeautifulSoup/`warcio` and bind images to the extracted article text yourself. WET files give plaintext only (no images); WAT gives metadata/links. To get text+image you must process full **WARC**.
- **Labels.** None.
- **FR/EN.** Both — CC-NEWS is global; French news sites are well represented. (`CC-News-En` is a curated English-only derivative on AWS ODR.)
- **Binding rights (critical — judge on the clause).** Common Crawl ToU: the crawled content _"is the sole responsibility of the individual or entity from which such Crawled Content originated"_; CC grants only a _"limited, non-assignable, non-transferable, non-sublicensable, non-exclusive, limited license to access and use the Service"_ and _"do not and cannot offer a license to the crawled page contents."_ By using it _"YOU AGREE TO RESPECT THE COPYRIGHTS AND OTHER APPLICABLE RIGHTS OF THIRD PARTIES."_ **Section 9 indemnification names AI/ML explicitly:** users must indemnify CC for claims arising from _"use of Crawled Content in connection with artificial intelligence, machine learning … including large language models"_ and for third-party copyright/trademark infringement; CC's liability is capped at **$100**. → CC licenses *the service*, not the *content*. For a non-commercial student exercise the risk is low, but the ToU explicitly flags ML use and pushes all third-party-rights liability onto the user. Document this; do not present CC as a clean license.
- **Free-tier limits.** Free. **2025 change:** unsigned `s3://commoncrawl/` access has been **disabled** — `aws s3 --no-sign-request` no longer works. Free access is now via HTTPS (`https://data.commoncrawl.org/...`) or the new CloudFront endpoint; S3 API needs an authenticated AWS account (egress applies if you copy out of AWS).
- **Metadata fields.** WARC record headers: `WARC-Target-URI`, `WARC-Date`, `Content-Type`, HTTP headers; payload = full HTML (parse title/og:image/img/body yourself). CC publishes a `cc-index` (columnar, Athena-queryable) to locate URLs by domain/date/mime before fetching byte-ranges.
- **Extraction.** `warcio.ArchiveIterator` over WARC + BeautifulSoup, or the `news-please` library which reads CC-NEWS WARCs and returns structured articles (title, text, top image). For scale use the columnar index + byte-range GETs rather than whole files.
- **Effort-to-first-record.** Medium — you must understand WARC, set up parsing, and (for S3) authenticate. First *record* in an afternoon via `news-please` + one HTTPS WARC; first *clean text+image corpus* is days of plumbing.
- **Pipeline fit.** **Bulk corpus**, not a tidy daily feed (it *is* daily-published, but per-file processing is heavy and pairing is DIY). Better as a one-shot historical FR/EN news pull than the live pipeline spine.
- **fit: 2.5** (huge FR+EN coverage, free, daily; minus: no native pairing, no labels, ToU pushes ML/copyright liability onto user, 2025 unsigned-S3 removal raised effort).

## 5. Internet Archive / Wayback Machine — new analysis

- **URL:** https://archive.org ; Availability API https://archive.org/wayback/available ; CDX https://web.archive.org/cdx/search/cdx ; ToU https://archive.org/about/terms
- **What it is.** The web's archive. For OC12 the use case is recovering **snapshots of fact-checked / since-deleted fake-news pages** (a known fact-check page URL → its archived HTML+images at the time of the false claim) and building point-in-time corpora.
- **Pairing mechanism.** **None native.** CDX lists captures; you fetch the archived snapshot (`https://web.archive.org/web/<timestamp>/<url>` or its WARC) and parse `<img>` vs text. Pairing is DIY, identical in shape to Common Crawl.
- **Labels.** None from IA. But IA is the natural *companion* to fact-check feeds: a fact-check supplies the veracity label + the debunked URL; IA supplies the archived page (text+images) that the label refers to. This is the strongest labeling synergy in the category.
- **FR/EN.** Both — archives any public URL regardless of language; French fact-check targets fully covered.
- **Binding rights.** IA Terms: users _"certify that your use of any part of the Archive's Collections will be limited to noninfringing or fair use under copyright law"_ and must _"abide by all applicable laws … including intellectual property laws."_ Many items are _"non commercial use … with attribution"_ only. No blanket reuse license — IA is access, not a rights grant; the archived content's own copyright stands. Acceptable for a non-commercial research exercise under fair-use framing; cite the source page.
- **Free-tier limits.** Free, no key. **Note:** the `/cdx/search/cdx?url=*` wildcard `/all` endpoint is *temporarily blocked due to DDoS mitigation* (2025); exact/prefix/domain queries work. Be gentle (sub-1 req/sec); IA throttles heavy automated traffic and its ToU discourages bulk scraping.
- **Metadata fields.** Availability API JSON: `archived_snapshots.closest.{available, url, timestamp, status}`. CDX rows (`output=json`): `urlkey, timestamp, original, mimetype, statuscode, digest, length` — filterable (`filter=statuscode:200`, `filter=mimetype:text/html`, `collapse`, `from`/`to`, `matchType`).
- **Extraction.** `requests` against CDX (`output=json`) to enumerate captures, then fetch each snapshot and parse with BeautifulSoup; or `warcio`/the `wayback` Python lib. SavePageNow API can archive a live page on demand before it disappears.
- **Effort-to-first-record.** Low for a single known URL (one Availability call); medium to build a snapshot corpus.
- **Pipeline fit.** Best as a **point-lookup / enrichment** step inside an automated pipeline (resolve each fact-checked URL → archived snapshot), not a standalone feed. Excellent for the "fetch the actual fake page behind a fact-check label" job.
- **fit: 3.0** (free, FR+EN, the label-bridging companion to fact-check feeds, automatable point lookups; minus: no native pairing, no labels itself, DIY HTML parsing, throttling/DDoS-mode endpoint limits).

## 6. Academic Torrents — new analysis

- **URL:** https://academictorrents.com
- **What it is.** A BitTorrent-based distributed repository (>298 TB by 2025) where researchers host large datasets — including mirrors of fake-news/multimodal corpora too big for GitHub.
- **Pairing mechanism.** **Inherited** from the wrapped dataset (e.g. a Fakeddit or FakeNewsNet mirror keeps its `image_url`/JPEG pairing). AT is a transport, not a schema.
- **Labels.** Inherited from the dataset.
- **FR/EN.** Inherited.
- **Binding rights.** AT itself imposes none beyond requiring uploaders to _"have the legal right to share and distribute files"_ and to _"specify what use license — such as General Public License or Creative Commons"_; AT complies with takedown requests. → The binding license is **whatever the uploader declared on that torrent**; verify per dataset, and treat unlicensed mirrors as untrusted.
- **Free-tier limits.** Free; throughput depends on seeders (popular datasets fast, niche ones may stall).
- **Metadata fields.** Per torrent: title, size, files list, uploader-declared license, infohash, seeders/leechers.
- **Extraction.** `aria2c`/`transmission-cli` to fetch the `.torrent`/magnet; then process the contained dataset normally.
- **Effort-to-first-record.** Low-medium (install a torrent client; wait on seeders).
- **Pipeline fit.** **Bulk corpus** only — one-shot historical pull; not a daily feed. Mainly a resilience/mirror channel when a primary host (Google Drive, GitHub LFS) is down or rate-limited.
- **fit: 2.0** (free, can carry richly-paired labeled datasets; minus: it's a delivery channel not a source, license is per-uploader and must be re-verified, no automation value for a daily pipeline, seeder-dependent).

## 7. Hugging Face Hub (dataset meta-index + loader) — new analysis

- **URL:** https://huggingface.co/datasets ; search docs https://huggingface.co/docs/hub/search
- **What it is.** ~500k+ public datasets with a filterable index and a uniform `datasets`/`huggingface_hub` loader. The single best **discovery + one-line-load** surface for multimodal fake-news corpora (Fakeddit, MMFakeBench, MiRAGeNews, VERITE mirrors, etc. all live here).
- **Pairing mechanism.** **Inherited**, but HF normalises it: many multimodal datasets expose an `image` column (decoded to PIL/bytes by the `Image` feature) **next to** a `text`/`caption`/`title` column in the same row — true paired records once loaded. The dataset's `features` schema names the exact columns.
- **Labels.** Inherited; HF's `task_categories` / `tags` filters surface labeled fake-news sets.
- **FR/EN.** Filterable by `language:fr` / `language:en`; French multimodal fake-news sets are sparse but discoverable.
- **Binding rights.** **Per-dataset** — declared in the dataset card's YAML `license:` field (SPDX string) and enforced by HF's gating ("you must agree to share your contact information"/usage protocol for some, e.g. MMFakeBench). HF Hub ToS governs the *platform*; the dataset license governs *reuse*. Always read the card's `license:` + any gating prompt; do not infer from the platform.
- **Free-tier limits.** Free, anonymous read for public/ungated datasets; gated ones need a free account + accepting terms (a manual step — flag for "automatable without manual steps" scoring). No hard request quota for normal use; large pulls are CDN-served.
- **Metadata fields.** Via `HfApi().list_datasets(filter=[...], search=..., sort='downloads', limit=...)` → `DatasetInfo`: `id, author, last_modified, downloads, likes, tags, card_data` (license, language, task_categories, size_categories, modalities). `load_dataset(id)` then yields the rows; `dataset.features` gives the column schema. Croissant metadata also exposed.
- **Extraction.** `pip install huggingface_hub datasets`; `list_datasets(filter=["fake-news"], ...)` to discover, `load_dataset("liuxuannan/MMFakeBench")` to pull. Fully scriptable except the one-time gating click.
- **Effort-to-first-record.** Very low for ungated; one extra manual accept for gated.
- **Pipeline fit.** **Bulk corpus + meta-index** (discovery and historical training data). Not a live news feed. Best operationalised as a *catalogued* set of pinned dataset IDs your pipeline re-pulls, not an open daily search.
- **fit: 3.5** (normalised paired image+text columns, license filter, FR/EN filter, one-line load, scriptable; minus: meta-index/bulk not a daily feed, gating adds a manual step, per-dataset license must be checked).

## 8. Google Dataset Search — new analysis

- **URL:** https://datasetsearch.research.google.com
- **What it is.** A meta-search engine indexing dataset pages across the web that publish schema.org/Dataset structured data. **Discovery only** — it points you to a host (Zenodo/Kaggle/HF/figshare/university), it serves no data itself.
- **Pairing mechanism.** n/a (whatever the landed dataset offers).
- **Labels.** n/a.
- **FR/EN.** Multilingual UI and index; surfaces French-hosted datasets.
- **Binding rights.** None of its own; relies on each dataset's schema.org `license` field, which Dataset Search exposes as a **license filter** (Creative Commons / public-domain / commercial-allowed). The binding license is on the destination page — verify there.
- **Free-tier limits.** Free, web UI. **No official API** (the schema.org-based index is not exposed as a query endpoint), so programmatic use means scripting the web UI — brittle and against the spirit of automated reuse.
- **Metadata fields.** Surfaces from schema.org: `name, description, license, temporalCoverage, spatialCoverage, distribution`/download formats, provider, `sameAs`.
- **Extraction.** Manual/browser discovery; filter by data-type (image/text/tabular) and license, then go to the host and download there.
- **Effort-to-first-record.** Low to *discover*; the actual fetch happens on the host.
- **Pipeline fit.** **Discovery only** — a research step, not an automated pipeline component. Use it once to find candidate datasets, then wire the host (HF/Zenodo/Kaggle) into the pipeline.
- **fit: 1.5** (excellent free FR/EN discovery with license + datatype filters; minus: no API, serves no data, zero automation value, no pairing/labels of its own).

## 9. Kaggle Datasets — new analysis

- **URL:** https://www.kaggle.com/datasets ; API docs https://www.kaggle.com/docs/api
- **What it is.** Hosted datasets with a CLI/Python API. Carries the most-used mirrors of our target corpora — e.g. `vanshikavmittal/fakeddit-dataset` (Fakeddit text+image), `mdepak/fakenewsnet`, and many fake-news collections.
- **Pairing mechanism.** **Inherited** per dataset (Fakeddit mirror keeps `image_url` + the JPEG image folder; you join on the id/filename).
- **Labels.** Inherited (Fakeddit's 2/3/6-way labels travel with the mirror).
- **FR/EN.** Inherited; predominantly EN, some FR.
- **Binding rights.** **Per-dataset license** shown on each dataset page (CC0/CC-BY/CC-BY-SA/"Other"/unknown) + Kaggle's site ToS. Many community mirrors declare "Unknown" or "Other" license — treat those as unverified and fall back to the upstream original's terms. Judge on the dataset's stated license, not Kaggle's platform ToS.
- **Free-tier limits.** Free with a (free) account; API needs a `kaggle.json` token (`~/.kaggle/kaggle.json`) — i.e. **authenticated**, which the task's "public, unauthenticated checks" rule means I did not exercise, but it's a free token, not a paid key. `kagglehub` is the modern Python entry; legacy `kaggle` CLI still works.
- **Metadata fields.** API/`DatasetInfo`: `ref, title, subtitle, creatorName, totalBytes, lastUpdated, downloadCount, voteCount, licenseName, tags, usabilityRating`.
- **Extraction.** `kaggle datasets download -d <owner>/<slug>` or `kagglehub.dataset_download(...)`; unzip and process.
- **Effort-to-first-record.** Low once the free token is set (a one-time manual account+token step → counts against "automatable without manual steps").
- **Pipeline fit.** **Bulk corpus + meta-index.** Not a live feed. Best as pinned dataset slugs the pipeline re-pulls.
- **fit: 3.0** (carries fully-paired labeled mirrors like Fakeddit, scriptable download, free; minus: requires a free token = manual setup step, per-dataset license often "Unknown" on mirrors, bulk not daily-feed).
- **Datasets worth naming individually on Kaggle:** `vanshikavmittal/fakeddit-dataset` (Fakeddit, text+image, 2/3/6-way) — note its usage restriction ("only use the `6_way_label` and `clean_title` columns … not additional paired text/image data" appears on some mirrors — read the specific mirror's rules); `mdepak/fakenewsnet` (FakeNewsNet index); `emineyetm/fake-news-detection-datasets` (text-heavy, weak multimodal).

## 10. Zenodo — new analysis (meta-index / repository)

- **URL:** https://zenodo.org ; API https://developers.zenodo.org
- **What it is.** CERN+OpenAIRE open research repository; canonical DOI host for many published fake-news/multimodal datasets and their image archives.
- **Pairing mechanism.** Inherited per record.
- **Labels.** Inherited.
- **FR/EN.** Multilingual; French research datasets present.
- **Binding rights.** **Mandatory `license` metadata field per record** (must be an Open Definition license; defaults `cc-zero` for datasets, `cc-by` otherwise). This makes Zenodo unusually clean for rights — the binding license is structured and queryable, not buried in prose. Verify per record.
- **Free-tier limits.** Free REST API, no auth needed for public search/download. Rate limits: **guest 60 req/min, 2000 req/hour; authenticated 100 req/min, 5000 req/hour; search endpoint 30 req/min** (`X-RateLimit-*` headers). Anonymous page size ≤25 (100 authenticated).
- **Metadata fields.** `GET /api/records/?q=...&size=...`: per record `metadata.{title, creators, publication_date, license, access_right, keywords, resource_type}`, `files[].{key, links.self (download_url), size, checksum}`, `doi`.
- **Extraction.** `requests` against `/api/records/` with a `q=` Elasticsearch query (e.g. `q=multimodal AND "fake news"`), filter by `type=dataset` and `license`; download via each file's `links.self`. Fully scriptable, no key.
- **Effort-to-first-record.** Very low (no auth, clean JSON).
- **Pipeline fit.** **Bulk corpus + meta-index** with a *proper* API (unlike Google Dataset Search). Good automated discovery/fetch for published datasets; not a news feed.
- **fit: 2.5** (no-auth REST API, mandatory structured license, FR/EN, scriptable discovery+download; minus: meta-index/bulk not a daily feed, pairing/labels inherited and variable).
- **new:** true (not in 02-data-sources.md).

## 11. figshare — new analysis (meta-index / repository)

- **URL:** https://figshare.com ; API https://docs.figshare.com
- **What it is.** General research-output repository (Springer Nature-affiliated); hosts dataset deposits incl. fake-news image+text sets (e.g. the figshare "Image and Text Fake News Detection Dataset").
- **Pairing mechanism.** Inherited per article/deposit.
- **Labels.** Inherited.
- **FR/EN.** Mixed; mostly EN.
- **Binding rights.** Per-deposit license returned in article metadata (`license` object); verify per record. figshare API ToS: HTTPS-only, responsible-use.
- **Free-tier limits.** Public search/download **need no auth**. **No automatic rate limiting**, but figshare asks clients to stay **≤1 request/second** and reserves the right to throttle/block abuse.
- **Metadata fields.** `POST /v2/articles/search` (+ `GET /v2/articles/{id}`): `title, authors, doi, license, published_date, files[].{name, download_url, size}, custom_fields, tags`.
- **Extraction.** `requests` to `/v2/articles/search` (filter/search/sort/paginate), then GET each file's `download_url`. No key for public items.
- **Effort-to-first-record.** Very low.
- **Pipeline fit.** **Bulk corpus + meta-index** with a real REST API; not a feed.
- **fit: 2.0** (no-auth REST search+download, license in metadata; minus: smaller/less curated for our topic than Zenodo/HF, bulk not feed, pairing inherited).
- **new:** true.

## 12. IEEE DataPort — new analysis (meta-index / repository)

- **URL:** https://ieee-dataport.org
- **What it is.** IEEE's dataset repository; hosts several **directly on-topic** sets, e.g. "Multimodal fake news datasets" (2025) and "Multimodal Fake News Dataset Weibo23" (2023).
- **Pairing mechanism.** Inherited per dataset.
- **Labels.** Inherited (the Weibo23 / multimodal sets carry fake/real labels).
- **FR/EN.** Mixed; the named on-topic sets skew EN/ZH.
- **Binding rights.** _"Almost all IEEE DataPort datasets have a CC-BY license."_ **But access tier ≠ license:** the two on-topic multimodal sets above are **"Standard" (subscription-required)**, not "Open Access." Only datasets explicitly marked **Open Access** are free to any registered user. Individual subscription is free for IEEE Society members, else **$40/month** — i.e. the most interesting items here sit behind a paywall/membership, which fails the "free for research without account/payment" preference.
- **Free-tier limits.** Open Access subset free with a free account; Standard subset paywalled (free only via IEEE membership).
- **Metadata fields.** Dataset page: title, authors, DOI, license (mostly CC-BY), access type (Open Access vs Standard), files, description.
- **Extraction.** Browser download for Open Access; subscription/login for Standard. No clean public bulk API.
- **Effort-to-first-record.** Low for Open Access; blocked/paywalled for the headline multimodal sets.
- **Pipeline fit.** **Bulk corpus / meta-index**, partly paywalled; not a feed.
- **fit: 1.5** (on-topic labeled multimodal sets exist, mostly CC-BY; minus: the best ones are subscription-gated, requires account, no automation API, bulk not feed).
- **new:** true.

## 13. AWS Open Data Registry — new analysis (meta-index over S3)

- **URL:** https://registry.opendata.aws
- **What it is.** A catalogue of large public datasets hosted free on AWS S3 under the Open Data Sponsorship Program — including **Common Crawl** and the **`CC-News-En`** English news corpus.
- **Pairing mechanism.** n/a (meta-index); inherited from each S3 dataset (for CC-NEWS, DIY HTML parsing as in §4).
- **Labels.** Inherited (mostly none for news corpora).
- **FR/EN.** Per dataset (`CC-News-En` is EN-only; full CC-NEWS is multilingual incl. FR).
- **Binding rights.** Per-dataset license stated on each registry entry (CC's own ToU for Common Crawl — see §4 caveats). Registry itself adds no rights.
- **Free-tier limits.** S3 hosting free; **2025: unsigned S3 access to `s3://commoncrawl/` disabled** — use HTTPS (`data.commoncrawl.org`) or CloudFront for unauthenticated reads; in-AWS processing avoids egress, downloading out incurs none for sponsored buckets via the public endpoints.
- **Metadata fields.** Registry YAML per dataset: `Name, Description, Documentation, License, Resources[] (S3 ARN, region), Tags`.
- **Extraction.** Browse/`registry.opendata.aws` to find a bucket, then `aws s3 cp` (authenticated) or HTTPS/CloudFront GET; process WARC/files as that dataset requires.
- **Effort-to-first-record.** Medium (find bucket → auth/HTTPS → process the dataset's format).
- **Pipeline fit.** **Discovery + bulk** (it's the front door to CC-NEWS and similar). Not a feed of its own.
- **fit: 2.0** (free discovery of large FR/EN-bearing S3 corpora incl. CC-NEWS; minus: meta-index only, pairing/labels inherited, 2025 unsigned-S3 removal, bulk not feed).
- **new:** true.

---

## Synthesis for OC12

**For the AUTOMATED daily pipeline (Step 1/Airflow ETL spine):** GDELT is the standout in this whole category. **GDELT GKG 2.1** (`V2.1SHARINGIMAGE` per article row, free, no key, 15-min cadence, native French) is the cleanest free FR-capable text-reference+image daily feed; **GDELT DOC 2.0 API** (image-content queryable, JSON) is the best *targeted* companion; **VGKG 2.0** is a visual-features enrichment side-feed. None carry veracity labels — pair them with a fact-check feed (separate category) for weak labels.

**For bulk historical training data:** the meta-indexes — **Hugging Face Hub** (best: normalised paired `image`+`text` columns, license/lang filters, one-line load), **Kaggle** (best Fakeddit mirror), **Zenodo** (cleanest API + mandatory structured license) — are where the actual labeled multimodal corpora live. **Common Crawl CC-NEWS** and **Internet Archive/Wayback** are heavy DIY-pairing bulk sources; Wayback's real value is as the **label-bridge** that fetches the archived fake page behind a fact-check verdict.

**Rights flags to carry forward:** (1) Common Crawl ToU **explicitly names ML/LLM use** in its indemnification clause and licenses only the *service*, not the content — do not call it a clean license. (2) GDELT/VGKG image fields are **third-party publisher URLs**; GDELT's free grant covers its metadata, not the images — cache + record provenance. (3) IEEE DataPort's best multimodal sets are **subscription-gated**, not Open Access. (4) Academic Torrents / Kaggle mirror licenses are **per-uploader and frequently "Unknown"** — re-verify against the upstream original.

## Sources
- GDELT terms: https://www.gdeltproject.org/about.html
- GDELT data/download: https://www.gdeltproject.org/data.html
- GDELT 2.0 realtime (lastupdate URLs): https://blog.gdeltproject.org/gdelt-2-0-our-global-world-in-realtime/
- GDELT GKG 2.1 codebook (image fields): http://data.gdeltproject.org/documentation/GDELT-Global_Knowledge_Graph_Codebook-V2.1.pdf
- GKG 2.0 article metadata fields: https://blog.gdeltproject.org/new-gkg-2-0-article-metadata-fields/
- VGKG 2.0: https://blog.gdeltproject.org/vgkg-2-0-released/
- GDELT DOC 2.0 API: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
- GDELT DOC Gallery mode: https://blog.gdeltproject.org/gallery-mode-now-available-doc-2-0-api/
- GDELT Translingual (FR coverage): https://blog.gdeltproject.org/gdelt-translingual-translating-the-planet/
- Common Crawl ToU: https://commoncrawl.org/terms-of-use
- Common Crawl news crawl: https://commoncrawl.org/news-crawl
- Common Crawl CloudFront/S3 access change: https://commoncrawl.org/blog/introducing-cloudfront-access-to-common-crawl-data
- Common Crawl on AWS ODR: https://registry.opendata.aws/commoncrawl/
- Internet Archive Terms: https://archive.org/about/terms
- Wayback APIs: https://archive.org/help/wayback_api.php
- Wayback CDX server: https://github.com/internetarchive/wayback/blob/master/wayback-cdx-server/README.md
- Academic Torrents (re3data): https://www.re3data.org/repository/r3d100011043
- Hugging Face dataset search: https://huggingface.co/docs/hub/search
- huggingface_hub list_datasets: https://huggingface.co/docs/huggingface_hub/guides/search
- Google Dataset Search help: https://datasetsearch.research.google.com/help
- Kaggle API docs: https://www.kaggle.com/docs/api
- Kaggle Fakeddit dataset: https://www.kaggle.com/datasets/vanshikavmittal/fakeddit-dataset
- Zenodo developers API: https://developers.zenodo.org/
- Zenodo licenses: https://help.zenodo.org/docs/deposit/describe-records/licenses/
- figshare API: https://docs.figshare.com/
- IEEE DataPort multimodal fake news: https://ieee-dataport.org/documents/multimodal-fake-news-datasets
- IEEE DataPort subscribe: https://ieee-dataport.org/subscribe
- AWS Open Data Registry: https://registry.opendata.aws/
